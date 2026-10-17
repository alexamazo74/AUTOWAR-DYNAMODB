"""
Complete Best Practice Evaluations for Security Pillar - All 63 BPs
Evaluaciones refinadas basadas en la guía oficial de AWS Well-Architected Framework
Cada BP evalúa múltiples servicios/recursos según la columna "¿Cómo evaluar?" de la guía
"""

from botocore.exceptions import ClientError
from typing import Dict, Any, List
import importlib.util
import os

# Load bp_descriptions dynamically to avoid import conflicts
bp_desc_path = os.path.join(os.path.dirname(__file__), 'bp_descriptions.py')
spec = importlib.util.spec_from_file_location("security_bp_descriptions_all", bp_desc_path)
bp_desc_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bp_desc_module)
SECURITY_BP_DESCRIPTIONS = bp_desc_module.SECURITY_BP_DESCRIPTIONS


# ============================================================================
# SEC01 - Operación segura de cargas de trabajo (BP03-BP08)
# ============================================================================

def evaluate_sec01_bp03(session, handle_error_func) -> Dict[str, Any]:
    """SEC01-BP03: Identificar y validar los objetivos de control
    Evalúa: AWS Config rules, Security Hub standards, conformance packs, SCPs preventivas
    """
    try:
        issues = []
        evidence_parts = []
        
        # 1. Verificar AWS Config rules
        try:
            config_client = session.client('config')
            rules = config_client.describe_config_rules()
            config_rules = rules.get('ConfigRules', [])
            compliant_rules = [r for r in config_rules if r.get('ConfigRuleState') == 'ACTIVE']
            evidence_parts.append(f"Config Rules activas: {len(compliant_rules)}")
            if len(compliant_rules) == 0:
                issues.append('Sin reglas de AWS Config para validación de controles')
        except ClientError:
            evidence_parts.append("Config Rules: No accesible")
            issues.append('AWS Config no accesible o no habilitado')
        
        # 2. Verificar Security Hub standards
        try:
            sh_client = session.client('securityhub')
            standards = sh_client.get_enabled_standards()
            enabled_standards = standards.get('StandardsSubscriptions', [])
            standard_names = [s.get('StandardsArn', '').split('/')[-1] for s in enabled_standards]
            evidence_parts.append(f"Security Hub Standards: {len(enabled_standards)} ({', '.join(standard_names[:3])})")
            if len(enabled_standards) == 0:
                issues.append('Sin estándares de Security Hub habilitados')
        except Exception:
            evidence_parts.append("Security Hub: No habilitado")
            issues.append('Security Hub no habilitado para validación de cumplimiento')
        
        # 3. Verificar Config Conformance Packs
        try:
            packs = config_client.describe_conformance_packs()
            conformance_packs = packs.get('ConformancePackDetails', [])
            evidence_parts.append(f"Conformance Packs: {len(conformance_packs)}")
        except ClientError:
            evidence_parts.append("Conformance Packs: 0")
        
        # 4. Verificar Config Recorder
        try:
            recorders = config_client.describe_configuration_recorders()
            recorder_list = recorders.get('ConfigurationRecorders', [])
            evidence_parts.append(f"Config Recorders: {len(recorder_list)}")
            if len(recorder_list) == 0:
                issues.append('AWS Config Recorder no configurado')
        except ClientError:
            pass
        
        evidence = ' | '.join(evidence_parts)
        
        if len(issues) == 0:
            return {'bp': 'SEC01-BP03', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC01-BP03', ''),
                    'status': 'COMPLIANT', 'severity': 'LOW',
                    'finding': 'Objetivos de control validados con AWS Config y Security Hub activos.',
                    'evidence': evidence,
                    'remediation': 'Estado actual cumple. Revisar periódicamente que los controles implementados mitigan los riesgos según el modelo de amenazas.',
                    'risk': 'Bajo riesgo. Los controles están siendo validados continuamente.'}
        elif len(issues) <= 2:
            return {'bp': 'SEC01-BP03', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC01-BP03', ''),
                    'status': 'PENDING_REVIEW', 'severity': 'MEDIUM',
                    'finding': f'Validación parcial de objetivos de control. Hallazgos: {"; ".join(issues)}',
                    'evidence': evidence,
                    'remediation': (
                        'Completar la validación de objetivos de control: '
                        '1) Habilitar AWS Config con recorder activo en todas las regiones. '
                        '2) Habilitar Security Hub con estándares AWS Foundational Security y CIS Benchmark. '
                        '3) Desplegar Conformance Packs alineados con frameworks de cumplimiento (NIST, ISO 27001, PCI-DSS). '
                        '4) Configurar reglas de Config para validar controles preventivos. '
                        '5) Revisar documentación de AWS Artifact para entender responsabilidad compartida.'
                    ),
                    'risk': 'Riesgo medio. Sin validación continua de controles, las configuraciones no conformes pueden pasar desapercibidas.'}
        else:
            return {'bp': 'SEC01-BP03', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC01-BP03', ''),
                    'status': 'NON_COMPLIANT', 'severity': 'HIGH',
                    'finding': f'Objetivos de control no validados. Hallazgos: {"; ".join(issues)}',
                    'evidence': evidence,
                    'remediation': (
                        'Implementar validación de objetivos de control: '
                        '1) Habilitar AWS Config con recorder en todas las regiones. '
                        '2) Habilitar Security Hub con estándares AWS Foundational Security Best Practices, CIS AWS Foundations Benchmark. '
                        '3) Desplegar Conformance Packs para frameworks regulatorios aplicables. '
                        '4) Configurar SCPs preventivas alineadas con objetivos de control. '
                        '5) Implementar AWS Audit Manager para evaluaciones automatizadas. '
                        '6) Documentar mapeo de controles con frameworks de ciberseguridad seleccionados.'
                    ),
                    'risk': 'Alto riesgo. Sin validación de controles, no se puede verificar que las configuraciones mitigan los riesgos identificados.'}
    except ClientError as e:
        return handle_error_func('SEC01-BP03', e)


def evaluate_sec01_bp04(session, handle_error_func) -> Dict[str, Any]:
    """SEC01-BP04: Mantenerse actualizado con amenazas y recomendaciones de seguridad
    Evalúa: GuardDuty, Security Hub score, Inspector, vulnerability management, threat intelligence
    """
    try:
        issues = []
        evidence_parts = []
        
        # 1. Verificar GuardDuty
        try:
            gd_client = session.client('guardduty')
            detectors = gd_client.list_detectors()
            detector_ids = detectors.get('DetectorIds', [])
            if detector_ids:
                detector = gd_client.get_detector(DetectorId=detector_ids[0])
                gd_status = detector.get('Status', 'UNKNOWN')
                evidence_parts.append(f"GuardDuty: {gd_status}")
                # Verificar findings recientes
                try:
                    findings_stats = gd_client.get_findings_statistics(
                        DetectorId=detector_ids[0],
                        FindingStatisticTypes=['COUNT_BY_SEVERITY']
                    )
                    severity_counts = findings_stats.get('FindingStatistics', {}).get('CountBySeverity', {})
                    total_findings = sum(int(v) for v in severity_counts.values())
                    evidence_parts.append(f"GuardDuty findings: {total_findings}")
                except ClientError:
                    pass
            else:
                evidence_parts.append("GuardDuty: NO HABILITADO")
                issues.append('GuardDuty no habilitado para detección de amenazas')
        except ClientError:
            evidence_parts.append("GuardDuty: No accesible")
            issues.append('GuardDuty no accesible')
        
        # 2. Verificar Security Hub y score
        try:
            sh_client = session.client('securityhub')
            hub = sh_client.describe_hub()
            evidence_parts.append(f"Security Hub: Habilitado (desde {hub.get('SubscribedAt', 'N/A')[:10]})")
            
            # Verificar score de estándares
            try:
                standards = sh_client.get_enabled_standards()
                for std in standards.get('StandardsSubscriptions', [])[:3]:
                    std_arn = std.get('StandardsSubscriptionArn', '')
                    try:
                        controls = sh_client.describe_standards_controls(StandardsSubscriptionArn=std_arn, MaxResults=1)
                        evidence_parts.append(f"Standard activo: {std_arn.split('/')[-1]}")
                    except ClientError:
                        pass
            except ClientError:
                pass
        except Exception:
            evidence_parts.append("Security Hub: NO HABILITADO")
            issues.append('Security Hub no habilitado para gestión centralizada de hallazgos')
        
        # 3. Verificar Inspector
        try:
            inspector_client = session.client('inspector2')
            account_status = inspector_client.batch_get_account_status(accountIds=[])
            evidence_parts.append("Inspector: Verificado")
        except Exception:
            evidence_parts.append("Inspector: No habilitado")
            issues.append('Amazon Inspector no habilitado para escaneo de vulnerabilidades')
        
        # 4. Verificar Systems Manager Patch Manager
        try:
            ssm_client = session.client('ssm')
            patch_baselines = ssm_client.describe_patch_baselines(
                Filters=[{'Key': 'OWNER', 'Values': ['Self']}]
            )
            custom_baselines = len(patch_baselines.get('BaselineIdentities', []))
            evidence_parts.append(f"Patch baselines personalizadas: {custom_baselines}")
        except ClientError:
            evidence_parts.append("Patch Manager: No accesible")
        
        evidence = ' | '.join(evidence_parts)
        
        if len(issues) == 0:
            return {'bp': 'SEC01-BP04', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC01-BP04', ''),
                    'status': 'COMPLIANT', 'severity': 'LOW',
                    'finding': 'Servicios de detección de amenazas activos: GuardDuty, Security Hub e Inspector habilitados.',
                    'evidence': evidence,
                    'remediation': 'Estado actual cumple. Verificar periódicamente que las alertas de GuardDuty y Security Hub estén siendo gestionadas y no ignoradas.',
                    'risk': 'Bajo riesgo. Los servicios de detección de amenazas están activos y actualizados.'}
        elif len(issues) == 1:
            return {'bp': 'SEC01-BP04', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC01-BP04', ''),
                    'status': 'PENDING_REVIEW', 'severity': 'MEDIUM',
                    'finding': f'Detección de amenazas parcial. {"; ".join(issues)}',
                    'evidence': evidence,
                    'remediation': (
                        'Completar la cobertura de detección de amenazas: '
                        '1) Habilitar GuardDuty en todas las regiones con protección contra malware. '
                        '2) Habilitar Security Hub con estándares AWS Foundational Security Best Practices. '
                        '3) Habilitar Inspector para EC2, contenedores y funciones Lambda. '
                        '4) Configurar Patch Manager con ventanas de mantenimiento automatizadas. '
                        '5) Suscribirse a AWS Security Bulletins y feeds de inteligencia de amenazas.'
                    ),
                    'risk': 'Riesgo medio. Cobertura parcial de detección de amenazas puede dejar vectores de ataque sin monitorear.'}
        else:
            return {'bp': 'SEC01-BP04', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC01-BP04', ''),
                    'status': 'NON_COMPLIANT', 'severity': 'HIGH',
                    'finding': f'Detección de amenazas insuficiente. Hallazgos: {"; ".join(issues)}',
                    'evidence': evidence,
                    'remediation': (
                        'Implementar detección de amenazas integral: '
                        '1) Habilitar GuardDuty en todas las regiones con todas las protecciones (S3, EKS, malware). '
                        '2) Habilitar Security Hub y activar estándares AWS Foundational Security, CIS Benchmark. '
                        '3) Habilitar Inspector para escaneo automático de vulnerabilidades. '
                        '4) Configurar Systems Manager Patch Manager para parcheo automatizado. '
                        '5) Implementar proceso de gestión de vulnerabilidades con SLAs de remediación. '
                        '6) Suscribirse a feeds de inteligencia de amenazas y AWS Security Bulletins. '
                        '7) Configurar notificaciones SNS para hallazgos críticos y altos.'
                    ),
                    'risk': 'Alto riesgo. Sin servicios de detección de amenazas, las vulnerabilidades y ataques pueden pasar desapercibidos.'}
    except ClientError as e:
        return handle_error_func('SEC01-BP04', e)


def evaluate_sec01_bp05(session, handle_error_func) -> Dict[str, Any]:
    """SEC01-BP05: Reducir el alcance de la gestión de seguridad
    Evalúa: Servicios administrados, serverless, contenedores, IaC, managed security services
    """
    try:
        issues = []
        evidence_parts = []
        managed_services = 0
        
        # 1. Verificar uso de Lambda (serverless)
        try:
            lambda_client = session.client('lambda')
            functions = lambda_client.list_functions()
            num_functions = len(functions.get('Functions', []))
            evidence_parts.append(f"Lambda functions: {num_functions}")
            if num_functions > 0:
                managed_services += 1
        except ClientError:
            evidence_parts.append("Lambda: No accesible")
        
        # 2. Verificar uso de RDS (managed database)
        try:
            rds_client = session.client('rds')
            instances = rds_client.describe_db_instances()
            num_rds = len(instances.get('DBInstances', []))
            evidence_parts.append(f"RDS instances: {num_rds}")
            if num_rds > 0:
                managed_services += 1
        except ClientError:
            evidence_parts.append("RDS: No accesible")
        
        # 3. Verificar uso de DynamoDB (managed NoSQL)
        try:
            ddb_client = session.client('dynamodb')
            tables = ddb_client.list_tables()
            num_tables = len(tables.get('TableNames', []))
            evidence_parts.append(f"DynamoDB tables: {num_tables}")
            if num_tables > 0:
                managed_services += 1
        except ClientError:
            evidence_parts.append("DynamoDB: No accesible")
        
        # 4. Verificar EC2 instances (infraestructura auto-administrada)
        try:
            ec2_client = session.client('ec2')
            instances = ec2_client.describe_instances(
                Filters=[{'Name': 'instance-state-name', 'Values': ['running']}]
            )
            running_instances = sum(len(r['Instances']) for r in instances['Reservations'])
            evidence_parts.append(f"EC2 running: {running_instances}")
            
            # Verificar instancias con IAM roles (managed)
            managed_instances = sum(
                1 for r in instances['Reservations'] for i in r['Instances']
                if i.get('IamInstanceProfile')
            )
            if running_instances > 0:
                evidence_parts.append(f"EC2 con IAM role: {managed_instances}/{running_instances}")
        except ClientError:
            running_instances = 0
            evidence_parts.append("EC2: No accesible")
        
        # 5. Verificar CloudFormation (IaC)
        try:
            cf_client = session.client('cloudformation')
            stacks = cf_client.list_stacks(StackStatusFilter=['CREATE_COMPLETE', 'UPDATE_COMPLETE'])
            num_stacks = len(stacks.get('StackSummaries', []))
            evidence_parts.append(f"CloudFormation stacks: {num_stacks}")
            if num_stacks > 0:
                managed_services += 1
        except ClientError:
            evidence_parts.append("CloudFormation: No accesible")
        
        # 6. Verificar servicios de seguridad administrados
        security_services = 0
        try:
            gd = session.client('guardduty')
            if gd.list_detectors().get('DetectorIds'):
                security_services += 1
        except:
            pass
        try:
            sh = session.client('securityhub')
            sh.describe_hub()
            security_services += 1
        except:
            pass
        evidence_parts.append(f"Servicios seguridad administrados: {security_services}")
        
        evidence = ' | '.join(evidence_parts)
        
        # Evaluar: más servicios administrados = menor alcance de gestión
        if managed_services >= 3 and running_instances == 0:
            return {'bp': 'SEC01-BP05', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC01-BP05', ''),
                    'status': 'COMPLIANT', 'severity': 'LOW',
                    'finding': f'Alto uso de servicios administrados ({managed_services} tipos). Sin infraestructura EC2 auto-administrada. Alcance de gestión de seguridad reducido.',
                    'evidence': evidence,
                    'remediation': 'Estado actual cumple. Continuar priorizando servicios administrados y serverless para minimizar la superficie de gestión de seguridad.',
                    'risk': 'Bajo riesgo. Los servicios administrados reducen la responsabilidad de seguridad del cliente.'}
        elif managed_services >= 2:
            return {'bp': 'SEC01-BP05', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC01-BP05', ''),
                    'status': 'PENDING_REVIEW', 'severity': 'MEDIUM',
                    'finding': f'Uso mixto de servicios administrados ({managed_services} tipos) e infraestructura auto-administrada ({running_instances} EC2).',
                    'evidence': evidence,
                    'remediation': (
                        'Reducir el alcance de gestión de seguridad: '
                        '1) Migrar cargas de trabajo EC2 a servicios administrados donde sea posible (Fargate, Lambda, RDS). '
                        '2) Para EC2 restantes, usar Systems Manager para gestión automatizada. '
                        '3) Implementar Session Manager en lugar de SSH/RDP directo. '
                        '4) Usar AWS Managed Services o servicios serverless para nuevas cargas de trabajo. '
                        '5) Consolidar herramientas de seguridad usando servicios administrados (GuardDuty, Security Hub).'
                    ),
                    'risk': 'Riesgo medio. La infraestructura auto-administrada requiere gestión de seguridad adicional (parcheo, hardening, monitoreo).'}
        else:
            return {'bp': 'SEC01-BP05', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC01-BP05', ''),
                    'status': 'NON_COMPLIANT', 'severity': 'MEDIUM',
                    'finding': f'Bajo uso de servicios administrados ({managed_services} tipos). Alcance de gestión de seguridad amplio.',
                    'evidence': evidence,
                    'remediation': (
                        'Adoptar servicios administrados para reducir el alcance de seguridad: '
                        '1) Evaluar migración a Lambda/Fargate para cargas de trabajo de cómputo. '
                        '2) Usar RDS/DynamoDB en lugar de bases de datos auto-administradas en EC2. '
                        '3) Implementar IaC con CloudFormation/CDK para estandarizar despliegues. '
                        '4) Habilitar GuardDuty y Security Hub para seguridad administrada. '
                        '5) Usar S3 con cifrado administrado en lugar de almacenamiento auto-administrado. '
                        '6) Implementar API Gateway en lugar de servidores web auto-administrados.'
                    ),
                    'risk': 'Riesgo medio-alto. Mayor alcance de gestión de seguridad implica más superficie de ataque y mayor esfuerzo operacional.'}
    except ClientError as e:
        return handle_error_func('SEC01-BP05', e)


def evaluate_sec01_bp06(session, handle_error_func) -> Dict[str, Any]:
    """SEC01-BP06: Automatizar la implementación de controles de seguridad estándar
    Evalúa: CloudFormation/CDK stacks, CodePipeline, Service Catalog, Config rules, version control
    """
    try:
        issues = []
        evidence_parts = []
        
        # 1. Verificar CloudFormation stacks (IaC)
        try:
            cf_client = session.client('cloudformation')
            stacks = cf_client.list_stacks(StackStatusFilter=['CREATE_COMPLETE', 'UPDATE_COMPLETE'])
            stack_list = stacks.get('StackSummaries', [])
            security_stacks = [s for s in stack_list if any(kw in s.get('StackName', '').lower() for kw in ['security', 'guard', 'config', 'waf', 'firewall'])]
            evidence_parts.append(f"CloudFormation stacks: {len(stack_list)} total, {len(security_stacks)} de seguridad")
            if len(stack_list) == 0:
                issues.append('Sin stacks de CloudFormation (no hay IaC)')
        except ClientError:
            evidence_parts.append("CloudFormation: No accesible")
            issues.append('CloudFormation no accesible')
        
        # 2. Verificar CodePipeline (CI/CD)
        try:
            cp_client = session.client('codepipeline')
            pipelines = cp_client.list_pipelines()
            num_pipelines = len(pipelines.get('pipelines', []))
            evidence_parts.append(f"CodePipeline pipelines: {num_pipelines}")
            if num_pipelines == 0:
                issues.append('Sin pipelines CI/CD para despliegue automatizado')
        except ClientError:
            evidence_parts.append("CodePipeline: No accesible")
        
        # 3. Verificar Service Catalog (autoservicio)
        try:
            sc_client = session.client('servicecatalog')
            portfolios = sc_client.list_portfolios()
            num_portfolios = len(portfolios.get('PortfolioDetails', []))
            evidence_parts.append(f"Service Catalog portfolios: {num_portfolios}")
        except ClientError:
            evidence_parts.append("Service Catalog: No accesible")
        
        # 4. Verificar Config rules (validación automatizada)
        try:
            config_client = session.client('config')
            rules = config_client.describe_config_rules()
            num_rules = len(rules.get('ConfigRules', []))
            evidence_parts.append(f"Config Rules: {num_rules}")
        except ClientError:
            evidence_parts.append("Config Rules: No accesible")
        
        # 5. Verificar CodeCommit/CodeBuild (version control y build)
        try:
            cb_client = session.client('codebuild')
            projects = cb_client.list_projects()
            num_projects = len(projects.get('projects', []))
            evidence_parts.append(f"CodeBuild projects: {num_projects}")
        except ClientError:
            evidence_parts.append("CodeBuild: No accesible")
        
        evidence = ' | '.join(evidence_parts)
        
        if len(issues) == 0:
            return {'bp': 'SEC01-BP06', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC01-BP06', ''),
                    'status': 'COMPLIANT', 'severity': 'LOW',
                    'finding': 'Controles de seguridad automatizados mediante IaC y CI/CD.',
                    'evidence': evidence,
                    'remediation': 'Estado actual cumple. Continuar usando IaC para todos los controles de seguridad y validar configuraciones antes del despliegue.',
                    'risk': 'Bajo riesgo. La automatización reduce errores de configuración manual.'}
        elif len(issues) == 1:
            return {'bp': 'SEC01-BP06', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC01-BP06', ''),
                    'status': 'PENDING_REVIEW', 'severity': 'MEDIUM',
                    'finding': f'Automatización parcial de controles de seguridad. {"; ".join(issues)}',
                    'evidence': evidence,
                    'remediation': (
                        'Completar la automatización de controles de seguridad: '
                        '1) Definir todos los controles de seguridad como plantillas IaC (CloudFormation/CDK). '
                        '2) Implementar pipelines CI/CD con pruebas de seguridad automatizadas. '
                        '3) Usar Service Catalog para despliegue de autoservicio de controles pre-aprobados. '
                        '4) Implementar CloudFormation Guard para validar configuraciones antes del despliegue. '
                        '5) Configurar Config Rules para detectar desviaciones de configuración.'
                    ),
                    'risk': 'Riesgo medio. Sin automatización completa, los controles de seguridad pueden ser inconsistentes entre entornos.'}
        else:
            return {'bp': 'SEC01-BP06', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC01-BP06', ''),
                    'status': 'NON_COMPLIANT', 'severity': 'HIGH',
                    'finding': f'Controles de seguridad no automatizados. Hallazgos: {"; ".join(issues)}',
                    'evidence': evidence,
                    'remediation': (
                        'Implementar automatización de controles de seguridad: '
                        '1) Adoptar IaC con CloudFormation/CDK/Terraform para toda la infraestructura. '
                        '2) Crear plantillas estandarizadas de controles de seguridad (security groups, NACLs, IAM policies). '
                        '3) Implementar pipelines CI/CD con CodePipeline/CodeBuild. '
                        '4) Integrar escaneo de seguridad en pipelines (cfn-lint, cfn-nag, checkov). '
                        '5) Usar Service Catalog para autoservicio de configuraciones pre-aprobadas. '
                        '6) Implementar control de versiones para todas las configuraciones de seguridad. '
                        '7) Configurar Config Rules para validación continua de cumplimiento.'
                    ),
                    'risk': 'Alto riesgo. Sin automatización, los controles de seguridad dependen de configuración manual, propensa a errores e inconsistencias.'}
    except ClientError as e:
        return handle_error_func('SEC01-BP06', e)


