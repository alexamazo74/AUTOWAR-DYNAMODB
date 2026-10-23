"""
Complete Best Practice Evaluations for Performance Efficiency Pillar - All 32 BPs
Evaluaciones reales (solo lectura) contra APIs de AWS siguiendo el patrón del evaluador de Security.

Cada función pública tiene la firma evaluate_perfNN_bpMM(session, handle_error_func) y:
- Realiza llamadas boto3 de SOLO LECTURA (describe/list/get).
- Captura ClientError por BP y delega en handle_error_func(bp_id, error) -> PENDING_REVIEW.
- Devuelve NOT_APPLICABLE cuando no hay recursos del tipo evaluado.
- Nunca marca COMPLIANT por ausencia de recursos ni por excepción.

Convención de estados:
- COMPLIANT: solo cuando la evidencia real demuestra cumplimiento.
- NON_COMPLIANT: cuando la evidencia demuestra incumplimiento.
- NOT_APPLICABLE: no hay recursos del tipo evaluado (severity LOW).
- PENDING_REVIEW: fallo por permisos/excepción, o BP legítimamente no detectable vía API.
"""

from datetime import datetime, timedelta
from botocore.exceptions import ClientError
from typing import Dict, Any, List, Optional
import importlib.util
import os

# Load bp_descriptions dynamically to avoid import conflicts
bp_desc_path = os.path.join(os.path.dirname(__file__), 'bp_descriptions.py')
spec = importlib.util.spec_from_file_location("performance_bp_descriptions_all", bp_desc_path)
bp_desc_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bp_desc_module)
PERFORMANCE_BP_DESCRIPTIONS = bp_desc_module.PERFORMANCE_BP_DESCRIPTIONS


# ============================================================================
# Constructores de resultados y utilidades compartidas
# ============================================================================

def _result(bp_id: str, status: str, severity: str, finding: str,
            evidence: str, remediation: str, risk: str) -> Dict[str, Any]:
    """Construye el dict estándar de un hallazgo con las 8 claves requeridas."""
    return {
        'bp': bp_id,
        'description': PERFORMANCE_BP_DESCRIPTIONS.get(bp_id, ''),
        'status': status,
        'severity': severity,
        'finding': finding,
        'evidence': evidence,
        'remediation': remediation,
        'risk': risk
    }


def _na(bp_id: str, resource_label: str) -> Dict[str, Any]:
    """Resultado NOT_APPLICABLE: no hay recursos del tipo evaluado."""
    return _result(
        bp_id,
        'NOT_APPLICABLE',
        'LOW',
        f'No aplica: no hay recursos de tipo {resource_label}',
        f'No se detectaron recursos {resource_label} en la región evaluada',
        'No aplica en el entorno actual',
        'No aplica'
    )


def _pending(bp_id: str, note: str) -> Dict[str, Any]:
    """Resultado PENDING_REVIEW para BPs legítimamente no detectables vía API."""
    return _result(
        bp_id,
        'PENDING_REVIEW',
        'MEDIUM',
        'Requiere revisión manual: no es detectable automáticamente vía API',
        note,
        'Revisar manualmente según la guía AWS Well-Architected',
        'No se pudo determinar automáticamente'
    )


# Familias de instancias EC2 de generación antigua (evitar) y modernas/Graviton.
_LEGACY_EC2_PREFIXES = ('t2', 'm3', 'm4', 'c3', 'c4', 'r3', 'r4', 'i2', 'm1', 'm2', 'c1')
_ACCELERATOR_PREFIXES = ('p2', 'p3', 'p4', 'p5', 'g3', 'g4', 'g5', 'g6', 'inf1', 'inf2',
                         'trn1', 'trn2', 'dl1', 'dl2', 'vt1', 'f1')
_OBSOLETE_LAMBDA_RUNTIMES = (
    'python2.7', 'python3.6', 'python3.7', 'python3.8',
    'nodejs', 'nodejs4.3', 'nodejs6.10', 'nodejs8.10', 'nodejs10.x',
    'nodejs12.x', 'nodejs14.x', 'nodejs16.x',
    'go1.x', 'ruby2.5', 'ruby2.7', 'dotnetcore1.0', 'dotnetcore2.0',
    'dotnetcore2.1', 'dotnetcore3.1', 'java8', 'dotnet5.0'
)
_COST_TAG_KEYS = {'costcenter', 'cost-center', 'project', 'environment', 'env', 'owner', 'team'}


def _is_accelerated(instance_type: str) -> bool:
    family = instance_type.split('.')[0].lower()
    return any(family.startswith(p) for p in _ACCELERATOR_PREFIXES)


def _is_legacy(instance_type: str) -> bool:
    # El prefijo de familia es el bloque de letras+dígito, p.ej. 't2', 'm4', 'c5'
    family = instance_type.split('.')[0].lower()
    return family in _LEGACY_EC2_PREFIXES


def _is_graviton(instance_type: str) -> bool:
    # Las familias Graviton llevan 'g' justo tras el dígito de generación, p.ej. m6g, c7g, t4g, r6gd
    import re
    family = instance_type.split('.')[0].lower()
    return bool(re.match(r'^[a-z]+\d+g', family))


def _running_instances(session) -> List[Dict[str, Any]]:
    """Devuelve todas las instancias EC2 en estado running (paginado)."""
    ec2 = session.client('ec2')
    instances: List[Dict[str, Any]] = []
    paginator = ec2.get_paginator('describe_instances')
    for page in paginator.paginate():
        for reservation in page.get('Reservations', []):
            for inst in reservation.get('Instances', []):
                if inst.get('State', {}).get('Name') == 'running':
                    instances.append(inst)
    return instances


def _list_functions(session) -> List[Dict[str, Any]]:
    """Devuelve todas las funciones Lambda (paginado). El Runtime viene en el listado."""
    lambda_client = session.client('lambda')
    functions: List[Dict[str, Any]] = []
    paginator = lambda_client.get_paginator('list_functions')
    for page in paginator.paginate():
        functions.extend(page.get('Functions', []))
    return functions


def _list_active_stacks(session) -> List[Dict[str, Any]]:
    """Stacks de CloudFormation en estados activos (paginado)."""
    cfn = session.client('cloudformation')
    active_states = [
        'CREATE_COMPLETE', 'UPDATE_COMPLETE', 'UPDATE_ROLLBACK_COMPLETE',
        'IMPORT_COMPLETE', 'IMPORT_ROLLBACK_COMPLETE'
    ]
    stacks: List[Dict[str, Any]] = []
    paginator = cfn.get_paginator('list_stacks')
    for page in paginator.paginate(StackStatusFilter=active_states):
        stacks.extend(page.get('StackSummaries', []))
    return stacks


def _cpu_avg_14d(session, instance_id: str) -> Optional[float]:
    """Promedio de CPUUtilization de los últimos 14 días; None si no hay datos/permiso."""
    try:
        cw = session.client('cloudwatch')
        end = datetime.utcnow()
        start = end - timedelta(days=14)
        resp = cw.get_metric_statistics(
            Namespace='AWS/EC2',
            MetricName='CPUUtilization',
            Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
            StartTime=start,
            EndTime=end,
            Period=86400,
            Statistics=['Average']
        )
        datapoints = resp.get('Datapoints', [])
        if not datapoints:
            return None
        return sum(d['Average'] for d in datapoints) / len(datapoints)
    except ClientError:
        return None


def _describe_alarms(session) -> List[Dict[str, Any]]:
    cw = session.client('cloudwatch')
    alarms: List[Dict[str, Any]] = []
    paginator = cw.get_paginator('describe_alarms')
    for page in paginator.paginate():
        alarms.extend(page.get('MetricAlarms', []))
    return alarms


# ============================================================================
# PERF01 - Selección de recursos (7 BPs)
# ============================================================================

def evaluate_perf01_bp01(session, handle_error_func) -> Dict[str, Any]:
    """PERF01-BP01: Entender y usar los servicios disponibles (diversidad de tipos)."""
    bp_id = 'PERF01-BP01'
    try:
        instances = _running_instances(session)
        if not instances:
            return _na(bp_id, 'instancias EC2')
        instance_types = sorted({i['InstanceType'] for i in instances})
        evidence = f'{len(instance_types)} tipos de instancia distintos: {", ".join(instance_types[:10])}'
        if len(instance_types) > 5:
            return _result(bp_id, 'COMPLIANT', 'LOW',
                           'Se usa una diversidad amplia de tipos de instancia adecuados al workload',
                           evidence, 'Estado actual cumple', 'Bajo riesgo')
        return _result(bp_id, 'NON_COMPLIANT', 'MEDIUM',
                       'Diversidad limitada de tipos de instancia',
                       evidence,
                       'Evaluar tipos de instancia específicos por workload (cómputo, memoria, almacenamiento)',
                       'Rendimiento subóptimo por no ajustar el tipo de recurso al workload')
    except ClientError as e:
        return handle_error_func(bp_id, e)


def evaluate_perf01_bp02(session, handle_error_func) -> Dict[str, Any]:
    """PERF01-BP02: Usar guía del proveedor/partner (proxy: IaC / plantillas gestionadas)."""
    bp_id = 'PERF01-BP02'
    try:
        stacks = _list_active_stacks(session)
        if stacks:
            return _result(bp_id, 'COMPLIANT', 'LOW',
                           'Uso de plantillas/guía gestionada detectado (CloudFormation)',
                           f'{len(stacks)} stacks de CloudFormation activos',
                           'Estado actual cumple', 'Bajo riesgo')
        return _pending(bp_id,
                        'No se detectó IaC (CloudFormation). El uso de guía del proveedor/partner es '
                        'una decisión organizacional solo parcialmente detectable vía API')
    except ClientError as e:
        return handle_error_func(bp_id, e)


def evaluate_perf01_bp03(session, handle_error_func) -> Dict[str, Any]:
    """PERF01-BP03: Considerar el costo en las decisiones (proxy: tags de costo)."""
    bp_id = 'PERF01-BP03'
    try:
        instances = _running_instances(session)
        if not instances:
            return _na(bp_id, 'instancias EC2')
        tagged = 0
        for inst in instances:
            keys = {t['Key'].lower() for t in inst.get('Tags', [])}
            if keys & _COST_TAG_KEYS:
                tagged += 1
        ratio = tagged / len(instances)
        evidence = f'{tagged} de {len(instances)} instancias con tags de costo/propiedad'
        if ratio >= 0.5:
            return _result(bp_id, 'COMPLIANT', 'LOW',
                           'El costo se refleja en la gestión mediante etiquetado de recursos',
                           evidence, 'Estado actual cumple', 'Bajo riesgo')
        return _result(bp_id, 'NON_COMPLIANT', 'MEDIUM',
                       'Instancias sin etiquetado de costo suficiente',
                       evidence,
                       'Etiquetar recursos con CostCenter/Project/Environment para incorporar el costo en decisiones',
                       'Decisiones de arquitectura sin visibilidad de costo')
    except ClientError as e:
        return handle_error_func(bp_id, e)


def evaluate_perf01_bp04(session, handle_error_func) -> Dict[str, Any]:
    """PERF01-BP04: Evaluar trade-offs (no detectable vía API)."""
    return _pending('PERF01-BP04',
                    'Decisión de arquitectura: evaluar trade-offs de rendimiento vs costo/complejidad. '
                    'No es detectable automáticamente vía API')


def evaluate_perf01_bp05(session, handle_error_func) -> Dict[str, Any]:
    """PERF01-BP05: Usar políticas y arquitecturas de referencia (IaC)."""
    bp_id = 'PERF01-BP05'
    try:
        stacks = _list_active_stacks(session)
        if stacks:
            return _result(bp_id, 'COMPLIANT', 'LOW',
                           'Infraestructura definida como código (enfoque reproducible)',
                           f'{len(stacks)} stacks de CloudFormation activos',
                           'Estado actual cumple', 'Bajo riesgo')
        return _result(bp_id, 'NON_COMPLIANT', 'MEDIUM',
                       'Sin IaC detectada; la infraestructura puede estar gestionada manualmente',
                       '0 stacks de CloudFormation activos',
                       'Adoptar IaC (CloudFormation/CDK/Terraform) y arquitecturas de referencia',
                       'Infraestructura manual difícil de reproducir y optimizar de forma consistente')
    except ClientError as e:
        return handle_error_func(bp_id, e)


def evaluate_perf01_bp06(session, handle_error_func) -> Dict[str, Any]:
    """PERF01-BP06: Usar benchmarking (no detectable vía API)."""
    return _pending('PERF01-BP06',
                    'El benchmarking de rendimiento no es detectable automáticamente vía API')