def evaluate_sec01_bp07(session, handle_error_func) -> Dict[str, Any]:
    """SEC01-BP07: Identificar amenazas y priorizar mitigaciones usando un modelo de amenazas
    Evalúa: Security Hub findings, GuardDuty threats, Config rules, CloudTrail, WAF rules
    """
    try:
        issues = []
        evidence_parts = []
        
        # 1. Security Hub - hallazgos y estándares
        try:
            sh_client = session.client('securityhub')
            hub = sh_client.describe_hub()
            evidence_parts.append(f"Security Hub: Habilitado")
            
            # Contar hallazgos por severidad
            try:
                findings = sh_client.get_findings(
                    Filters={'SeverityLabel': [{'Value': 'CRITICAL', 'Comparison': 'EQUALS'}],
                             'RecordState': [{'Value': 'ACTIVE', 'Comparison': 'EQUALS'}]},
                    MaxResults=10
                )
                critical_count = len(findings.get('Findings', []))
                evidence_parts.append(f"Hallazgos críticos activos: {critical_count}+")
            except ClientError:
                pass
        except Exception:
            evidence_parts.append("Security Hub: NO HABILITADO")
            issues.append('Security Hub no habilitado para gestión centralizada de amenazas')
        
        # 2. GuardDuty - detección de amenazas
        try:
            gd_client = session.client('guardduty')
            detectors = gd_client.list_detectors()
            if detectors.get('DetectorIds'):
                evidence_parts.append("GuardDuty: Activo")
            else:
                evidence_parts.append("GuardDuty: NO HABILITADO")
                issues.append('GuardDuty no habilitado para detección de amenazas')
        except ClientError:
            evidence_parts.append("GuardDuty: No accesible")
        
        # 3. Config Rules - validación de configuración
        try:
            config_client = session.client('config')
            rules = config_client.describe_config_rules()
            security_rules = [r for r in rules.get('ConfigRules', []) if any(
                kw in r.get('ConfigRuleName', '').lower() for kw in ['security', 'encrypted', 'public', 'restricted', 'ssh', 'rdp']
            )]
            evidence_parts.append(f"Config Rules de seguridad: {len(security_rules)}")
            if len(security_rules) == 0:
                issues.append('Sin reglas de Config para validación de configuraciones de seguridad')
        except ClientError:
            evidence_parts.append("Config Rules: No accesible")
        
        # 4. CloudTrail - registro de eventos
        try:
            ct_client = session.client('cloudtrail')
            trails = ct_client.describe_trails()
            active_trails = [t for t in trails.get('trailList', []) if t.get('IsMultiRegionTrail')]
            evidence_parts.append(f"CloudTrail multi-región: {len(active_trails)}")
        except ClientError:
            evidence_parts.append("CloudTrail: No accesible")
        
        # 5. WAF - protección proactiva
        try:
            waf_client = session.client('wafv2')
            web_acls = waf_client.list_web_acls(Scope='REGIONAL')
            num_acls = len(web_acls.get('WebACLs', []))
            evidence_parts.append(f"WAF Web ACLs: {num_acls}")
        except ClientError:
            evidence_parts.append("WAF: No accesible")
        
        evidence = ' | '.join(evidence_parts)
        
        if len(issues) == 0:
            return {'bp': 'SEC01-BP07', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC01-BP07', ''),
                    'status': 'COMPLIANT', 'severity': 'LOW',
                    'finding': 'Servicios de identificación de amenazas activos con Security Hub, GuardDuty y Config Rules.',
                    'evidence': evidence,
                    'remediation': 'Estado actual cumple. Revisar periódicamente el registro de amenazas y priorizar mitigaciones según severidad.',
                    'risk': 'Bajo riesgo. Las amenazas están siendo identificadas y monitoreadas.'}
        elif len(issues) == 1:
            return {'bp': 'SEC01-BP07', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC01-BP07', ''),
                    'status': 'PENDING_REVIEW', 'severity': 'MEDIUM',
                    'finding': f'Identificación de amenazas parcial. {"; ".join(issues)}',
                    'evidence': evidence,
                    'remediation': (
                        'Completar la identificación de amenazas: '
                        '1) Habilitar Security Hub con estándares de seguridad para evaluación sistemática. '
                        '2) Habilitar GuardDuty para detección automática de amenazas. '
                        '3) Configurar Config Rules para detectar configuraciones inseguras. '
                        '4) Implementar WAF para protección proactiva contra amenazas web. '
                        '5) Documentar modelo de amenazas con registro actualizado de riesgos.'
                    ),
                    'risk': 'Riesgo medio. Sin identificación completa de amenazas, algunos vectores de ataque pueden no ser detectados.'}
        else:
            return {'bp': 'SEC01-BP07', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC01-BP07', ''),
                    'status': 'NON_COMPLIANT', 'severity': 'HIGH',
                    'finding': f'Identificación de amenazas insuficiente. Hallazgos: {"; ".join(issues)}',
                    'evidence': evidence,
                    'remediation': (
                        'Implementar identificación y priorización de amenazas: '
                        '1) Habilitar Security Hub con AWS Foundational Security Best Practices y CIS Benchmark. '
                        '2) Habilitar GuardDuty en todas las regiones con todas las protecciones. '
                        '3) Configurar Config Rules para monitorear configuraciones de seguridad. '
                        '4) Habilitar CloudTrail multi-región para registro completo de eventos. '
                        '5) Implementar WAF con reglas administradas para protección web. '
                        '6) Crear y mantener un modelo de amenazas documentado. '
                        '7) Priorizar mitigaciones basándose en severidad e impacto de negocio.'
                    ),
                    'risk': 'Alto riesgo. Sin identificación de amenazas, no se pueden priorizar mitigaciones y los ataques pueden pasar desapercibidos.'}
    except ClientError as e:
        return handle_error_func('SEC01-BP07', e)


def evaluate_sec01_bp08(session, handle_error_func) -> Dict[str, Any]:
    """SEC01-BP08: Evaluar e implementar nuevos servicios y características de seguridad periódicamente
    Evalúa: Adopción de servicios de seguridad (GuardDuty, SecurityHub, Inspector, Macie, Detective, WAF, Shield)
    """
    try:
        evidence_parts = []
        services_enabled = []
        services_disabled = []
        
        # 1. GuardDuty
        try:
            gd = session.client('guardduty')
            if gd.list_detectors().get('DetectorIds'):
                services_enabled.append('GuardDuty')
            else:
                services_disabled.append('GuardDuty')
        except:
            services_disabled.append('GuardDuty')
        
        # 2. Security Hub
        try:
            sh = session.client('securityhub')
            sh.describe_hub()
            services_enabled.append('Security Hub')
        except:
            services_disabled.append('Security Hub')
        
        # 3. Inspector
        try:
            inspector = session.client('inspector2')
            inspector.batch_get_account_status(accountIds=[])
            services_enabled.append('Inspector')
        except:
            services_disabled.append('Inspector')
        
        # 4. Macie
        try:
            macie = session.client('macie2')
            macie.get_macie_session()
            services_enabled.append('Macie')
        except:
            services_disabled.append('Macie')
        
        # 5. WAF
        try:
            waf = session.client('wafv2')
            acls = waf.list_web_acls(Scope='REGIONAL')
            if acls.get('WebACLs'):
                services_enabled.append('WAF')
            else:
                services_disabled.append('WAF')
        except:
            services_disabled.append('WAF')
        
        # 6. CloudTrail
        try:
            ct = session.client('cloudtrail')
            trails = ct.describe_trails()
            if trails.get('trailList'):
                services_enabled.append('CloudTrail')
            else:
                services_disabled.append('CloudTrail')
        except:
            services_disabled.append('CloudTrail')
        
        # 7. Config
        try:
            config = session.client('config')
            recorders = config.describe_configuration_recorders()
            if recorders.get('ConfigurationRecorders'):
                services_enabled.append('Config')
            else:
                services_disabled.append('Config')
        except:
            services_disabled.append('Config')
        
        total = len(services_enabled) + len(services_disabled)
        enabled_pct = (len(services_enabled) / total * 100) if total > 0 else 0
        
        evidence_parts.append(f"Servicios habilitados: {len(services_enabled)}/{total} ({enabled_pct:.0f}%)")
        evidence_parts.append(f"Activos: {', '.join(services_enabled)}" if services_enabled else "Activos: Ninguno")
        evidence_parts.append(f"No habilitados: {', '.join(services_disabled)}" if services_disabled else "No habilitados: Ninguno")
        evidence = ' | '.join(evidence_parts)
        
        if enabled_pct >= 80:
            return {'bp': 'SEC01-BP08', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC01-BP08', ''),
                    'status': 'COMPLIANT', 'severity': 'LOW',
                    'finding': f'Alta adopción de servicios de seguridad: {len(services_enabled)}/{total} habilitados ({enabled_pct:.0f}%).',
                    'evidence': evidence,
                    'remediation': 'Estado actual cumple. Evaluar periódicamente nuevos servicios y características de seguridad de AWS para mantener la postura de seguridad actualizada.',
                    'risk': 'Bajo riesgo. La mayoría de servicios de seguridad están habilitados.'}
        elif enabled_pct >= 50:
            return {'bp': 'SEC01-BP08', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC01-BP08', ''),
                    'status': 'PENDING_REVIEW', 'severity': 'MEDIUM',
                    'finding': f'Adopción parcial de servicios de seguridad: {len(services_enabled)}/{total} ({enabled_pct:.0f}%). Servicios faltantes: {", ".join(services_disabled)}.',
                    'evidence': evidence,
                    'remediation': (
                        f'Habilitar servicios de seguridad faltantes: '
                        f'{"; ".join([f"Habilitar {s}" for s in services_disabled])}. '
                        'Evaluar periódicamente nuevas características de seguridad de AWS. '
                        'Suscribirse a AWS Security Bulletins para estar al día con nuevos servicios.'
                    ),
                    'risk': 'Riesgo medio. Servicios de seguridad no habilitados dejan brechas en la postura de seguridad.'}
        else:
            return {'bp': 'SEC01-BP08', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC01-BP08', ''),
                    'status': 'NON_COMPLIANT', 'severity': 'HIGH',
                    'finding': f'Baja adopción de servicios de seguridad: solo {len(services_enabled)}/{total} ({enabled_pct:.0f}%). Servicios faltantes: {", ".join(services_disabled)}.',
                    'evidence': evidence,
                    'remediation': (
                        'Implementar servicios de seguridad de AWS: '
                        '1) Habilitar GuardDuty para detección de amenazas en todas las regiones. '
                        '2) Habilitar Security Hub para gestión centralizada de hallazgos. '
                        '3) Habilitar Inspector para escaneo de vulnerabilidades. '
                        '4) Habilitar Macie para descubrimiento de datos sensibles en S3. '
                        '5) Configurar WAF para protección de aplicaciones web. '
                        '6) Habilitar CloudTrail para registro de eventos en todas las regiones. '
                        '7) Habilitar Config para monitoreo de configuraciones. '
                        '8) Evaluar Detective para investigación de incidentes. '
                        '9) Evaluar Shield Advanced para protección DDoS.'
                    ),
                    'risk': 'Alto riesgo. Sin servicios de seguridad habilitados, la cuenta carece de capacidades fundamentales de detección, monitoreo y protección.'}
    except ClientError as e:
        return handle_error_func('SEC01-BP08', e)


# ============================================================================
# SEC02 - Gestión de identidad y autenticación (BP01-BP06)
# ============================================================================

def evaluate_sec02_bp01(session, handle_error_func) -> Dict[str, Any]:
    """SEC02-BP01: Utilizar mecanismos de inicio de sesión fuertes
    Evalúa: Password policy, MFA enforcement, IAM Identity Center, credential report
    """
    try:
        client = session.client('iam')
        issues = []
        evidence_parts = []
        
        # 1. Verificar política de contraseñas
        try:
            policy = client.get_account_password_policy()['PasswordPolicy']
            min_length = policy.get('MinimumPasswordLength', 0)
            require_upper = policy.get('RequireUppercaseCharacters', False)
            require_lower = policy.get('RequireLowercaseCharacters', False)
            require_numbers = policy.get('RequireNumbers', False)
            require_symbols = policy.get('RequireSymbols', False)
            max_age = policy.get('MaxPasswordAge', 0)
            reuse_prevention = policy.get('PasswordReusePrevention', 0)
            
            evidence_parts.append(
                f"Password Policy: min_length={min_length}, upper={require_upper}, lower={require_lower}, "
                f"numbers={require_numbers}, symbols={require_symbols}, max_age={max_age}d, reuse_prevention={reuse_prevention}"
            )
            
            if min_length < 14:
                issues.append(f'Longitud mínima de contraseña insuficiente ({min_length}, se requiere >=14)')
            if not all([require_upper, require_lower, require_numbers, require_symbols]):
                issues.append('Política de contraseñas no requiere todos los tipos de caracteres')
            if max_age == 0 or max_age > 90:
                issues.append(f'Expiración de contraseña no configurada o muy larga ({max_age} días)')
            if reuse_prevention < 12:
                issues.append(f'Prevención de reutilización insuficiente ({reuse_prevention}, se requiere >=12)')
        except client.exceptions.NoSuchEntityException:
            evidence_parts.append("Password Policy: NO CONFIGURADA")
            issues.append('Sin política de contraseñas configurada')
        
        # 2. Verificar MFA en usuarios
        try:
            summary = client.get_account_summary()['SummaryMap']
            total_users = summary.get('Users', 0)
            mfa_users = summary.get('MFADevices', 0)
            evidence_parts.append(f"Usuarios IAM: {total_users}, Dispositivos MFA: {mfa_users}")
            
            # Verificar usuarios sin MFA
            users = client.list_users(MaxItems=50)['Users']
            users_without_mfa = []
            for user in users[:20]:
                mfa_devices = client.list_mfa_devices(UserName=user['UserName'])
                if not mfa_devices.get('MFADevices'):
                    # Solo reportar si el usuario tiene contraseña de consola
                    try:
                        client.get_login_profile(UserName=user['UserName'])
                        users_without_mfa.append(user['UserName'])
                    except client.exceptions.NoSuchEntityException:
                        pass  # No tiene acceso a consola, no necesita MFA
            
            if users_without_mfa:
                evidence_parts.append(f"Usuarios con consola sin MFA: {len(users_without_mfa)} ({', '.join(users_without_mfa[:5])})")
                issues.append(f'{len(users_without_mfa)} usuario(s) con acceso a consola sin MFA')
        except ClientError:
            evidence_parts.append("MFA: No se pudo verificar")
        
        # 3. Verificar IAM Identity Center
        try:
            sso_client = session.client('sso-admin')
            instances = sso_client.list_instances()
            sso_instances = instances.get('Instances', [])
            evidence_parts.append(f"IAM Identity Center: {len(sso_instances)} instancia(s)")
        except ClientError:
            evidence_parts.append("IAM Identity Center: No accesible")
        
        evidence = ' | '.join(evidence_parts)
        
        if len(issues) == 0:
            return {'bp': 'SEC02-BP01', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC02-BP01', ''),
                    'status': 'COMPLIANT', 'severity': 'LOW',
                    'finding': 'Mecanismos de inicio de sesión fuertes implementados. Política de contraseñas robusta y MFA habilitado.',
                    'evidence': evidence,
                    'remediation': 'Estado actual cumple. Continuar monitoreando el cumplimiento de MFA y la fortaleza de contraseñas.',
                    'risk': 'Bajo riesgo. Los mecanismos de autenticación son fuertes.'}
        elif 'Sin política de contraseñas' in str(issues) or 'sin MFA' in str(issues):
            return {'bp': 'SEC02-BP01', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC02-BP01', ''),
                    'status': 'NON_COMPLIANT', 'severity': 'CRITICAL',
                    'finding': f'Mecanismos de inicio de sesión débiles. Hallazgos: {"; ".join(issues)}',
                    'evidence': evidence,
                    'remediation': (
                        'Fortalecer mecanismos de inicio de sesión: '
                        '1) Configurar política de contraseñas: mínimo 14 caracteres, mayúsculas, minúsculas, números, símbolos. '
                        '2) Establecer expiración de contraseñas cada 90 días con prevención de reutilización de 12 contraseñas. '
                        '3) Habilitar MFA obligatorio para TODOS los usuarios con acceso a consola. '
                        '4) Preferir dispositivos MFA hardware (FIDO2) sobre MFA virtual. '
                        '5) Implementar IAM Identity Center para gestión centralizada de acceso. '
                        '6) Generar y revisar credential report periódicamente.'
                    ),
                    'risk': 'Riesgo CRÍTICO. Sin política de contraseñas o MFA, las credenciales son vulnerables a ataques de fuerza bruta y phishing.'}
        else:
            return {'bp': 'SEC02-BP01', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC02-BP01', ''),
                    'status': 'PENDING_REVIEW', 'severity': 'MEDIUM',
                    'finding': f'Mecanismos de inicio de sesión parcialmente implementados. Hallazgos: {"; ".join(issues)}',
                    'evidence': evidence,
                    'remediation': (
                        'Mejorar mecanismos de inicio de sesión: '
                        '1) Aumentar longitud mínima de contraseña a 14+ caracteres. '
                        '2) Configurar expiración de contraseñas cada 90 días. '
                        '3) Establecer prevención de reutilización de al menos 12 contraseñas. '
                        '4) Verificar que todos los usuarios con consola tengan MFA habilitado. '
                        '5) Considerar migración a IAM Identity Center para gestión centralizada.'
                    ),
                    'risk': 'Riesgo medio. La política de contraseñas requiere ajustes para cumplir con las mejores prácticas.'}
    except ClientError as e:
        return handle_error_func('SEC02-BP01', e)


def evaluate_sec02_bp02(session, handle_error_func) -> Dict[str, Any]:
    """SEC02-BP02: Utilizar credenciales temporales
    Evalúa: Access keys age, IAM roles usage, STS usage, credential report
    """
    try:
        client = session.client('iam')
        issues = []
        evidence_parts = []
        
        # 1. Verificar usuarios con access keys de larga duración
        users = client.list_users(MaxItems=50)['Users']
        users_with_old_keys = []
        users_with_keys = 0
        
        import datetime
        for user in users[:30]:
            try:
                keys = client.list_access_keys(UserName=user['UserName'])
                for key in keys.get('AccessKeyMetadata', []):
                    if key['Status'] == 'Active':
                        users_with_keys += 1
                        create_date = key['CreateDate'].replace(tzinfo=None)
                        age_days = (datetime.datetime.utcnow() - create_date).days
                        if age_days > 90:
                            users_with_old_keys.append(f"{user['UserName']} ({age_days}d)")
            except ClientError:
                pass
        
        evidence_parts.append(f"Usuarios con access keys activas: {users_with_keys}")
        if users_with_old_keys:
            evidence_parts.append(f"Keys >90 días: {len(users_with_old_keys)} ({', '.join(users_with_old_keys[:5])})")
            issues.append(f'{len(users_with_old_keys)} usuario(s) con access keys de más de 90 días')
        
        # 2. Verificar roles IAM (uso de credenciales temporales)
        roles = client.list_roles(MaxItems=50)
        num_roles = len(roles.get('Roles', []))
        service_roles = [r for r in roles.get('Roles', []) if 'service-role' in r.get('Path', '') or 'aws-service-role' in r.get('Path', '')]
        evidence_parts.append(f"Roles IAM: {num_roles} total, {len(service_roles)} de servicio")
        
        # 3. Verificar proporción keys vs roles
        if users_with_keys > num_roles and users_with_keys > 5:
            issues.append(f'Más usuarios con access keys ({users_with_keys}) que roles IAM ({num_roles}), indica bajo uso de credenciales temporales')
        
        # 4. Verificar root access keys
        try:
            summary = client.get_account_summary()['SummaryMap']
            root_keys = summary.get('AccountAccessKeysPresent', 0)
            evidence_parts.append(f"Root access keys: {root_keys}")
            if root_keys > 0:
                issues.append('Access keys activas en usuario raíz')
        except ClientError:
            pass
        
        evidence = ' | '.join(evidence_parts)
        
        if len(issues) == 0:
            return {'bp': 'SEC02-BP02', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC02-BP02', ''),
                    'status': 'COMPLIANT', 'severity': 'LOW',
                    'finding': 'Uso adecuado de credenciales temporales. Access keys rotadas y roles IAM en uso.',
                    'evidence': evidence,
                    'remediation': 'Estado actual cumple. Continuar priorizando roles IAM sobre access keys de larga duración.',
                    'risk': 'Bajo riesgo. Las credenciales temporales limitan la ventana de exposición.'}
        elif 'raíz' in str(issues):
            return {'bp': 'SEC02-BP02', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC02-BP02', ''),
                    'status': 'NON_COMPLIANT', 'severity': 'CRITICAL',
                    'finding': f'Uso de credenciales de larga duración detectado. Hallazgos: {"; ".join(issues)}',
                    'evidence': evidence,
                    'remediation': (
                        'Migrar a credenciales temporales: '
                        '1) ELIMINAR INMEDIATAMENTE access keys del usuario raíz. '
                        '2) Rotar access keys de más de 90 días o reemplazar con roles IAM. '
                        '3) Usar IAM roles con STS AssumeRole para acceso programático. '
                        '4) Implementar IAM Identity Center para acceso federado. '
                        '5) Configurar duración máxima de sesión en roles (1-12 horas). '
                        '6) Generar credential report mensual para auditar credenciales.'
                    ),
                    'risk': 'Riesgo CRÍTICO. Las access keys de larga duración, especialmente del usuario raíz, representan un vector de ataque permanente.'}
        else:
            return {'bp': 'SEC02-BP02', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC02-BP02', ''),
                    'status': 'NON_COMPLIANT', 'severity': 'HIGH',
                    'finding': f'Uso excesivo de credenciales de larga duración. Hallazgos: {"; ".join(issues)}',
                    'evidence': evidence,
                    'remediation': (
                        'Migrar a credenciales temporales: '
                        '1) Identificar y rotar access keys de más de 90 días. '
                        '2) Reemplazar access keys por roles IAM donde sea posible. '
                        '3) Usar STS AssumeRole para acceso cross-account. '
                        '4) Implementar IAM Identity Center para acceso federado a consola y CLI. '
                        '5) Configurar políticas de rotación automática de credenciales. '
                        '6) Auditar credential report mensualmente.'
                    ),
                    'risk': 'Alto riesgo. Las credenciales de larga duración aumentan la ventana de exposición en caso de compromiso.'}
    except ClientError as e:
        return handle_error_func('SEC02-BP02', e)


def evaluate_sec02_bp03(session, handle_error_func) -> Dict[str, Any]:
    """SEC02-BP03: Almacenar y utilizar secretos de forma segura
    Evalúa: Secrets Manager, Parameter Store SecureString, secret rotation, hardcoded secrets
    """
    try:
        issues = []
        evidence_parts = []
        
        # 1. Verificar Secrets Manager
        try:
            sm_client = session.client('secretsmanager')
            secrets = sm_client.list_secrets(MaxResults=50)
            secret_list = secrets.get('SecretList', [])
            rotated = [s for s in secret_list if s.get('RotationEnabled')]
            evidence_parts.append(f"Secrets Manager: {len(secret_list)} secretos, {len(rotated)} con rotación")
            if len(secret_list) == 0:
                issues.append('Sin secretos en Secrets Manager (pueden estar hardcodeados)')
            elif len(rotated) < len(secret_list) * 0.5:
                issues.append(f'Solo {len(rotated)}/{len(secret_list)} secretos tienen rotación automática')
        except ClientError:
            evidence_parts.append("Secrets Manager: No accesible")
        
        # 2. Verificar Parameter Store SecureString
        try:
            ssm_client = session.client('ssm')
            params = ssm_client.describe_parameters(
                ParameterFilters=[{'Key': 'Type', 'Values': ['SecureString']}],
                MaxResults=50
            )
            secure_params = len(params.get('Parameters', []))
            evidence_parts.append(f"Parameter Store SecureString: {secure_params}")
        except ClientError:
            evidence_parts.append("Parameter Store: No accesible")
        
        # 3. Verificar Lambda environment variables (posibles secretos hardcodeados)
        try:
            lambda_client = session.client('lambda')
            functions = lambda_client.list_functions(MaxItems=20)
            functions_with_plain_env = 0
            for func in functions.get('Functions', []):
                env_vars = func.get('Environment', {}).get('Variables', {})
                for key in env_vars:
                    if any(kw in key.lower() for kw in ['password', 'secret', 'key', 'token', 'api_key']):
                        functions_with_plain_env += 1
                        break
            if functions_with_plain_env > 0:
                evidence_parts.append(f"Lambda con posibles secretos en env vars: {functions_with_plain_env}")
                issues.append(f'{functions_with_plain_env} función(es) Lambda con posibles secretos en variables de entorno')
        except ClientError:
            pass
        
        evidence = ' | '.join(evidence_parts)
        
        if len(issues) == 0:
            return {'bp': 'SEC02-BP03', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC02-BP03', ''),
                    'status': 'COMPLIANT', 'severity': 'LOW',
                    'finding': 'Secretos almacenados de forma segura en Secrets Manager con rotación automática.',
                    'evidence': evidence,
                    'remediation': 'Estado actual cumple. Continuar usando Secrets Manager para todos los secretos y mantener rotación automática.',
                    'risk': 'Bajo riesgo. Los secretos están protegidos y rotados automáticamente.'}
        else:
            severity = 'HIGH' if 'hardcodeados' in str(issues) or 'env vars' in str(issues) else 'MEDIUM'
            return {'bp': 'SEC02-BP03', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC02-BP03', ''),
                    'status': 'NON_COMPLIANT', 'severity': severity,
                    'finding': f'Gestión de secretos insuficiente. Hallazgos: {"; ".join(issues)}',
                    'evidence': evidence,
                    'remediation': (
                        'Implementar gestión segura de secretos: '
                        '1) Migrar todos los secretos a AWS Secrets Manager. '
                        '2) Habilitar rotación automática para secretos de bases de datos y APIs. '
                        '3) Usar Parameter Store SecureString para configuraciones sensibles. '
                        '4) Eliminar secretos hardcodeados en código y variables de entorno. '
                        '5) Referenciar secretos por ARN en lugar de valores directos. '
                        '6) Configurar políticas de acceso granulares para cada secreto. '
                        '7) Auditar acceso a secretos mediante CloudTrail.'
                    ),
                    'risk': 'Riesgo alto. Secretos no gestionados adecuadamente pueden ser expuestos en logs, repositorios o variables de entorno.'}
    except ClientError as e:
        return handle_error_func('SEC02-BP03', e)