def evaluate_perf01_bp07(session, handle_error_func) -> Dict[str, Any]:
    """PERF01-BP07: Enfoque data-driven (proxy: generaciones modernas vs antiguas de EC2)."""
    bp_id = 'PERF01-BP07'
    try:
        instances = _running_instances(session)
        if not instances:
            return _na(bp_id, 'instancias EC2')
        legacy = sorted({i['InstanceType'] for i in instances if _is_legacy(i['InstanceType'])})
        if legacy:
            return _result(bp_id, 'NON_COMPLIANT', 'MEDIUM',
                           'Se detectaron instancias de generación antigua',
                           f'Tipos de generación antigua en uso: {", ".join(legacy[:10])}',
                           'Migrar a familias de generación actual (p.ej. Graviton m6g/c7g/t4g) basándose en métricas',
                           'Rendimiento y eficiencia subóptimos frente a generaciones actuales')
        return _result(bp_id, 'COMPLIANT', 'LOW',
                       'Todas las instancias usan generaciones actuales',
                       f'{len(instances)} instancias sin familias de generación antigua',
                       'Estado actual cumple', 'Bajo riesgo')
    except ClientError as e:
        return handle_error_func(bp_id, e)


# ============================================================================
# PERF02 - Solución de cómputo (6 BPs)
# ============================================================================

def evaluate_perf02_bp01(session, handle_error_func) -> Dict[str, Any]:
    """PERF02-BP01: Seleccionar las mejores opciones de cómputo (mezcla EC2/Lambda)."""
    bp_id = 'PERF02-BP01'
    try:
        instances = _running_instances(session)
        functions = _list_functions(session)
        has_ec2 = len(instances) > 0
        has_lambda = len(functions) > 0
        evidence = f'EC2 running: {len(instances)} | Funciones Lambda: {len(functions)}'
        if has_ec2 and has_lambda:
            return _result(bp_id, 'COMPLIANT', 'LOW',
                           'Se usan múltiples opciones de cómputo (EC2 y Lambda)',
                           evidence, 'Estado actual cumple', 'Bajo riesgo')
        if has_ec2 or has_lambda:
            return _result(bp_id, 'NON_COMPLIANT', 'MEDIUM',
                           'Única opción de cómputo en uso',
                           evidence,
                           'Evaluar serverless/contenedores (Lambda, Fargate, ECS/EKS) según el patrón del workload',
                           'Flexibilidad y eficiencia limitadas al no ajustar el modelo de cómputo al workload')
        return _na(bp_id, 'recursos de cómputo (EC2/Lambda)')
    except ClientError as e:
        return handle_error_func(bp_id, e)


def evaluate_perf02_bp02(session, handle_error_func) -> Dict[str, Any]:
    """PERF02-BP02: Entender configuración/features disponibles (Graviton / Lambda arm64)."""
    bp_id = 'PERF02-BP02'
    try:
        instances = _running_instances(session)
        functions = _list_functions(session)
        if not instances and not functions:
            return _na(bp_id, 'recursos de cómputo (EC2/Lambda)')
        graviton = [i['InstanceType'] for i in instances if _is_graviton(i['InstanceType'])]
        arm_lambdas = [f['FunctionName'] for f in functions if 'arm64' in f.get('Architectures', [])]
        evidence = (f'Instancias Graviton: {len(graviton)} | '
                    f'Funciones Lambda arm64: {len(arm_lambdas)}')
        if graviton or arm_lambdas:
            return _result(bp_id, 'COMPLIANT', 'LOW',
                           'Se aprovechan features modernas de cómputo (Graviton/arm64)',
                           evidence, 'Estado actual cumple', 'Bajo riesgo')
        return _result(bp_id, 'NON_COMPLIANT', 'MEDIUM',
                       'No se detecta uso de features modernas de cómputo',
                       evidence,
                       'Evaluar procesadores Graviton (EC2) y arquitectura arm64 (Lambda) para mejor relación precio/rendimiento',
                       'Se dejan de aprovechar mejoras de eficiencia y rendimiento disponibles')
    except ClientError as e:
        return handle_error_func(bp_id, e)


def evaluate_perf02_bp03(session, handle_error_func) -> Dict[str, Any]:
    """PERF02-BP03: Recolectar métricas de cómputo (alarmas CloudWatch sobre cómputo)."""
    bp_id = 'PERF02-BP03'
    try:
        instances = _running_instances(session)
        functions = _list_functions(session)
        if not instances and not functions:
            return _na(bp_id, 'recursos de cómputo (EC2/Lambda)')
        alarms = _describe_alarms(session)
        compute_alarms = [a for a in alarms
                          if a.get('Namespace') in ('AWS/EC2', 'AWS/Lambda')
                          or a.get('MetricName') in ('CPUUtilization', 'Errors', 'Duration', 'Throttles')]
        evidence = f'Alarmas de cómputo detectadas: {len(compute_alarms)} de {len(alarms)} alarmas totales'
        if compute_alarms:
            return _result(bp_id, 'COMPLIANT', 'LOW',
                           'Se recolectan métricas de cómputo mediante alarmas de CloudWatch',
                           evidence, 'Estado actual cumple', 'Bajo riesgo')
        return _result(bp_id, 'NON_COMPLIANT', 'MEDIUM',
                       'Recursos de cómputo sin alarmas de métricas',
                       evidence,
                       'Crear alarmas de CloudWatch para CPUUtilization, Errors, Duration y Throttles',
                       'Sin visibilidad de métricas no es posible detectar degradaciones de rendimiento')
    except ClientError as e:
        return handle_error_func(bp_id, e)


def evaluate_perf02_bp04(session, handle_error_func) -> Dict[str, Any]:
    """PERF02-BP04: Right-sizing de cómputo (CPU promedio 14 días)."""
    bp_id = 'PERF02-BP04'
    try:
        instances = _running_instances(session)
        if not instances:
            return _na(bp_id, 'instancias EC2')
        underutilized = []
        datapoints_found = False
        for inst in instances:
            avg = _cpu_avg_14d(session, inst['InstanceId'])
            if avg is not None:
                datapoints_found = True
                if avg < 10.0:
                    underutilized.append((inst['InstanceId'], inst['InstanceType'], round(avg, 2)))
        if underutilized:
            detail = ', '.join(f'{iid} ({itype}): {cpu}%' for iid, itype, cpu in underutilized[:5])
            return _result(bp_id, 'NON_COMPLIANT', 'MEDIUM',
                           'Instancias subutilizadas (CPU promedio < 10% en 14 días)',
                           f'{len(underutilized)} instancia(s) subutilizada(s): {detail}',
                           'Right-sizing: reducir el tamaño o consolidar las instancias subutilizadas',
                           'Sobredimensionamiento genera costo y uso ineficiente de recursos')
        if datapoints_found:
            return _result(bp_id, 'COMPLIANT', 'LOW',
                           'Las instancias presentan utilización de CPU adecuada',
                           f'{len(instances)} instancias con CPU promedio >= 10% en 14 días',
                           'Estado actual cumple', 'Bajo riesgo')
        return _pending(bp_id,
                        'No hay suficientes datos de CloudWatch (CPUUtilization) para evaluar right-sizing')
    except ClientError as e:
        return handle_error_func(bp_id, e)


def evaluate_perf02_bp05(session, handle_error_func) -> Dict[str, Any]:
    """PERF02-BP05: Escalado dinámico (Auto Scaling Groups)."""
    bp_id = 'PERF02-BP05'
    try:
        instances = _running_instances(session)
        asg = session.client('autoscaling')
        groups: List[Dict[str, Any]] = []
        paginator = asg.get_paginator('describe_auto_scaling_groups')
        for page in paginator.paginate():
            groups.extend(page.get('AutoScalingGroups', []))
        active_groups = [g for g in groups if g.get('Instances')]
        evidence = f'Auto Scaling Groups con instancias: {len(active_groups)} | EC2 running: {len(instances)}'
        if active_groups:
            return _result(bp_id, 'COMPLIANT', 'LOW',
                           'Escalado dinámico mediante Auto Scaling en uso',
                           evidence, 'Estado actual cumple', 'Bajo riesgo')
        if instances:
            return _result(bp_id, 'NON_COMPLIANT', 'HIGH',
                           'Instancias EC2 en uso sin Auto Scaling',
                           evidence,
                           'Configurar Auto Scaling Groups con políticas de escalado dinámico',
                           'Sin escalado, el rendimiento se degrada ante picos y se desperdician recursos en valles')
        return _na(bp_id, 'instancias EC2')
    except ClientError as e:
        return handle_error_func(bp_id, e)


def evaluate_perf02_bp06(session, handle_error_func) -> Dict[str, Any]:
    """PERF02-BP06: Aceleradores de hardware (familias p/g/inf/trn/dl)."""
    bp_id = 'PERF02-BP06'
    try:
        instances = _running_instances(session)
        if not instances:
            return _na(bp_id, 'instancias EC2')
        accelerated = sorted({i['InstanceType'] for i in instances if _is_accelerated(i['InstanceType'])})
        if accelerated:
            return _result(bp_id, 'COMPLIANT', 'LOW',
                           'Se usan aceleradores de hardware optimizados',
                           f'Instancias con acelerador: {", ".join(accelerated)}',
                           'Estado actual cumple', 'Bajo riesgo')
        # No penalizar: no todos los workloads requieren aceleradores.
        return _na(bp_id, 'instancias con aceleradores de hardware (no requeridas por el workload actual)')
    except ClientError as e:
        return handle_error_func(bp_id, e)


# ============================================================================
# PERF03 - Almacenamiento y acceso a datos (5 BPs)
# ============================================================================

def _datastore_inventory(session) -> Dict[str, Any]:
    """Inventario de datastores (cada bloque captura su propio ClientError sin romper los demás)."""
    inv = {'s3': 0, 'dynamodb': [], 'rds': [], 'elasticache': 0, 'errors': []}
    try:
        buckets = session.client('s3').list_buckets().get('Buckets', [])
        inv['s3'] = len(buckets)
    except ClientError as e:
        inv['errors'].append(('s3', e))
    try:
        ddb = session.client('dynamodb')
        tables: List[str] = []
        paginator = ddb.get_paginator('list_tables')
        for page in paginator.paginate():
            tables.extend(page.get('TableNames', []))
        inv['dynamodb'] = tables
    except ClientError as e:
        inv['errors'].append(('dynamodb', e))
    try:
        rds = session.client('rds')
        dbs: List[Dict[str, Any]] = []
        paginator = rds.get_paginator('describe_db_instances')
        for page in paginator.paginate():
            dbs.extend(page.get('DBInstances', []))
        inv['rds'] = dbs
    except ClientError as e:
        inv['errors'].append(('rds', e))
    try:
        ec = session.client('elasticache')
        clusters = ec.describe_cache_clusters().get('CacheClusters', [])
        inv['elasticache'] = len(clusters)
    except ClientError as e:
        inv['errors'].append(('elasticache', e))
    return inv


def evaluate_perf03_bp01(session, handle_error_func) -> Dict[str, Any]:
    """PERF03-BP01: Usar datastores especializados (purpose-built)."""
    bp_id = 'PERF03-BP01'
    inv = _datastore_inventory(session)
    if inv['errors'] and not any([inv['s3'], inv['dynamodb'], inv['rds'], inv['elasticache']]):
        return handle_error_func(bp_id, inv['errors'][0][1])
    stores = []
    if inv['s3']:
        stores.append('S3')
    if inv['dynamodb']:
        stores.append('DynamoDB')
    if inv['rds']:
        stores.append('RDS')
    if inv['elasticache']:
        stores.append('ElastiCache')
    if not stores:
        return _na(bp_id, 'datastores (S3/DynamoDB/RDS/ElastiCache)')
    evidence = f'Tipos de datastore en uso: {", ".join(stores)}'
    if len(stores) >= 2:
        return _result(bp_id, 'COMPLIANT', 'LOW',
                       'Se usan múltiples datastores especializados',
                       evidence, 'Estado actual cumple', 'Bajo riesgo')
    return _result(bp_id, 'NON_COMPLIANT', 'MEDIUM',
                   'Único tipo de datastore en uso',
                   evidence,
                   'Evaluar stores especializados según el patrón de acceso (relacional, NoSQL, caché, objetos)',
                   'Un único tipo de store puede no ser óptimo para todos los patrones de acceso')