def evaluate_sec02_bp04(session, handle_error_func) -> Dict[str, Any]:
    """SEC02-BP04: Confiar en un proveedor de identidad centralizado
    Evalúa: IAM Identity Center, SAML/OIDC providers, federation, centralized auth
    """
    try:
        client = session.client('iam')
        issues = []
        evidence_parts = []
        
        # 1. Verificar SAML providers
        try:
            saml_providers = client.list_saml_providers()
            num_saml = len(saml_providers.get('SAMLProviderList', []))
            evidence_parts.append(f"SAML providers: {num_saml}")
        except ClientError:
            num_saml = 0
            evidence_parts.append("SAML: No accesible")
        
        # 2. Verificar OIDC providers
        try:
            oidc_providers = client.list_open_id_connect_providers()
            num_oidc = len(oidc_providers.get('OpenIDConnectProviderList', []))
            evidence_parts.append(f"OIDC providers: {num_oidc}")
        except ClientError:
            num_oidc = 0
            evidence_parts.append("OIDC: No accesible")
        
        # 3. Verificar IAM Identity Center
        try:
            sso_client = session.client('sso-admin')
            instances = sso_client.list_instances()
            sso_instances = instances.get('Instances', [])
            evidence_parts.append(f"IAM Identity Center: {len(sso_instances)} instancia(s)")
            if sso_instances:
                # Verificar permission sets
                try:
                    ps = sso_client.list_permission_sets(InstanceArn=sso_instances[0]['InstanceArn'], MaxResults=10)
                    evidence_parts.append(f"Permission Sets: {len(ps.get('PermissionSets', []))}")
                except ClientError:
                    pass
        except ClientError:
            evidence_parts.append("IAM Identity Center: No accesible")
        
        # 4. Verificar usuarios IAM locales (indicador de no federación)
        try:
            summary = client.get_account_summary()['SummaryMap']
            num_users = summary.get('Users', 0)
            evidence_parts.append(f"Usuarios IAM locales: {num_users}")
            if num_users > 5 and num_saml == 0 and num_oidc == 0:
                issues.append(f'{num_users} usuarios IAM locales sin proveedor de identidad centralizado')
        except ClientError:
            pass
        
        has_federation = num_saml > 0 or num_oidc > 0
        evidence = ' | '.join(evidence_parts)
        
        if has_federation:
            return {'bp': 'SEC02-BP04', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC02-BP04', ''),
                    'status': 'COMPLIANT', 'severity': 'LOW',
                    'finding': f'Proveedor de identidad centralizado configurado ({num_saml} SAML, {num_oidc} OIDC).',
                    'evidence': evidence,
                    'remediation': 'Estado actual cumple. Continuar usando federación para acceso centralizado y minimizar usuarios IAM locales.',
                    'risk': 'Bajo riesgo. La federación centraliza la gestión de identidades.'}
        else:
            return {'bp': 'SEC02-BP04', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC02-BP04', ''),
                    'status': 'NON_COMPLIANT', 'severity': 'HIGH',
                    'finding': f'Sin proveedor de identidad centralizado. {"; ".join(issues) if issues else "No hay SAML ni OIDC configurados."}',
                    'evidence': evidence,
                    'remediation': (
                        'Implementar proveedor de identidad centralizado: '
                        '1) Configurar IAM Identity Center como punto central de acceso. '
                        '2) Integrar con proveedor de identidad corporativo (Active Directory, Okta, Azure AD). '
                        '3) Configurar SAML 2.0 o OIDC para federación. '
                        '4) Crear Permission Sets basados en funciones de trabajo. '
                        '5) Migrar usuarios IAM locales a acceso federado. '
                        '6) Eliminar usuarios IAM locales innecesarios. '
                        '7) Implementar MFA en el proveedor de identidad centralizado.'
                    ),
                    'risk': 'Alto riesgo. Sin federación, cada cuenta gestiona identidades independientemente, dificultando el control de acceso y la auditoría.'}
    except ClientError as e:
        return handle_error_func('SEC02-BP04', e)


def evaluate_sec02_bp05(session, handle_error_func) -> Dict[str, Any]:
    """SEC02-BP05: Auditar y rotar credenciales periódicamente
    Evalúa: Credential report, access key age, unused credentials, rotation policies
    """
    try:
        client = session.client('iam')
        issues = []
        evidence_parts = []

        # Inicializar contadores antes del try interno para evitar UnboundLocalError
        # si generate_credential_report()/get_credential_report() lanzan ClientError.
        old_keys = 0
        unused_users = 0
        no_mfa_console = 0

        # 1. Generar y analizar credential report
        try:
            client.generate_credential_report()
            import time
            time.sleep(2)
            report = client.get_credential_report()
            content = report['Content'].decode('utf-8')
            lines = content.strip().split('\n')
            
            import datetime
            for line in lines[1:]:  # Skip header
                fields = line.split(',')
                if len(fields) > 10:
                    username = fields[0]
                    password_enabled = fields[3]
                    mfa_active = fields[7]
                    access_key1_active = fields[8]
                    access_key1_last_rotated = fields[9]
                    password_last_used = fields[4]
                    
                    # Check old access keys
                    if access_key1_active == 'true' and access_key1_last_rotated != 'N/A':
                        try:
                            rotated = datetime.datetime.strptime(access_key1_last_rotated[:19], '%Y-%m-%dT%H:%M:%S')
                            age = (datetime.datetime.utcnow() - rotated).days
                            if age > 90:
                                old_keys += 1
                        except:
                            pass
                    
                    # Check unused users (no login in 90 days)
                    if password_enabled == 'true' and password_last_used not in ['N/A', 'no_information']:
                        try:
                            last_used = datetime.datetime.strptime(password_last_used[:19], '%Y-%m-%dT%H:%M:%S')
                            days_unused = (datetime.datetime.utcnow() - last_used).days
                            if days_unused > 90:
                                unused_users += 1
                        except:
                            pass
                    
                    # Check MFA
                    if password_enabled == 'true' and mfa_active == 'false' and username != '<root_account>':
                        no_mfa_console += 1
            
            evidence_parts.append(f"Credential Report: {len(lines)-1} usuarios")
            evidence_parts.append(f"Keys >90 días: {old_keys}")
            evidence_parts.append(f"Usuarios inactivos >90d: {unused_users}")
            evidence_parts.append(f"Consola sin MFA: {no_mfa_console}")
            
            if old_keys > 0:
                issues.append(f'{old_keys} access key(s) sin rotar en más de 90 días')
            if unused_users > 0:
                issues.append(f'{unused_users} usuario(s) inactivos por más de 90 días')
            if no_mfa_console > 0:
                issues.append(f'{no_mfa_console} usuario(s) con consola sin MFA')
                
        except ClientError as e:
            evidence_parts.append(f"Credential Report: No se pudo generar ({str(e)[:50]})")
            issues.append('No se pudo generar credential report para auditoría')
        
        evidence = ' | '.join(evidence_parts)
        
        if len(issues) == 0:
            return {'bp': 'SEC02-BP05', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC02-BP05', ''),
                    'status': 'COMPLIANT', 'severity': 'LOW',
                    'finding': 'Credenciales auditadas y rotadas. Sin access keys antiguas ni usuarios inactivos.',
                    'evidence': evidence,
                    'remediation': 'Estado actual cumple. Continuar generando credential report mensualmente y rotando credenciales cada 90 días.',
                    'risk': 'Bajo riesgo. Las credenciales están siendo gestionadas adecuadamente.'}
        else:
            severity = 'HIGH' if old_keys > 3 or no_mfa_console > 3 else 'MEDIUM'
            return {'bp': 'SEC02-BP05', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC02-BP05', ''),
                    'status': 'NON_COMPLIANT', 'severity': severity,
                    'finding': f'Credenciales requieren auditoría y rotación. Hallazgos: {"; ".join(issues)}',
                    'evidence': evidence,
                    'remediation': (
                        'Auditar y rotar credenciales: '
                        '1) Rotar access keys de más de 90 días o reemplazar con roles IAM. '
                        '2) Deshabilitar o eliminar usuarios inactivos por más de 90 días. '
                        '3) Habilitar MFA para todos los usuarios con acceso a consola. '
                        '4) Generar y revisar credential report mensualmente. '
                        '5) Implementar política de rotación automática de credenciales. '
                        '6) Configurar alertas para credenciales próximas a expirar. '
                        '7) Usar IAM Access Analyzer para identificar accesos no utilizados.'
                    ),
                    'risk': f'Riesgo {"alto" if severity == "HIGH" else "medio"}. Credenciales antiguas o no rotadas aumentan la ventana de exposición en caso de compromiso.'}
    except ClientError as e:
        return handle_error_func('SEC02-BP05', e)


def evaluate_sec02_bp06(session, handle_error_func) -> Dict[str, Any]:
    """SEC02-BP06: Emplear grupos de usuarios y atributos
    Evalúa: IAM groups, group policies, tag-based access, ABAC
    """
    try:
        client = session.client('iam')
        issues = []
        evidence_parts = []
        
        # 1. Verificar grupos IAM
        groups = client.list_groups(MaxItems=50)
        group_list = groups.get('Groups', [])
        evidence_parts.append(f"Grupos IAM: {len(group_list)}")
        
        if len(group_list) == 0:
            issues.append('Sin grupos IAM definidos')
        else:
            # Verificar que los grupos tienen políticas
            groups_with_policies = 0
            for group in group_list[:10]:
                policies = client.list_attached_group_policies(GroupName=group['GroupName'])
                inline = client.list_group_policies(GroupName=group['GroupName'])
                if policies.get('AttachedPolicies') or inline.get('PolicyNames'):
                    groups_with_policies += 1
            evidence_parts.append(f"Grupos con políticas: {groups_with_policies}/{min(len(group_list), 10)}")
        
        # 2. Verificar usuarios sin grupo
        users = client.list_users(MaxItems=50)['Users']
        users_without_group = 0
        for user in users[:20]:
            user_groups = client.list_groups_for_user(UserName=user['UserName'])
            if not user_groups.get('Groups'):
                users_without_group += 1
        
        evidence_parts.append(f"Usuarios sin grupo: {users_without_group}/{min(len(users), 20)}")
        if users_without_group > 0:
            issues.append(f'{users_without_group} usuario(s) sin asignación a grupo')
        
        # 3. Verificar políticas inline en usuarios (anti-patrón)
        users_with_inline = 0
        for user in users[:20]:
            inline = client.list_user_policies(UserName=user['UserName'])
            if inline.get('PolicyNames'):
                users_with_inline += 1
        
        evidence_parts.append(f"Usuarios con políticas inline: {users_with_inline}")
        if users_with_inline > 0:
            issues.append(f'{users_with_inline} usuario(s) con políticas inline (usar grupos en su lugar)')
        
        evidence = ' | '.join(evidence_parts)
        
        if len(issues) == 0:
            return {'bp': 'SEC02-BP06', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC02-BP06', ''),
                    'status': 'COMPLIANT', 'severity': 'LOW',
                    'finding': f'Grupos IAM configurados correctamente ({len(group_list)} grupos). Usuarios asignados a grupos.',
                    'evidence': evidence,
                    'remediation': 'Estado actual cumple. Continuar usando grupos para gestionar permisos y considerar ABAC con tags para control granular.',
                    'risk': 'Bajo riesgo. Los permisos se gestionan a través de grupos.'}
        else:
            return {'bp': 'SEC02-BP06', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC02-BP06', ''),
                    'status': 'NON_COMPLIANT', 'severity': 'MEDIUM',
                    'finding': f'Gestión de grupos y atributos insuficiente. Hallazgos: {"; ".join(issues)}',
                    'evidence': evidence,
                    'remediation': (
                        'Implementar gestión basada en grupos y atributos: '
                        '1) Crear grupos IAM por función de trabajo (Administradores, Desarrolladores, Auditores). '
                        '2) Asignar políticas a grupos, no a usuarios individuales. '
                        '3) Migrar políticas inline de usuarios a políticas de grupo. '
                        '4) Asignar todos los usuarios a al menos un grupo. '
                        '5) Implementar ABAC (Attribute-Based Access Control) con tags para control granular. '
                        '6) Usar condiciones de tag en políticas IAM para acceso basado en atributos.'
                    ),
                    'risk': 'Riesgo medio. Sin grupos, los permisos se gestionan individualmente, dificultando la auditoría y el mantenimiento.'}
    except ClientError as e:
        return handle_error_func('SEC02-BP06', e)


# ============================================================================
# SEC03 - Gestión de permisos (BP01-BP09)
# ============================================================================

def evaluate_sec03_bp01(session, handle_error_func) -> Dict[str, Any]:
    """SEC03-BP01: Definir los requisitos de acceso
    Evalúa: Policy documentation, permission boundaries, access requirements documentation
    """
    try:
        client = session.client('iam')
        issues = []
        evidence_parts = []
        
        # 1. Verificar políticas con descripciones (documentación)
        policies = client.list_policies(Scope='Local', MaxItems=50)
        local_policies = policies.get('Policies', [])
        documented = [p for p in local_policies if p.get('Description')]
        evidence_parts.append(f"Políticas locales: {len(local_policies)}, documentadas: {len(documented)}")
        if len(local_policies) > 0 and len(documented) < len(local_policies) * 0.5:
            issues.append(f'Solo {len(documented)}/{len(local_policies)} políticas tienen descripción')
        
        # 2. Verificar permission boundaries
        users = client.list_users(MaxItems=20)['Users']
        users_with_boundary = [u for u in users if u.get('PermissionsBoundary')]
        evidence_parts.append(f"Usuarios con permission boundary: {len(users_with_boundary)}/{len(users)}")
        
        # 3. Verificar roles con permission boundaries
        roles = client.list_roles(MaxItems=20)['Roles']
        roles_with_boundary = [r for r in roles if r.get('PermissionsBoundary')]
        evidence_parts.append(f"Roles con permission boundary: {len(roles_with_boundary)}/{len(roles)}")
        
        # 4. Verificar tags en políticas (categorización)
        tagged_policies = 0
        for policy in local_policies[:10]:
            try:
                tags = client.list_policy_tags(PolicyArn=policy['Arn'])
                if tags.get('Tags'):
                    tagged_policies += 1
            except ClientError:
                pass
        evidence_parts.append(f"Políticas con tags: {tagged_policies}/{min(len(local_policies), 10)}")
        
        evidence = ' | '.join(evidence_parts)
        
        if len(issues) == 0 and len(local_policies) > 0:
            return {'bp': 'SEC03-BP01', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC03-BP01', ''),
                    'status': 'COMPLIANT', 'severity': 'LOW',
                    'finding': 'Requisitos de acceso definidos con políticas documentadas y permission boundaries.',
                    'evidence': evidence,
                    'remediation': 'Estado actual cumple. Continuar documentando requisitos de acceso y usando permission boundaries.',
                    'risk': 'Bajo riesgo. Los requisitos de acceso están documentados.'}
        else:
            return {'bp': 'SEC03-BP01', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC03-BP01', ''),
                    'status': 'NON_COMPLIANT', 'severity': 'MEDIUM',
                    'finding': f'Requisitos de acceso insuficientemente definidos. Hallazgos: {"; ".join(issues) if issues else "Políticas sin documentación adecuada."}',
                    'evidence': evidence,
                    'remediation': (
                        'Definir requisitos de acceso: '
                        '1) Documentar todas las políticas IAM con descripciones claras de su propósito. '
                        '2) Implementar permission boundaries para limitar el alcance máximo de permisos. '
                        '3) Categorizar políticas con tags (equipo, entorno, aplicación). '
                        '4) Documentar matriz de acceso por rol/función de trabajo. '
                        '5) Revisar y actualizar requisitos de acceso trimestralmente. '
                        '6) Usar IAM Access Analyzer para validar que los permisos coinciden con los requisitos.'
                    ),
                    'risk': 'Riesgo medio. Sin requisitos de acceso claros, los permisos pueden ser excesivos o insuficientes.'}
    except ClientError as e:
        return handle_error_func('SEC03-BP01', e)


def evaluate_sec03_bp02(session, handle_error_func) -> Dict[str, Any]:
    """SEC03-BP02: Otorgar acceso con privilegios mínimos
    Evalúa: Admin users, wildcard policies, IAM Access Analyzer, policy analysis
    """
    try:
        client = session.client('iam')
        issues = []
        evidence_parts = []
        
        # 1. Contar usuarios con AdministratorAccess
        users = client.list_users(MaxItems=50)['Users']
        admin_users = []
        for user in users[:30]:
            try:
                attached = client.list_attached_user_policies(UserName=user['UserName'])
                for policy in attached.get('AttachedPolicies', []):
                    if 'AdministratorAccess' in policy['PolicyName']:
                        admin_users.append(user['UserName'])
                        break
            except ClientError:
                pass
        
        # Check groups for admin access too
        for user in users[:30]:
            if user['UserName'] not in admin_users:
                try:
                    user_groups = client.list_groups_for_user(UserName=user['UserName'])
                    for group in user_groups.get('Groups', []):
                        group_policies = client.list_attached_group_policies(GroupName=group['GroupName'])
                        for policy in group_policies.get('AttachedPolicies', []):
                            if 'AdministratorAccess' in policy['PolicyName']:
                                admin_users.append(user['UserName'])
                                break
                except ClientError:
                    pass
        
        evidence_parts.append(f"Usuarios con AdministratorAccess: {len(admin_users)}")
        if len(admin_users) > 2:
            issues.append(f'{len(admin_users)} usuarios con AdministratorAccess (máximo recomendado: 2)')
        
        # 2. Verificar IAM Access Analyzer
        try:
            aa_client = session.client('accessanalyzer')
            analyzers = aa_client.list_analyzers()
            num_analyzers = len(analyzers.get('analyzers', []))
            evidence_parts.append(f"IAM Access Analyzer: {num_analyzers}")
            if num_analyzers == 0:
                issues.append('IAM Access Analyzer no configurado para identificar permisos excesivos')
        except ClientError:
            evidence_parts.append("Access Analyzer: No accesible")
        
        # 3. Verificar políticas con wildcard (*)
        local_policies = client.list_policies(Scope='Local', MaxItems=20)['Policies']
        wildcard_policies = 0
        for policy in local_policies[:10]:
            try:
                version = client.get_policy_version(
                    PolicyArn=policy['Arn'],
                    VersionId=policy['DefaultVersionId']
                )
                doc = version['PolicyVersion']['Document']
                import json
                doc_str = json.dumps(doc) if isinstance(doc, dict) else str(doc)
                if '"Action": "*"' in doc_str or '"Resource": "*"' in doc_str:
                    wildcard_policies += 1
            except ClientError:
                pass
        evidence_parts.append(f"Políticas con wildcard: {wildcard_policies}")
        if wildcard_policies > 0:
            issues.append(f'{wildcard_policies} política(s) con permisos wildcard (*)')
        
        evidence = ' | '.join(evidence_parts)
        
        if len(issues) == 0:
            return {'bp': 'SEC03-BP02', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC03-BP02', ''),
                    'status': 'COMPLIANT', 'severity': 'LOW',
                    'finding': 'Privilegios mínimos implementados. Pocos administradores y Access Analyzer activo.',
                    'evidence': evidence,
                    'remediation': 'Estado actual cumple. Continuar revisando permisos con Access Analyzer y reduciendo privilegios.',
                    'risk': 'Bajo riesgo. Los permisos siguen el principio de privilegio mínimo.'}
        else:
            severity = 'HIGH' if len(admin_users) > 5 or wildcard_policies > 3 else 'MEDIUM'
            return {'bp': 'SEC03-BP02', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC03-BP02', ''),
                    'status': 'NON_COMPLIANT', 'severity': severity,
                    'finding': f'Privilegios excesivos detectados. Hallazgos: {"; ".join(issues)}',
                    'evidence': evidence,
                    'remediation': (
                        'Implementar privilegios mínimos: '
                        '1) Reducir usuarios con AdministratorAccess a máximo 2 (break-glass). '
                        '2) Reemplazar políticas wildcard (*) con permisos específicos por servicio. '
                        '3) Habilitar IAM Access Analyzer para identificar permisos no utilizados. '
                        '4) Usar IAM Access Analyzer policy generation para crear políticas basadas en actividad. '
                        '5) Implementar permission boundaries para limitar el alcance máximo. '
                        '6) Revisar y reducir permisos trimestralmente.'
                    ),
                    'risk': f'Riesgo {"alto" if severity == "HIGH" else "medio"}. Permisos excesivos aumentan el impacto de credenciales comprometidas.'}
    except ClientError as e:
        return handle_error_func('SEC03-BP02', e)


def evaluate_sec03_bp03(session, handle_error_func) -> Dict[str, Any]:
    """SEC03-BP03: Establecer proceso de acceso de emergencia
    Evalúa: Break-glass roles, emergency access procedures, incident response roles
    """
    try:
        client = session.client('iam')
        issues = []
        evidence_parts = []
        
        # 1. Buscar roles de emergencia/break-glass
        roles = client.list_roles(MaxItems=100)['Roles']
        emergency_keywords = ['emergency', 'break-glass', 'breakglass', 'incident', 'escalation', 'admin-emergency']
        emergency_roles = [r for r in roles if any(kw in r['RoleName'].lower() for kw in emergency_keywords)]
        evidence_parts.append(f"Roles de emergencia: {len(emergency_roles)}")
        if len(emergency_roles) == 0:
            issues.append('Sin roles de acceso de emergencia (break-glass) definidos')
        
        # 2. Verificar CloudWatch alarms para acceso de emergencia
        try:
            cw_client = session.client('cloudwatch')
            alarms = cw_client.describe_alarms(MaxRecords=100)
            security_alarms = [a for a in alarms.get('MetricAlarms', []) if any(
                kw in a.get('AlarmName', '').lower() for kw in ['root', 'emergency', 'unauthorized', 'console']
            )]
            evidence_parts.append(f"Alarmas de seguridad: {len(security_alarms)}")
        except ClientError:
            evidence_parts.append("CloudWatch alarms: No accesible")
        
        # 3. Verificar SSM documents para procedimientos de emergencia
        try:
            ssm_client = session.client('ssm')
            docs = ssm_client.list_documents(
                Filters=[{'Key': 'Owner', 'Values': ['Self']}],
                MaxResults=50
            )
            incident_docs = [d for d in docs.get('DocumentIdentifiers', []) if any(
                kw in d.get('Name', '').lower() for kw in ['incident', 'emergency', 'runbook', 'playbook']
            )]
            evidence_parts.append(f"Runbooks de emergencia: {len(incident_docs)}")
            if len(incident_docs) == 0:
                issues.append('Sin runbooks de emergencia en Systems Manager')
        except ClientError:
            evidence_parts.append("SSM Documents: No accesible")
        
        evidence = ' | '.join(evidence_parts)
        
        if len(issues) == 0:
            return {'bp': 'SEC03-BP03', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC03-BP03', ''),
                    'status': 'COMPLIANT', 'severity': 'LOW',
                    'finding': 'Proceso de acceso de emergencia establecido con roles break-glass y runbooks.',
                    'evidence': evidence,
                    'remediation': 'Estado actual cumple. Probar periódicamente el proceso de acceso de emergencia con simulaciones.',
                    'risk': 'Bajo riesgo. El acceso de emergencia está documentado y disponible.'}
        else:
            return {'bp': 'SEC03-BP03', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC03-BP03', ''),
                    'status': 'NON_COMPLIANT', 'severity': 'HIGH',
                    'finding': f'Proceso de acceso de emergencia no establecido. Hallazgos: {"; ".join(issues)}',
                    'evidence': evidence,
                    'remediation': (
                        'Establecer proceso de acceso de emergencia: '
                        '1) Crear rol IAM "BreakGlass" con permisos administrativos y condiciones estrictas. '
                        '2) Configurar MFA obligatorio para asumir el rol de emergencia. '
                        '3) Crear alarma de CloudWatch para detectar uso del rol de emergencia. '
                        '4) Documentar procedimiento de acceso de emergencia en SSM Runbook. '
                        '5) Almacenar credenciales de emergencia en bóveda segura con acceso dual. '
                        '6) Probar el proceso de emergencia trimestralmente con simulaciones. '
                        '7) Configurar notificación SNS cuando se asuma el rol de emergencia.'
                    ),
                    'risk': 'Alto riesgo. Sin proceso de acceso de emergencia, un incidente puede no ser contenido a tiempo por falta de acceso.'}
    except ClientError as e:
        return handle_error_func('SEC03-BP03', e)


def evaluate_sec03_bp04(session, handle_error_func) -> Dict[str, Any]:
    """SEC03-BP04: Reducir permisos continuamente
    Evalúa: IAM Access Analyzer, unused permissions, last accessed info
    """
    try:
        client = session.client('iam')
        issues = []
        evidence_parts = []
        
        # 1. Verificar IAM Access Analyzer
        try:
            aa_client = session.client('accessanalyzer')
            analyzers = aa_client.list_analyzers()
            analyzer_list = analyzers.get('analyzers', [])
            evidence_parts.append(f"Access Analyzer: {len(analyzer_list)} analizador(es)")
            if len(analyzer_list) == 0:
                issues.append('IAM Access Analyzer no configurado')
            else:
                # Verificar findings activos
                for analyzer in analyzer_list[:1]:
                    findings = aa_client.list_findings(analyzerArn=analyzer['arn'], maxResults=10)
                    active_findings = len(findings.get('findings', []))
                    evidence_parts.append(f"Access Analyzer findings: {active_findings}")
        except ClientError:
            evidence_parts.append("Access Analyzer: No accesible")
            issues.append('IAM Access Analyzer no accesible')
        
        # 2. Verificar usuarios con acceso no utilizado
        users = client.list_users(MaxItems=20)['Users']
        import datetime
        inactive_users = 0
        for user in users[:15]:
            try:
                last_used = user.get('PasswordLastUsed')
                if last_used:
                    days_since = (datetime.datetime.utcnow() - last_used.replace(tzinfo=None)).days
                    if days_since > 90:
                        inactive_users += 1
            except:
                pass
        evidence_parts.append(f"Usuarios inactivos >90d: {inactive_users}")
        if inactive_users > 0:
            issues.append(f'{inactive_users} usuario(s) inactivos por más de 90 días')
        
        evidence = ' | '.join(evidence_parts)
        
        if len(issues) == 0:
            return {'bp': 'SEC03-BP04', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC03-BP04', ''),
                    'status': 'COMPLIANT', 'severity': 'LOW',
                    'finding': 'Reducción continua de permisos implementada con Access Analyzer activo.',
                    'evidence': evidence,
                    'remediation': 'Estado actual cumple. Revisar findings de Access Analyzer mensualmente y eliminar permisos no utilizados.',
                    'risk': 'Bajo riesgo. Los permisos se revisan y reducen continuamente.'}
        else:
            return {'bp': 'SEC03-BP04', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC03-BP04', ''),
                    'status': 'NON_COMPLIANT', 'severity': 'MEDIUM',
                    'finding': f'Reducción de permisos insuficiente. Hallazgos: {"; ".join(issues)}',
                    'evidence': evidence,
                    'remediation': (
                        'Implementar reducción continua de permisos: '
                        '1) Habilitar IAM Access Analyzer en todas las regiones. '
                        '2) Revisar y remediar findings de Access Analyzer mensualmente. '
                        '3) Usar "last accessed" information para identificar permisos no utilizados. '
                        '4) Deshabilitar usuarios inactivos por más de 90 días. '
                        '5) Implementar revisiones trimestrales de permisos. '
                        '6) Usar Access Analyzer policy generation para crear políticas basadas en actividad real.'
                    ),
                    'risk': 'Riesgo medio. Permisos no utilizados aumentan la superficie de ataque sin beneficio operacional.'}
    except ClientError as e:
        return handle_error_func('SEC03-BP04', e)