def evaluate_perf03_bp02(session, handle_error_func) -> Dict[str, Any]:
    """PERF03-BP02: Evaluar opciones de configuración del datastore (RDS/DynamoDB)."""
    bp_id = 'PERF03-BP02'
    try:
        rds = session.client('rds')
        dbs: List[Dict[str, Any]] = []
        paginator = rds.get_paginator('describe_db_instances')
        for page in paginator.paginate():
            dbs.extend(page.get('DBInstances', []))
        if dbs:
            suboptimal = []
            for db in dbs:
                storage = db.get('StorageType', '')
                if storage in ('gp2', 'standard'):
                    suboptimal.append(f"{db['DBInstanceIdentifier']} ({storage})")
                if not db.get('MultiAZ'):
                    suboptimal.append(f"{db['DBInstanceIdentifier']} (sin Multi-AZ)")
            evidence = (f'{len(dbs)} instancias RDS | '
                        f'Config subóptima: {", ".join(suboptimal[:5]) if suboptimal else "ninguna"}')
            if suboptimal:
                return _result(bp_id, 'NON_COMPLIANT', 'MEDIUM',
                               'Configuración de almacenamiento/durabilidad subóptima en RDS',
                               evidence,
                               'Migrar a gp3/io1 y habilitar Multi-AZ donde aplique',
                               'Almacenamiento gp2/standard y falta de Multi-AZ limitan rendimiento y disponibilidad')
            return _result(bp_id, 'COMPLIANT', 'LOW',
                           'RDS con almacenamiento moderno y Multi-AZ',
                           evidence, 'Estado actual cumple', 'Bajo riesgo')
        # Sin RDS: evaluar DynamoDB como evidencia de configuración consciente
        ddb = session.client('dynamodb')
        tables: List[str] = []
        paginator = ddb.get_paginator('list_tables')
        for page in paginator.paginate():
            tables.extend(page.get('TableNames', []))
        if tables:
            modes = []
            for name in tables[:20]:
                desc = ddb.describe_table(TableName=name)['Table']
                billing = desc.get('BillingModeSummary', {}).get('BillingMode', 'PROVISIONED')
                modes.append(f'{name}: {billing}')
            return _result(bp_id, 'COMPLIANT', 'LOW',
                           'Opciones de configuración de DynamoDB evaluadas (modo de capacidad)',
                           f'{len(tables)} tablas DynamoDB | ' + '; '.join(modes[:5]),
                           'Estado actual cumple', 'Bajo riesgo')
        return _na(bp_id, 'bases de datos (RDS/DynamoDB)')
    except ClientError as e:
        return handle_error_func(bp_id, e)


def evaluate_perf03_bp03(session, handle_error_func) -> Dict[str, Any]:
    """PERF03-BP03: Recolectar métricas del datastore (Performance Insights / alarmas)."""
    bp_id = 'PERF03-BP03'
    try:
        rds = session.client('rds')
        dbs: List[Dict[str, Any]] = []
        paginator = rds.get_paginator('describe_db_instances')
        for page in paginator.paginate():
            dbs.extend(page.get('DBInstances', []))
        ddb_tables: List[str] = []
        try:
            ddb = session.client('dynamodb')
            pag = ddb.get_paginator('list_tables')
            for page in pag.paginate():
                ddb_tables.extend(page.get('TableNames', []))
        except ClientError:
            pass
        if not dbs and not ddb_tables:
            return _na(bp_id, 'bases de datos (RDS/DynamoDB)')
        pi_enabled = [db['DBInstanceIdentifier'] for db in dbs if db.get('PerformanceInsightsEnabled')]
        alarms = _describe_alarms(session)
        db_alarms = [a for a in alarms if a.get('Namespace') in ('AWS/RDS', 'AWS/DynamoDB')]
        evidence = (f'RDS con Performance Insights: {len(pi_enabled)} | '
                    f'Alarmas de base de datos: {len(db_alarms)}')
        if pi_enabled or db_alarms:
            return _result(bp_id, 'COMPLIANT', 'LOW',
                           'Se recolectan métricas del datastore (Performance Insights/alarmas)',
                           evidence, 'Estado actual cumple', 'Bajo riesgo')
        return _result(bp_id, 'NON_COMPLIANT', 'MEDIUM',
                       'Datastores sin métricas de rendimiento',
                       evidence,
                       'Habilitar RDS Performance Insights y crear alarmas de CloudWatch para RDS/DynamoDB',
                       'Sin métricas no se pueden detectar cuellos de botella en la capa de datos')
    except ClientError as e:
        return handle_error_func(bp_id, e)


def evaluate_perf03_bp04(session, handle_error_func) -> Dict[str, Any]:
    """PERF03-BP04: Mejorar performance de queries (Performance Insights / caché)."""
    bp_id = 'PERF03-BP04'
    try:
        rds = session.client('rds')
        dbs: List[Dict[str, Any]] = []
        paginator = rds.get_paginator('describe_db_instances')
        for page in paginator.paginate():
            dbs.extend(page.get('DBInstances', []))
        try:
            cache_clusters = session.client('elasticache').describe_cache_clusters().get('CacheClusters', [])
        except ClientError:
            cache_clusters = []
        if not dbs:
            if cache_clusters:
                return _result(bp_id, 'COMPLIANT', 'LOW',
                               'Capa de caché presente para optimizar accesos a datos',
                               f'{len(cache_clusters)} clusters de ElastiCache',
                               'Estado actual cumple', 'Bajo riesgo')
            return _na(bp_id, 'bases de datos relacionales (RDS)')
        pi_enabled = [db['DBInstanceIdentifier'] for db in dbs if db.get('PerformanceInsightsEnabled')]
        evidence = (f'{len(dbs)} instancias RDS | con Performance Insights: {len(pi_enabled)} | '
                    f'ElastiCache: {len(cache_clusters)} clusters')
        if pi_enabled or cache_clusters:
            return _result(bp_id, 'COMPLIANT', 'LOW',
                           'Estrategias de optimización de queries presentes (Performance Insights/caché)',
                           evidence, 'Estado actual cumple', 'Bajo riesgo')
        return _result(bp_id, 'NON_COMPLIANT', 'MEDIUM',
                       'RDS sin Performance Insights ni capa de caché',
                       evidence,
                       'Habilitar Performance Insights para analizar y optimizar queries; evaluar ElastiCache/DAX',
                       'Queries no optimizadas degradan el rendimiento y aumentan la carga de la base de datos')
    except ClientError as e:
        return handle_error_func(bp_id, e)