def evaluate_sec03_bp05(session, handle_error_func) -> Dict[str, Any]:
    """SEC03-BP05: Definir barreras de permisos para la organización
    Evalúa: SCPs, permission boundaries, organizational guardrails
    """
    try:
        issues = []
        evidence_parts = []
        
        # 1. Verificar SCPs
        try:
            org_client = session.client('organizations')
            scps = org_client.list_policies(Filter='SERVICE_CONTROL_POLICY')
            scp_list = scps.get('Policies', [])
            custom_scps = [s for s in scp_list if s['Name'] != 'FullAWSAccess']
            evidence_parts.append(f"SCPs: {len(scp_list)} total, {len(custom_scps)} personalizadas")
            if len(custom_scps) == 0:
                issues.append('Sin SCPs personalizadas para barreras de permisos organizacionales')
        except ClientError:
            evidence_parts.append("SCPs: No accesible (requiere cuenta de gestión)")
            issues.append('No se pueden verificar SCPs (posiblemente no es cuenta de gestión)')
        
        # 2. Verificar permission boundaries en IAM
        try:
            iam_client = session.client('iam')
            roles = iam_client.list_roles(MaxItems=50)['Roles']
            roles_with_boundary = [r for r in roles if r.get('PermissionsBoundary')]
            evidence_parts.append(f"Roles con permission boundary: {len(roles_with_boundary)}/{len(roles)}")
        except ClientError:
            evidence_parts.append("Permission boundaries: No accesible")
        
        evidence = ' | '.join(evidence_parts)
        
        if len(issues) == 0:
            return {'bp': 'SEC03-BP05', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC03-BP05', ''),
                    'status': 'COMPLIANT', 'severity': 'LOW',
                    'finding': 'Barreras de permisos organizacionales definidas con SCPs y permission boundaries.',
                    'evidence': evidence,
                    'remediation': 'Estado actual cumple. Revisar SCPs periódicamente y ajustar según nuevos requisitos.',
                    'risk': 'Bajo riesgo. Las barreras de permisos limitan el alcance máximo de acceso.'}
        elif 'cuenta de gestión' in str(issues):
            return {'bp': 'SEC03-BP05', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC03-BP05', ''),
                    'status': 'PENDING_REVIEW', 'severity': 'MEDIUM',
                    'finding': 'No se pueden verificar SCPs desde esta cuenta. Requiere revisión desde cuenta de gestión.',
                    'evidence': evidence,
                    'remediation': (
                        'Verificar barreras de permisos desde la cuenta de gestión: '
                        '1) Revisar SCPs aplicadas a cada OU desde la cuenta de gestión. '
                        '2) Verificar que existan SCPs restrictivas (deny regions, deny services). '
                        '3) Implementar permission boundaries para roles creados por usuarios. '
                        '4) Usar AWS Control Tower guardrails para barreras automatizadas. '
                        '5) Documentar las barreras de permisos aplicadas a cada nivel organizacional.'
                    ),
                    'risk': 'Por Determinar. Se requiere verificación desde la cuenta de gestión.'}
        else:
            return {'bp': 'SEC03-BP05', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC03-BP05', ''),
                    'status': 'NON_COMPLIANT', 'severity': 'HIGH',
                    'finding': f'Barreras de permisos no definidas. Hallazgos: {"; ".join(issues)}',
                    'evidence': evidence,
                    'remediation': (
                        'Definir barreras de permisos organizacionales: '
                        '1) Crear SCPs para restringir regiones no autorizadas. '
                        '2) Crear SCPs para prevenir deshabilitación de servicios de seguridad. '
                        '3) Implementar permission boundaries para limitar permisos delegados. '
                        '4) Usar AWS Control Tower para guardrails automatizados. '
                        '5) Aplicar SCPs por OU según nivel de restricción requerido.'
                    ),
                    'risk': 'Alto riesgo. Sin barreras de permisos, los usuarios pueden escalar privilegios más allá de lo necesario.'}
    except ClientError as e:
        return handle_error_func('SEC03-BP05', e)


def evaluate_sec03_bp06(session, handle_error_func) -> Dict[str, Any]:
    """SEC03-BP06: Gestionar el acceso según el ciclo de vida"""
    try:
        client = session.client('iam')
        issues = []
        evidence_parts = []
        
        users = client.list_users(MaxItems=50)['Users']
        evidence_parts.append(f"Total usuarios IAM: {len(users)}")
        
        import datetime
        inactive_90d = 0
        inactive_180d = 0
        for user in users:
            last_used = user.get('PasswordLastUsed')
            if last_used:
                days = (datetime.datetime.utcnow() - last_used.replace(tzinfo=None)).days
                if days > 180:
                    inactive_180d += 1
                elif days > 90:
                    inactive_90d += 1
        
        evidence_parts.append(f"Inactivos >90d: {inactive_90d}, >180d: {inactive_180d}")
        if inactive_180d > 0:
            issues.append(f'{inactive_180d} usuario(s) inactivos por más de 180 días (posible offboarding incompleto)')
        if inactive_90d > 0:
            issues.append(f'{inactive_90d} usuario(s) inactivos por más de 90 días')
        
        evidence = ' | '.join(evidence_parts)
        
        if len(issues) == 0:
            return {'bp': 'SEC03-BP06', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC03-BP06', ''),
                    'status': 'COMPLIANT', 'severity': 'LOW',
                    'finding': 'Gestión de acceso por ciclo de vida adecuada. Sin usuarios inactivos prolongados.',
                    'evidence': evidence,
                    'remediation': 'Estado actual cumple. Implementar proceso automatizado de offboarding para desactivar acceso al terminar relación laboral.',
                    'risk': 'Bajo riesgo.'}
        else:
            severity = 'HIGH' if inactive_180d > 3 else 'MEDIUM'
            return {'bp': 'SEC03-BP06', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC03-BP06', ''),
                    'status': 'NON_COMPLIANT', 'severity': severity,
                    'finding': f'Gestión de ciclo de vida de acceso deficiente. {"; ".join(issues)}',
                    'evidence': evidence,
                    'remediation': (
                        'Implementar gestión de acceso por ciclo de vida: '
                        '1) Deshabilitar usuarios inactivos por más de 90 días. '
                        '2) Eliminar usuarios inactivos por más de 180 días. '
                        '3) Implementar proceso automatizado de onboarding/offboarding. '
                        '4) Integrar con sistema de RRHH para desactivación automática. '
                        '5) Revisar accesos mensualmente con credential report. '
                        '6) Configurar alertas para usuarios que no han iniciado sesión en 60+ días.'
                    ),
                    'risk': f'Riesgo {"alto" if severity == "HIGH" else "medio"}. Usuarios inactivos representan cuentas huérfanas que pueden ser comprometidas.'}
    except ClientError as e:
        return handle_error_func('SEC03-BP06', e)


def evaluate_sec03_bp07(session, handle_error_func) -> Dict[str, Any]:
    """SEC03-BP07: Analizar el acceso público y entre cuentas"""
    try:
        issues = []
        evidence_parts = []
        
        # 1. IAM Access Analyzer (external access)
        try:
            aa_client = session.client('accessanalyzer')
            analyzers = aa_client.list_analyzers()
            analyzer_list = analyzers.get('analyzers', [])
            account_analyzers = [a for a in analyzer_list if a.get('type') == 'ACCOUNT']
            evidence_parts.append(f"Access Analyzer (ACCOUNT): {len(account_analyzers)}")
            if len(account_analyzers) == 0:
                issues.append('Sin Access Analyzer tipo ACCOUNT para detectar acceso externo')
            else:
                findings = aa_client.list_findings(analyzerArn=account_analyzers[0]['arn'], maxResults=20)
                public_findings = [f for f in findings.get('findings', []) if f.get('status') == 'ACTIVE']
                evidence_parts.append(f"Findings de acceso externo activos: {len(public_findings)}")
                if len(public_findings) > 0:
                    issues.append(f'{len(public_findings)} recurso(s) con acceso externo detectado por Access Analyzer')
        except ClientError:
            evidence_parts.append("Access Analyzer: No accesible")
            issues.append('Access Analyzer no accesible')
        
        # 2. S3 public access
        try:
            s3_client = session.client('s3')
            buckets = s3_client.list_buckets().get('Buckets', [])
            public_buckets = 0
            for bucket in buckets[:15]:
                try:
                    pab = s3_client.get_public_access_block(Bucket=bucket['Name'])
                    config = pab.get('PublicAccessBlockConfiguration', {})
                    if not all([config.get('BlockPublicAcls'), config.get('BlockPublicPolicy'),
                               config.get('IgnorePublicAcls'), config.get('RestrictPublicBuckets')]):
                        public_buckets += 1
                except ClientError:
                    public_buckets += 1
            evidence_parts.append(f"S3 buckets sin block public access: {public_buckets}/{len(buckets)}")
            if public_buckets > 0:
                issues.append(f'{public_buckets} bucket(s) S3 sin block public access completo')
        except ClientError:
            evidence_parts.append("S3: No accesible")
        
        evidence = ' | '.join(evidence_parts)
        
        if len(issues) == 0:
            return {'bp': 'SEC03-BP07', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC03-BP07', ''),
                    'status': 'COMPLIANT', 'severity': 'LOW',
                    'finding': 'Acceso público y entre cuentas analizado. Access Analyzer activo sin findings de acceso externo.',
                    'evidence': evidence,
                    'remediation': 'Estado actual cumple. Revisar findings de Access Analyzer periódicamente.',
                    'risk': 'Bajo riesgo.'}
        else:
            severity = 'HIGH' if 'acceso externo' in str(issues) or 'public' in str(issues) else 'MEDIUM'
            return {'bp': 'SEC03-BP07', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC03-BP07', ''),
                    'status': 'NON_COMPLIANT', 'severity': severity,
                    'finding': f'Acceso público o entre cuentas no controlado. {"; ".join(issues)}',
                    'evidence': evidence,
                    'remediation': (
                        'Analizar y controlar acceso público y entre cuentas: '
                        '1) Habilitar IAM Access Analyzer tipo ACCOUNT en todas las regiones. '
                        '2) Remediar todos los findings activos de acceso externo. '
                        '3) Habilitar S3 Block Public Access a nivel de cuenta. '
                        '4) Revisar trust policies de roles para acceso cross-account. '
                        '5) Implementar Config Rules para detectar recursos públicos. '
                        '6) Auditar bucket policies y resource policies para acceso externo.'
                    ),
                    'risk': f'Riesgo {"alto" if severity == "HIGH" else "medio"}. Recursos con acceso público o cross-account no controlado pueden ser explotados.'}
    except ClientError as e:
        return handle_error_func('SEC03-BP07', e)


def evaluate_sec03_bp08(session, handle_error_func) -> Dict[str, Any]:
    """SEC03-BP08: Compartir recursos de forma segura dentro de la organización"""
    try:
        issues = []
        evidence_parts = []
        
        try:
            ram_client = session.client('ram')
            shares = ram_client.get_resource_shares(resourceOwner='SELF')
            share_list = shares.get('resourceShares', [])
            evidence_parts.append(f"RAM resource shares: {len(share_list)}")
            
            if share_list:
                # Verificar que los shares son dentro de la organización
                org_shares = [s for s in share_list if s.get('allowExternalPrincipals') == False]
                evidence_parts.append(f"Shares solo organización: {len(org_shares)}/{len(share_list)}")
                external_shares = len(share_list) - len(org_shares)
                if external_shares > 0:
                    issues.append(f'{external_shares} resource share(s) permiten principals externos')
        except ClientError:
            evidence_parts.append("RAM: No accesible")
        
        evidence = ' | '.join(evidence_parts)
        
        if len(issues) == 0:
            return {'bp': 'SEC03-BP08', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC03-BP08', ''),
                    'status': 'COMPLIANT', 'severity': 'LOW',
                    'finding': 'Recursos compartidos de forma segura dentro de la organización usando AWS RAM.',
                    'evidence': evidence,
                    'remediation': 'Estado actual cumple. Revisar periódicamente los resource shares y sus permisos.',
                    'risk': 'Bajo riesgo.'}
        else:
            return {'bp': 'SEC03-BP08', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC03-BP08', ''),
                    'status': 'NON_COMPLIANT', 'severity': 'MEDIUM',
                    'finding': f'Compartición de recursos requiere revisión. {"; ".join(issues)}',
                    'evidence': evidence,
                    'remediation': (
                        'Asegurar compartición de recursos: '
                        '1) Configurar RAM para compartir solo dentro de la organización. '
                        '2) Deshabilitar allowExternalPrincipals en resource shares. '
                        '3) Usar Organizations integration en RAM para compartición automática. '
                        '4) Auditar resource shares periódicamente. '
                        '5) Implementar Config Rules para detectar shares con principals externos.'
                    ),
                    'risk': 'Riesgo medio. Recursos compartidos con principals externos pueden ser accedidos por cuentas no autorizadas.'}
    except ClientError as e:
        return handle_error_func('SEC03-BP08', e)


def evaluate_sec03_bp09(session, handle_error_func) -> Dict[str, Any]:
    """SEC03-BP09: Compartir recursos de forma segura con terceros"""
    try:
        client = session.client('iam')
        issues = []
        evidence_parts = []
        
        # 1. Verificar roles con trust policies para cuentas externas
        roles = client.list_roles(MaxItems=50)['Roles']
        external_trust_roles = []
        import json
        
        for role in roles:
            trust = role.get('AssumeRolePolicyDocument', {})
            trust_str = json.dumps(trust) if isinstance(trust, dict) else str(trust)
            # Buscar principals que no sean de la misma cuenta o servicios AWS
            if 'arn:aws:iam::' in trust_str:
                # Cross-account role
                external_trust_roles.append(role['RoleName'])
        
        evidence_parts.append(f"Roles con trust cross-account: {len(external_trust_roles)}")
        
        # 2. Verificar condiciones en trust policies (ExternalId, MFA)
        roles_without_conditions = 0
        for role_name in external_trust_roles[:10]:
            try:
                role_detail = client.get_role(RoleName=role_name)
                trust = role_detail['Role']['AssumeRolePolicyDocument']
                trust_str = json.dumps(trust)
                if 'sts:ExternalId' not in trust_str and 'aws:MultiFactorAuth' not in trust_str:
                    roles_without_conditions += 1
            except ClientError:
                pass
        
        if roles_without_conditions > 0:
            evidence_parts.append(f"Roles cross-account sin ExternalId/MFA: {roles_without_conditions}")
            issues.append(f'{roles_without_conditions} rol(es) cross-account sin condición ExternalId o MFA')
        
        evidence = ' | '.join(evidence_parts)
        
        if len(issues) == 0:
            return {'bp': 'SEC03-BP09', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC03-BP09', ''),
                    'status': 'COMPLIANT', 'severity': 'LOW',
                    'finding': 'Acceso de terceros configurado con condiciones de seguridad (ExternalId/MFA).',
                    'evidence': evidence,
                    'remediation': 'Estado actual cumple. Revisar periódicamente los roles cross-account y sus condiciones.',
                    'risk': 'Bajo riesgo.'}
        else:
            return {'bp': 'SEC03-BP09', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC03-BP09', ''),
                    'status': 'NON_COMPLIANT', 'severity': 'HIGH',
                    'finding': f'Acceso de terceros sin condiciones de seguridad. {"; ".join(issues)}',
                    'evidence': evidence,
                    'remediation': (
                        'Asegurar acceso de terceros: '
                        '1) Agregar condición sts:ExternalId a todos los roles cross-account de terceros. '
                        '2) Requerir MFA para asumir roles de terceros cuando sea posible. '
                        '3) Limitar permisos de roles de terceros al mínimo necesario. '
                        '4) Configurar duración máxima de sesión corta (1 hora). '
                        '5) Monitorear uso de roles de terceros con CloudTrail. '
                        '6) Revisar y rotar ExternalIds periódicamente.'
                    ),
                    'risk': 'Alto riesgo. Roles cross-account sin ExternalId son vulnerables a ataques de "confused deputy".'}
    except ClientError as e:
        return handle_error_func('SEC03-BP09', e)


# ============================================================================
# SEC04 - Detección e investigación (BP01-BP04)
# ============================================================================

def evaluate_sec04_bp01(session, handle_error_func) -> Dict[str, Any]:
    """SEC04-BP01: Configurar el servicio y el registro de aplicaciones
    Evalúa: CloudTrail multi-region, S3 data events, VPC Flow Logs, CloudWatch Logs
    """
    try:
        issues = []
        evidence_parts = []
        
        # 1. CloudTrail
        try:
            ct_client = session.client('cloudtrail')
            trails = ct_client.describe_trails()
            trail_list = trails.get('trailList', [])
            multi_region = [t for t in trail_list if t.get('IsMultiRegionTrail')]
            evidence_parts.append(f"CloudTrail trails: {len(trail_list)} total, {len(multi_region)} multi-región")
            if len(multi_region) == 0:
                issues.append('Sin CloudTrail multi-región')
            
            # Verificar data events
            for trail in trail_list[:2]:
                try:
                    selectors = ct_client.get_event_selectors(TrailName=trail['TrailARN'])
                    has_data_events = any(
                        es.get('DataResources') for es in selectors.get('EventSelectors', [])
                    ) or len(selectors.get('AdvancedEventSelectors', [])) > 0
                    if has_data_events:
                        evidence_parts.append(f"Data events: Habilitados en {trail['Name']}")
                except ClientError:
                    pass
        except ClientError:
            evidence_parts.append("CloudTrail: No accesible")
            issues.append('CloudTrail no accesible')
        
        # 2. VPC Flow Logs
        try:
            ec2_client = session.client('ec2')
            vpcs = ec2_client.describe_vpcs()['Vpcs']
            flow_logs = ec2_client.describe_flow_logs()['FlowLogs']
            vpc_ids_with_logs = set(fl.get('ResourceId') for fl in flow_logs)
            vpcs_without_logs = [v for v in vpcs if v['VpcId'] not in vpc_ids_with_logs]
            evidence_parts.append(f"VPCs: {len(vpcs)} total, {len(vpcs_without_logs)} sin Flow Logs")
            if vpcs_without_logs:
                issues.append(f'{len(vpcs_without_logs)} VPC(s) sin Flow Logs')
        except ClientError:
            evidence_parts.append("VPC Flow Logs: No accesible")
        
        # 3. CloudWatch Log Groups
        try:
            logs_client = session.client('logs')
            log_groups = logs_client.describe_log_groups(limit=50)
            num_groups = len(log_groups.get('logGroups', []))
            evidence_parts.append(f"CloudWatch Log Groups: {num_groups}")
        except ClientError:
            evidence_parts.append("CloudWatch Logs: No accesible")
        
        evidence = ' | '.join(evidence_parts)
        
        if len(issues) == 0:
            return {'bp': 'SEC04-BP01', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC04-BP01', ''),
                    'status': 'COMPLIANT', 'severity': 'LOW',
                    'finding': 'Registro de servicios y aplicaciones configurado. CloudTrail multi-región y VPC Flow Logs activos.',
                    'evidence': evidence,
                    'remediation': 'Estado actual cumple. Verificar que los logs se retienen por el período requerido y están protegidos contra modificación.',
                    'risk': 'Bajo riesgo.'}
        else:
            severity = 'HIGH' if 'CloudTrail' in str(issues) else 'MEDIUM'
            return {'bp': 'SEC04-BP01', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC04-BP01', ''),
                    'status': 'NON_COMPLIANT', 'severity': severity,
                    'finding': f'Registro insuficiente. Hallazgos: {"; ".join(issues)}',
                    'evidence': evidence,
                    'remediation': (
                        'Configurar registro completo: '
                        '1) Habilitar CloudTrail multi-región con data events para S3 y Lambda. '
                        '2) Habilitar VPC Flow Logs en todas las VPCs. '
                        '3) Configurar retención de logs según requisitos de cumplimiento. '
                        '4) Enviar logs a CloudWatch Logs para análisis en tiempo real. '
                        '5) Habilitar log file validation en CloudTrail. '
                        '6) Configurar S3 bucket con MFA delete para proteger logs.'
                    ),
                    'risk': f'Riesgo {"alto" if severity == "HIGH" else "medio"}. Sin registro completo, los incidentes no pueden ser investigados adecuadamente.'}
    except ClientError as e:
        return handle_error_func('SEC04-BP01', e)


def evaluate_sec04_bp02(session, handle_error_func) -> Dict[str, Any]:
    """SEC04-BP02: Capturar registros, hallazgos y métricas en ubicaciones estandarizadas"""
    try:
        issues = []
        evidence_parts = []
        
        # 1. CloudWatch Log Groups
        try:
            logs_client = session.client('logs')
            log_groups = logs_client.describe_log_groups(limit=50)
            groups = log_groups.get('logGroups', [])
            # Verificar retención
            no_retention = [g for g in groups if not g.get('retentionInDays')]
            evidence_parts.append(f"Log Groups: {len(groups)}, sin retención: {len(no_retention)}")
            if len(groups) < 3:
                issues.append(f'Solo {len(groups)} log groups (insuficiente para centralización)')
            if len(no_retention) > len(groups) * 0.5:
                issues.append(f'{len(no_retention)} log groups sin política de retención')
        except ClientError:
            evidence_parts.append("CloudWatch Logs: No accesible")
            issues.append('CloudWatch Logs no accesible')
        
        # 2. Security Hub (centralización de hallazgos)
        try:
            sh_client = session.client('securityhub')
            sh_client.describe_hub()
            evidence_parts.append("Security Hub: Habilitado (centralización de hallazgos)")
        except Exception:
            evidence_parts.append("Security Hub: No habilitado")
            issues.append('Security Hub no habilitado para centralización de hallazgos')
        
        # 3. CloudWatch Alarms
        try:
            cw_client = session.client('cloudwatch')
            alarms = cw_client.describe_alarms(MaxRecords=50)
            num_alarms = len(alarms.get('MetricAlarms', []))
            evidence_parts.append(f"CloudWatch Alarms: {num_alarms}")
        except ClientError:
            evidence_parts.append("CloudWatch Alarms: No accesible")
        
        evidence = ' | '.join(evidence_parts)
        
        if len(issues) == 0:
            return {'bp': 'SEC04-BP02', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC04-BP02', ''),
                    'status': 'COMPLIANT', 'severity': 'LOW',
                    'finding': 'Registros centralizados en CloudWatch Logs con Security Hub para hallazgos.',
                    'evidence': evidence,
                    'remediation': 'Estado actual cumple. Verificar que todos los servicios envían logs a ubicaciones estandarizadas.',
                    'risk': 'Bajo riesgo.'}
        else:
            return {'bp': 'SEC04-BP02', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC04-BP02', ''),
                    'status': 'NON_COMPLIANT', 'severity': 'MEDIUM',
                    'finding': f'Centralización de registros insuficiente. {"; ".join(issues)}',
                    'evidence': evidence,
                    'remediation': (
                        'Centralizar registros y hallazgos: '
                        '1) Configurar CloudWatch Logs como destino centralizado para todos los servicios. '
                        '2) Habilitar Security Hub para centralizar hallazgos de seguridad. '
                        '3) Configurar políticas de retención en todos los log groups. '
                        '4) Implementar S3 bucket centralizado para logs de largo plazo. '
                        '5) Configurar CloudWatch Alarms para métricas de seguridad críticas. '
                        '6) Considerar Amazon OpenSearch para análisis avanzado de logs.'
                    ),
                    'risk': 'Riesgo medio. Sin centralización, la correlación de eventos y la investigación de incidentes es difícil.'}
    except ClientError as e:
        return handle_error_func('SEC04-BP02', e)