def evaluate_perf03_bp05(session, handle_error_func) -> Dict[str, Any]:
    """PERF03-BP05: Caching (ElastiCache / replication groups)."""
    bp_id = 'PERF03-BP05'
    try:
        ec = session.client('elasticache')
        clusters = ec.describe_cache_clusters().get('CacheClusters', [])
        repl_groups = ec.describe_replication_groups().get('ReplicationGroups', [])
        if clusters or repl_groups:
            return _result(bp_id, 'COMPLIANT', 'LOW',
                           'Capa de caché implementada',
                           f'ElastiCache clusters: {len(clusters)} | Replication groups: {len(repl_groups)}',
                           'Estado actual cumple', 'Bajo riesgo')
        # Determinar si hay datastores que justifiquen caché
        try:
            rds = session.client('rds')
            has_rds = bool(rds.describe_db_instances().get('DBInstances', []))
        except ClientError:
            has_rds = False
        try:
            ddb = session.client('dynamodb')
            has_ddb = bool(ddb.list_tables().get('TableNames', []))
        except ClientError:
            has_ddb = False
        if has_rds or has_ddb:
            return _result(bp_id, 'NON_COMPLIANT', 'MEDIUM',
                           'Datastores presentes sin capa de caché',
                           f'RDS: {has_rds} | DynamoDB: {has_ddb} | ElastiCache: 0',
                           'Evaluar ElastiCache (Redis/Memcached) o DAX para reducir latencia y carga',
                           'Sin caché, accesos repetidos aumentan latencia y carga sobre la base de datos')
        return _na(bp_id, 'datastores que requieran caché')
    except ClientError as e:
        return handle_error_func(bp_id, e)


# ============================================================================
# PERF04 - Recursos de red (7 BPs)
# ============================================================================

def _list_vpcs(session) -> List[Dict[str, Any]]:
    return session.client('ec2').describe_vpcs().get('Vpcs', [])


def _list_load_balancers(session) -> List[Dict[str, Any]]:
    elbv2 = session.client('elbv2')
    lbs: List[Dict[str, Any]] = []
    paginator = elbv2.get_paginator('describe_load_balancers')
    for page in paginator.paginate():
        lbs.extend(page.get('LoadBalancers', []))
    return lbs


def _list_cloudfront(session) -> List[Dict[str, Any]]:
    cf = session.client('cloudfront')
    items: List[Dict[str, Any]] = []
    paginator = cf.get_paginator('list_distributions')
    for page in paginator.paginate():
        dist_list = page.get('DistributionList', {})
        items.extend(dist_list.get('Items', []) or [])
    return items


def evaluate_perf04_bp01(session, handle_error_func) -> Dict[str, Any]:
    """PERF04-BP01: Entender el impacto de la red (presencia de VPC)."""
    bp_id = 'PERF04-BP01'
    try:
        vpcs = _list_vpcs(session)
        if not vpcs:
            return _na(bp_id, 'VPC')
        return _result(bp_id, 'COMPLIANT', 'LOW',
                       'Topología de red definida mediante VPC',
                       f'{len(vpcs)} VPC(s) configurada(s)',
                       'Estado actual cumple', 'Bajo riesgo')
    except ClientError as e:
        return handle_error_func(bp_id, e)


def evaluate_perf04_bp02(session, handle_error_func) -> Dict[str, Any]:
    """PERF04-BP02: Evaluar features de red (VPC endpoints)."""
    bp_id = 'PERF04-BP02'
    try:
        vpcs = _list_vpcs(session)
        if not vpcs:
            return _na(bp_id, 'VPC')
        endpoints = session.client('ec2').describe_vpc_endpoints().get('VpcEndpoints', [])
        evidence = f'VPC endpoints: {len(endpoints)} | VPCs: {len(vpcs)}'
        if endpoints:
            return _result(bp_id, 'COMPLIANT', 'LOW',
                           'Uso de VPC endpoints (PrivateLink) para acceso optimizado a servicios AWS',
                           evidence, 'Estado actual cumple', 'Bajo riesgo')
        return _result(bp_id, 'NON_COMPLIANT', 'MEDIUM',
                       'Sin VPC endpoints: tráfico a servicios AWS vía Internet/NAT',
                       evidence,
                       'Crear VPC endpoints (gateway/interface) para S3, DynamoDB y servicios usados',
                       'Mayor latencia y costo de transferencia al no usar endpoints privados')
    except ClientError as e:
        return handle_error_func(bp_id, e)


def evaluate_perf04_bp03(session, handle_error_func) -> Dict[str, Any]:
    """PERF04-BP03: Conectividad dedicada/VPN (no penalizar si no se requiere híbrido)."""
    bp_id = 'PERF04-BP03'
    try:
        vpns = session.client('ec2').describe_vpn_connections().get('VpnConnections', [])
        active = [v for v in vpns if v.get('State') in ('available', 'pending')]
        if active:
            return _result(bp_id, 'COMPLIANT', 'LOW',
                           'Conectividad híbrida configurada (VPN)',
                           f'{len(active)} conexiones VPN activas',
                           'Estado actual cumple', 'Bajo riesgo')
        return _na(bp_id, 'conectividad híbrida (VPN/DX) no requerida por el workload actual')
    except ClientError as e:
        return handle_error_func(bp_id, e)


def evaluate_perf04_bp04(session, handle_error_func) -> Dict[str, Any]:
    """PERF04-BP04: Balanceo de carga (ELB con listeners)."""
    bp_id = 'PERF04-BP04'
    try:
        lbs = _list_load_balancers(session)
        instances = _running_instances(session)
        if lbs:
            elbv2 = session.client('elbv2')
            lbs_with_listeners = 0
            for lb in lbs:
                try:
                    listeners = elbv2.describe_listeners(LoadBalancerArn=lb['LoadBalancerArn']).get('Listeners', [])
                    if listeners:
                        lbs_with_listeners += 1
                except ClientError:
                    continue
            evidence = f'Load balancers: {len(lbs)} | con listeners activos: {lbs_with_listeners}'
            if lbs_with_listeners:
                return _result(bp_id, 'COMPLIANT', 'LOW',
                               'Balanceo de carga en uso (ELB con listeners)',
                               evidence, 'Estado actual cumple', 'Bajo riesgo')
            return _result(bp_id, 'NON_COMPLIANT', 'MEDIUM',
                           'Load balancers sin listeners activos',
                           evidence,
                           'Configurar listeners en los balanceadores o retirar los no utilizados',
                           'Balanceadores mal configurados no distribuyen tráfico correctamente')
        if len(instances) > 1:
            return _result(bp_id, 'NON_COMPLIANT', 'MEDIUM',
                           'Múltiples instancias EC2 sin balanceador de carga',
                           f'{len(instances)} instancias EC2 | 0 load balancers',
                           'Introducir un ALB/NLB para distribuir tráfico entre instancias',
                           'Sin balanceo, el tráfico no se distribuye y la disponibilidad/rendimiento se reduce')
        return _na(bp_id, 'balanceadores de carga (una sola instancia o ninguna)')
    except ClientError as e:
        return handle_error_func(bp_id, e)