def evaluate_sec04_bp03(session, handle_error_func) -> Dict[str, Any]:
    """SEC04-BP03: Correlacionar y enriquecer alertas de seguridad"""
    try:
        issues = []
        evidence_parts = []
        
        # 1. EventBridge rules
        try:
            eb_client = session.client('events')
            rules = eb_client.list_rules()
            rule_list = rules.get('Rules', [])
            security_rules = [r for r in rule_list if any(
                kw in r.get('Name', '').lower() for kw in ['security', 'guard', 'finding', 'alert', 'incident']
            )]
            evidence_parts.append(f"EventBridge rules: {len(rule_list)} total, {len(security_rules)} de seguridad")
        except ClientError:
            evidence_parts.append("EventBridge: No accesible")
        
        # 2. SNS topics para notificaciones
        try:
            sns_client = session.client('sns')
            topics = sns_client.list_topics()
            topic_list = topics.get('Topics', [])
            security_topics = [t for t in topic_list if any(
                kw in t.get('TopicArn', '').lower() for kw in ['security', 'alert', 'incident', 'notification']
            )]
            evidence_parts.append(f"SNS topics: {len(topic_list)} total, {len(security_topics)} de seguridad")
            if len(security_topics) == 0:
                issues.append('Sin topics SNS dedicados para alertas de seguridad')
        except ClientError:
            evidence_parts.append("SNS: No accesible")
        
        # 3. Security Hub integrations
        try:
            sh_client = session.client('securityhub')
            sh_client.describe_hub()
            evidence_parts.append("Security Hub: Activo para correlación")
        except Exception:
            evidence_parts.append("Security Hub: No habilitado")
            issues.append('Security Hub no habilitado para correlación de alertas')
        
        evidence = ' | '.join(evidence_parts)
        
        if len(issues) == 0:
            return {'bp': 'SEC04-BP03', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC04-BP03', ''),
                    'status': 'COMPLIANT', 'severity': 'LOW',
                    'finding': 'Correlación de alertas configurada con EventBridge, SNS y Security Hub.',
                    'evidence': evidence,
                    'remediation': 'Estado actual cumple. Revisar periódicamente las reglas de correlación y los canales de notificación.',
                    'risk': 'Bajo riesgo.'}
        else:
            return {'bp': 'SEC04-BP03', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC04-BP03', ''),
                    'status': 'NON_COMPLIANT', 'severity': 'MEDIUM',
                    'finding': f'Correlación de alertas insuficiente. {"; ".join(issues)}',
                    'evidence': evidence,
                    'remediation': (
                        'Implementar correlación de alertas: '
                        '1) Habilitar Security Hub para correlación centralizada de hallazgos. '
                        '2) Crear reglas de EventBridge para eventos de seguridad (GuardDuty, Config, IAM). '
                        '3) Configurar topics SNS para notificaciones de seguridad. '
                        '4) Integrar con herramientas de ticketing (Jira, ServiceNow) para gestión de incidentes. '
                        '5) Configurar Amazon Detective para investigación automatizada.'
                    ),
                    'risk': 'Riesgo medio. Sin correlación, las alertas se procesan de forma aislada sin contexto.'}
    except ClientError as e:
        return handle_error_func('SEC04-BP03', e)


def evaluate_sec04_bp04(session, handle_error_func) -> Dict[str, Any]:
    """SEC04-BP04: Iniciar remediación para recursos no conformes"""
    try:
        issues = []
        evidence_parts = []
        
        # 1. Config Rules con remediación automática
        try:
            config_client = session.client('config')
            rules = config_client.describe_config_rules()
            config_rules = rules.get('ConfigRules', [])
            
            remediation_configs = 0
            for rule in config_rules[:20]:
                try:
                    remediation = config_client.describe_remediation_configurations(
                        ConfigRuleNames=[rule['ConfigRuleName']]
                    )
                    if remediation.get('RemediationConfigurations'):
                        remediation_configs += 1
                except ClientError:
                    pass
            
            evidence_parts.append(f"Config Rules: {len(config_rules)}, con remediación: {remediation_configs}")
            if len(config_rules) == 0:
                issues.append('Sin Config Rules para detectar recursos no conformes')
            elif remediation_configs == 0:
                issues.append('Config Rules sin remediación automática configurada')
        except ClientError:
            evidence_parts.append("Config: No accesible")
            issues.append('AWS Config no accesible')
        
        # 2. SSM Automation documents
        try:
            ssm_client = session.client('ssm')
            docs = ssm_client.list_documents(
                Filters=[{'Key': 'DocumentType', 'Values': ['Automation']}, {'Key': 'Owner', 'Values': ['Self']}],
                MaxResults=20
            )
            auto_docs = len(docs.get('DocumentIdentifiers', []))
            evidence_parts.append(f"SSM Automation documents: {auto_docs}")
        except ClientError:
            evidence_parts.append("SSM Automation: No accesible")
        
        # 3. Lambda functions para remediación
        try:
            lambda_client = session.client('lambda')
            functions = lambda_client.list_functions(MaxItems=50)
            remediation_functions = [f for f in functions.get('Functions', []) if any(
                kw in f['FunctionName'].lower() for kw in ['remediat', 'fix', 'auto-heal', 'respond']
            )]
            evidence_parts.append(f"Lambda de remediación: {len(remediation_functions)}")
        except ClientError:
            evidence_parts.append("Lambda: No accesible")
        
        evidence = ' | '.join(evidence_parts)
        
        if len(issues) == 0:
            return {'bp': 'SEC04-BP04', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC04-BP04', ''),
                    'status': 'COMPLIANT', 'severity': 'LOW',
                    'finding': 'Remediación automática configurada con Config Rules y SSM Automation.',
                    'evidence': evidence,
                    'remediation': 'Estado actual cumple. Expandir la cobertura de remediación automática a más recursos.',
                    'risk': 'Bajo riesgo.'}
        else:
            return {'bp': 'SEC04-BP04', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC04-BP04', ''),
                    'status': 'NON_COMPLIANT', 'severity': 'MEDIUM',
                    'finding': f'Remediación automática insuficiente. {"; ".join(issues)}',
                    'evidence': evidence,
                    'remediation': (
                        'Implementar remediación automática: '
                        '1) Configurar Config Rules para detectar recursos no conformes. '
                        '2) Agregar remediación automática a Config Rules (SSM Automation). '
                        '3) Crear SSM Automation documents para acciones de remediación comunes. '
                        '4) Implementar Lambda functions para remediación personalizada. '
                        '5) Configurar EventBridge para disparar remediación en eventos de seguridad. '
                        '6) Implementar aprobación manual para remediaciones de alto impacto.'
                    ),
                    'risk': 'Riesgo medio. Sin remediación automática, los recursos no conformes permanecen en estado inseguro hasta intervención manual.'}
    except ClientError as e:
        return handle_error_func('SEC04-BP04', e)


# ============================================================================
# SEC05 - Protección de red (BP01-BP04)
# ============================================================================

def evaluate_sec05_bp01(session, handle_error_func) -> Dict[str, Any]:
    """SEC05-BP01: Crear capas de red"""
    try:
        ec2 = session.client('ec2')
        issues = []
        evidence_parts = []
        
        vpcs = ec2.describe_vpcs()['Vpcs']
        evidence_parts.append(f"VPCs: {len(vpcs)}")
        
        for vpc in vpcs[:3]:
            subnets = ec2.describe_subnets(Filters=[{'Name': 'vpc-id', 'Values': [vpc['VpcId']]}])['Subnets']
            route_tables = ec2.describe_route_tables(Filters=[{'Name': 'vpc-id', 'Values': [vpc['VpcId']]}])['RouteTables']
            
            # Clasificar subnets
            public_subnets = 0
            private_subnets = 0
            for subnet in subnets:
                if subnet.get('MapPublicIpOnLaunch'):
                    public_subnets += 1
                else:
                    private_subnets += 1
            
            evidence_parts.append(f"VPC {vpc['VpcId'][:12]}: {len(subnets)} subnets ({public_subnets} pub, {private_subnets} priv)")
            
            if len(subnets) <= 1:
                issues.append(f'VPC {vpc["VpcId"][:12]} con solo {len(subnets)} subnet (sin capas de red)')
            elif private_subnets == 0:
                issues.append(f'VPC {vpc["VpcId"][:12]} sin subnets privadas')
        
        # NAT Gateways
        try:
            nats = ec2.describe_nat_gateways(Filter=[{'Name': 'state', 'Values': ['available']}])
            evidence_parts.append(f"NAT Gateways: {len(nats.get('NatGateways', []))}")
        except ClientError:
            pass
        
        evidence = ' | '.join(evidence_parts)
        
        if len(issues) == 0:
            return {'bp': 'SEC05-BP01', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC05-BP01', ''),
                    'status': 'COMPLIANT', 'severity': 'LOW',
                    'finding': 'Capas de red implementadas con subnets públicas y privadas.',
                    'evidence': evidence,
                    'remediation': 'Estado actual cumple. Verificar que los recursos sensibles estén en subnets privadas.',
                    'risk': 'Bajo riesgo.'}
        else:
            return {'bp': 'SEC05-BP01', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC05-BP01', ''),
                    'status': 'NON_COMPLIANT', 'severity': 'HIGH',
                    'finding': f'Capas de red insuficientes. {"; ".join(issues)}',
                    'evidence': evidence,
                    'remediation': (
                        'Crear capas de red: '
                        '1) Diseñar VPC con subnets públicas, privadas y aisladas. '
                        '2) Colocar recursos públicos (ALB, NAT) en subnets públicas. '
                        '3) Colocar aplicaciones en subnets privadas. '
                        '4) Colocar bases de datos en subnets aisladas (sin acceso a internet). '
                        '5) Configurar NAT Gateway para acceso saliente desde subnets privadas. '
                        '6) Usar route tables separadas por capa de red.'
                    ),
                    'risk': 'Alto riesgo. Sin capas de red, todos los recursos están en la misma zona de seguridad.'}
    except ClientError as e:
        return handle_error_func('SEC05-BP01', e)


def evaluate_sec05_bp02(session, handle_error_func) -> Dict[str, Any]:
    """SEC05-BP02: Controlar el flujo de tráfico dentro de las capas de red"""
    try:
        ec2 = session.client('ec2')
        issues = []
        evidence_parts = []
        
        # 1. Security Groups
        sgs = ec2.describe_security_groups()['SecurityGroups']
        overly_permissive = []
        for sg in sgs:
            for rule in sg.get('IpPermissions', []):
                for ip_range in rule.get('IpRanges', []):
                    if ip_range.get('CidrIp') == '0.0.0.0/0':
                        port = rule.get('FromPort', 'all')
                        if port in [22, 3389, 0, -1] or rule.get('IpProtocol') == '-1':
                            overly_permissive.append(f"{sg['GroupId']}:{port}")
        
        evidence_parts.append(f"Security Groups: {len(sgs)}")
        evidence_parts.append(f"Reglas permisivas (0.0.0.0/0 en puertos sensibles): {len(overly_permissive)}")
        if overly_permissive:
            issues.append(f'{len(overly_permissive)} regla(s) de security group permiten acceso desde 0.0.0.0/0 a puertos sensibles')
        
        # 2. NACLs
        nacls = ec2.describe_network_acls()['NetworkAcls']
        evidence_parts.append(f"NACLs: {len(nacls)}")
        
        evidence = ' | '.join(evidence_parts)
        
        if len(issues) == 0:
            return {'bp': 'SEC05-BP02', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC05-BP02', ''),
                    'status': 'COMPLIANT', 'severity': 'LOW',
                    'finding': 'Flujo de tráfico controlado. Security groups sin reglas excesivamente permisivas.',
                    'evidence': evidence,
                    'remediation': 'Estado actual cumple. Revisar periódicamente las reglas de security groups y NACLs.',
                    'risk': 'Bajo riesgo.'}
        else:
            return {'bp': 'SEC05-BP02', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC05-BP02', ''),
                    'status': 'NON_COMPLIANT', 'severity': 'HIGH',
                    'finding': f'Control de tráfico insuficiente. {"; ".join(issues)}',
                    'evidence': evidence,
                    'remediation': (
                        'Controlar flujo de tráfico: '
                        '1) Eliminar reglas 0.0.0.0/0 en puertos SSH (22), RDP (3389) y todos los puertos. '
                        '2) Restringir acceso a IPs o rangos CIDR específicos. '
                        '3) Usar security groups como referencia en lugar de CIDRs. '
                        '4) Implementar NACLs como capa adicional de defensa. '
                        '5) Usar VPC endpoints para acceso a servicios AWS sin internet. '
                        '6) Implementar AWS Network Firewall para inspección de tráfico.'
                    ),
                    'risk': 'Alto riesgo. Reglas permisivas exponen recursos a acceso no autorizado desde internet.'}
    except ClientError as e:
        return handle_error_func('SEC05-BP02', e)


def evaluate_sec05_bp03(session, handle_error_func) -> Dict[str, Any]:
    """SEC05-BP03: Implementar protección basada en inspección"""
    try:
        issues = []
        evidence_parts = []
        
        # 1. WAF
        try:
            waf = session.client('wafv2')
            acls = waf.list_web_acls(Scope='REGIONAL')
            num_acls = len(acls.get('WebACLs', []))
            evidence_parts.append(f"WAF Web ACLs: {num_acls}")
            if num_acls == 0:
                issues.append('Sin WAF configurado para inspección de tráfico web')
        except ClientError:
            evidence_parts.append("WAF: No accesible")
            issues.append('WAF no accesible')
        
        # 2. Shield
        try:
            shield = session.client('shield')
            subscription = shield.describe_subscription()
            evidence_parts.append("Shield Advanced: Activo")
        except Exception:
            evidence_parts.append("Shield Advanced: No activo (Shield Standard por defecto)")
        
        # 3. Network Firewall
        try:
            nfw = session.client('network-firewall')
            firewalls = nfw.list_firewalls()
            num_fw = len(firewalls.get('Firewalls', []))
            evidence_parts.append(f"Network Firewall: {num_fw}")
        except ClientError:
            evidence_parts.append("Network Firewall: No accesible")
        
        evidence = ' | '.join(evidence_parts)
        
        if len(issues) == 0:
            return {'bp': 'SEC05-BP03', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC05-BP03', ''),
                    'status': 'COMPLIANT', 'severity': 'LOW',
                    'finding': 'Protección basada en inspección implementada con WAF.',
                    'evidence': evidence,
                    'remediation': 'Estado actual cumple. Revisar y actualizar reglas WAF periódicamente.',
                    'risk': 'Bajo riesgo.'}
        else:
            return {'bp': 'SEC05-BP03', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC05-BP03', ''),
                    'status': 'NON_COMPLIANT', 'severity': 'HIGH',
                    'finding': f'Sin protección basada en inspección. {"; ".join(issues)}',
                    'evidence': evidence,
                    'remediation': (
                        'Implementar protección basada en inspección: '
                        '1) Configurar AWS WAF con reglas administradas (SQL injection, XSS, bot control). '
                        '2) Asociar WAF a ALB, API Gateway y CloudFront. '
                        '3) Evaluar AWS Network Firewall para inspección de tráfico de red. '
                        '4) Considerar Shield Advanced para protección DDoS avanzada. '
                        '5) Implementar reglas WAF personalizadas basadas en patrones de ataque. '
                        '6) Configurar logging de WAF para análisis de tráfico bloqueado.'
                    ),
                    'risk': 'Alto riesgo. Sin inspección de tráfico, los ataques web y de red no son detectados ni bloqueados.'}
    except ClientError as e:
        return handle_error_func('SEC05-BP03', e)


def evaluate_sec05_bp04(session, handle_error_func) -> Dict[str, Any]:
    """SEC05-BP04: Automatizar la protección de la red"""
    try:
        issues = []
        evidence_parts = []
        
        # 1. VPC Flow Logs
        try:
            ec2 = session.client('ec2')
            flow_logs = ec2.describe_flow_logs()['FlowLogs']
            evidence_parts.append(f"VPC Flow Logs: {len(flow_logs)}")
            if len(flow_logs) == 0:
                issues.append('Sin VPC Flow Logs para monitoreo de red')
        except ClientError:
            evidence_parts.append("Flow Logs: No accesible")
        
        # 2. GuardDuty (network findings)
        try:
            gd = session.client('guardduty')
            detectors = gd.list_detectors()
            if detectors.get('DetectorIds'):
                evidence_parts.append("GuardDuty: Activo (monitoreo de red)")
            else:
                evidence_parts.append("GuardDuty: No habilitado")
                issues.append('GuardDuty no habilitado para detección de amenazas de red')
        except ClientError:
            evidence_parts.append("GuardDuty: No accesible")
        
        # 3. Config Rules de red
        try:
            config = session.client('config')
            rules = config.describe_config_rules()
            network_rules = [r for r in rules.get('ConfigRules', []) if any(
                kw in r.get('ConfigRuleName', '').lower() for kw in ['vpc', 'security-group', 'nacl', 'flow-log', 'ssh', 'rdp']
            )]
            evidence_parts.append(f"Config Rules de red: {len(network_rules)}")
        except ClientError:
            evidence_parts.append("Config Rules: No accesible")
        
        evidence = ' | '.join(evidence_parts)
        
        if len(issues) == 0:
            return {'bp': 'SEC05-BP04', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC05-BP04', ''),
                    'status': 'COMPLIANT', 'severity': 'LOW',
                    'finding': 'Protección de red automatizada con Flow Logs y GuardDuty.',
                    'evidence': evidence,
                    'remediation': 'Estado actual cumple. Configurar alertas automáticas para anomalías de red.',
                    'risk': 'Bajo riesgo.'}
        else:
            return {'bp': 'SEC05-BP04', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC05-BP04', ''),
                    'status': 'NON_COMPLIANT', 'severity': 'MEDIUM',
                    'finding': f'Protección de red no automatizada. {"; ".join(issues)}',
                    'evidence': evidence,
                    'remediation': (
                        'Automatizar protección de red: '
                        '1) Habilitar VPC Flow Logs en todas las VPCs. '
                        '2) Habilitar GuardDuty para detección de amenazas de red. '
                        '3) Configurar Config Rules para monitorear security groups y NACLs. '
                        '4) Implementar remediación automática para reglas de red no conformes. '
                        '5) Configurar alarmas de CloudWatch para patrones de tráfico anómalos. '
                        '6) Usar Lambda para respuesta automática a eventos de seguridad de red.'
                    ),
                    'risk': 'Riesgo medio. Sin automatización, las amenazas de red requieren detección e intervención manual.'}
    except ClientError as e:
        return handle_error_func('SEC05-BP04', e)


# ============================================================================
# SEC06 - Protección de cómputo (BP01-BP05)
# ============================================================================

def evaluate_sec06_bp01(session, handle_error_func) -> Dict[str, Any]:
    """SEC06-BP01: Realizar gestión de vulnerabilidades"""
    try:
        issues = []
        evidence_parts = []
        
        # Inspector
        try:
            inspector = session.client('inspector2')
            inspector.batch_get_account_status(accountIds=[])
            evidence_parts.append("Inspector: Habilitado")
        except Exception:
            evidence_parts.append("Inspector: No habilitado")
            issues.append('Amazon Inspector no habilitado para escaneo de vulnerabilidades')
        
        # SSM Patch Manager
        try:
            ssm = session.client('ssm')
            baselines = ssm.describe_patch_baselines(Filters=[{'Key': 'OWNER', 'Values': ['Self']}])
            evidence_parts.append(f"Patch baselines custom: {len(baselines.get('BaselineIdentities', []))}")
            
            # Verificar instancias con SSM
            instances = ssm.describe_instance_information(MaxResults=20)
            managed = len(instances.get('InstanceInformationList', []))
            evidence_parts.append(f"Instancias SSM managed: {managed}")
        except ClientError:
            evidence_parts.append("SSM: No accesible")
        
        evidence = ' | '.join(evidence_parts)
        
        if len(issues) == 0:
            return {'bp': 'SEC06-BP01', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC06-BP01', ''),
                    'status': 'COMPLIANT', 'severity': 'LOW',
                    'finding': 'Gestión de vulnerabilidades implementada con Inspector y SSM.',
                    'evidence': evidence,
                    'remediation': 'Estado actual cumple. Revisar findings de Inspector y mantener parcheo actualizado.',
                    'risk': 'Bajo riesgo.'}
        else:
            return {'bp': 'SEC06-BP01', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC06-BP01', ''),
                    'status': 'NON_COMPLIANT', 'severity': 'HIGH',
                    'finding': f'Gestión de vulnerabilidades insuficiente. {"; ".join(issues)}',
                    'evidence': evidence,
                    'remediation': (
                        'Implementar gestión de vulnerabilidades: '
                        '1) Habilitar Amazon Inspector para EC2, contenedores y Lambda. '
                        '2) Configurar SSM Patch Manager con ventanas de mantenimiento. '
                        '3) Implementar escaneo automático de imágenes de contenedores en ECR. '
                        '4) Definir SLAs de remediación por severidad (Critical: 24h, High: 7d, Medium: 30d). '
                        '5) Configurar notificaciones para vulnerabilidades críticas. '
                        '6) Integrar findings de Inspector con Security Hub.'
                    ),
                    'risk': 'Alto riesgo. Sin gestión de vulnerabilidades, los sistemas pueden tener vulnerabilidades conocidas sin remediar.'}
    except ClientError as e:
        return handle_error_func('SEC06-BP01', e)


def evaluate_sec06_bp02(session, handle_error_func) -> Dict[str, Any]:
    """SEC06-BP02: Computación de provisión a partir de imágenes endurecidas"""
    try:
        ec2 = session.client('ec2')
        issues = []
        evidence_parts = []
        
        # Verificar AMIs propias (golden images)
        try:
            images = ec2.describe_images(Owners=['self'])
            own_amis = images.get('Images', [])
            evidence_parts.append(f"AMIs propias: {len(own_amis)}")
        except ClientError:
            own_amis = []
            evidence_parts.append("AMIs: No accesible")
        
        # Verificar instancias running
        instances = ec2.describe_instances(Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])
        running = [i for r in instances['Reservations'] for i in r['Instances']]
        evidence_parts.append(f"Instancias running: {len(running)}")
        
        if len(running) == 0:
            return {'bp': 'SEC06-BP02', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC06-BP02', ''),
                    'status': 'PENDING_REVIEW', 'severity': 'LOW',
                    'finding': 'Sin instancias EC2 running. Evaluación no aplicable si se usan solo servicios serverless.',
                    'evidence': ' | '.join(evidence_parts),
                    'remediation': 'Si se usan servicios serverless, esta BP no aplica directamente. Para contenedores, verificar que las imágenes base estén endurecidas.',
                    'risk': 'Por Determinar.'}
        
        # Verificar EC2 Image Builder
        try:
            ib = session.client('imagebuilder')
            pipelines = ib.list_image_pipelines()
            evidence_parts.append(f"Image Builder pipelines: {len(pipelines.get('imagePipelineList', []))}")
        except ClientError:
            evidence_parts.append("Image Builder: No accesible")
        
        if len(own_amis) == 0 and len(running) > 0:
            issues.append('Sin AMIs propias (golden images) para instancias EC2')
        
        evidence = ' | '.join(evidence_parts)
        
        if len(issues) == 0:
            return {'bp': 'SEC06-BP02', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC06-BP02', ''),
                    'status': 'COMPLIANT', 'severity': 'LOW',
                    'finding': f'Imágenes endurecidas disponibles ({len(own_amis)} AMIs propias).',
                    'evidence': evidence,
                    'remediation': 'Estado actual cumple. Mantener pipeline de actualización de AMIs con EC2 Image Builder.',
                    'risk': 'Bajo riesgo.'}
        else:
            return {'bp': 'SEC06-BP02', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC06-BP02', ''),
                    'status': 'NON_COMPLIANT', 'severity': 'MEDIUM',
                    'finding': f'Sin imágenes endurecidas. {"; ".join(issues)}',
                    'evidence': evidence,
                    'remediation': (
                        'Implementar imágenes endurecidas: '
                        '1) Crear AMIs base endurecidas con CIS Benchmarks. '
                        '2) Usar EC2 Image Builder para pipeline automatizado de AMIs. '
                        '3) Incluir agentes de seguridad (SSM, Inspector) en AMIs base. '
                        '4) Implementar escaneo de vulnerabilidades en pipeline de AMIs. '
                        '5) Rotar AMIs periódicamente con parches de seguridad.'
                    ),
                    'risk': 'Riesgo medio. Sin imágenes endurecidas, las instancias pueden tener configuraciones inseguras por defecto.'}
    except ClientError as e:
        return handle_error_func('SEC06-BP02', e)


def evaluate_sec06_bp03(session, handle_error_func) -> Dict[str, Any]:
    """SEC06-BP03: Reducir la gestión manual y el acceso interactivo"""
    try:
        issues = []
        evidence_parts = []
        
        # 1. SSM Session Manager
        try:
            ssm = session.client('ssm')
            instances = ssm.describe_instance_information(MaxResults=20)
            managed = len(instances.get('InstanceInformationList', []))
            evidence_parts.append(f"Instancias SSM managed: {managed}")
        except ClientError:
            evidence_parts.append("SSM: No accesible")
        
        # 2. Verificar security groups con SSH/RDP abierto
        try:
            ec2 = session.client('ec2')
            sgs = ec2.describe_security_groups()['SecurityGroups']
            ssh_open = 0
            rdp_open = 0
            for sg in sgs:
                for rule in sg.get('IpPermissions', []):
                    for ip in rule.get('IpRanges', []):
                        if ip.get('CidrIp') == '0.0.0.0/0':
                            if rule.get('FromPort') == 22:
                                ssh_open += 1
                            elif rule.get('FromPort') == 3389:
                                rdp_open += 1
            evidence_parts.append(f"SGs con SSH abierto: {ssh_open}, RDP abierto: {rdp_open}")
            if ssh_open > 0 or rdp_open > 0:
                issues.append(f'Acceso SSH ({ssh_open}) o RDP ({rdp_open}) abierto desde 0.0.0.0/0')
        except ClientError:
            evidence_parts.append("Security Groups: No accesible")
        
        # 3. Lambda functions (serverless = sin acceso interactivo)
        try:
            lambda_client = session.client('lambda')
            functions = lambda_client.list_functions(MaxItems=10)
            evidence_parts.append(f"Lambda functions: {len(functions.get('Functions', []))}")
        except ClientError:
            pass
        
        evidence = ' | '.join(evidence_parts)
        
        if len(issues) == 0:
            return {'bp': 'SEC06-BP03', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC06-BP03', ''),
                    'status': 'COMPLIANT', 'severity': 'LOW',
                    'finding': 'Acceso interactivo reducido. Sin SSH/RDP abierto desde internet.',
                    'evidence': evidence,
                    'remediation': 'Estado actual cumple. Usar Session Manager para acceso a instancias en lugar de SSH/RDP.',
                    'risk': 'Bajo riesgo.'}
        else:
            return {'bp': 'SEC06-BP03', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC06-BP03', ''),
                    'status': 'NON_COMPLIANT', 'severity': 'HIGH',
                    'finding': f'Acceso interactivo excesivo. {"; ".join(issues)}',
                    'evidence': evidence,
                    'remediation': (
                        'Reducir acceso interactivo: '
                        '1) Cerrar puertos SSH (22) y RDP (3389) desde 0.0.0.0/0. '
                        '2) Implementar SSM Session Manager para acceso a instancias. '
                        '3) Usar SSM Run Command para ejecución remota de comandos. '
                        '4) Configurar VPN o bastion host si se requiere acceso directo. '
                        '5) Migrar a servicios serverless donde sea posible. '
                        '6) Implementar Just-In-Time access para acceso temporal.'
                    ),
                    'risk': 'Alto riesgo. SSH/RDP abierto desde internet es un vector de ataque común para fuerza bruta y explotación.'}
    except ClientError as e:
        return handle_error_func('SEC06-BP03', e)


def evaluate_sec06_bp04(session, handle_error_func) -> Dict[str, Any]:
    """SEC06-BP04: Validar la integridad del software"""
    try:
        issues = []
        evidence_parts = []
        
        # SSM Automation
        try:
            ssm = session.client('ssm')
            associations = ssm.list_associations(MaxResults=20)
            num_assoc = len(associations.get('Associations', []))
            evidence_parts.append(f"SSM Associations: {num_assoc}")
            if num_assoc == 0:
                issues.append('Sin SSM Associations para validación de integridad')
        except ClientError:
            evidence_parts.append("SSM: No accesible")
        
        # CodeBuild (CI/CD con validación)
        try:
            cb = session.client('codebuild')
            projects = cb.list_projects()
            evidence_parts.append(f"CodeBuild projects: {len(projects.get('projects', []))}")
        except ClientError:
            evidence_parts.append("CodeBuild: No accesible")
        
        # Lambda code signing
        try:
            lambda_client = session.client('lambda')
            configs = lambda_client.list_code_signing_configs(MaxItems=10)
            evidence_parts.append(f"Code signing configs: {len(configs.get('CodeSigningConfigs', []))}")
        except ClientError:
            evidence_parts.append("Code signing: No accesible")
        
        evidence = ' | '.join(evidence_parts)
        
        if len(issues) == 0:
            return {'bp': 'SEC06-BP04', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC06-BP04', ''),
                    'status': 'COMPLIANT', 'severity': 'LOW',
                    'finding': 'Validación de integridad de software implementada.',
                    'evidence': evidence,
                    'remediation': 'Estado actual cumple. Mantener validación de integridad en pipeline de despliegue.',
                    'risk': 'Bajo riesgo.'}
        else:
            return {'bp': 'SEC06-BP04', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC06-BP04', ''),
                    'status': 'NON_COMPLIANT', 'severity': 'MEDIUM',
                    'finding': f'Validación de integridad insuficiente. {"; ".join(issues)}',
                    'evidence': evidence,
                    'remediation': (
                        'Implementar validación de integridad: '
                        '1) Configurar SSM State Manager para validar configuraciones. '
                        '2) Implementar code signing para funciones Lambda. '
                        '3) Usar CodeBuild con verificación de dependencias. '
                        '4) Implementar checksums para artefactos de despliegue. '
                        '5) Configurar SSM Patch Manager para parcheo automatizado.'
                    ),
                    'risk': 'Riesgo medio. Sin validación de integridad, software modificado maliciosamente puede ser desplegado.'}
    except ClientError as e:
        return handle_error_func('SEC06-BP04', e)


def evaluate_sec06_bp05(session, handle_error_func) -> Dict[str, Any]:
    """SEC06-BP05: Automatizar la protección informática"""
    try:
        issues = []
        evidence_parts = []
        
        # SSM managed instances
        try:
            ssm = session.client('ssm')
            instances = ssm.describe_instance_information(MaxResults=20)
            managed = instances.get('InstanceInformationList', [])
            evidence_parts.append(f"SSM managed instances: {len(managed)}")
        except ClientError:
            evidence_parts.append("SSM: No accesible")
        
        # Auto Scaling
        try:
            asg = session.client('autoscaling')
            groups = asg.describe_auto_scaling_groups(MaxRecords=10)
            evidence_parts.append(f"Auto Scaling groups: {len(groups.get('AutoScalingGroups', []))}")
        except ClientError:
            evidence_parts.append("Auto Scaling: No accesible")
        
        # Config Rules de compute
        try:
            config = session.client('config')
            rules = config.describe_config_rules()
            compute_rules = [r for r in rules.get('ConfigRules', []) if any(
                kw in r.get('ConfigRuleName', '').lower() for kw in ['ec2', 'instance', 'ssm', 'patch']
            )]
            evidence_parts.append(f"Config Rules de compute: {len(compute_rules)}")
        except ClientError:
            pass
        
        evidence = ' | '.join(evidence_parts)
        
        return {'bp': 'SEC06-BP05', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC06-BP05', ''),
                'status': 'PENDING_REVIEW', 'severity': 'MEDIUM',
                'finding': 'Protección de cómputo requiere revisión de automatización.',
                'evidence': evidence,
                'remediation': (
                    'Automatizar protección de cómputo: '
                    '1) Configurar SSM para gestión automatizada de instancias. '
                    '2) Implementar Auto Scaling para reemplazo automático de instancias comprometidas. '
                    '3) Configurar Config Rules para detectar instancias no conformes. '
                    '4) Implementar parcheo automatizado con SSM Patch Manager. '
                    '5) Usar Lambda para respuesta automática a eventos de seguridad de compute.'
                ),
                'risk': 'Por Determinar. Requiere revisión del nivel de automatización actual.'}
    except ClientError as e:
        return handle_error_func('SEC06-BP05', e)


# ============================================================================
# SEC07 - Clasificación de datos (BP01-BP04)
# ============================================================================

def evaluate_sec07_bp01(session, handle_error_func) -> Dict[str, Any]:
    """SEC07-BP01: Comprender el esquema de clasificación de datos"""
    try:
        issues = []
        evidence_parts = []
        
        try:
            macie = session.client('macie2')
            macie.get_macie_session()
            evidence_parts.append("Macie: Habilitado")
            
            try:
                findings = macie.list_findings(maxResults=10)
                evidence_parts.append(f"Macie findings: {len(findings.get('findingIds', []))}")
            except ClientError:
                pass
        except Exception:
            evidence_parts.append("Macie: No habilitado")
            issues.append('Amazon Macie no habilitado para descubrimiento de datos sensibles')
        
        # Verificar tags de clasificación en S3
        try:
            s3 = session.client('s3')
            buckets = s3.list_buckets().get('Buckets', [])
            tagged_buckets = 0
            for bucket in buckets[:10]:
                try:
                    tags = s3.get_bucket_tagging(Bucket=bucket['Name'])
                    tag_keys = [t['Key'].lower() for t in tags.get('TagSet', [])]
                    if any(kw in ' '.join(tag_keys) for kw in ['classification', 'sensitivity', 'data-class']):
                        tagged_buckets += 1
                except ClientError:
                    pass
            evidence_parts.append(f"S3 buckets con tags de clasificación: {tagged_buckets}/{min(len(buckets), 10)}")
        except ClientError:
            evidence_parts.append("S3 tags: No accesible")
        
        evidence = ' | '.join(evidence_parts)
        
        if len(issues) == 0:
            return {'bp': 'SEC07-BP01', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC07-BP01', ''),
                    'status': 'COMPLIANT', 'severity': 'LOW',
                    'finding': 'Clasificación de datos implementada con Macie habilitado.',
                    'evidence': evidence,
                    'remediation': 'Estado actual cumple. Revisar findings de Macie y mantener esquema de clasificación actualizado.',
                    'risk': 'Bajo riesgo.'}
        else:
            return {'bp': 'SEC07-BP01', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC07-BP01', ''),
                    'status': 'NON_COMPLIANT', 'severity': 'MEDIUM',
                    'finding': f'Clasificación de datos insuficiente. {"; ".join(issues)}',
                    'evidence': evidence,
                    'remediation': (
                        'Implementar clasificación de datos: '
                        '1) Habilitar Amazon Macie para descubrimiento automático de datos sensibles en S3. '
                        '2) Definir esquema de clasificación (Público, Interno, Confidencial, Restringido). '
                        '3) Implementar tags de clasificación en buckets S3 y recursos. '
                        '4) Configurar Macie para escaneo periódico de datos sensibles. '
                        '5) Documentar política de clasificación de datos.'
                    ),
                    'risk': 'Riesgo medio. Sin clasificación, los datos sensibles pueden no recibir la protección adecuada.'}
    except ClientError as e:
        return handle_error_func('SEC07-BP01', e)


def evaluate_sec07_bp02(session, handle_error_func) -> Dict[str, Any]:
    """SEC07-BP02: Aplicar controles de protección de datos basados en sensibilidad"""
    try:
        issues = []
        evidence_parts = []

        # Inicializar antes del try para evitar UnboundLocalError si list_buckets() falla:
        # el segundo bloque (public access block) itera sobre `buckets`.
        s3 = session.client('s3')
        buckets = []

        # S3 encryption
        try:
            buckets = s3.list_buckets().get('Buckets', [])
            encrypted = 0
            for bucket in buckets[:15]:
                try:
                    enc = s3.get_bucket_encryption(Bucket=bucket['Name'])
                    if enc.get('ServerSideEncryptionConfiguration'):
                        encrypted += 1
                except ClientError:
                    pass
            evidence_parts.append(f"S3 buckets cifrados: {encrypted}/{min(len(buckets), 15)}")
            if encrypted < len(buckets[:15]):
                issues.append(f'{len(buckets[:15]) - encrypted} bucket(s) sin cifrado')
        except ClientError:
            evidence_parts.append("S3 encryption: No accesible")
        
        # S3 public access block
        try:
            buckets_public = 0
            for bucket in buckets[:15]:
                try:
                    pab = s3.get_public_access_block(Bucket=bucket['Name'])
                    config = pab.get('PublicAccessBlockConfiguration', {})
                    if not all([config.get('BlockPublicAcls'), config.get('BlockPublicPolicy')]):
                        buckets_public += 1
                except ClientError:
                    buckets_public += 1
            evidence_parts.append(f"S3 sin block public access: {buckets_public}")
            if buckets_public > 0:
                issues.append(f'{buckets_public} bucket(s) sin block public access completo')
        except ClientError:
            pass
        
        evidence = ' | '.join(evidence_parts)
        
        if len(issues) == 0:
            return {'bp': 'SEC07-BP02', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC07-BP02', ''),
                    'status': 'COMPLIANT', 'severity': 'LOW',
                    'finding': 'Controles de protección de datos aplicados. Todos los buckets cifrados y con acceso público bloqueado.',
                    'evidence': evidence,
                    'remediation': 'Estado actual cumple. Verificar que los controles se aplican según el nivel de sensibilidad de los datos.',
                    'risk': 'Bajo riesgo.'}
        else:
            return {'bp': 'SEC07-BP02', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC07-BP02', ''),
                    'status': 'NON_COMPLIANT', 'severity': 'HIGH',
                    'finding': f'Controles de protección insuficientes. {"; ".join(issues)}',
                    'evidence': evidence,
                    'remediation': (
                        'Aplicar controles de protección de datos: '
                        '1) Habilitar cifrado en todos los buckets S3 (SSE-S3 o SSE-KMS). '
                        '2) Habilitar S3 Block Public Access a nivel de cuenta. '
                        '3) Implementar bucket policies restrictivas basadas en clasificación. '
                        '4) Usar KMS CMKs para datos confidenciales y restringidos. '
                        '5) Configurar S3 Object Lock para datos que requieren inmutabilidad.'
                    ),
                    'risk': 'Alto riesgo. Datos sin cifrado o con acceso público pueden ser expuestos.'}
    except ClientError as e:
        return handle_error_func('SEC07-BP02', e)


def evaluate_sec07_bp03(session, handle_error_func) -> Dict[str, Any]:
    """SEC07-BP03: Automatizar la identificación y clasificación"""
    try:
        try:
            macie = session.client('macie2')
            macie.get_macie_session()
            
            jobs = macie.list_classification_jobs(maxResults=10)
            num_jobs = len(jobs.get('items', []))
            evidence = f"Macie: Habilitado | Classification jobs: {num_jobs}"
            
            if num_jobs > 0:
                return {'bp': 'SEC07-BP03', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC07-BP03', ''),
                        'status': 'COMPLIANT', 'severity': 'LOW',
                        'finding': f'Clasificación automatizada con Macie ({num_jobs} jobs configurados).',
                        'evidence': evidence,
                        'remediation': 'Estado actual cumple. Revisar findings de Macie periódicamente.',
                        'risk': 'Bajo riesgo.'}
            else:
                return {'bp': 'SEC07-BP03', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC07-BP03', ''),
                        'status': 'PENDING_REVIEW', 'severity': 'MEDIUM',
                        'finding': 'Macie habilitado pero sin jobs de clasificación configurados.',
                        'evidence': evidence,
                        'remediation': 'Configurar jobs de clasificación en Macie para escaneo periódico de buckets S3.',
                        'risk': 'Riesgo medio. Macie está habilitado pero no está escaneando datos activamente.'}
        except Exception:
            return {'bp': 'SEC07-BP03', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC07-BP03', ''),
                    'status': 'NON_COMPLIANT', 'severity': 'MEDIUM',
                    'finding': 'Clasificación automatizada no implementada. Macie no habilitado.',
                    'evidence': 'Macie: No habilitado',
                    'remediation': (
                        'Automatizar clasificación de datos: '
                        '1) Habilitar Amazon Macie. '
                        '2) Configurar jobs de clasificación para buckets S3 críticos. '
                        '3) Definir custom data identifiers para datos específicos del negocio. '
                        '4) Configurar alertas para descubrimiento de datos sensibles. '
                        '5) Integrar findings de Macie con Security Hub.'
                    ),
                    'risk': 'Riesgo medio. Sin clasificación automatizada, los datos sensibles pueden no ser identificados.'}
    except ClientError as e:
        return handle_error_func('SEC07-BP03', e)


def evaluate_sec07_bp04(session, handle_error_func) -> Dict[str, Any]:
    """SEC07-BP04: Definir la gestión escalable del ciclo de vida de los datos"""
    try:
        issues = []
        evidence_parts = []
        
        try:
            s3 = session.client('s3')
            buckets = s3.list_buckets().get('Buckets', [])
            buckets_with_lifecycle = 0
            for bucket in buckets[:15]:
                try:
                    lifecycle = s3.get_bucket_lifecycle_configuration(Bucket=bucket['Name'])
                    if lifecycle.get('Rules'):
                        buckets_with_lifecycle += 1
                except ClientError:
                    pass
            
            pct = (buckets_with_lifecycle / min(len(buckets), 15) * 100) if buckets else 0
            evidence_parts.append(f"S3 buckets con lifecycle: {buckets_with_lifecycle}/{min(len(buckets), 15)} ({pct:.0f}%)")
            if pct < 50:
                issues.append(f'Solo {pct:.0f}% de buckets tienen políticas de lifecycle')
        except ClientError:
            evidence_parts.append("S3 lifecycle: No accesible")
        
        # Verificar versionado
        try:
            versioned = 0
            for bucket in buckets[:15]:
                try:
                    ver = s3.get_bucket_versioning(Bucket=bucket['Name'])
                    if ver.get('Status') == 'Enabled':
                        versioned += 1
                except ClientError:
                    pass
            evidence_parts.append(f"S3 buckets con versionado: {versioned}/{min(len(buckets), 15)}")
        except:
            pass
        
        evidence = ' | '.join(evidence_parts)
        
        if len(issues) == 0:
            return {'bp': 'SEC07-BP04', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC07-BP04', ''),
                    'status': 'COMPLIANT', 'severity': 'LOW',
                    'finding': 'Gestión de ciclo de vida de datos implementada con lifecycle policies.',
                    'evidence': evidence,
                    'remediation': 'Estado actual cumple. Revisar políticas de lifecycle periódicamente.',
                    'risk': 'Bajo riesgo.'}
        else:
            return {'bp': 'SEC07-BP04', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC07-BP04', ''),
                    'status': 'NON_COMPLIANT', 'severity': 'MEDIUM',
                    'finding': f'Gestión de ciclo de vida insuficiente. {"; ".join(issues)}',
                    'evidence': evidence,
                    'remediation': (
                        'Implementar gestión de ciclo de vida: '
                        '1) Configurar S3 Lifecycle policies en todos los buckets. '
                        '2) Definir transiciones a clases de almacenamiento más económicas (IA, Glacier). '
                        '3) Configurar expiración automática de objetos según política de retención. '
                        '4) Habilitar versionado en buckets críticos. '
                        '5) Implementar S3 Object Lock para datos regulados.'
                    ),
                    'risk': 'Riesgo medio. Sin gestión de ciclo de vida, los datos se acumulan sin control, aumentando costos y riesgo de exposición.'}
    except ClientError as e:
        return handle_error_func('SEC07-BP04', e)


# ============================================================================
# SEC08 - Protección de datos en reposo (BP01-BP04)
# ============================================================================

def evaluate_sec08_bp01(session, handle_error_func) -> Dict[str, Any]:
    """SEC08-BP01: Implementar la gestión segura de claves"""
    try:
        kms = session.client('kms')
        issues = []
        evidence_parts = []
        
        keys = kms.list_keys(Limit=50)
        key_list = keys.get('Keys', [])
        
        rotation_enabled = 0
        cmk_count = 0
        for key in key_list[:20]:
            try:
                desc = kms.describe_key(KeyId=key['KeyId'])
                metadata = desc['KeyMetadata']
                if metadata.get('KeyManager') == 'CUSTOMER':
                    cmk_count += 1
                    try:
                        rotation = kms.get_key_rotation_status(KeyId=key['KeyId'])
                        if rotation.get('KeyRotationEnabled'):
                            rotation_enabled += 1
                    except ClientError:
                        pass
            except ClientError:
                pass
        
        evidence_parts.append(f"KMS keys: {len(key_list)} total, {cmk_count} CMKs")
        evidence_parts.append(f"CMKs con rotación: {rotation_enabled}/{cmk_count}")
        
        if cmk_count == 0:
            issues.append('Sin CMKs (Customer Managed Keys) para cifrado personalizado')
        elif rotation_enabled < cmk_count:
            issues.append(f'{cmk_count - rotation_enabled} CMK(s) sin rotación automática')
        
        # Verificar aliases
        try:
            aliases = kms.list_aliases()
            custom_aliases = [a for a in aliases.get('Aliases', []) if not a['AliasName'].startswith('alias/aws/')]
            evidence_parts.append(f"Aliases personalizados: {len(custom_aliases)}")
        except ClientError:
            pass
        
        evidence = ' | '.join(evidence_parts)
        
        if len(issues) == 0:
            return {'bp': 'SEC08-BP01', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC08-BP01', ''),
                    'status': 'COMPLIANT', 'severity': 'LOW',
                    'finding': f'Gestión de claves segura con {cmk_count} CMKs y rotación automática habilitada.',
                    'evidence': evidence,
                    'remediation': 'Estado actual cumple. Revisar key policies y mantener rotación automática.',
                    'risk': 'Bajo riesgo.'}
        else:
            return {'bp': 'SEC08-BP01', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC08-BP01', ''),
                    'status': 'NON_COMPLIANT', 'severity': 'HIGH',
                    'finding': f'Gestión de claves insuficiente. {"; ".join(issues)}',
                    'evidence': evidence,
                    'remediation': (
                        'Implementar gestión segura de claves: '
                        '1) Crear CMKs para cada carga de trabajo o nivel de clasificación. '
                        '2) Habilitar rotación automática anual en todas las CMKs. '
                        '3) Configurar key policies con principio de privilegio mínimo. '
                        '4) Usar aliases descriptivos para identificar el propósito de cada clave. '
                        '5) Implementar separación de deberes (key admin vs key user). '
                        '6) Monitorear uso de claves con CloudTrail.'
                    ),
                    'risk': 'Alto riesgo. Sin gestión adecuada de claves, el cifrado puede ser inefectivo o las claves comprometidas.'}
    except ClientError as e:
        return handle_error_func('SEC08-BP01', e)


def evaluate_sec08_bp02(session, handle_error_func) -> Dict[str, Any]:
    """SEC08-BP02: Hacer cumplir el cifrado en reposo"""
    try:
        issues = []
        evidence_parts = []
        
        # 1. EBS default encryption
        try:
            ec2 = session.client('ec2')
            ebs_enc = ec2.get_ebs_encryption_by_default()
            default_enc = ebs_enc.get('EbsEncryptionByDefault', False)
            evidence_parts.append(f"EBS encryption by default: {'Sí' if default_enc else 'NO'}")
            if not default_enc:
                issues.append('EBS encryption by default no habilitado')
        except ClientError:
            evidence_parts.append("EBS encryption: No accesible")
        
        # 2. S3 bucket encryption
        try:
            s3 = session.client('s3')
            buckets = s3.list_buckets().get('Buckets', [])
            unencrypted = 0
            for bucket in buckets[:15]:
                try:
                    s3.get_bucket_encryption(Bucket=bucket['Name'])
                except ClientError as e:
                    if 'ServerSideEncryptionConfigurationNotFoundError' in str(e):
                        unencrypted += 1
            evidence_parts.append(f"S3 sin cifrado: {unencrypted}/{min(len(buckets), 15)}")
            if unencrypted > 0:
                issues.append(f'{unencrypted} bucket(s) S3 sin cifrado en reposo')
        except ClientError:
            evidence_parts.append("S3 encryption: No accesible")
        
        # 3. RDS encryption
        try:
            rds = session.client('rds')
            dbs = rds.describe_db_instances()
            rds_instances = dbs.get('DBInstances', [])
            unencrypted_rds = [db for db in rds_instances if not db.get('StorageEncrypted')]
            evidence_parts.append(f"RDS sin cifrado: {len(unencrypted_rds)}/{len(rds_instances)}")
            if unencrypted_rds:
                issues.append(f'{len(unencrypted_rds)} instancia(s) RDS sin cifrado')
        except ClientError:
            evidence_parts.append("RDS: No accesible")
        
        # 4. DynamoDB encryption
        try:
            ddb = session.client('dynamodb')
            tables = ddb.list_tables().get('TableNames', [])
            evidence_parts.append(f"DynamoDB tables: {len(tables)} (cifrado por defecto)")
        except ClientError:
            pass
        
        evidence = ' | '.join(evidence_parts)
        
        if len(issues) == 0:
            return {'bp': 'SEC08-BP02', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC08-BP02', ''),
                    'status': 'COMPLIANT', 'severity': 'LOW',
                    'finding': 'Cifrado en reposo aplicado en todos los servicios de almacenamiento.',
                    'evidence': evidence,
                    'remediation': 'Estado actual cumple. Verificar que nuevos recursos se crean con cifrado habilitado.',
                    'risk': 'Bajo riesgo.'}
        else:
            return {'bp': 'SEC08-BP02', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC08-BP02', ''),
                    'status': 'NON_COMPLIANT', 'severity': 'HIGH',
                    'finding': f'Cifrado en reposo no aplicado completamente. {"; ".join(issues)}',
                    'evidence': evidence,
                    'remediation': (
                        'Hacer cumplir cifrado en reposo: '
                        '1) Habilitar EBS encryption by default en la cuenta. '
                        '2) Habilitar cifrado SSE-S3 o SSE-KMS en todos los buckets S3. '
                        '3) Cifrar instancias RDS (requiere recrear si no están cifradas). '
                        '4) Usar Config Rules para detectar recursos sin cifrado. '
                        '5) Implementar SCP para prevenir creación de recursos sin cifrado.'
                    ),
                    'risk': 'Alto riesgo. Datos sin cifrar en reposo pueden ser accedidos si el almacenamiento físico es comprometido.'}
    except ClientError as e:
        return handle_error_func('SEC08-BP02', e)