def evaluate_perf04_bp05(session, handle_error_func) -> Dict[str, Any]:
    """PERF04-BP05: Protocolos de red (proxy: CloudFront/ALB con HTTP/2-3)."""
    bp_id = 'PERF04-BP05'
    try:
        try:
            distributions = _list_cloudfront(session)
        except ClientError:
            distributions = []
        lbs = _list_load_balancers(session)
        app_lbs = [lb for lb in lbs if lb.get('Type') == 'application']
        if distributions or app_lbs:
            return _result(bp_id, 'COMPLIANT', 'LOW',
                           'Protocolos modernos disponibles vía CloudFront/ALB (HTTP/2, TLS moderno)',
                           f'CloudFront: {len(distributions)} | Application LBs: {len(app_lbs)}',
                           'Estado actual cumple', 'Bajo riesgo')
        return _pending(bp_id,
                        'La elección de protocolos de red no es completamente detectable vía API '
                        '(sin CloudFront ni ALB para inferirla)')
    except ClientError as e:
        return handle_error_func(bp_id, e)


def evaluate_perf04_bp06(session, handle_error_func) -> Dict[str, Any]:
    """PERF04-BP06: Ubicación del workload (multi-AZ + CDN)."""
    bp_id = 'PERF04-BP06'
    try:
        vpcs = _list_vpcs(session)
        if not vpcs:
            return _na(bp_id, 'VPC')
        subnets = session.client('ec2').describe_subnets().get('Subnets', [])
        azs = {s['AvailabilityZone'] for s in subnets}
        try:
            distributions = _list_cloudfront(session)
        except ClientError:
            distributions = []
        evidence = f'AZs con subnets: {len(azs)} ({", ".join(sorted(azs)[:6])}) | CloudFront: {len(distributions)}'
        if len(azs) >= 2 or distributions:
            return _result(bp_id, 'COMPLIANT', 'LOW',
                           'Ubicación optimizada (multi-AZ y/o CDN)',
                           evidence, 'Estado actual cumple', 'Bajo riesgo')
        return _result(bp_id, 'NON_COMPLIANT', 'MEDIUM',
                       'Despliegue en una sola AZ y sin CDN',
                       evidence,
                       'Distribuir subnets en múltiples AZ y evaluar CloudFront para contenido de borde',
                       'Una sola AZ limita disponibilidad; sin CDN aumenta la latencia para usuarios distribuidos')
    except ClientError as e:
        return handle_error_func(bp_id, e)


def evaluate_perf04_bp07(session, handle_error_func) -> Dict[str, Any]:
    """PERF04-BP07: Optimizar la red según métricas (alarmas de red)."""
    bp_id = 'PERF04-BP07'
    try:
        vpcs = _list_vpcs(session)
        lbs = _list_load_balancers(session)
        if not vpcs and not lbs:
            return _na(bp_id, 'recursos de red (VPC/ELB)')
        alarms = _describe_alarms(session)
        net_alarms = [a for a in alarms
                      if a.get('MetricName') in ('NetworkIn', 'NetworkOut', 'TargetResponseTime',
                                                 'ActiveConnectionCount', 'ProcessedBytes',
                                                 'RequestCount', 'Latency')
                      or a.get('Namespace') in ('AWS/ApplicationELB', 'AWS/NetworkELB', 'AWS/CloudFront')]
        evidence = f'Alarmas de red detectadas: {len(net_alarms)} de {len(alarms)} alarmas totales'
        if net_alarms:
            return _result(bp_id, 'COMPLIANT', 'LOW',
                           'La red se optimiza con base en métricas (alarmas de red)',
                           evidence, 'Estado actual cumple', 'Bajo riesgo')
        return _result(bp_id, 'NON_COMPLIANT', 'MEDIUM',
                       'Recursos de red sin alarmas de métricas',
                       evidence,
                       'Crear alarmas de CloudWatch para métricas de red (TargetResponseTime, NetworkIn/Out)',
                       'Sin métricas de red no es posible detectar ni optimizar cuellos de botella de latencia')
    except ClientError as e:
        return handle_error_func(bp_id, e)


# ============================================================================
# PERF05 - Evolución del workload (7 BPs)
# ============================================================================

def evaluate_perf05_bp01(session, handle_error_func) -> Dict[str, Any]:
    """PERF05-BP01: Establecer KPIs (dashboards de CloudWatch)."""
    bp_id = 'PERF05-BP01'
    try:
        cw = session.client('cloudwatch')
        dashboards: List[Dict[str, Any]] = []
        paginator = cw.get_paginator('list_dashboards')
        for page in paginator.paginate():
            dashboards.extend(page.get('DashboardEntries', []))
        if dashboards:
            return _result(bp_id, 'COMPLIANT', 'LOW',
                           'KPIs visualizados mediante dashboards de CloudWatch',
                           f'{len(dashboards)} dashboards de CloudWatch',
                           'Estado actual cumple', 'Bajo riesgo')
        return _result(bp_id, 'NON_COMPLIANT', 'MEDIUM',
                       'Sin dashboards de CloudWatch para KPIs de rendimiento',
                       '0 dashboards de CloudWatch',
                       'Crear dashboards de CloudWatch con los KPIs de rendimiento del workload',
                       'Sin KPIs visibles es difícil evaluar la evolución del rendimiento')
    except ClientError as e:
        return handle_error_func(bp_id, e)