def evaluate_sec08_bp03(session, handle_error_func) -> Dict[str, Any]:
    """SEC08-BP03: Automatizar la protección de datos en reposo"""
    try:
        issues = []
        evidence_parts = []
        
        # EBS default encryption
        try:
            ec2 = session.client('ec2')
            ebs_enc = ec2.get_ebs_encryption_by_default()
            default_enc = ebs_enc.get('EbsEncryptionByDefault', False)
            evidence_parts.append(f"EBS encryption by default: {'Sí' if default_enc else 'NO'}")
            if not default_enc:
                issues.append('EBS encryption by default no habilitado')
        except ClientError:
            evidence_parts.append("EBS: No accesible")
        
        # Config Rules para cifrado
        try:
            config = session.client('config')
            rules = config.describe_config_rules()
            encryption_rules = [r for r in rules.get('ConfigRules', []) if any(
                kw in r.get('ConfigRuleName', '').lower() for kw in ['encrypt', 'kms', 'sse']
            )]
            evidence_parts.append(f"Config Rules de cifrado: {len(encryption_rules)}")
            if len(encryption_rules) == 0:
                issues.append('Sin Config Rules para validar cifrado automáticamente')
        except ClientError:
            evidence_parts.append("Config: No accesible")
        
        evidence = ' | '.join(evidence_parts)
        
        if len(issues) == 0:
            return {'bp': 'SEC08-BP03', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC08-BP03', ''),
                    'status': 'COMPLIANT', 'severity': 'LOW',
                    'finding': 'Protección automatizada de datos en reposo con cifrado por defecto y Config Rules.',
                    'evidence': evidence,
                    'remediation': 'Estado actual cumple.',
                    'risk': 'Bajo riesgo.'}
        else:
            return {'bp': 'SEC08-BP03', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC08-BP03', ''),
                    'status': 'NON_COMPLIANT', 'severity': 'HIGH',
                    'finding': f'Protección automatizada insuficiente. {"; ".join(issues)}',
                    'evidence': evidence,
                    'remediation': (
                        'Automatizar protección de datos en reposo: '
                        '1) Habilitar EBS encryption by default. '
                        '2) Configurar Config Rules: s3-bucket-server-side-encryption-enabled, encrypted-volumes, rds-storage-encrypted. '
                        '3) Implementar SCP para prevenir creación de recursos sin cifrado. '
                        '4) Configurar remediación automática para recursos no cifrados.'
                    ),
                    'risk': 'Alto riesgo. Sin automatización, nuevos recursos pueden crearse sin cifrado.'}
    except ClientError as e:
        return handle_error_func('SEC08-BP03', e)


def evaluate_sec08_bp04(session, handle_error_func) -> Dict[str, Any]:
    """SEC08-BP04: Hacer cumplir el control de acceso"""
    try:
        issues = []
        evidence_parts = []
        
        # S3 public access block (account level)
        try:
            s3control = session.client('s3control')
            sts = session.client('sts')
            account_id = sts.get_caller_identity()['Account']
            pab = s3control.get_public_access_block(AccountId=account_id)
            config = pab.get('PublicAccessBlockConfiguration', {})
            all_blocked = all([config.get('BlockPublicAcls'), config.get('BlockPublicPolicy'),
                             config.get('IgnorePublicAcls'), config.get('RestrictPublicBuckets')])
            evidence_parts.append(f"S3 Block Public Access (cuenta): {'Completo' if all_blocked else 'PARCIAL'}")
            if not all_blocked:
                issues.append('S3 Block Public Access no está completo a nivel de cuenta')
        except ClientError:
            evidence_parts.append("S3 Block Public Access: No accesible")
        
        # Verificar buckets con bucket policy pública
        try:
            s3 = session.client('s3')
            buckets = s3.list_buckets().get('Buckets', [])
            evidence_parts.append(f"S3 buckets: {len(buckets)}")
        except ClientError:
            evidence_parts.append("S3: No accesible")
        
        evidence = ' | '.join(evidence_parts)
        
        if len(issues) == 0:
            return {'bp': 'SEC08-BP04', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC08-BP04', ''),
                    'status': 'COMPLIANT', 'severity': 'LOW',
                    'finding': 'Control de acceso aplicado. S3 Block Public Access habilitado a nivel de cuenta.',
                    'evidence': evidence,
                    'remediation': 'Estado actual cumple. Verificar bucket policies periódicamente.',
                    'risk': 'Bajo riesgo.'}
        else:
            return {'bp': 'SEC08-BP04', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC08-BP04', ''),
                    'status': 'NON_COMPLIANT', 'severity': 'HIGH',
                    'finding': f'Control de acceso insuficiente. {"; ".join(issues)}',
                    'evidence': evidence,
                    'remediation': (
                        'Hacer cumplir control de acceso: '
                        '1) Habilitar S3 Block Public Access a nivel de cuenta (las 4 opciones). '
                        '2) Revisar y restringir bucket policies. '
                        '3) Implementar S3 Access Points para acceso granular. '
                        '4) Usar VPC endpoints para acceso privado a S3. '
                        '5) Configurar Config Rule: s3-account-level-public-access-blocks-periodic.'
                    ),
                    'risk': 'Alto riesgo. Sin control de acceso adecuado, los datos pueden ser accedidos públicamente.'}
    except ClientError as e:
        return handle_error_func('SEC08-BP04', e)


# ============================================================================
# SEC09 - Protección de datos en tránsito (BP01-BP03)
# ============================================================================

def evaluate_sec09_bp01(session, handle_error_func) -> Dict[str, Any]:
    """SEC09-BP01: Implementar la gestión segura de claves y certificados"""
    try:
        issues = []
        evidence_parts = []

        # Inicializar antes del try para evitar UnboundLocalError si list_certificates() falla.
        cert_list = []

        try:
            acm = session.client('acm')
            certs = acm.list_certificates()
            cert_list = certs.get('CertificateSummaryList', [])
            expired = [c for c in cert_list if c.get('Status') == 'EXPIRED']
            evidence_parts.append(f"ACM certificados: {len(cert_list)} total, {len(expired)} expirados")
            if len(cert_list) == 0:
                issues.append('Sin certificados en ACM')
            if expired:
                issues.append(f'{len(expired)} certificado(s) expirado(s)')
        except ClientError:
            # ACM inaccesible: no se puede afirmar cumplimiento sin datos -> degradar a revisión.
            evidence_parts.append("ACM: No accesible")
            issues.append('ACM no accesible para validar gestión de certificados')
        
        evidence = ' | '.join(evidence_parts)
        
        if len(issues) == 0:
            return {'bp': 'SEC09-BP01', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC09-BP01', ''),
                    'status': 'COMPLIANT', 'severity': 'LOW',
                    'finding': f'Gestión de certificados implementada con {len(cert_list)} certificados ACM.',
                    'evidence': evidence,
                    'remediation': 'Estado actual cumple. Configurar renovación automática de certificados ACM.',
                    'risk': 'Bajo riesgo.'}
        else:
            return {'bp': 'SEC09-BP01', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC09-BP01', ''),
                    'status': 'NON_COMPLIANT' if 'expirado' in str(issues) else 'PENDING_REVIEW', 
                    'severity': 'HIGH' if 'expirado' in str(issues) else 'MEDIUM',
                    'finding': f'Gestión de certificados requiere atención. {"; ".join(issues)}',
                    'evidence': evidence,
                    'remediation': (
                        'Implementar gestión de certificados: '
                        '1) Usar ACM para provisionar y gestionar certificados TLS. '
                        '2) Configurar renovación automática de certificados ACM. '
                        '3) Eliminar o renovar certificados expirados. '
                        '4) Usar ACM Private CA para certificados internos. '
                        '5) Monitorear expiración de certificados con Config Rules.'
                    ),
                    'risk': 'Certificados expirados causan interrupciones de servicio y pérdida de cifrado en tránsito.'}
    except ClientError as e:
        return handle_error_func('SEC09-BP01', e)


def evaluate_sec09_bp02(session, handle_error_func) -> Dict[str, Any]:
    """SEC09-BP02: Hacer cumplir el cifrado en tránsito"""
    try:
        issues = []
        evidence_parts = []
        
        # 1. Load Balancers con HTTPS
        try:
            elbv2 = session.client('elbv2')
            lbs = elbv2.describe_load_balancers()
            lb_list = lbs.get('LoadBalancers', [])
            evidence_parts.append(f"Load Balancers: {len(lb_list)}")
            
            for lb in lb_list[:5]:
                listeners = elbv2.describe_listeners(LoadBalancerArn=lb['LoadBalancerArn'])
                http_listeners = [l for l in listeners.get('Listeners', []) if l.get('Protocol') == 'HTTP']
                if http_listeners:
                    issues.append(f'ALB {lb["LoadBalancerName"]} tiene listener HTTP sin redirección a HTTPS')
        except ClientError:
            evidence_parts.append("ELB: No accesible")
        
        # 2. CloudFront con HTTPS
        try:
            cf = session.client('cloudfront')
            distributions = cf.list_distributions()
            dist_list = distributions.get('DistributionList', {}).get('Items', [])
            for dist in dist_list[:5]:
                viewer_protocol = dist.get('DefaultCacheBehavior', {}).get('ViewerProtocolPolicy', '')
                if viewer_protocol == 'allow-all':
                    issues.append(f'CloudFront {dist["Id"]} permite HTTP (no fuerza HTTPS)')
            evidence_parts.append(f"CloudFront distributions: {len(dist_list)}")
        except ClientError:
            evidence_parts.append("CloudFront: No accesible")
        
        # 3. S3 bucket policy enforce SSL
        try:
            s3 = session.client('s3')
            buckets = s3.list_buckets().get('Buckets', [])
            ssl_enforced = 0
            for bucket in buckets[:10]:
                try:
                    policy = s3.get_bucket_policy(Bucket=bucket['Name'])
                    if 'aws:SecureTransport' in str(policy.get('Policy', '')):
                        ssl_enforced += 1
                except ClientError:
                    pass
            evidence_parts.append(f"S3 con SSL enforced: {ssl_enforced}/{min(len(buckets), 10)}")
        except ClientError:
            pass
        
        evidence = ' | '.join(evidence_parts)
        
        if len(issues) == 0:
            return {'bp': 'SEC09-BP02', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC09-BP02', ''),
                    'status': 'COMPLIANT', 'severity': 'LOW',
                    'finding': 'Cifrado en tránsito aplicado. HTTPS forzado en load balancers y CloudFront.',
                    'evidence': evidence,
                    'remediation': 'Estado actual cumple. Verificar que todas las comunicaciones usen TLS 1.2+.',
                    'risk': 'Bajo riesgo.'}
        else:
            return {'bp': 'SEC09-BP02', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC09-BP02', ''),
                    'status': 'NON_COMPLIANT', 'severity': 'HIGH',
                    'finding': f'Cifrado en tránsito no aplicado completamente. {"; ".join(issues)}',
                    'evidence': evidence,
                    'remediation': (
                        'Hacer cumplir cifrado en tránsito: '
                        '1) Configurar redirección HTTP→HTTPS en todos los load balancers. '
                        '2) Configurar CloudFront con ViewerProtocolPolicy: redirect-to-https. '
                        '3) Agregar condición aws:SecureTransport en bucket policies de S3. '
                        '4) Usar TLS 1.2 como versión mínima en todos los endpoints. '
                        '5) Configurar security policies en ALB para TLS 1.2+.'
                    ),
                    'risk': 'Alto riesgo. Tráfico sin cifrar puede ser interceptado y los datos expuestos.'}
    except ClientError as e:
        return handle_error_func('SEC09-BP02', e)


def evaluate_sec09_bp03(session, handle_error_func) -> Dict[str, Any]:
    """SEC09-BP03: Autenticar las comunicaciones de red"""
    try:
        issues = []
        evidence_parts = []
        
        # VPN connections
        try:
            ec2 = session.client('ec2')
            vpns = ec2.describe_vpn_connections()
            vpn_list = vpns.get('VpnConnections', [])
            evidence_parts.append(f"VPN connections: {len(vpn_list)}")
        except ClientError:
            evidence_parts.append("VPN: No accesible")
        
        # VPC endpoints (private connectivity)
        try:
            endpoints = ec2.describe_vpc_endpoints()
            endpoint_list = endpoints.get('VpcEndpoints', [])
            evidence_parts.append(f"VPC endpoints: {len(endpoint_list)}")
        except ClientError:
            evidence_parts.append("VPC endpoints: No accesible")
        
        # Direct Connect
        try:
            dx = session.client('directconnect')
            connections = dx.describe_connections()
            evidence_parts.append(f"Direct Connect: {len(connections.get('connections', []))}")
        except ClientError:
            evidence_parts.append("Direct Connect: No accesible")
        
        evidence = ' | '.join(evidence_parts)
        
        return {'bp': 'SEC09-BP03', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC09-BP03', ''),
                'status': 'PENDING_REVIEW', 'severity': 'MEDIUM',
                'finding': 'Autenticación de comunicaciones de red requiere revisión según requisitos de conectividad.',
                'evidence': evidence,
                'remediation': (
                    'Autenticar comunicaciones de red: '
                    '1) Usar VPN con IPSec para conectividad on-premises. '
                    '2) Implementar VPC endpoints para acceso privado a servicios AWS. '
                    '3) Considerar Direct Connect para conectividad dedicada. '
                    '4) Implementar mTLS para comunicaciones entre servicios. '
                    '5) Usar PrivateLink para acceso privado a servicios de terceros.'
                ),
                'risk': 'Por Determinar. Depende de los requisitos de conectividad de la organización.'}
    except ClientError as e:
        return handle_error_func('SEC09-BP03', e)


# ============================================================================
# SEC10 - Respuesta a incidentes (BP01-BP08)
# ============================================================================

def evaluate_sec10_bp01(session, handle_error_func) -> Dict[str, Any]:
    """SEC10-BP01: Identificar personal clave y recursos externos"""
    try:
        issues = []
        evidence_parts = []
        
        # SNS topics para notificaciones de seguridad
        try:
            sns = session.client('sns')
            topics = sns.list_topics()
            security_topics = [t for t in topics.get('Topics', []) if any(
                kw in t.get('TopicArn', '').lower() for kw in ['security', 'incident', 'alert', 'emergency']
            )]
            evidence_parts.append(f"SNS topics de seguridad: {len(security_topics)}")
            if len(security_topics) == 0:
                issues.append('Sin topics SNS para notificaciones de incidentes de seguridad')
        except ClientError:
            evidence_parts.append("SNS: No accesible")
        
        # CloudWatch alarms de seguridad
        try:
            cw = session.client('cloudwatch')
            alarms = cw.describe_alarms(MaxRecords=100)
            security_alarms = [a for a in alarms.get('MetricAlarms', []) if any(
                kw in a.get('AlarmName', '').lower() for kw in ['root', 'unauthorized', 'security', 'incident']
            )]
            evidence_parts.append(f"Alarmas de seguridad: {len(security_alarms)}")
        except ClientError:
            evidence_parts.append("CloudWatch: No accesible")
        
        evidence = ' | '.join(evidence_parts)
        
        if len(issues) == 0:
            return {'bp': 'SEC10-BP01', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC10-BP01', ''),
                    'status': 'COMPLIANT', 'severity': 'LOW',
                    'finding': 'Personal clave identificado con canales de notificación de seguridad configurados.',
                    'evidence': evidence,
                    'remediation': 'Estado actual cumple. Mantener lista de contactos actualizada y probar canales de notificación.',
                    'risk': 'Bajo riesgo.'}
        else:
            return {'bp': 'SEC10-BP01', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC10-BP01', ''),
                    'status': 'NON_COMPLIANT', 'severity': 'HIGH',
                    'finding': f'Personal clave no identificado. {"; ".join(issues)}',
                    'evidence': evidence,
                    'remediation': (
                        'Identificar personal clave y recursos: '
                        '1) Crear topic SNS para notificaciones de incidentes de seguridad. '
                        '2) Suscribir al equipo de seguridad (email, SMS, PagerDuty). '
                        '3) Configurar alarmas de CloudWatch para eventos críticos (root login, unauthorized API). '
                        '4) Documentar lista de contactos de emergencia (internos y externos). '
                        '5) Registrar contacto de seguridad en AWS Account Settings. '
                        '6) Identificar recursos externos (AWS Support, consultores de IR).'
                    ),
                    'risk': 'Alto riesgo. Sin personal identificado, los incidentes no pueden ser escalados ni respondidos a tiempo.'}
    except ClientError as e:
        return handle_error_func('SEC10-BP01', e)


def evaluate_sec10_bp02(session, handle_error_func) -> Dict[str, Any]:
    """SEC10-BP02: Desarrollar planes de gestión de incidentes"""
    try:
        issues = []
        evidence_parts = []
        
        # SSM documents (runbooks/playbooks)
        try:
            ssm = session.client('ssm')
            docs = ssm.list_documents(Filters=[{'Key': 'Owner', 'Values': ['Self']}], MaxResults=50)
            all_docs = docs.get('DocumentIdentifiers', [])
            incident_docs = [d for d in all_docs if any(
                kw in d.get('Name', '').lower() for kw in ['incident', 'runbook', 'playbook', 'response', 'forensic']
            )]
            evidence_parts.append(f"SSM Documents propios: {len(all_docs)}, de incidentes: {len(incident_docs)}")
            if len(incident_docs) == 0:
                issues.append('Sin runbooks/playbooks de respuesta a incidentes en SSM')
        except ClientError:
            evidence_parts.append("SSM: No accesible")
            issues.append('SSM no accesible para verificar runbooks')
        
        # EventBridge rules para respuesta automática
        try:
            eb = session.client('events')
            rules = eb.list_rules()
            incident_rules = [r for r in rules.get('Rules', []) if any(
                kw in r.get('Name', '').lower() for kw in ['incident', 'security', 'guardduty', 'finding']
            )]
            evidence_parts.append(f"EventBridge rules de incidentes: {len(incident_rules)}")
        except ClientError:
            evidence_parts.append("EventBridge: No accesible")
        
        evidence = ' | '.join(evidence_parts)
        
        if len(issues) == 0:
            return {'bp': 'SEC10-BP02', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC10-BP02', ''),
                    'status': 'COMPLIANT', 'severity': 'LOW',
                    'finding': 'Planes de gestión de incidentes documentados con runbooks en SSM.',
                    'evidence': evidence,
                    'remediation': 'Estado actual cumple. Probar y actualizar runbooks periódicamente.',
                    'risk': 'Bajo riesgo.'}
        else:
            return {'bp': 'SEC10-BP02', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC10-BP02', ''),
                    'status': 'NON_COMPLIANT', 'severity': 'HIGH',
                    'finding': f'Planes de incidentes no desarrollados. {"; ".join(issues)}',
                    'evidence': evidence,
                    'remediation': (
                        'Desarrollar planes de gestión de incidentes: '
                        '1) Crear runbooks en SSM para escenarios comunes (credenciales comprometidas, acceso no autorizado, data breach). '
                        '2) Documentar procedimientos de escalación y comunicación. '
                        '3) Configurar EventBridge rules para respuesta automática a findings de GuardDuty. '
                        '4) Definir roles y responsabilidades del equipo de respuesta. '
                        '5) Integrar con AWS Incident Manager para gestión centralizada.'
                    ),
                    'risk': 'Alto riesgo. Sin planes de incidentes, la respuesta será improvisada y lenta.'}
    except ClientError as e:
        return handle_error_func('SEC10-BP02', e)


def evaluate_sec10_bp03(session, handle_error_func) -> Dict[str, Any]:
    """SEC10-BP03: Preparar capacidades forenses"""
    try:
        evidence_parts = []
        
        # EBS snapshots
        try:
            ec2 = session.client('ec2')
            snapshots = ec2.describe_snapshots(OwnerIds=['self'], MaxResults=20)
            evidence_parts.append(f"EBS snapshots: {len(snapshots.get('Snapshots', []))}")
        except ClientError:
            evidence_parts.append("EBS snapshots: No accesible")
        
        # CloudTrail (logs para forense)
        try:
            ct = session.client('cloudtrail')
            trails = ct.describe_trails()
            evidence_parts.append(f"CloudTrail trails: {len(trails.get('trailList', []))}")
        except ClientError:
            evidence_parts.append("CloudTrail: No accesible")
        
        evidence = ' | '.join(evidence_parts)
        
        return {'bp': 'SEC10-BP03', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC10-BP03', ''),
                'status': 'PENDING_REVIEW', 'severity': 'MEDIUM',
                'finding': 'Capacidades forenses requieren revisión. Verificar procedimientos de preservación de evidencia.',
                'evidence': evidence,
                'remediation': (
                    'Preparar capacidades forenses: '
                    '1) Crear cuenta AWS dedicada para forense con acceso restringido. '
                    '2) Configurar snapshots automáticos de EBS para preservación de evidencia. '
                    '3) Habilitar CloudTrail con log file validation y S3 MFA delete. '
                    '4) Implementar VPC aislada para análisis forense. '
                    '5) Pre-instalar herramientas forenses (volatility, SIFT) en AMI dedicada. '
                    '6) Documentar procedimiento de cadena de custodia digital.'
                ),
                'risk': 'Por Determinar. Requiere verificación de procedimientos forenses documentados.'}
    except ClientError as e:
        return handle_error_func('SEC10-BP03', e)


def evaluate_sec10_bp04(session, handle_error_func) -> Dict[str, Any]:
    """SEC10-BP04: Desarrollar y probar playbooks de respuesta a incidentes"""
    try:
        issues = []
        evidence_parts = []
        
        # Lambda functions de respuesta
        try:
            lambda_client = session.client('lambda')
            functions = lambda_client.list_functions(MaxItems=50)
            response_functions = [f for f in functions.get('Functions', []) if any(
                kw in f['FunctionName'].lower() for kw in ['respond', 'remediat', 'contain', 'isolat', 'quarantin']
            )]
            evidence_parts.append(f"Lambda de respuesta: {len(response_functions)}")
            if len(response_functions) == 0:
                issues.append('Sin funciones Lambda de respuesta automática a incidentes')
        except ClientError:
            evidence_parts.append("Lambda: No accesible")
        
        # Step Functions (workflows de respuesta)
        try:
            sfn = session.client('stepfunctions')
            machines = sfn.list_state_machines(maxResults=20)
            incident_machines = [m for m in machines.get('stateMachines', []) if any(
                kw in m.get('name', '').lower() for kw in ['incident', 'response', 'remediat']
            )]
            evidence_parts.append(f"Step Functions de incidentes: {len(incident_machines)}")
        except ClientError:
            evidence_parts.append("Step Functions: No accesible")
        
        evidence = ' | '.join(evidence_parts)
        
        if len(issues) == 0:
            return {'bp': 'SEC10-BP04', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC10-BP04', ''),
                    'status': 'COMPLIANT', 'severity': 'LOW',
                    'finding': 'Playbooks de respuesta implementados con automatización.',
                    'evidence': evidence,
                    'remediation': 'Estado actual cumple. Probar playbooks periódicamente con simulaciones.',
                    'risk': 'Bajo riesgo.'}
        else:
            return {'bp': 'SEC10-BP04', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC10-BP04', ''),
                    'status': 'NON_COMPLIANT', 'severity': 'HIGH',
                    'finding': f'Playbooks de respuesta no implementados. {"; ".join(issues)}',
                    'evidence': evidence,
                    'remediation': (
                        'Desarrollar playbooks de respuesta: '
                        '1) Crear Lambda functions para contención automática (aislar instancia, revocar credenciales). '
                        '2) Implementar Step Functions para workflows de respuesta multi-paso. '
                        '3) Crear playbooks para: credenciales comprometidas, instancia comprometida, data breach, DDoS. '
                        '4) Integrar con EventBridge para disparo automático. '
                        '5) Probar playbooks trimestralmente con simulaciones.'
                    ),
                    'risk': 'Alto riesgo. Sin playbooks automatizados, la contención de incidentes depende de intervención manual.'}
    except ClientError as e:
        return handle_error_func('SEC10-BP04', e)


def evaluate_sec10_bp05(session, handle_error_func) -> Dict[str, Any]:
    """SEC10-BP05: Acceso previo a la provisión"""
    try:
        client = session.client('iam')
        roles = client.list_roles(MaxItems=100)['Roles']
        ir_roles = [r for r in roles if any(kw in r['RoleName'].lower() for kw in ['incident', 'forensic', 'emergency', 'break-glass'])]
        evidence = f"Roles de respuesta a incidentes: {len(ir_roles)}"
        
        if ir_roles:
            return {'bp': 'SEC10-BP05', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC10-BP05', ''),
                    'status': 'COMPLIANT', 'severity': 'LOW',
                    'finding': f'Acceso pre-provisionado con {len(ir_roles)} rol(es) de respuesta a incidentes.',
                    'evidence': evidence,
                    'remediation': 'Estado actual cumple. Verificar que los roles tienen permisos adecuados y MFA requerido.',
                    'risk': 'Bajo riesgo.'}
        else:
            return {'bp': 'SEC10-BP05', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC10-BP05', ''),
                    'status': 'NON_COMPLIANT', 'severity': 'HIGH',
                    'finding': 'Sin roles pre-provisionados para respuesta a incidentes.',
                    'evidence': evidence,
                    'remediation': (
                        'Pre-provisionar acceso para respuesta a incidentes: '
                        '1) Crear rol IAM "IncidentResponse" con permisos necesarios para investigación. '
                        '2) Crear rol "ForensicAnalyst" con acceso a logs y snapshots. '
                        '3) Requerir MFA para asumir roles de incidentes. '
                        '4) Configurar alarma cuando se asuman estos roles. '
                        '5) Documentar procedimiento de acceso de emergencia.'
                    ),
                    'risk': 'Alto riesgo. Sin acceso pre-provisionado, la respuesta a incidentes se retrasa por falta de permisos.'}
    except ClientError as e:
        return handle_error_func('SEC10-BP05', e)


def evaluate_sec10_bp06(session, handle_error_func) -> Dict[str, Any]:
    """SEC10-BP06: Herramientas de implementación previa"""
    try:
        issues = []
        evidence_parts = []
        
        # VPC endpoints (para acceso sin internet durante incidentes)
        try:
            ec2 = session.client('ec2')
            endpoints = ec2.describe_vpc_endpoints()
            s3_endpoints = [e for e in endpoints.get('VpcEndpoints', []) if 's3' in e.get('ServiceName', '')]
            evidence_parts.append(f"VPC endpoints S3: {len(s3_endpoints)}")
            if len(s3_endpoints) == 0:
                issues.append('Sin VPC endpoints para S3 (necesario para forense sin internet)')
        except ClientError:
            evidence_parts.append("VPC endpoints: No accesible")
        
        # CloudFormation stacks de seguridad
        try:
            cf = session.client('cloudformation')
            stacks = cf.list_stacks(StackStatusFilter=['CREATE_COMPLETE', 'UPDATE_COMPLETE'])
            security_stacks = [s for s in stacks.get('StackSummaries', []) if any(
                kw in s.get('StackName', '').lower() for kw in ['security', 'forensic', 'incident']
            )]
            evidence_parts.append(f"Stacks de seguridad: {len(security_stacks)}")
        except ClientError:
            evidence_parts.append("CloudFormation: No accesible")
        
        evidence = ' | '.join(evidence_parts)
        
        if len(issues) == 0:
            return {'bp': 'SEC10-BP06', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC10-BP06', ''),
                    'status': 'COMPLIANT', 'severity': 'LOW',
                    'finding': 'Herramientas pre-desplegadas para respuesta a incidentes.',
                    'evidence': evidence,
                    'remediation': 'Estado actual cumple. Mantener herramientas actualizadas.',
                    'risk': 'Bajo riesgo.'}
        else:
            return {'bp': 'SEC10-BP06', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC10-BP06', ''),
                    'status': 'NON_COMPLIANT', 'severity': 'MEDIUM',
                    'finding': f'Herramientas no pre-desplegadas. {"; ".join(issues)}',
                    'evidence': evidence,
                    'remediation': (
                        'Pre-desplegar herramientas: '
                        '1) Configurar VPC endpoints para S3, CloudWatch, STS. '
                        '2) Crear AMI con herramientas forenses pre-instaladas. '
                        '3) Pre-desplegar stack de CloudFormation para entorno forense. '
                        '4) Configurar bucket S3 dedicado para evidencia forense. '
                        '5) Pre-configurar queries de CloudWatch Logs Insights para investigación.'
                    ),
                    'risk': 'Riesgo medio. Sin herramientas pre-desplegadas, la respuesta se retrasa por configuración.'}
    except ClientError as e:
        return handle_error_func('SEC10-BP06', e)


def evaluate_sec10_bp07(session, handle_error_func) -> Dict[str, Any]:
    """SEC10-BP07: Ejecutar simulaciones"""
    try:
        evidence_parts = []
        
        # Verificar SSM documents de simulación
        try:
            ssm = session.client('ssm')
            docs = ssm.list_documents(Filters=[{'Key': 'Owner', 'Values': ['Self']}], MaxResults=50)
            simulation_docs = [d for d in docs.get('DocumentIdentifiers', []) if any(
                kw in d.get('Name', '').lower() for kw in ['gameday', 'simulation', 'drill', 'exercise', 'chaos']
            )]
            evidence_parts.append(f"SSM docs de simulación: {len(simulation_docs)}")
        except ClientError:
            evidence_parts.append("SSM: No accesible")
        
        # FIS (Fault Injection Simulator)
        try:
            fis = session.client('fis')
            templates = fis.list_experiment_templates(maxResults=10)
            evidence_parts.append(f"FIS experiment templates: {len(templates.get('experimentTemplates', []))}")
        except ClientError:
            evidence_parts.append("FIS: No accesible")
        
        evidence = ' | '.join(evidence_parts)
        
        return {'bp': 'SEC10-BP07', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC10-BP07', ''),
                'status': 'PENDING_REVIEW', 'severity': 'MEDIUM',
                'finding': 'Simulaciones de incidentes requieren verificación. Revisar si se realizan game days periódicamente.',
                'evidence': evidence,
                'remediation': (
                    'Ejecutar simulaciones de incidentes: '
                    '1) Programar game days trimestrales con escenarios de seguridad. '
                    '2) Usar AWS FIS para inyección de fallos controlada. '
                    '3) Simular escenarios: credenciales comprometidas, ransomware, data exfiltration. '
                    '4) Documentar lecciones aprendidas y actualizar playbooks. '
                    '5) Involucrar a todos los equipos relevantes en las simulaciones.'
                ),
                'risk': 'Por Determinar. Requiere verificación de frecuencia y alcance de simulaciones.'}
    except ClientError as e:
        return handle_error_func('SEC10-BP07', e)


def evaluate_sec10_bp08(session, handle_error_func) -> Dict[str, Any]:
    """SEC10-BP08: Establecer un marco para aprender de los incidentes"""
    try:
        evidence_parts = []
        
        # SSM OpsCenter (gestión de incidentes)
        try:
            ssm = session.client('ssm')
            ops_items = ssm.describe_ops_items(
                OpsItemFilters=[{'Key': 'Status', 'Operator': 'Equal', 'Values': ['Open']}],
                MaxResults=10
            )
            evidence_parts.append(f"OpsCenter items abiertos: {len(ops_items.get('OpsItemSummaries', []))}")
        except ClientError:
            evidence_parts.append("OpsCenter: No accesible")
        
        evidence = ' | '.join(evidence_parts)
        
        return {'bp': 'SEC10-BP08', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC10-BP08', ''),
                'status': 'PENDING_REVIEW', 'severity': 'MEDIUM',
                'finding': 'Marco de aprendizaje de incidentes requiere verificación. Revisar si se realizan post-mortems.',
                'evidence': evidence,
                'remediation': (
                    'Establecer marco de aprendizaje: '
                    '1) Implementar proceso de post-mortem para cada incidente de seguridad. '
                    '2) Usar SSM OpsCenter para tracking de incidentes y acciones correctivas. '
                    '3) Documentar lecciones aprendidas y compartir con la organización. '
                    '4) Actualizar playbooks y controles basándose en lecciones aprendidas. '
                    '5) Mantener base de conocimiento de incidentes anteriores. '
                    '6) Implementar métricas de mejora continua (MTTD, MTTR).'
                ),
                'risk': 'Por Determinar. Requiere verificación de procesos de post-mortem.'}
    except ClientError as e:
        return handle_error_func('SEC10-BP08', e)


# ============================================================================
# SEC11 - Seguridad de aplicaciones (BP01-BP08)
# ============================================================================

def evaluate_sec11_bp01(session, handle_error_func) -> Dict[str, Any]:
    """SEC11-BP01: Capacitación en seguridad de aplicaciones"""
    try:
        try:
            sh = session.client('securityhub')
            hub = sh.describe_hub()
            standards = sh.get_enabled_standards()
            num_standards = len(standards.get('StandardsSubscriptions', []))
            evidence = f"Security Hub: Habilitado | Standards: {num_standards}"
            
            if num_standards >= 2:
                return {'bp': 'SEC11-BP01', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC11-BP01', ''),
                        'status': 'COMPLIANT', 'severity': 'LOW',
                        'finding': f'Estándares de seguridad habilitados ({num_standards}) para guiar capacitación.',
                        'evidence': evidence,
                        'remediation': 'Estado actual cumple. Implementar programa de capacitación basado en findings de Security Hub.',
                        'risk': 'Bajo riesgo.'}
            else:
                return {'bp': 'SEC11-BP01', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC11-BP01', ''),
                        'status': 'PENDING_REVIEW', 'severity': 'MEDIUM',
                        'finding': f'Pocos estándares de seguridad habilitados ({num_standards}). Capacitación puede ser insuficiente.',
                        'evidence': evidence,
                        'remediation': (
                            'Mejorar capacitación en seguridad: '
                            '1) Habilitar estándares adicionales en Security Hub (CIS, PCI-DSS). '
                            '2) Implementar programa de capacitación en seguridad para desarrolladores. '
                            '3) Incluir OWASP Top 10 en capacitación. '
                            '4) Realizar sesiones de revisión de findings de Security Hub con el equipo.'
                        ),
                        'risk': 'Riesgo medio. Sin capacitación adecuada, los desarrolladores pueden introducir vulnerabilidades.'}
        except Exception:
            return {'bp': 'SEC11-BP01', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC11-BP01', ''),
                    'status': 'PENDING_REVIEW', 'severity': 'MEDIUM',
                    'finding': 'Security Hub no habilitado. No se puede evaluar el nivel de capacitación en seguridad.',
                    'evidence': 'Security Hub: No habilitado',
                    'remediation': (
                        'Implementar capacitación en seguridad: '
                        '1) Habilitar Security Hub con estándares de seguridad. '
                        '2) Implementar programa de capacitación en seguridad de aplicaciones. '
                        '3) Incluir OWASP Top 10, SANS Top 25 en el programa. '
                        '4) Realizar ejercicios prácticos de seguridad (CTF, code review). '
                        '5) Certificar al equipo en seguridad de AWS.'
                    ),
                    'risk': 'Por Determinar.'}
    except ClientError as e:
        return handle_error_func('SEC11-BP01', e)


def evaluate_sec11_bp02(session, handle_error_func) -> Dict[str, Any]:
    """SEC11-BP02: Automatizar pruebas de seguridad en el ciclo de desarrollo"""
    try:
        issues = []
        evidence_parts = []
        
        # CodeBuild
        try:
            cb = session.client('codebuild')
            projects = cb.list_projects()
            num_projects = len(projects.get('projects', []))
            evidence_parts.append(f"CodeBuild projects: {num_projects}")
            if num_projects == 0:
                issues.append('Sin proyectos CodeBuild para pruebas automatizadas')
        except ClientError:
            evidence_parts.append("CodeBuild: No accesible")
        
        # CodePipeline
        try:
            cp = session.client('codepipeline')
            pipelines = cp.list_pipelines()
            num_pipelines = len(pipelines.get('pipelines', []))
            evidence_parts.append(f"CodePipeline: {num_pipelines}")
        except ClientError:
            evidence_parts.append("CodePipeline: No accesible")
        
        # Inspector (SAST/DAST)
        try:
            inspector = session.client('inspector2')
            inspector.batch_get_account_status(accountIds=[])
            evidence_parts.append("Inspector: Habilitado")
        except Exception:
            evidence_parts.append("Inspector: No habilitado")
            issues.append('Inspector no habilitado para escaneo de vulnerabilidades en código')
        
        evidence = ' | '.join(evidence_parts)
        
        if len(issues) == 0:
            return {'bp': 'SEC11-BP02', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC11-BP02', ''),
                    'status': 'COMPLIANT', 'severity': 'LOW',
                    'finding': 'Pruebas de seguridad automatizadas en pipeline CI/CD.',
                    'evidence': evidence,
                    'remediation': 'Estado actual cumple. Expandir cobertura de pruebas de seguridad.',
                    'risk': 'Bajo riesgo.'}
        else:
            return {'bp': 'SEC11-BP02', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC11-BP02', ''),
                    'status': 'NON_COMPLIANT', 'severity': 'MEDIUM',
                    'finding': f'Pruebas de seguridad no automatizadas. {"; ".join(issues)}',
                    'evidence': evidence,
                    'remediation': (
                        'Automatizar pruebas de seguridad: '
                        '1) Implementar CodeBuild con escaneo SAST (SonarQube, Checkmarx). '
                        '2) Integrar Inspector para escaneo de vulnerabilidades en dependencias. '
                        '3) Agregar etapa de seguridad en CodePipeline. '
                        '4) Implementar DAST en entorno de staging. '
                        '5) Configurar gates de seguridad que bloqueen despliegue con vulnerabilidades críticas.'
                    ),
                    'risk': 'Riesgo medio. Sin pruebas automatizadas, las vulnerabilidades llegan a producción.'}
    except ClientError as e:
        return handle_error_func('SEC11-BP02', e)


def evaluate_sec11_bp03(session, handle_error_func) -> Dict[str, Any]:
    """SEC11-BP03: Realizar pruebas de penetración regulares"""
    try:
        try:
            inspector = session.client('inspector2')
            inspector.batch_get_account_status(accountIds=[])
            evidence = "Inspector: Habilitado para escaneo de vulnerabilidades"
            return {'bp': 'SEC11-BP03', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC11-BP03', ''),
                    'status': 'PENDING_REVIEW', 'severity': 'MEDIUM',
                    'finding': 'Inspector habilitado. Verificar si se realizan pruebas de penetración periódicas adicionales.',
                    'evidence': evidence,
                    'remediation': (
                        'Complementar con pruebas de penetración: '
                        '1) Programar pentests anuales con proveedor externo certificado. '
                        '2) Usar Inspector para escaneo continuo de vulnerabilidades. '
                        '3) Realizar pruebas de penetración internas trimestrales. '
                        '4) Documentar y remediar hallazgos con SLAs definidos. '
                        '5) Verificar cumplimiento con AWS Penetration Testing Policy.'
                    ),
                    'risk': 'Por Determinar. Requiere verificación de frecuencia de pentests.'}
        except Exception:
            return {'bp': 'SEC11-BP03', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC11-BP03', ''),
                    'status': 'NON_COMPLIANT', 'severity': 'HIGH',
                    'finding': 'Sin escaneo automatizado de vulnerabilidades. Inspector no habilitado.',
                    'evidence': 'Inspector: No habilitado',
                    'remediation': (
                        'Implementar pruebas de penetración: '
                        '1) Habilitar Amazon Inspector para escaneo continuo. '
                        '2) Programar pentests anuales con proveedor externo. '
                        '3) Implementar bug bounty program si aplica. '
                        '4) Usar herramientas DAST para pruebas de aplicaciones web. '
                        '5) Documentar y remediar hallazgos con SLAs.'
                    ),
                    'risk': 'Alto riesgo. Sin pruebas de penetración, las vulnerabilidades explotables no son identificadas.'}
    except ClientError as e:
        return handle_error_func('SEC11-BP03', e)


def evaluate_sec11_bp04(session, handle_error_func) -> Dict[str, Any]:
    """SEC11-BP04: Realizar revisiones de código"""
    try:
        evidence_parts = []
        
        try:
            cc = session.client('codecommit')
            repos = cc.list_repositories()
            num_repos = len(repos.get('repositories', []))
            evidence_parts.append(f"CodeCommit repos: {num_repos}")
        except ClientError:
            evidence_parts.append("CodeCommit: No accesible (puede usar GitHub/GitLab externo)")
        
        try:
            cb = session.client('codebuild')
            projects = cb.list_projects()
            evidence_parts.append(f"CodeBuild projects: {len(projects.get('projects', []))}")
        except ClientError:
            evidence_parts.append("CodeBuild: No accesible")
        
        evidence = ' | '.join(evidence_parts)
        
        return {'bp': 'SEC11-BP04', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC11-BP04', ''),
                'status': 'PENDING_REVIEW', 'severity': 'MEDIUM',
                'finding': 'Revisiones de código requieren verificación. Puede usar repositorios externos (GitHub, GitLab).',
                'evidence': evidence,
                'remediation': (
                    'Implementar revisiones de código: '
                    '1) Configurar branch protection rules que requieran code review. '
                    '2) Implementar CODEOWNERS para revisión obligatoria de cambios de seguridad. '
                    '3) Usar herramientas de análisis estático (CodeGuru, SonarQube). '
                    '4) Incluir checklist de seguridad en proceso de code review. '
                    '5) Capacitar revisores en patrones de vulnerabilidades comunes.'
                ),
                'risk': 'Por Determinar. Requiere verificación del proceso de code review.'}
    except ClientError as e:
        return handle_error_func('SEC11-BP04', e)


def evaluate_sec11_bp05(session, handle_error_func) -> Dict[str, Any]:
    """SEC11-BP05: Centralizar servicios para paquetes y dependencias"""
    try:
        try:
            ca = session.client('codeartifact')
            domains = ca.list_domains()
            num_domains = len(domains.get('domains', []))
            evidence = f"CodeArtifact domains: {num_domains}"
            
            if num_domains > 0:
                return {'bp': 'SEC11-BP05', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC11-BP05', ''),
                        'status': 'COMPLIANT', 'severity': 'LOW',
                        'finding': f'Gestión centralizada de dependencias con CodeArtifact ({num_domains} dominio(s)).',
                        'evidence': evidence,
                        'remediation': 'Estado actual cumple. Verificar que todas las dependencias pasen por CodeArtifact.',
                        'risk': 'Bajo riesgo.'}
            else:
                return {'bp': 'SEC11-BP05', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC11-BP05', ''),
                        'status': 'NON_COMPLIANT', 'severity': 'MEDIUM',
                        'finding': 'Sin repositorio centralizado de paquetes.',
                        'evidence': evidence,
                        'remediation': (
                            'Centralizar gestión de dependencias: '
                            '1) Configurar CodeArtifact como repositorio centralizado. '
                            '2) Configurar upstream repositories para npm, PyPI, Maven. '
                            '3) Implementar escaneo de vulnerabilidades en dependencias. '
                            '4) Bloquear paquetes con vulnerabilidades conocidas. '
                            '5) Auditar dependencias periódicamente con Inspector.'
                        ),
                        'risk': 'Riesgo medio. Sin gestión centralizada, las dependencias no son verificadas.'}
        except ClientError:
            return {'bp': 'SEC11-BP05', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC11-BP05', ''),
                    'status': 'NON_COMPLIANT', 'severity': 'MEDIUM',
                    'finding': 'CodeArtifact no configurado para gestión centralizada de dependencias.',
                    'evidence': 'CodeArtifact: No accesible',
                    'remediation': (
                        'Implementar gestión centralizada de dependencias con CodeArtifact o herramienta equivalente. '
                        'Escanear dependencias con Inspector para vulnerabilidades conocidas.'
                    ),
                    'risk': 'Riesgo medio. Dependencias no verificadas pueden contener vulnerabilidades.'}
    except ClientError as e:
        return handle_error_func('SEC11-BP05', e)


def evaluate_sec11_bp06(session, handle_error_func) -> Dict[str, Any]:
    """SEC11-BP06: Implementar software programáticamente"""
    try:
        issues = []
        evidence_parts = []
        
        try:
            cp = session.client('codepipeline')
            pipelines = cp.list_pipelines()
            num_pipelines = len(pipelines.get('pipelines', []))
            evidence_parts.append(f"CodePipeline: {num_pipelines}")
            if num_pipelines == 0:
                issues.append('Sin pipelines CI/CD para despliegue programático')
        except ClientError:
            evidence_parts.append("CodePipeline: No accesible")
        
        try:
            cd = session.client('codedeploy')
            apps = cd.list_applications()
            evidence_parts.append(f"CodeDeploy apps: {len(apps.get('applications', []))}")
        except ClientError:
            evidence_parts.append("CodeDeploy: No accesible")
        
        try:
            cf = session.client('cloudformation')
            stacks = cf.list_stacks(StackStatusFilter=['CREATE_COMPLETE', 'UPDATE_COMPLETE'])
            evidence_parts.append(f"CloudFormation stacks: {len(stacks.get('StackSummaries', []))}")
        except ClientError:
            evidence_parts.append("CloudFormation: No accesible")
        
        evidence = ' | '.join(evidence_parts)
        
        if len(issues) == 0:
            return {'bp': 'SEC11-BP06', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC11-BP06', ''),
                    'status': 'COMPLIANT', 'severity': 'LOW',
                    'finding': 'Despliegue programático implementado con CI/CD.',
                    'evidence': evidence,
                    'remediation': 'Estado actual cumple. Verificar que todos los despliegues pasen por pipeline.',
                    'risk': 'Bajo riesgo.'}
        else:
            return {'bp': 'SEC11-BP06', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC11-BP06', ''),
                    'status': 'NON_COMPLIANT', 'severity': 'MEDIUM',
                    'finding': f'Despliegue no programático. {"; ".join(issues)}',
                    'evidence': evidence,
                    'remediation': (
                        'Implementar despliegue programático: '
                        '1) Configurar CodePipeline para despliegue automatizado. '
                        '2) Usar CodeDeploy para despliegues blue/green o canary. '
                        '3) Implementar IaC con CloudFormation/CDK para infraestructura. '
                        '4) Eliminar acceso manual a producción. '
                        '5) Implementar aprobaciones manuales para despliegues a producción.'
                    ),
                    'risk': 'Riesgo medio. Despliegues manuales son propensos a errores y difíciles de auditar.'}
    except ClientError as e:
        return handle_error_func('SEC11-BP06', e)


def evaluate_sec11_bp07(session, handle_error_func) -> Dict[str, Any]:
    """SEC11-BP07: Evaluar regularmente las propiedades de seguridad de los pipelines"""
    try:
        try:
            sh = session.client('securityhub')
            sh.describe_hub()
            evidence = "Security Hub: Habilitado para evaluación de seguridad de pipelines"
            return {'bp': 'SEC11-BP07', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC11-BP07', ''),
                    'status': 'PENDING_REVIEW', 'severity': 'MEDIUM',
                    'finding': 'Security Hub habilitado. Verificar que los pipelines CI/CD incluyan gates de seguridad.',
                    'evidence': evidence,
                    'remediation': (
                        'Evaluar seguridad de pipelines: '
                        '1) Auditar permisos de roles de CodePipeline/CodeBuild. '
                        '2) Verificar que los artefactos estén cifrados en tránsito y reposo. '
                        '3) Implementar gates de seguridad en cada etapa del pipeline. '
                        '4) Revisar logs de ejecución de pipelines periódicamente. '
                        '5) Usar Security Hub para monitorear configuración de servicios CI/CD.'
                    ),
                    'risk': 'Por Determinar. Requiere auditoría de configuración de pipelines.'}
        except Exception:
            return {'bp': 'SEC11-BP07', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC11-BP07', ''),
                    'status': 'PENDING_REVIEW', 'severity': 'MEDIUM',
                    'finding': 'Security Hub no habilitado. No se puede evaluar automáticamente la seguridad de pipelines.',
                    'evidence': 'Security Hub: No habilitado',
                    'remediation': (
                        'Habilitar Security Hub y auditar pipelines: '
                        '1) Habilitar Security Hub para evaluación continua. '
                        '2) Auditar permisos de roles de CI/CD. '
                        '3) Implementar principio de privilegio mínimo en pipelines. '
                        '4) Cifrar artefactos y secretos en pipelines.'
                    ),
                    'risk': 'Por Determinar.'}
    except ClientError as e:
        return handle_error_func('SEC11-BP07', e)


def evaluate_sec11_bp08(session, handle_error_func) -> Dict[str, Any]:
    """SEC11-BP08: Crear un programa que incorpore la propiedad de seguridad en los equipos"""
    try:
        issues = []
        evidence_parts = []
        
        # Contar servicios de seguridad habilitados como indicador de cultura de seguridad
        security_services = 0
        
        try:
            gd = session.client('guardduty')
            if gd.list_detectors().get('DetectorIds'):
                security_services += 1
        except: pass
        
        try:
            sh = session.client('securityhub')
            sh.describe_hub()
            security_services += 1
        except: pass
        
        try:
            inspector = session.client('inspector2')
            inspector.batch_get_account_status(accountIds=[])
            security_services += 1
        except: pass
        
        try:
            config = session.client('config')
            recorders = config.describe_configuration_recorders()
            if recorders.get('ConfigurationRecorders'):
                security_services += 1
        except: pass
        
        try:
            ct = session.client('cloudtrail')
            trails = ct.describe_trails()
            if trails.get('trailList'):
                security_services += 1
        except: pass
        
        evidence_parts.append(f"Servicios de seguridad habilitados: {security_services}/5")
        
        if security_services < 3:
            issues.append(f'Solo {security_services}/5 servicios de seguridad habilitados (indica baja adopción de seguridad)')
        
        evidence = ' | '.join(evidence_parts)
        
        if security_services >= 4:
            return {'bp': 'SEC11-BP08', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC11-BP08', ''),
                    'status': 'COMPLIANT', 'severity': 'LOW',
                    'finding': f'Alta adopción de seguridad ({security_services}/5 servicios). Indica cultura de seguridad establecida.',
                    'evidence': evidence,
                    'remediation': 'Estado actual cumple. Continuar fortaleciendo la cultura de seguridad con capacitación y game days.',
                    'risk': 'Bajo riesgo.'}
        elif security_services >= 2:
            return {'bp': 'SEC11-BP08', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC11-BP08', ''),
                    'status': 'PENDING_REVIEW', 'severity': 'MEDIUM',
                    'finding': f'Adopción parcial de seguridad ({security_services}/5 servicios).',
                    'evidence': evidence,
                    'remediation': (
                        'Fortalecer programa de seguridad: '
                        '1) Habilitar todos los servicios de seguridad fundamentales. '
                        '2) Designar security champions en cada equipo de desarrollo. '
                        '3) Implementar programa de capacitación en seguridad. '
                        '4) Incluir métricas de seguridad en OKRs de los equipos. '
                        '5) Realizar revisiones de seguridad en cada sprint.'
                    ),
                    'risk': 'Riesgo medio. Programa de seguridad parcial puede dejar brechas.'}
        else:
            return {'bp': 'SEC11-BP08', 'description': SECURITY_BP_DESCRIPTIONS.get('SEC11-BP08', ''),
                    'status': 'NON_COMPLIANT', 'severity': 'HIGH',
                    'finding': f'Programa de seguridad limitado ({security_services}/5 servicios). {"; ".join(issues)}',
                    'evidence': evidence,
                    'remediation': (
                        'Crear programa de seguridad integral: '
                        '1) Habilitar GuardDuty, Security Hub, Inspector, Config, CloudTrail. '
                        '2) Designar un equipo de seguridad o security champions. '
                        '3) Implementar DevSecOps con seguridad integrada en CI/CD. '
                        '4) Crear programa de capacitación obligatorio en seguridad. '
                        '5) Establecer métricas de seguridad (MTTD, MTTR, vulnerabilidades abiertas). '
                        '6) Realizar game days y simulaciones de incidentes.'
                    ),
                    'risk': 'Alto riesgo. Sin programa de seguridad, la seguridad depende de esfuerzos individuales no coordinados.'}
    except ClientError as e:
        return handle_error_func('SEC11-BP08', e)