def evaluate_perf05_bp02(session, handle_error_func) -> Dict[str, Any]:
    """PERF05-BP02: Usar soluciones de monitoreo (alarmas de CloudWatch)."""
    bp_id = 'PERF05-BP02'
    try:
        alarms = _describe_alarms(session)
        if alarms:
            return _result(bp_id, 'COMPLIANT', 'LOW',
                           'Monitoreo activo mediante alarmas de CloudWatch',
                           f'{len(alarms)} alarmas de CloudWatch',
                           'Estado actual cumple', 'Bajo riesgo')
        return _result(bp_id, 'NON_COMPLIANT', 'MEDIUM',
                       'Sin alarmas de CloudWatch configuradas',
                       '0 alarmas de CloudWatch',
                       'Configurar alarmas de CloudWatch para métricas clave del workload',
                       'Sin monitoreo no se detectan degradaciones de rendimiento de forma proactiva')
    except ClientError as e:
        return handle_error_func(bp_id, e)


def evaluate_perf05_bp03(session, handle_error_func) -> Dict[str, Any]:
    """PERF05-BP03: Proceso de mejora de rendimiento (no detectable vía API)."""
    return _pending('PERF05-BP03',
                    'El proceso organizacional de mejora de rendimiento no es detectable vía API')


def evaluate_perf05_bp04(session, handle_error_func) -> Dict[str, Any]:
    """PERF05-BP04: Load testing (no detectable vía API)."""
    return _pending('PERF05-BP04',
                    'Las pruebas de carga (load testing) no son detectables automáticamente vía API')


def evaluate_perf05_bp05(session, handle_error_func) -> Dict[str, Any]:
    """PERF05-BP05: Automatización para remediar (scaling policies / SSM)."""
    bp_id = 'PERF05-BP05'
    try:
        instances = _running_instances(session)
        asg = session.client('autoscaling')
        policies: List[Dict[str, Any]] = []
        paginator = asg.get_paginator('describe_policies')
        for page in paginator.paginate():
            policies.extend(page.get('ScalingPolicies', []))
        try:
            ssm_nodes = session.client('ssm').describe_instance_information().get('InstanceInformationList', [])
        except ClientError:
            ssm_nodes = []
        evidence = f'Políticas de escalado: {len(policies)} | Nodos gestionados por SSM: {len(ssm_nodes)}'
        if policies or ssm_nodes:
            return _result(bp_id, 'COMPLIANT', 'LOW',
                           'Automatización de remediación presente (escalado y/o gestión SSM)',
                           evidence, 'Estado actual cumple', 'Bajo riesgo')
        if instances:
            return _result(bp_id, 'NON_COMPLIANT', 'MEDIUM',
                           'Instancias EC2 sin automatización de remediación',
                           evidence,
                           'Configurar políticas de escalado y/o gestión automatizada con SSM',
                           'Sin automatización, la remediación es manual y lenta ante problemas de rendimiento')
        return _na(bp_id, 'instancias EC2')
    except ClientError as e:
        return handle_error_func(bp_id, e)


def evaluate_perf05_bp06(session, handle_error_func) -> Dict[str, Any]:
    """PERF05-BP06: Mantener actualizado (runtimes Lambda obsoletos / EC2 antiguas)."""
    bp_id = 'PERF05-BP06'
    try:
        functions = _list_functions(session)
        if functions:
            obsolete = [(f['FunctionName'], f.get('Runtime', ''))
                        for f in functions
                        if f.get('Runtime') and f['Runtime'].lower() in _OBSOLETE_LAMBDA_RUNTIMES]
            if obsolete:
                detail = ', '.join(f'{name} ({rt})' for name, rt in obsolete[:5])
                return _result(bp_id, 'NON_COMPLIANT', 'MEDIUM',
                               'Funciones Lambda con runtimes obsoletos',
                               f'{len(obsolete)} función(es) con runtime obsoleto: {detail}',
                               'Actualizar las funciones a runtimes soportados actualmente',
                               'Runtimes obsoletos pierden soporte, parches de seguridad y mejoras de rendimiento')
            return _result(bp_id, 'COMPLIANT', 'LOW',
                           'Funciones Lambda con runtimes actuales',
                           f'{len(functions)} funciones Lambda sin runtimes obsoletos',
                           'Estado actual cumple', 'Bajo riesgo')
        # Sin Lambda: usar EC2 de generación antigua como señal
        instances = _running_instances(session)
        if not instances:
            return _na(bp_id, 'recursos de cómputo (Lambda/EC2)')
        legacy = sorted({i['InstanceType'] for i in instances if _is_legacy(i['InstanceType'])})
        if legacy:
            return _result(bp_id, 'NON_COMPLIANT', 'MEDIUM',
                           'Instancias EC2 de generación antigua (no actualizadas)',
                           f'Tipos antiguos: {", ".join(legacy[:10])}',
                           'Migrar a generaciones actuales de instancias',
                           'Mantener componentes obsoletos reduce rendimiento y eficiencia')
        return _result(bp_id, 'COMPLIANT', 'LOW',
                       'Instancias EC2 en generaciones actuales',
                       f'{len(instances)} instancias sin familias de generación antigua',
                       'Estado actual cumple', 'Bajo riesgo')
    except ClientError as e:
        return handle_error_func(bp_id, e)


def evaluate_perf05_bp07(session, handle_error_func) -> Dict[str, Any]:
    """PERF05-BP07: Revisión periódica de métricas (dashboards + alarmas)."""
    bp_id = 'PERF05-BP07'
    try:
        cw = session.client('cloudwatch')
        dashboards: List[Dict[str, Any]] = []
        paginator = cw.get_paginator('list_dashboards')
        for page in paginator.paginate():
            dashboards.extend(page.get('DashboardEntries', []))
        alarms = _describe_alarms(session)
        evidence = f'Dashboards: {len(dashboards)} | Alarmas: {len(alarms)}'
        if dashboards and alarms:
            return _result(bp_id, 'COMPLIANT', 'LOW',
                           'Revisión periódica soportada por dashboards y alarmas',
                           evidence, 'Estado actual cumple', 'Bajo riesgo')
        if dashboards or alarms:
            return _pending(bp_id,
                            f'Observabilidad parcial para revisión periódica ({evidence}). '
                            'La cadencia de revisión es una práctica organizacional')
        return _result(bp_id, 'NON_COMPLIANT', 'MEDIUM',
                       'Sin dashboards ni alarmas para revisión periódica de métricas',
                       evidence,
                       'Crear dashboards y alarmas y establecer una cadencia de revisión periódica',
                       'Sin revisión de métricas, las oportunidades de mejora de rendimiento pasan desapercibidas')
    except ClientError as e:
        return handle_error_func(bp_id, e)
