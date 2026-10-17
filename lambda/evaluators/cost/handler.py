"""
Cost Optimization Pillar Evaluator Lambda
Evaluates 11 Cost Optimization questions with 50 Best Practices
Evaluaciones refinadas basadas en la guía oficial de AWS Well-Architected Framework
"""

import json
import boto3
import os
from datetime import datetime
from typing import Dict, List, Any
from botocore.exceptions import ClientError

# Import from common layer
import sys
sys.path.append('/opt/python')
from autowar_common.credentials_manager import CredentialsManager
import importlib.util

# Load bp_descriptions dynamically to avoid import conflicts
bp_desc_path = os.path.join(os.path.dirname(__file__), 'bp_descriptions.py')
spec = importlib.util.spec_from_file_location("cost_bp_descriptions", bp_desc_path)
bp_desc_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bp_desc_module)
COST_BP_DESCRIPTIONS = bp_desc_module.COST_BP_DESCRIPTIONS


def lambda_handler(event, context):
    """Main handler for Cost Optimization pillar evaluation"""
    cors_headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,X-Session-ID',
        'Access-Control-Allow-Methods': 'POST,OPTIONS'
    }
    
    try:
        headers = event.get('headers', {})
        session_id = headers.get('X-Session-ID') or headers.get('x-session-id')
        
        if not session_id:
            return {'statusCode': 401, 'headers': cors_headers,
                    'body': json.dumps({'error': 'Missing X-Session-ID header'})}
        
        # Check cache
        dynamodb = boto3.resource('dynamodb')
        table_name = os.environ.get('DYNAMODB_TABLE')
        if table_name:
            table = dynamodb.Table(table_name)
            import time
            from boto3.dynamodb.conditions import Key
            response = table.query(
                KeyConditionExpression=Key('session_id').eq(session_id) & Key('evaluation_id').begins_with('cost#'),
                ScanIndexForward=False, Limit=1
            )
            if response.get('Items'):
                latest_eval = response['Items'][0]
                eval_timestamp = int(latest_eval['evaluation_id'].split('#')[1])
                if (int(time.time()) - eval_timestamp) < 300:
                    return {'statusCode': 200, 'headers': cors_headers,
                            'body': json.dumps(latest_eval['data'], default=str)}
        
        creds_manager = CredentialsManager()
        credentials = creds_manager.get_session_credentials(session_id)
        if not credentials:
            return {'statusCode': 401, 'headers': cors_headers,
                    'body': json.dumps({'error': 'Session expired or invalid'})}
        
        regions = credentials.get('regions', [credentials.get('region', 'us-east-1')])
        all_results = []
        
        if len(regions) > 1:
            from concurrent.futures import ThreadPoolExecutor, as_completed
            def evaluate_region(region):
                session = boto3.Session(
                    aws_access_key_id=credentials['access_key_id'],
                    aws_secret_access_key=credentials['secret_access_key'],
                    aws_session_token=credentials.get('session_token'),
                    region_name=region)
                return CostOptimizationEvaluator(session, region).evaluate()
            with ThreadPoolExecutor(max_workers=min(len(regions), 4)) as executor:
                futures = {executor.submit(evaluate_region, r): r for r in regions}
                for future in as_completed(futures):
                    try: all_results.append(future.result())
                    except Exception as e: print(f"Error region {futures[future]}: {e}")
        else:
            region = regions[0] if regions else 'us-east-1'
            session = boto3.Session(
                aws_access_key_id=credentials['access_key_id'],
                aws_secret_access_key=credentials['secret_access_key'],
                aws_session_token=credentials.get('session_token'),
                region_name=region)
            all_results.append(CostOptimizationEvaluator(session, region).evaluate())
        
        final_result = all_results[0] if len(all_results) == 1 else all_results[0]
        if len(all_results) > 1:
            final_result['regions'] = [r.get('region') for r in all_results]
            final_result['multi_region'] = True
        
        if table_name:
            from decimal import Decimal
            def convert_floats(obj):
                if isinstance(obj, float): return Decimal(str(obj))
                elif isinstance(obj, dict): return {k: convert_floats(v) for k, v in obj.items()}
                elif isinstance(obj, list): return [convert_floats(i) for i in obj]
                return obj
            table.put_item(Item={
                'session_id': session_id, 'evaluation_id': f'cost#{int(time.time())}',
                'pillar_id': 'cost', 'timestamp': final_result['timestamp'],
                'data': convert_floats(json.loads(json.dumps(final_result, default=str)))
            })
        
        return {'statusCode': 200, 'headers': cors_headers,
                'body': json.dumps(final_result, default=str)}
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback; traceback.print_exc()
        return {'statusCode': 500, 'headers': cors_headers,
                'body': json.dumps({'error': f'Evaluation failed: {str(e)}'})}


class CostOptimizationEvaluator:
    """Evaluates Cost Optimization pillar (11 questions, 50 BPs)"""
    
    def __init__(self, session: boto3.Session, region: str = None):
        self.session = session
        self.region = region or session.region_name
    
    def evaluate(self) -> Dict[str, Any]:
        questions = []
        questions.append(self._evaluate_cost01())
        questions.append(self._evaluate_cost02())
        questions.append(self._evaluate_cost03())
        questions.append(self._evaluate_cost04())
        questions.append(self._evaluate_cost05())
        questions.append(self._evaluate_cost06())
        questions.append(self._evaluate_cost07())
        questions.append(self._evaluate_cost08())
        questions.append(self._evaluate_cost09())
        questions.append(self._evaluate_cost10())
        questions.append(self._evaluate_cost11())
        
        pillar_score = self._calculate_pillar_score(questions)
        compliance_dist, severity_dist = self._calculate_distributions(questions)
        
        return {
            'pillar_id': 'cost',
            'region': self.region,
            'pillar_name': {'es': 'Optimización de Costos', 'en': 'Cost Optimization'},
            'description': {'es': 'Ejecutar sistemas para entregar valor de negocio al menor precio',
                          'en': 'Run systems to deliver business value at the lowest price point'},
            'overall_score': pillar_score,
            'total_findings': sum(len(q['findings']) for q in questions),
            'total_best_practices': sum(q['bps_evaluated'] for q in questions),
            'timestamp': datetime.utcnow().isoformat(),
            'questions': questions,
            'compliance_distribution': compliance_dist,
            'severity_distribution': severity_dist
        }
    
    def _handle_error(self, bp_id, e):
        return {
            'bp': bp_id, 'description': COST_BP_DESCRIPTIONS.get(bp_id, ''),
            'status': 'PENDING_REVIEW', 'severity': 'MEDIUM',
            'finding': 'No se pudo evaluar por permisos insuficientes',
            'evidence': f'Error: {str(e)[:200]}',
            'remediation': 'Otorgar permisos IAM necesarios al rol de evaluación para acceder a los servicios de costos.',
            'risk': 'Por Determinar'
        }
    
    def _pending(self, bp_id, remediation):
        return {
            'bp': bp_id, 'description': COST_BP_DESCRIPTIONS.get(bp_id, ''),
            'status': 'PENDING_REVIEW', 'severity': 'MEDIUM',
            'finding': 'Revisión manual requerida',
            'evidence': f'{bp_id} requiere revisión manual',
            'remediation': remediation, 'risk': 'Por Determinar'
        }

    # ========================================================================
    # COST01: Gestión financiera en la nube (9 BPs)
    # ========================================================================
    def _evaluate_cost01(self) -> Dict[str, Any]:
        findings = []
        
        # COST01-BP01: Establecer propiedad de optimización de costos
        try:
            iam = self.session.client('iam')
            groups = iam.list_groups()['Groups']
            finops_groups = [g for g in groups if any(kw in g['GroupName'].lower() for kw in ['finops', 'cost', 'billing'])]
            
            # Verificar roles con permisos de billing
            roles = iam.list_roles(MaxItems=50)['Roles']
            cost_roles = [r for r in roles if any(kw in r['RoleName'].lower() for kw in ['cost', 'billing', 'finops'])]
            
            evidence = f"Grupos FinOps/Cost: {len(finops_groups)} | Roles de costos: {len(cost_roles)}"
            if finops_groups or cost_roles:
                findings.append({'bp': 'COST01-BP01', 'description': COST_BP_DESCRIPTIONS.get('COST01-BP01', ''),
                    'status': 'COMPLIANT', 'severity': 'LOW',
                    'finding': f'Equipo de gestión de costos identificado con {len(finops_groups)} grupo(s) y {len(cost_roles)} rol(es).',
                    'evidence': evidence,
                    'remediation': 'Estado actual cumple. Verificar que el equipo incluye perfiles financieros, técnicos y empresariales con acceso a Cost Explorer y Budgets.',
                    'risk': 'Bajo riesgo.'})
            else:
                findings.append({'bp': 'COST01-BP01', 'description': COST_BP_DESCRIPTIONS.get('COST01-BP01', ''),
                    'status': 'NON_COMPLIANT', 'severity': 'HIGH',
                    'finding': 'No se identificó equipo de gestión de costos en IAM.',
                    'evidence': evidence,
                    'remediation': ('Establecer propiedad de optimización de costos: '
                        '1) Crear grupo IAM "FinOps" con políticas ViewBilling, CostExplorerAccess, BudgetsAccess. '
                        '2) Asignar perfiles financieros, técnicos y empresariales al grupo. '
                        '3) Crear rol de servicio para acceso programático a APIs de costos. '
                        '4) Definir responsabilidades claras de optimización de costos.'),
                    'risk': 'Sin propiedad de costos, no hay responsable de optimización y los gastos crecen sin control.'})
        except ClientError as e:
            findings.append(self._handle_error('COST01-BP01', e))
        
        # COST01-BP02: Alianza entre finanzas y tecnología
        try:
            iam = self.session.client('iam')
            # Verificar si hay múltiples roles con acceso a Cost Explorer
            roles = iam.list_roles(MaxItems=50)['Roles']
            ce_roles = 0
            for role in roles[:20]:
                try:
                    policies = iam.list_attached_role_policies(RoleName=role['RoleName'])
                    for p in policies.get('AttachedPolicies', []):
                        if any(kw in p['PolicyName'].lower() for kw in ['billing', 'cost', 'finance']):
                            ce_roles += 1
                            break
                except ClientError:
                    pass
            
            evidence = f"Roles con acceso a billing/costos: {ce_roles}"
            if ce_roles >= 2:
                findings.append({'bp': 'COST01-BP02', 'description': COST_BP_DESCRIPTIONS.get('COST01-BP02', ''),
                    'status': 'COMPLIANT', 'severity': 'LOW',
                    'finding': f'Acceso colaborativo a herramientas de costos ({ce_roles} roles con permisos de billing).',
                    'evidence': evidence,
                    'remediation': 'Estado actual cumple. Verificar que existen reuniones recurrentes entre TI y Finanzas para discutir costos.',
                    'risk': 'Bajo riesgo.'})
            else:
                findings.append({'bp': 'COST01-BP02', 'description': COST_BP_DESCRIPTIONS.get('COST01-BP02', ''),
                    'status': 'PENDING_REVIEW', 'severity': 'MEDIUM',
                    'finding': f'Acceso limitado a herramientas de costos ({ce_roles} roles). Requiere verificación de alianza finanzas-tecnología.',
                    'evidence': evidence,
                    'remediation': ('Establecer alianza finanzas-tecnología: '
                        '1) Crear roles IAM compartidos con acceso a Cost Explorer y Budgets para ambos equipos. '
                        '2) Programar reuniones recurrentes entre TI y Finanzas para revisar costos. '
                        '3) Configurar reportes compartidos en Cost Explorer. '
                        '4) Implementar dashboards de costos accesibles para ambos equipos.'),
                    'risk': 'Por Determinar.'})
        except ClientError as e:
            findings.append(self._handle_error('COST01-BP02', e))
        
        # COST01-BP03: Establecer presupuestos y pronósticos
        try:
            budgets_client = self.session.client('budgets')
            account_id = self.session.client('sts').get_caller_identity()['Account']
            budget_list = budgets_client.describe_budgets(AccountId=account_id)
            budgets = budget_list.get('Budgets', [])
            
            # Verificar Cost Explorer forecasting
            try:
                ce = self.session.client('ce')
                forecast = ce.get_cost_forecast(
                    TimePeriod={'Start': datetime.utcnow().strftime('%Y-%m-%d'),
                               'End': (datetime.utcnow().replace(day=28) + __import__('datetime').timedelta(days=4)).strftime('%Y-%m-01')},
                    Metric='UNBLENDED_COST', Granularity='MONTHLY'
                )
                has_forecast = True
                forecast_amount = forecast.get('Total', {}).get('Amount', 'N/A')
            except:
                has_forecast = False
                forecast_amount = 'N/A'
            
            evidence = f"Budgets: {len(budgets)} | Forecast disponible: {'Sí' if has_forecast else 'No'} | Pronóstico: ${forecast_amount}"
            
            if len(budgets) > 0 and has_forecast:
                findings.append({'bp': 'COST01-BP03', 'description': COST_BP_DESCRIPTIONS.get('COST01-BP03', ''),
                    'status': 'COMPLIANT', 'severity': 'LOW',
                    'finding': f'Presupuestos configurados ({len(budgets)}) con forecasting activo.',
                    'evidence': evidence,
                    'remediation': 'Estado actual cumple. Revisar que los presupuestos usen algoritmos basados en tendencias de negocio.',
                    'risk': 'Bajo riesgo.'})
            elif len(budgets) > 0:
                findings.append({'bp': 'COST01-BP03', 'description': COST_BP_DESCRIPTIONS.get('COST01-BP03', ''),
                    'status': 'PENDING_REVIEW', 'severity': 'MEDIUM',
                    'finding': f'Presupuestos configurados ({len(budgets)}) pero forecasting no verificado.',
                    'evidence': evidence,
                    'remediation': ('Completar configuración de presupuestos: '
                        '1) Habilitar Cost Explorer forecasting para proyecciones automáticas. '
                        '2) Configurar alertas en budgets al 80% y 100% del umbral. '
                        '3) Crear budgets por servicio, cuenta y tags para granularidad.'),
                    'risk': 'Riesgo medio. Sin forecasting, los presupuestos son estáticos.'})
            else:
                findings.append({'bp': 'COST01-BP03', 'description': COST_BP_DESCRIPTIONS.get('COST01-BP03', ''),
                    'status': 'NON_COMPLIANT', 'severity': 'HIGH',
                    'finding': 'Sin presupuestos de AWS Budgets configurados.',
                    'evidence': evidence,
                    'remediation': ('Implementar presupuestos y pronósticos: '
                        '1) Crear AWS Budgets con filtros por servicio, región y tags. '
                        '2) Configurar alertas al 50%, 80% y 100% del presupuesto. '
                        '3) Habilitar Cost Explorer con forecasting dinámico. '
                        '4) Crear presupuestos separados por entorno (producción, desarrollo). '
                        '5) Configurar notificaciones SNS para alertas de presupuesto.'),
                    'risk': 'Gasto sin control ni pronóstico. Riesgo de sobrecostos no detectados.'})
        except ClientError as e:
            findings.append(self._handle_error('COST01-BP03', e))
        
        # COST01-BP04: Conciencia de costos en procesos
        try:
            cp = self.session.client('codepipeline')
            pipelines = cp.list_pipelines().get('pipelines', [])
            cf = self.session.client('cloudformation')
            stacks = cf.list_stacks(StackStatusFilter=['CREATE_COMPLETE', 'UPDATE_COMPLETE']).get('StackSummaries', [])
            
            evidence = f"CodePipeline: {len(pipelines)} | CloudFormation stacks: {len(stacks)}"
            if pipelines and stacks:
                findings.append({'bp': 'COST01-BP04', 'description': COST_BP_DESCRIPTIONS.get('COST01-BP04', ''),
                    'status': 'PENDING_REVIEW', 'severity': 'MEDIUM',
                    'finding': f'Procesos CI/CD e IaC detectados. Verificar si incluyen estimaciones de costo.',
                    'evidence': evidence,
                    'remediation': ('Integrar conciencia de costos en procesos: '
                        '1) Agregar estimación de costos en revisiones de arquitectura. '
                        '2) Incluir análisis de costo en pipelines CI/CD (Infracost, cfn-cost). '
                        '3) Capacitar al personal en optimización de costos AWS. '
                        '4) Incluir métricas de costo en OKRs de los equipos.'),
                    'risk': 'Por Determinar.'})
            else:
                findings.append({'bp': 'COST01-BP04', 'description': COST_BP_DESCRIPTIONS.get('COST01-BP04', ''),
                    'status': 'NON_COMPLIANT', 'severity': 'HIGH',
                    'finding': 'Sin procesos CI/CD ni IaC detectados para integrar conciencia de costos.',
                    'evidence': evidence,
                    'remediation': ('Implementar conciencia de costos en procesos organizacionales: '
                        '1) Implementar CI/CD con CodePipeline para despliegues controlados. '
                        '2) Usar IaC (CloudFormation/CDK) para estimar costos antes del despliegue. '
                        '3) Incluir revisión de costos en proceso de aprobación de cambios. '
                        '4) Capacitar equipos en AWS Pricing Calculator y Cost Explorer.'),
                    'risk': 'Sin conciencia de costos, los equipos despliegan sin considerar el impacto financiero.'})
        except ClientError as e:
            findings.append(self._handle_error('COST01-BP04', e))
        
        # COST01-BP05: Reportar y notificar sobre optimización de costos
        try:
            ce = self.session.client('ce')
            monitors = ce.get_anomaly_monitors().get('AnomalyMonitors', [])
            subscriptions = ce.get_anomaly_subscriptions().get('AnomalySubscriptions', []) if monitors else []
            
            evidence = f"Anomaly monitors: {len(monitors)} | Subscriptions: {len(subscriptions)}"
            if monitors and subscriptions:
                findings.append({'bp': 'COST01-BP05', 'description': COST_BP_DESCRIPTIONS.get('COST01-BP05', ''),
                    'status': 'COMPLIANT', 'severity': 'LOW',
                    'finding': f'Detección de anomalías de costos activa con {len(monitors)} monitor(es) y {len(subscriptions)} suscripción(es).',
                    'evidence': evidence,
                    'remediation': 'Estado actual cumple. Verificar que las notificaciones llegan a los responsables correctos.',
                    'risk': 'Bajo riesgo.'})
            elif monitors:
                findings.append({'bp': 'COST01-BP05', 'description': COST_BP_DESCRIPTIONS.get('COST01-BP05', ''),
                    'status': 'NON_COMPLIANT', 'severity': 'MEDIUM',
                    'finding': f'Monitores de anomalías configurados ({len(monitors)}) pero sin suscripciones de notificación.',
                    'evidence': evidence,
                    'remediation': ('Configurar notificaciones de anomalías: '
                        '1) Crear suscripciones en Cost Anomaly Detection con email/SNS. '
                        '2) Configurar umbrales de alerta apropiados. '
                        '3) Asignar responsables para cada tipo de anomalía.'),
                    'risk': 'Anomalías detectadas pero no notificadas al equipo.'})
            else:
                findings.append({'bp': 'COST01-BP05', 'description': COST_BP_DESCRIPTIONS.get('COST01-BP05', ''),
                    'status': 'NON_COMPLIANT', 'severity': 'HIGH',
                    'finding': 'Sin detección de anomalías de costos configurada.',
                    'evidence': evidence,
                    'remediation': ('Implementar reportes y notificaciones de costos: '
                        '1) Habilitar Cost Anomaly Detection con monitores por servicio y cuenta. '
                        '2) Crear suscripciones con notificaciones por email y SNS. '
                        '3) Configurar AWS Budgets con alertas al 80% y 100%. '
                        '4) Crear dashboards de costos en CloudWatch o QuickSight. '
                        '5) Programar reportes semanales de costos al equipo de gestión.'),
                    'risk': 'Sin alertas de costos, los sobrecostos pasan desapercibidos hasta la factura mensual.'})
        except ClientError as e:
            findings.append(self._handle_error('COST01-BP05', e))
        
        # COST01-BP06: Monitoreo proactivo de costos
        try:
            cw = self.session.client('cloudwatch')
            dashboards = cw.list_dashboards().get('DashboardEntries', [])
            cost_dashboards = [d for d in dashboards if any(kw in d['DashboardName'].lower() for kw in ['cost', 'billing', 'spend'])]
            
            evidence = f"Dashboards totales: {len(dashboards)} | Dashboards de costos: {len(cost_dashboards)}"
            if cost_dashboards:
                findings.append({'bp': 'COST01-BP06', 'description': COST_BP_DESCRIPTIONS.get('COST01-BP06', ''),
                    'status': 'COMPLIANT', 'severity': 'LOW',
                    'finding': f'Dashboards de monitoreo de costos configurados ({len(cost_dashboards)}).',
                    'evidence': evidence,
                    'remediation': 'Estado actual cumple. Evaluar si se identifican y promueven tendencias de ahorro positivas.',
                    'risk': 'Bajo riesgo.'})
            else:
                findings.append({'bp': 'COST01-BP06', 'description': COST_BP_DESCRIPTIONS.get('COST01-BP06', ''),
                    'status': 'NON_COMPLIANT', 'severity': 'MEDIUM',
                    'finding': 'Sin dashboards de monitoreo de costos.',
                    'evidence': evidence,
                    'remediation': ('Implementar monitoreo proactivo de costos: '
                        '1) Crear dashboard de CloudWatch con métricas de billing. '
                        '2) Configurar Cost Explorer con reportes personalizados. '
                        '3) Implementar QuickSight para análisis avanzado de costos. '
                        '4) Crear alarmas de CloudWatch para métricas de billing.'),
                    'risk': 'Gestión reactiva de costos. Solo se detectan problemas al revisar la factura.'})
        except ClientError as e:
            findings.append(self._handle_error('COST01-BP06', e))
        
        # COST01-BP07 a BP09: Requieren revisión manual/organizacional
        try:
            # BP07: Verificar Trusted Advisor
            support = self.session.client('support', region_name='us-east-1')
            checks = support.describe_trusted_advisor_checks(language='en')
            cost_checks = [c for c in checks.get('checks', []) if c.get('category') == 'cost_optimizing']
            evidence_bp07 = f"Trusted Advisor cost checks: {len(cost_checks)}"
            if cost_checks:
                findings.append({'bp': 'COST01-BP07', 'description': COST_BP_DESCRIPTIONS.get('COST01-BP07', ''),
                    'status': 'PENDING_REVIEW', 'severity': 'MEDIUM',
                    'finding': f'Trusted Advisor disponible con {len(cost_checks)} verificaciones de costos. Verificar si el equipo las consulta regularmente.',
                    'evidence': evidence_bp07,
                    'remediation': ('Mantenerse actualizado con servicios de menor costo: '
                        '1) Revisar recomendaciones de Trusted Advisor mensualmente. '
                        '2) Suscribirse a AWS What\'s New para nuevos servicios. '
                        '3) Consultar AWS Solutions Architects para optimización. '
                        '4) Evaluar nuevos servicios que puedan reducir costos.'),
                    'risk': 'Por Determinar.'})
            else:
                findings.append(self._pending('COST01-BP07',
                    'Revisar recomendaciones de Trusted Advisor y consultar expertos AWS sobre servicios de menor costo.'))
        except:
            findings.append(self._pending('COST01-BP07',
                'Habilitar AWS Support Business/Enterprise para acceso a Trusted Advisor completo. Consultar expertos AWS sobre servicios de menor costo.'))
        
        findings.append(self._pending('COST01-BP08',
            'Crear cultura de conciencia de costos: 1) Implementar programa de capacitación en costos AWS. '
            '2) Incluir métricas de costo en evaluaciones de desempeño. '
            '3) Gamificar la optimización de costos con reconocimientos. '
            '4) Compartir reportes de ahorro con toda la organización.'))
        
        findings.append(self._pending('COST01-BP09',
            'Cuantificar valor de negocio: 1) Calcular ROI de optimizaciones realizadas. '
            '2) Presentar métricas de ahorro a stakeholders en términos de negocio. '
            '3) Correlacionar inversión en nube con resultados de negocio. '
            '4) Documentar casos de éxito de optimización.'))
        
        return self._create_question('COST01', findings,
            'How do you implement cloud financial management?', 'Gestión financiera en la nube')

    # ========================================================================
    # COST02: Gobernanza de uso (6 BPs)
    # ========================================================================
    def _evaluate_cost02(self) -> Dict[str, Any]:
        findings = []
        
        # COST02-BP01: Políticas basadas en requisitos organizacionales
        findings.append(self._pending('COST02-BP01',
            'Revisar políticas documentadas de gestión de ciclo de vida de recursos: '
            '1) Verificar que existen políticas de aprovisionamiento y desaprovisionamiento. '
            '2) Confirmar que las políticas definen quién puede crear/eliminar recursos. '
            '3) Validar que existen procesos de aprobación para recursos costosos.'))
        
        # COST02-BP02: Implementar metas y objetivos
        findings.append(self._pending('COST02-BP02',
            'Validar objetivos de costo medibles: '
            '1) Verificar que cada carga de trabajo tiene objetivos de costo asignados. '
            '2) Confirmar que los objetivos se evalúan periódicamente. '
            '3) Revisar si existen KPIs de costo por equipo/proyecto.'))
        
        # COST02-BP03: Implementar estructura de cuentas
        try:
            org = self.session.client('organizations')
            org_info = org.describe_organization()['Organization']
            accounts = org.list_accounts()['Accounts']
            roots = org.list_roots()['Roots']
            ous = []
            if roots:
                try:
                    ous = org.list_organizational_units_for_parent(ParentId=roots[0]['Id']).get('OrganizationalUnits', [])
                except: pass
            
            evidence = f"Organización: {org_info['Id']} | Cuentas: {len(accounts)} | OUs: {len(ous)}"
            if len(accounts) > 1 and len(ous) > 0:
                findings.append({'bp': 'COST02-BP03', 'description': COST_BP_DESCRIPTIONS.get('COST02-BP03', ''),
                    'status': 'COMPLIANT', 'severity': 'LOW',
                    'finding': f'Estructura de cuentas implementada con {len(accounts)} cuentas y {len(ous)} OUs.',
                    'evidence': evidence,
                    'remediation': 'Estado actual cumple. Auditar que la estructura de OUs facilita la asignación de costos organizacionales.',
                    'risk': 'Bajo riesgo.'})
            else:
                findings.append({'bp': 'COST02-BP03', 'description': COST_BP_DESCRIPTIONS.get('COST02-BP03', ''),
                    'status': 'NON_COMPLIANT', 'severity': 'MEDIUM',
                    'finding': 'Estructura de cuentas insuficiente para gestión de costos.',
                    'evidence': evidence,
                    'remediation': ('Implementar estructura de cuentas: '
                        '1) Crear OUs por entorno (Producción, Desarrollo, Staging). '
                        '2) Separar cuentas por carga de trabajo para asignación de costos. '
                        '3) Habilitar consolidated billing en Organizations. '
                        '4) Configurar cost allocation tags a nivel de organización.'),
                    'risk': 'Sin estructura de cuentas, la asignación de costos es difícil.'})
        except ClientError as e:
            findings.append(self._handle_error('COST02-BP03', e))
        
        # COST02-BP04: Implementar grupos y roles
        try:
            iam = self.session.client('iam')
            groups = iam.list_groups()['Groups']
            env_groups = [g for g in groups if any(kw in g['GroupName'].lower() for kw in ['dev', 'prod', 'staging', 'test', 'admin'])]
            
            evidence = f"Grupos IAM: {len(groups)} total | Grupos por entorno: {len(env_groups)}"
            if len(env_groups) >= 2:
                findings.append({'bp': 'COST02-BP04', 'description': COST_BP_DESCRIPTIONS.get('COST02-BP04', ''),
                    'status': 'COMPLIANT', 'severity': 'LOW',
                    'finding': f'Grupos IAM por entorno configurados ({len(env_groups)}).',
                    'evidence': evidence,
                    'remediation': 'Estado actual cumple. Verificar que los permisos restringen quién puede lanzar o modificar infraestructura.',
                    'risk': 'Bajo riesgo.'})
            else:
                findings.append({'bp': 'COST02-BP04', 'description': COST_BP_DESCRIPTIONS.get('COST02-BP04', ''),
                    'status': 'NON_COMPLIANT', 'severity': 'MEDIUM',
                    'finding': f'Grupos IAM por entorno insuficientes ({len(env_groups)}).',
                    'evidence': evidence,
                    'remediation': ('Implementar grupos y roles por entorno: '
                        '1) Crear grupos IAM por entorno (desarrollo, pruebas, producción). '
                        '2) Restringir permisos de creación de recursos por grupo. '
                        '3) Implementar SCPs para limitar tipos de instancias por OU. '
                        '4) Usar permission boundaries para limitar costos máximos.'),
                    'risk': 'Sin control de acceso por entorno, cualquier usuario puede crear recursos costosos.'})
        except ClientError as e:
            findings.append(self._handle_error('COST02-BP04', e))
        
        # COST02-BP05: Implementar controles de costos
        findings.append(self._pending('COST02-BP05',
            'Verificar controles de costos: '
            '1) Revisar SCPs que limiten regiones o tipos de instancias. '
            '2) Verificar que existen límites de gasto por cuenta/OU. '
            '3) Confirmar que hay procesos de aprobación para recursos costosos. '
            '4) Evaluar uso de AWS Service Catalog para controlar aprovisionamiento.'))
        
        # COST02-BP06: Rastrear ciclo de vida de proyectos
        findings.append(self._pending('COST02-BP06',
            'Controlar ciclo de vida de entornos: '
            '1) Verificar si existen procesos de auditoría al cerrar proyectos. '
            '2) Confirmar que los recursos se eliminan al finalizar proyectos. '
            '3) Implementar tags de fecha de expiración en recursos temporales. '
            '4) Configurar Lambda para limpieza automática de recursos expirados.'))
        
        return self._create_question('COST02', findings,
            'How do you govern usage?', 'Gobernanza de uso')

    # ========================================================================
    # COST03: Monitoreo de costos y uso (6 BPs)
    # ========================================================================
    def _evaluate_cost03(self) -> Dict[str, Any]:
        findings = []
        
        # COST03-BP01: Configurar fuentes de información detalladas
        try:
            ce = self.session.client('ce')
            cost_data = ce.get_cost_and_usage(
                TimePeriod={'Start': (datetime.utcnow().replace(day=1)).strftime('%Y-%m-%d'),
                           'End': datetime.utcnow().strftime('%Y-%m-%d')},
                Granularity='MONTHLY', Metrics=['UnblendedCost']
            )
            current_cost = cost_data['ResultsByTime'][0]['Total']['UnblendedCost']['Amount'] if cost_data.get('ResultsByTime') else '0'
            
            evidence = f"Cost Explorer: Accesible | Costo mes actual: ${float(current_cost):.2f}"
            findings.append({'bp': 'COST03-BP01', 'description': COST_BP_DESCRIPTIONS.get('COST03-BP01', ''),
                'status': 'COMPLIANT', 'severity': 'LOW',
                'finding': f'Cost Explorer accesible. Costo del mes actual: ${float(current_cost):.2f}.',
                'evidence': evidence,
                'remediation': 'Estado actual cumple. Verificar que el CUR (Cost and Usage Report) esté activo para análisis detallado.',
                'risk': 'Bajo riesgo.'})
        except ClientError:
            findings.append({'bp': 'COST03-BP01', 'description': COST_BP_DESCRIPTIONS.get('COST03-BP01', ''),
                'status': 'NON_COMPLIANT', 'severity': 'HIGH',
                'finding': 'Cost Explorer no accesible. Sin visibilidad de costos.',
                'evidence': 'Cost Explorer: No accesible (posible falta de permisos o no habilitado)',
                'remediation': ('Configurar fuentes de información de costos: '
                    '1) Habilitar Cost Explorer en la consola de Billing. '
                    '2) Activar Cost and Usage Report (CUR) con granularidad horaria. '
                    '3) Configurar CUR para exportar a S3 para análisis con Athena. '
                    '4) Otorgar permisos ce:GetCostAndUsage al rol de evaluación.'),
                'risk': 'Sin visibilidad de costos, no se pueden tomar decisiones informadas.'})
        
        # COST03-BP02: Agregar información organizacional a costos
        try:
            # Verificar tagging de recursos
            ec2 = self.session.client('ec2')
            s3 = self.session.client('s3')
            
            # Sample de recursos para verificar tags
            tagged_count = 0
            total_checked = 0
            
            try:
                buckets = s3.list_buckets().get('Buckets', [])[:10]
                for bucket in buckets:
                    total_checked += 1
                    try:
                        tags = s3.get_bucket_tagging(Bucket=bucket['Name'])
                        if tags.get('TagSet'):
                            tagged_count += 1
                    except ClientError:
                        pass
            except: pass
            
            try:
                instances = ec2.describe_instances(MaxResults=10)
                for r in instances.get('Reservations', []):
                    for i in r['Instances']:
                        total_checked += 1
                        if i.get('Tags'):
                            tagged_count += 1
            except: pass
            
            pct = (tagged_count / total_checked * 100) if total_checked > 0 else 0
            evidence = f"Recursos verificados: {total_checked} | Con tags: {tagged_count} ({pct:.0f}%)"
            
            if pct >= 80:
                findings.append({'bp': 'COST03-BP02', 'description': COST_BP_DESCRIPTIONS.get('COST03-BP02', ''),
                    'status': 'COMPLIANT', 'severity': 'LOW',
                    'finding': f'Buen nivel de etiquetado ({pct:.0f}% de recursos con tags).',
                    'evidence': evidence,
                    'remediation': 'Estado actual cumple. Verificar que las tags de asignación de costos estén activadas en Billing.',
                    'risk': 'Bajo riesgo.'})
            else:
                findings.append({'bp': 'COST03-BP02', 'description': COST_BP_DESCRIPTIONS.get('COST03-BP02', ''),
                    'status': 'NON_COMPLIANT', 'severity': 'HIGH',
                    'finding': f'Etiquetado insuficiente ({pct:.0f}% de recursos con tags, se requiere >=80%).',
                    'evidence': evidence,
                    'remediation': ('Implementar etiquetado organizacional: '
                        '1) Definir esquema de tags obligatorias (Environment, Team, Project, CostCenter). '
                        '2) Activar cost allocation tags en la consola de Billing. '
                        '3) Implementar AWS Tag Policies en Organizations. '
                        '4) Usar Config Rules para detectar recursos sin tags. '
                        '5) Automatizar etiquetado con Lambda y EventBridge.'),
                    'risk': 'Sin etiquetado, no se puede asignar costos por equipo, proyecto o entorno.'})
        except ClientError as e:
            findings.append(self._handle_error('COST03-BP02', e))
        
        # COST03-BP03: Identificar categorías de atribución de costos
        findings.append(self._pending('COST03-BP03',
            'Configurar categorías de costos: '
            '1) Revisar Cost Categories en la consola de Billing. '
            '2) Crear categorías por unidad de negocio o departamento. '
            '3) Mapear cuentas y tags a categorías de costos. '
            '4) Configurar reportes por categoría en Cost Explorer.'))
        
        # COST03-BP04: Establecer métricas organizacionales
        findings.append(self._pending('COST03-BP04',
            'Establecer métricas de eficiencia: '
            '1) Definir métricas de negocio correlacionadas con infraestructura (costo por transacción, por usuario). '
            '2) Configurar dashboards que muestren eficiencia de costo. '
            '3) Establecer benchmarks de costo por unidad de trabajo.'))
        
        # COST03-BP05: Configurar herramientas de billing y gestión de costos
        try:
            # Verificar CUR
            cur = self.session.client('cur', region_name='us-east-1')
            reports = cur.describe_report_definitions()
            num_reports = len(reports.get('ReportDefinitions', []))
            
            evidence = f"Cost and Usage Reports: {num_reports}"
            if num_reports > 0:
                findings.append({'bp': 'COST03-BP05', 'description': COST_BP_DESCRIPTIONS.get('COST03-BP05', ''),
                    'status': 'COMPLIANT', 'severity': 'LOW',
                    'finding': f'CUR configurado ({num_reports} reporte(s)).',
                    'evidence': evidence,
                    'remediation': 'Estado actual cumple. Verificar que el CUR se exporta a S3 para análisis con Athena/QuickSight.',
                    'risk': 'Bajo riesgo.'})
            else:
                findings.append({'bp': 'COST03-BP05', 'description': COST_BP_DESCRIPTIONS.get('COST03-BP05', ''),
                    'status': 'NON_COMPLIANT', 'severity': 'HIGH',
                    'finding': 'Sin Cost and Usage Reports configurados.',
                    'evidence': evidence,
                    'remediation': ('Configurar herramientas de billing: '
                        '1) Crear Cost and Usage Report con granularidad horaria. '
                        '2) Exportar CUR a S3 para análisis con Athena. '
                        '3) Habilitar facturación consolidada en Organizations. '
                        '4) Configurar AWS Budgets con alertas automáticas.'),
                    'risk': 'Sin CUR, el análisis detallado de costos es limitado.'})
        except ClientError:
            findings.append(self._pending('COST03-BP05',
                'Configurar Cost and Usage Report (CUR) con granularidad horaria y exportación a S3.'))
        
        # COST03-BP06: Asignar costos basados en métricas de workload
        findings.append(self._pending('COST03-BP06',
            'Asignar costos por métricas: '
            '1) Analizar datos de CUR con Athena para medir eficiencia. '
            '2) Correlacionar costos con métricas de negocio. '
            '3) Implementar chargeback/showback por equipo. '
            '4) Crear reportes de eficiencia de costo por workload.'))
        
        return self._create_question('COST03', findings,
            'How do you monitor your cost and usage?', 'Monitoreo de costos y uso')

    # ========================================================================
    # COST04: Desmantelamiento de recursos (5 BPs)
    # ========================================================================
    def _evaluate_cost04(self) -> Dict[str, Any]:
        findings = []
        
        # COST04-BP01: Rastrear recursos durante su vida útil
        findings.append(self._pending('COST04-BP01',
            'Rastrear recursos: 1) Verificar uso de tags para rastrear asociaciones de sistemas. '
            '2) Implementar tags de fecha de creación y propietario. '
            '3) Usar AWS Config para inventario de recursos. '
            '4) Configurar Resource Groups para agrupar recursos relacionados.'))
        
        # COST04-BP02: Implementar proceso de desmantelamiento
        findings.append(self._pending('COST04-BP02',
            'Proceso de desmantelamiento: 1) Documentar proceso para identificar y retirar recursos sin usar. '
            '2) Definir criterios de inactividad (ej: sin tráfico por 30 días). '
            '3) Implementar flujo de aprobación para eliminación de recursos. '
            '4) Mantener registro de recursos desmantelados.'))
        
        # COST04-BP03: Desmantelar recursos no utilizados
        try:
            ec2 = self.session.client('ec2')
            issues = []
            evidence_parts = []
            
            # Instancias detenidas
            stopped = ec2.describe_instances(Filters=[{'Name': 'instance-state-name', 'Values': ['stopped']}])
            stopped_count = sum(len(r['Instances']) for r in stopped['Reservations'])
            evidence_parts.append(f"EC2 detenidas: {stopped_count}")
            if stopped_count > 0:
                issues.append(f'{stopped_count} instancia(s) EC2 detenidas')
            
            # Volúmenes no adjuntos
            volumes = ec2.describe_volumes(Filters=[{'Name': 'status', 'Values': ['available']}])
            unattached = len(volumes.get('Volumes', []))
            evidence_parts.append(f"EBS no adjuntos: {unattached}")
            if unattached > 0:
                issues.append(f'{unattached} volumen(es) EBS no adjuntos')
            
            # EIPs no asociadas
            eips = ec2.describe_addresses()
            unassociated = [e for e in eips.get('Addresses', []) if not e.get('AssociationId')]
            evidence_parts.append(f"EIPs no asociadas: {len(unassociated)}")
            if unassociated:
                issues.append(f'{len(unassociated)} EIP(s) no asociadas')
            
            evidence = ' | '.join(evidence_parts)
            if not issues:
                findings.append({'bp': 'COST04-BP03', 'description': COST_BP_DESCRIPTIONS.get('COST04-BP03', ''),
                    'status': 'COMPLIANT', 'severity': 'LOW',
                    'finding': 'Sin recursos no utilizados detectados.',
                    'evidence': evidence,
                    'remediation': 'Estado actual cumple. Revisar periódicamente con Trusted Advisor.',
                    'risk': 'Bajo riesgo.'})
            else:
                findings.append({'bp': 'COST04-BP03', 'description': COST_BP_DESCRIPTIONS.get('COST04-BP03', ''),
                    'status': 'NON_COMPLIANT', 'severity': 'MEDIUM',
                    'finding': f'Recursos no utilizados detectados: {"; ".join(issues)}.',
                    'evidence': evidence,
                    'remediation': ('Desmantelar recursos no utilizados: '
                        '1) Terminar instancias EC2 detenidas por más de 30 días. '
                        '2) Eliminar volúmenes EBS no adjuntos (crear snapshot primero si necesario). '
                        '3) Liberar EIPs no asociadas. '
                        '4) Revisar Trusted Advisor para más recomendaciones de recursos inactivos.'),
                    'risk': f'Costo innecesario por recursos no utilizados.'})
        except ClientError as e:
            findings.append(self._handle_error('COST04-BP03', e))
        
        # COST04-BP04: Desmantelar recursos automáticamente
        try:
            lambda_client = self.session.client('lambda')
            functions = lambda_client.list_functions(MaxItems=50)
            cleanup_functions = [f for f in functions.get('Functions', []) if any(
                kw in f['FunctionName'].lower() for kw in ['cleanup', 'decommission', 'terminate', 'delete', 'expire'])]
            
            evidence = f"Lambda de limpieza: {len(cleanup_functions)}"
            if cleanup_functions:
                findings.append({'bp': 'COST04-BP04', 'description': COST_BP_DESCRIPTIONS.get('COST04-BP04', ''),
                    'status': 'COMPLIANT', 'severity': 'LOW',
                    'finding': f'Automatización de limpieza detectada ({len(cleanup_functions)} función(es)).',
                    'evidence': evidence,
                    'remediation': 'Estado actual cumple. Verificar que las funciones se ejecutan periódicamente.',
                    'risk': 'Bajo riesgo.'})
            else:
                findings.append({'bp': 'COST04-BP04', 'description': COST_BP_DESCRIPTIONS.get('COST04-BP04', ''),
                    'status': 'NON_COMPLIANT', 'severity': 'MEDIUM',
                    'finding': 'Sin automatización de limpieza de recursos.',
                    'evidence': evidence,
                    'remediation': ('Automatizar desmantelamiento: '
                        '1) Crear Lambda para apagar recursos con poco uso automáticamente. '
                        '2) Implementar tags de expiración y Lambda que elimine recursos expirados. '
                        '3) Usar EventBridge para programar limpieza periódica. '
                        '4) Configurar AWS Instance Scheduler para apagar/encender por horario.'),
                    'risk': 'Sin automatización, los recursos no utilizados se acumulan.'})
        except ClientError as e:
            findings.append(self._handle_error('COST04-BP04', e))
        
        # COST04-BP05: Aplicar políticas de retención de datos
        try:
            s3 = self.session.client('s3')
            buckets = s3.list_buckets().get('Buckets', [])
            with_lifecycle = 0
            for bucket in buckets[:20]:
                try:
                    s3.get_bucket_lifecycle_configuration(Bucket=bucket['Name'])
                    with_lifecycle += 1
                except ClientError:
                    pass
            
            pct = (with_lifecycle / min(len(buckets), 20) * 100) if buckets else 0
            evidence = f"S3 buckets con lifecycle: {with_lifecycle}/{min(len(buckets), 20)} ({pct:.0f}%)"
            
            if pct >= 50:
                findings.append({'bp': 'COST04-BP05', 'description': COST_BP_DESCRIPTIONS.get('COST04-BP05', ''),
                    'status': 'COMPLIANT', 'severity': 'LOW',
                    'finding': f'Políticas de retención implementadas ({pct:.0f}% de buckets con lifecycle).',
                    'evidence': evidence,
                    'remediation': 'Estado actual cumple. Expandir lifecycle policies a todos los buckets.',
                    'risk': 'Bajo riesgo.'})
            else:
                findings.append({'bp': 'COST04-BP05', 'description': COST_BP_DESCRIPTIONS.get('COST04-BP05', ''),
                    'status': 'NON_COMPLIANT', 'severity': 'MEDIUM',
                    'finding': f'Políticas de retención insuficientes ({pct:.0f}% de buckets con lifecycle).',
                    'evidence': evidence,
                    'remediation': ('Implementar políticas de retención: '
                        '1) Configurar S3 Lifecycle policies en todos los buckets. '
                        '2) Definir transiciones a Glacier/Deep Archive para datos antiguos. '
                        '3) Configurar expiración automática según requisitos de retención. '
                        '4) Implementar S3 Intelligent-Tiering para optimización automática.'),
                    'risk': 'Costos de almacenamiento innecesarios por datos no gestionados.'})
        except ClientError as e:
            findings.append(self._handle_error('COST04-BP05', e))
        
        return self._create_question('COST04', findings,
            'How do you decommission resources?', 'Desmantelamiento de recursos')
    
    # ========================================================================
    # COST05: Evaluación de costos al seleccionar servicios (6 BPs)
    # ========================================================================
    def _evaluate_cost05(self) -> Dict[str, Any]:
        findings = []
        
        # COST05-BP01 a BP03: Requieren revisión de procesos organizacionales
        findings.append(self._pending('COST05-BP01',
            'Identificar requisitos de costo: 1) Verificar que se discutió el trade-off entre costo, rendimiento y fiabilidad. '
            '2) Documentar requisitos de costo por carga de trabajo. '
            '3) Definir presupuesto máximo por componente.'))
        
        findings.append(self._pending('COST05-BP02',
            'Analizar componentes del workload: 1) Evaluar costos actuales y previstos de cada componente. '
            '2) Identificar componentes con mayor costo. '
            '3) Evaluar alternativas de menor costo para cada componente.'))
        
        findings.append(self._pending('COST05-BP03',
            'Análisis detallado por componente: 1) Considerar costo de operaciones y administración. '
            '2) Verificar que el tiempo de análisis fue proporcional al costo del componente. '
            '3) Incluir costos de transferencia de datos en el análisis.'))
        
        # COST05-BP04: Seleccionar software con licenciamiento eficiente
        findings.append(self._pending('COST05-BP04',
            'Evaluar licenciamiento: 1) Preferir software de código abierto para evitar costos de licencia. '
            '2) Evitar licencias vinculadas a CPUs o cores. '
            '3) Evaluar BYOL vs licencias incluidas en AWS. '
            '4) Considerar AWS Marketplace para licencias optimizadas.'))
        
        # COST05-BP05: Seleccionar componentes para optimizar costo
        try:
            # Verificar uso de servicios serverless/managed
            lambda_client = self.session.client('lambda')
            functions = lambda_client.list_functions(MaxItems=10).get('Functions', [])
            
            ddb = self.session.client('dynamodb')
            tables = ddb.list_tables().get('TableNames', [])
            
            evidence = f"Lambda functions: {len(functions)} | DynamoDB tables: {len(tables)}"
            if functions or tables:
                findings.append({'bp': 'COST05-BP05', 'description': COST_BP_DESCRIPTIONS.get('COST05-BP05', ''),
                    'status': 'COMPLIANT', 'severity': 'LOW',
                    'finding': 'Uso de servicios administrados/serverless detectado.',
                    'evidence': evidence,
                    'remediation': 'Estado actual cumple. Continuar priorizando servicios serverless y administrados para minimizar costos operacionales.',
                    'risk': 'Bajo riesgo.'})
            else:
                findings.append({'bp': 'COST05-BP05', 'description': COST_BP_DESCRIPTIONS.get('COST05-BP05', ''),
                    'status': 'PENDING_REVIEW', 'severity': 'MEDIUM',
                    'finding': 'Bajo uso de servicios serverless/administrados.',
                    'evidence': evidence,
                    'remediation': ('Optimizar selección de componentes: '
                        '1) Evaluar migración a Lambda para cargas de trabajo event-driven. '
                        '2) Usar DynamoDB en lugar de RDS para cargas NoSQL. '
                        '3) Considerar Fargate en lugar de EC2 para contenedores. '
                        '4) Usar S3 en lugar de EBS para almacenamiento de objetos.'),
                    'risk': 'Por Determinar.'})
        except ClientError as e:
            findings.append(self._handle_error('COST05-BP05', e))
        
        # COST05-BP06: Análisis de costo para diferentes niveles de uso
        findings.append(self._pending('COST05-BP06',
            'Análisis de costo por uso: 1) Analizar uso previsto a lo largo de la vida útil del componente. '
            '2) Evaluar qué niveles de uso son más rentables (on-demand vs reserved vs spot). '
            '3) Modelar costos para diferentes escenarios de crecimiento.'))
        
        return self._create_question('COST05', findings,
            'How do you evaluate cost when you select services?', 'Evaluación de costos al seleccionar servicios')

    # ========================================================================
    # COST06: Selección de tipo, tamaño y número de recursos (4 BPs)
    # ========================================================================
    def _evaluate_cost06(self) -> Dict[str, Any]:
        findings = []
        
        findings.append(self._pending('COST06-BP01',
            'Modelado de costos: 1) Realizar benchmarks bajo diferentes cargas previstas. '
            '2) Comparar costos generales entre opciones de recursos. '
            '3) Usar AWS Pricing Calculator para estimaciones.'))
        
        # COST06-BP02: Seleccionar tipo y tamaño basado en datos
        try:
            # Verificar Compute Optimizer
            co = self.session.client('compute-optimizer')
            status = co.get_enrollment_status()
            enrolled = status.get('status') == 'Active'
            
            evidence = f"Compute Optimizer: {'Activo' if enrolled else 'No activo'}"
            if enrolled:
                findings.append({'bp': 'COST06-BP02', 'description': COST_BP_DESCRIPTIONS.get('COST06-BP02', ''),
                    'status': 'COMPLIANT', 'severity': 'LOW',
                    'finding': 'Compute Optimizer activo para recomendaciones de right-sizing.',
                    'evidence': evidence,
                    'remediation': 'Estado actual cumple. Revisar recomendaciones de Compute Optimizer periódicamente.',
                    'risk': 'Bajo riesgo.'})
            else:
                findings.append({'bp': 'COST06-BP02', 'description': COST_BP_DESCRIPTIONS.get('COST06-BP02', ''),
                    'status': 'NON_COMPLIANT', 'severity': 'MEDIUM',
                    'finding': 'Compute Optimizer no activo. Sin recomendaciones de right-sizing.',
                    'evidence': evidence,
                    'remediation': ('Seleccionar recursos basado en datos: '
                        '1) Habilitar AWS Compute Optimizer para recomendaciones de right-sizing. '
                        '2) Revisar métricas de uso (CPU, memoria) en CloudWatch. '
                        '3) Usar datos históricos para seleccionar tipo/tamaño correcto. '
                        '4) Implementar revisiones trimestrales de right-sizing.'),
                    'risk': 'Sin datos, los recursos pueden estar sobre/sub-dimensionados.'})
        except ClientError as e:
            findings.append(self._handle_error('COST06-BP02', e))
        
        # COST06-BP03: Seleccionar tipo automáticamente basado en métricas
        try:
            asg = self.session.client('autoscaling')
            groups = asg.describe_auto_scaling_groups().get('AutoScalingGroups', [])
            
            evidence = f"Auto Scaling Groups: {len(groups)}"
            if groups:
                findings.append({'bp': 'COST06-BP03', 'description': COST_BP_DESCRIPTIONS.get('COST06-BP03', ''),
                    'status': 'COMPLIANT', 'severity': 'LOW',
                    'finding': f'Auto Scaling configurado ({len(groups)} grupo(s)).',
                    'evidence': evidence,
                    'remediation': 'Estado actual cumple. Verificar que las políticas de escalado están optimizadas.',
                    'risk': 'Bajo riesgo.'})
            else:
                findings.append({'bp': 'COST06-BP03', 'description': COST_BP_DESCRIPTIONS.get('COST06-BP03', ''),
                    'status': 'NON_COMPLIANT', 'severity': 'MEDIUM',
                    'finding': 'Sin Auto Scaling configurado.',
                    'evidence': evidence,
                    'remediation': ('Implementar escalado automático: '
                        '1) Configurar Auto Scaling Groups con políticas basadas en métricas. '
                        '2) Usar target tracking scaling para CPU/memoria. '
                        '3) Implementar scheduled scaling para patrones predecibles. '
                        '4) Considerar predictive scaling para cargas variables.'),
                    'risk': 'Sin escalado automático, los recursos son estáticos y pueden estar sobre-dimensionados.'})
        except ClientError as e:
            findings.append(self._handle_error('COST06-BP03', e))
        
        # COST06-BP04: Considerar recursos compartidos
        try:
            elb = self.session.client('elbv2')
            lbs = elb.describe_load_balancers().get('LoadBalancers', [])
            
            # Transit Gateway
            ec2 = self.session.client('ec2')
            tgws = ec2.describe_transit_gateways().get('TransitGateways', [])
            
            evidence = f"Load Balancers: {len(lbs)} | Transit Gateways: {len(tgws)}"
            if lbs or tgws:
                findings.append({'bp': 'COST06-BP04', 'description': COST_BP_DESCRIPTIONS.get('COST06-BP04', ''),
                    'status': 'COMPLIANT', 'severity': 'LOW',
                    'finding': 'Recursos compartidos en uso.',
                    'evidence': evidence,
                    'remediation': 'Estado actual cumple. Evaluar más oportunidades de compartir recursos entre workloads.',
                    'risk': 'Bajo riesgo.'})
            else:
                findings.append({'bp': 'COST06-BP04', 'description': COST_BP_DESCRIPTIONS.get('COST06-BP04', ''),
                    'status': 'PENDING_REVIEW', 'severity': 'LOW',
                    'finding': 'Sin recursos compartidos detectados.',
                    'evidence': evidence,
                    'remediation': ('Considerar recursos compartidos: '
                        '1) Centralizar supervisión y monitoreo para múltiples workloads. '
                        '2) Compartir VPCs y Transit Gateways entre cuentas. '
                        '3) Usar ALB compartidos con path-based routing. '
                        '4) Centralizar backups y logging.'),
                    'risk': 'Por Determinar.'})
        except ClientError as e:
            findings.append(self._handle_error('COST06-BP04', e))
        
        return self._create_question('COST06', findings,
            'How do you meet cost targets when you select resource type, size and number?',
            'Selección de tipo, tamaño y número de recursos')
    
    # ========================================================================
    # COST07: Uso de modelos de precios (5 BPs)
    # ========================================================================
    def _evaluate_cost07(self) -> Dict[str, Any]:
        findings = []
        
        findings.append(self._pending('COST07-BP01',
            'Análisis de modelos de precios: 1) Determinar si los recursos se ejecutan por periodos extensos o cortos. '
            '2) Aplicar reglas empresariales de descuento según duración. '
            '3) Evaluar Savings Plans vs Reserved Instances vs On-Demand.'))
        
        findings.append(self._pending('COST07-BP02',
            'Selección de regiones por costo: 1) Identificar diferencias regionales de precios. '
            '2) Implementar en regiones costosas solo si hay requisitos de latencia o residencia de datos. '
            '3) Usar AWS Pricing API para comparar costos entre regiones.'))
        
        findings.append(self._pending('COST07-BP03',
            'Acuerdos con terceros: 1) Revisar que los acuerdos se escalen con el uso. '
            '2) Verificar que los precios son acordes a los beneficios. '
            '3) Evaluar alternativas de AWS Marketplace.'))
        
        # COST07-BP04: Implementar modelos de precios para todos los componentes
        try:
            ec2 = self.session.client('ec2')
            # Verificar Reserved Instances
            ris = ec2.describe_reserved_instances(Filters=[{'Name': 'state', 'Values': ['active']}])
            active_ris = len(ris.get('ReservedInstances', []))
            
            # Verificar Savings Plans
            try:
                sp = self.session.client('savingsplans')
                plans = sp.describe_savings_plans(states=['active'])
                active_sps = len(plans.get('savingsPlans', []))
            except:
                active_sps = 0
            
            evidence = f"Reserved Instances activas: {active_ris} | Savings Plans activos: {active_sps}"
            if active_ris > 0 or active_sps > 0:
                findings.append({'bp': 'COST07-BP04', 'description': COST_BP_DESCRIPTIONS.get('COST07-BP04', ''),
                    'status': 'COMPLIANT', 'severity': 'LOW',
                    'finding': f'Modelos de precios con descuento en uso ({active_ris} RIs, {active_sps} Savings Plans).',
                    'evidence': evidence,
                    'remediation': 'Estado actual cumple. Revisar cobertura de Savings Plans y evaluar oportunidades adicionales.',
                    'risk': 'Bajo riesgo.'})
            else:
                findings.append({'bp': 'COST07-BP04', 'description': COST_BP_DESCRIPTIONS.get('COST07-BP04', ''),
                    'status': 'NON_COMPLIANT', 'severity': 'HIGH',
                    'finding': 'Sin Reserved Instances ni Savings Plans. Todos los recursos en pricing on-demand.',
                    'evidence': evidence,
                    'remediation': ('Implementar modelos de precios con descuento: '
                        '1) Evaluar Compute Savings Plans para descuentos de hasta 72%. '
                        '2) Considerar EC2 Instance Savings Plans para cargas estables. '
                        '3) Usar Spot Instances para cargas tolerantes a interrupciones. '
                        '4) Revisar recomendaciones de Cost Explorer para RIs/Savings Plans. '
                        '5) Implementar mix: 25-75% Savings Plans, resto On-Demand/Spot.'),
                    'risk': 'Costos significativamente más altos sin descuentos por compromiso.'})
        except ClientError as e:
            findings.append(self._handle_error('COST07-BP04', e))
        
        findings.append(self._pending('COST07-BP05',
            'Análisis a nivel de cuenta de gestión: 1) Consultar facturación consolidada para aplicar reservas. '
            '2) Compartir Savings Plans entre cuentas de la organización. '
            '3) Optimizar descuentos a nivel organizacional.'))
        
        return self._create_question('COST07', findings,
            'How do you use pricing models to reduce cost?', 'Uso de modelos de precios')

    # ========================================================================
    # COST08: Planificación de cargos por transferencia de datos (3 BPs)
    # ========================================================================
    def _evaluate_cost08(self) -> Dict[str, Any]:
        findings = []
        
        findings.append(self._pending('COST08-BP01',
            'Modelado de transferencia de datos: 1) Identificar el punto de costo más bajo para transferencias. '
            '2) Modelar transferencias de cada componente. '
            '3) Considerar costos de transferencia inter-región e inter-AZ.'))
        
        findings.append(self._pending('COST08-BP02',
            'Seleccionar componentes para optimizar transferencia: 1) Diseñar arquitectura para reducir transferencia cross-AZ. '
            '2) Usar VPC endpoints para tráfico a servicios AWS. '
            '3) Considerar colocación de recursos en la misma AZ cuando sea posible.'))
        
        # COST08-BP03: Implementar servicios para reducir costos de transferencia
        try:
            cf = self.session.client('cloudfront')
            distributions = cf.list_distributions()
            dist_count = len(distributions.get('DistributionList', {}).get('Items', []))
            
            ec2 = self.session.client('ec2')
            endpoints = ec2.describe_vpc_endpoints().get('VpcEndpoints', [])
            
            evidence = f"CloudFront distributions: {dist_count} | VPC endpoints: {len(endpoints)}"
            if dist_count > 0 or len(endpoints) > 0:
                findings.append({'bp': 'COST08-BP03', 'description': COST_BP_DESCRIPTIONS.get('COST08-BP03', ''),
                    'status': 'COMPLIANT', 'severity': 'LOW',
                    'finding': f'Servicios de optimización de transferencia en uso (CloudFront: {dist_count}, VPC endpoints: {len(endpoints)}).',
                    'evidence': evidence,
                    'remediation': 'Estado actual cumple. Evaluar más VPC endpoints para reducir costos de NAT Gateway.',
                    'risk': 'Bajo riesgo.'})
            else:
                findings.append({'bp': 'COST08-BP03', 'description': COST_BP_DESCRIPTIONS.get('COST08-BP03', ''),
                    'status': 'NON_COMPLIANT', 'severity': 'MEDIUM',
                    'finding': 'Sin servicios de optimización de transferencia de datos.',
                    'evidence': evidence,
                    'remediation': ('Implementar servicios para reducir transferencia: '
                        '1) Configurar CloudFront CDN para contenido estático y dinámico. '
                        '2) Crear VPC endpoints para S3, DynamoDB y otros servicios frecuentes. '
                        '3) Considerar Direct Connect para transferencias on-premises de alto volumen. '
                        '4) Usar S3 Transfer Acceleration para uploads globales.'),
                    'risk': 'Costos de transferencia de datos pueden ser significativos sin optimización.'})
        except ClientError as e:
            findings.append(self._handle_error('COST08-BP03', e))
        
        return self._create_question('COST08', findings,
            'How do you plan for data transfer charges?', 'Planificación de cargos por transferencia de datos')
    
    # ========================================================================
    # COST09: Gestión de demanda y suministro de recursos (3 BPs)
    # ========================================================================
    def _evaluate_cost09(self) -> Dict[str, Any]:
        findings = []
        
        findings.append(self._pending('COST09-BP01',
            'Análisis de demanda del workload: 1) Analizar si la demanda cubre tendencias estacionales. '
            '2) Identificar patrones de uso (picos, valles, estacionalidad). '
            '3) Usar CloudWatch métricas históricas para proyectar demanda.'))
        
        # COST09-BP02: Implementar buffer o throttle para gestionar demanda
        try:
            sqs = self.session.client('sqs')
            queues = sqs.list_queues()
            num_queues = len(queues.get('QueueUrls', []))
            
            evidence = f"SQS queues: {num_queues}"
            if num_queues > 0:
                findings.append({'bp': 'COST09-BP02', 'description': COST_BP_DESCRIPTIONS.get('COST09-BP02', ''),
                    'status': 'COMPLIANT', 'severity': 'LOW',
                    'finding': f'Mecanismos de buffering detectados ({num_queues} cola(s) SQS).',
                    'evidence': evidence,
                    'remediation': 'Estado actual cumple. Verificar que el throttling garantiza respuesta en tiempo requerido.',
                    'risk': 'Bajo riesgo.'})
            else:
                findings.append({'bp': 'COST09-BP02', 'description': COST_BP_DESCRIPTIONS.get('COST09-BP02', ''),
                    'status': 'NON_COMPLIANT', 'severity': 'MEDIUM',
                    'finding': 'Sin mecanismos de buffering para suavizar picos de demanda.',
                    'evidence': evidence,
                    'remediation': ('Implementar buffering/throttling: '
                        '1) Usar SQS para desacoplar y suavizar picos de carga. '
                        '2) Implementar API Gateway throttling para limitar requests. '
                        '3) Usar Kinesis para streaming de datos con buffering. '
                        '4) Configurar Lambda reserved concurrency para control de costos.'),
                    'risk': 'Sin buffering, los picos de demanda causan sobre-aprovisionamiento costoso.'})
        except ClientError as e:
            findings.append(self._handle_error('COST09-BP02', e))
        
        # COST09-BP03: Suministrar recursos dinámicamente
        try:
            asg = self.session.client('autoscaling')
            groups = asg.describe_auto_scaling_groups().get('AutoScalingGroups', [])
            
            # Verificar Lambda (serverless = suministro dinámico automático)
            lambda_client = self.session.client('lambda')
            functions = lambda_client.list_functions(MaxItems=10).get('Functions', [])
            
            evidence = f"Auto Scaling Groups: {len(groups)} | Lambda functions: {len(functions)}"
            if groups or functions:
                findings.append({'bp': 'COST09-BP03', 'description': COST_BP_DESCRIPTIONS.get('COST09-BP03', ''),
                    'status': 'COMPLIANT', 'severity': 'LOW',
                    'finding': f'Suministro dinámico de recursos ({len(groups)} ASGs, {len(functions)} Lambda).',
                    'evidence': evidence,
                    'remediation': 'Estado actual cumple. Verificar que el escalado responde a la demanda real.',
                    'risk': 'Bajo riesgo.'})
            else:
                findings.append({'bp': 'COST09-BP03', 'description': COST_BP_DESCRIPTIONS.get('COST09-BP03', ''),
                    'status': 'NON_COMPLIANT', 'severity': 'HIGH',
                    'finding': 'Sin suministro dinámico de recursos. Aprovisionamiento estático.',
                    'evidence': evidence,
                    'remediation': ('Implementar suministro dinámico: '
                        '1) Configurar Auto Scaling para EC2 basado en demanda. '
                        '2) Usar Lambda para cargas event-driven (escalado automático). '
                        '3) Implementar Fargate para contenedores con escalado automático. '
                        '4) Usar DynamoDB on-demand para escalado automático de base de datos.'),
                    'risk': 'Aprovisionamiento estático causa sobre-costos en periodos de baja demanda.'})
        except ClientError as e:
            findings.append(self._handle_error('COST09-BP03', e))
        
        return self._create_question('COST09', findings,
            'How do you manage demand, and supply resources?', 'Gestión de demanda y suministro de recursos')
    
    # ========================================================================
    # COST10: Evaluación de nuevos servicios (2 BPs)
    # ========================================================================
    def _evaluate_cost10(self) -> Dict[str, Any]:
        findings = []
        
        findings.append(self._pending('COST10-BP01',
            'Proceso de revisión de workloads: 1) Definir criterios de revisión periódica. '
            '2) Revisar cargas >10% de la factura trimestral/semestralmente. '
            '3) Revisar el resto anualmente. '
            '4) Documentar hallazgos y acciones de cada revisión.'))
        
        findings.append(self._pending('COST10-BP02',
            'Revisión y análisis regular: 1) Comprobar si es posible adoptar nuevos servicios más económicos. '
            '2) Evaluar reemplazo de componentes por servicios administrados. '
            '3) Revisar AWS What\'s New para servicios que reduzcan costos. '
            '4) Programar revisiones de arquitectura anuales.'))
        
        return self._create_question('COST10', findings,
            'How do you evaluate new services?', 'Evaluación de nuevos servicios')
    
    # ========================================================================
    # COST11: Evaluación del costo del esfuerzo (1 BP)
    # ========================================================================
    def _evaluate_cost11(self) -> Dict[str, Any]:
        findings = []
        
        try:
            evidence_parts = []
            automation_score = 0
            
            # CloudFormation (IaC)
            try:
                cf = self.session.client('cloudformation')
                stacks = cf.list_stacks(StackStatusFilter=['CREATE_COMPLETE', 'UPDATE_COMPLETE']).get('StackSummaries', [])
                evidence_parts.append(f"CloudFormation stacks: {len(stacks)}")
                if stacks: automation_score += 1
            except: evidence_parts.append("CloudFormation: No accesible")
            
            # Lambda (serverless automation)
            try:
                lambda_client = self.session.client('lambda')
                functions = lambda_client.list_functions(MaxItems=20).get('Functions', [])
                evidence_parts.append(f"Lambda functions: {len(functions)}")
                if functions: automation_score += 1
            except: evidence_parts.append("Lambda: No accesible")
            
            # SSM Automation
            try:
                ssm = self.session.client('ssm')
                docs = ssm.list_documents(Filters=[{'Key': 'DocumentType', 'Values': ['Automation']}], MaxResults=20)
                auto_docs = len(docs.get('DocumentIdentifiers', []))
                evidence_parts.append(f"SSM Automation docs: {auto_docs}")
                if auto_docs: automation_score += 1
            except: evidence_parts.append("SSM: No accesible")
            
            # EventBridge (event-driven automation)
            try:
                eb = self.session.client('events')
                rules = eb.list_rules().get('Rules', [])
                evidence_parts.append(f"EventBridge rules: {len(rules)}")
                if rules: automation_score += 1
            except: evidence_parts.append("EventBridge: No accesible")
            
            evidence = ' | '.join(evidence_parts)
            
            if automation_score >= 3:
                findings.append({'bp': 'COST11-BP01', 'description': COST_BP_DESCRIPTIONS.get('COST11-BP01', ''),
                    'status': 'COMPLIANT', 'severity': 'LOW',
                    'finding': f'Alto nivel de automatización ({automation_score}/4 categorías). Reduce costo operacional.',
                    'evidence': evidence,
                    'remediation': 'Estado actual cumple. Cuantificar ahorro de tiempo y costo vs operaciones manuales.',
                    'risk': 'Bajo riesgo.'})
            elif automation_score >= 1:
                findings.append({'bp': 'COST11-BP01', 'description': COST_BP_DESCRIPTIONS.get('COST11-BP01', ''),
                    'status': 'PENDING_REVIEW', 'severity': 'MEDIUM',
                    'finding': f'Automatización parcial ({automation_score}/4 categorías).',
                    'evidence': evidence,
                    'remediation': ('Expandir automatización: '
                        '1) Implementar IaC con CloudFormation/CDK para toda la infraestructura. '
                        '2) Usar Lambda para automatización de tareas operacionales. '
                        '3) Configurar SSM Automation para tareas de mantenimiento. '
                        '4) Usar EventBridge para respuesta automática a eventos. '
                        '5) Cuantificar ahorro de automatización vs operación manual.'),
                    'risk': 'Por Determinar.'})
            else:
                findings.append({'bp': 'COST11-BP01', 'description': COST_BP_DESCRIPTIONS.get('COST11-BP01', ''),
                    'status': 'NON_COMPLIANT', 'severity': 'HIGH',
                    'finding': 'Bajo nivel de automatización. Alto costo operacional.',
                    'evidence': evidence,
                    'remediation': ('Implementar automatización para reducir costos operacionales: '
                        '1) Adoptar IaC con CloudFormation/CDK/Terraform. '
                        '2) Automatizar tareas repetitivas con Lambda y Step Functions. '
                        '3) Implementar CI/CD con CodePipeline. '
                        '4) Usar SSM para gestión automatizada de instancias. '
                        '5) Calcular ROI de automatización vs operación manual.'),
                    'risk': 'Alto costo operacional por tareas manuales repetitivas.'})
        except ClientError as e:
            findings.append(self._handle_error('COST11-BP01', e))
        
        return self._create_question('COST11', findings,
            'How do you evaluate the cost of effort?', 'Evaluación del costo del esfuerzo')

    # ========================================================================
    # Helper methods
    # ========================================================================
    def _create_question(self, question_id, findings, title_en, title_es):
        score = self._calculate_question_score(findings)
        status = 'NON_COMPLIANT' if any(f['status'] == 'NON_COMPLIANT' for f in findings) else \
                 'COMPLIANT' if all(f['status'] == 'COMPLIANT' for f in findings) else 'PENDING_REVIEW'
        return {
            'question_id': question_id,
            'title': {'es': title_es, 'en': title_en},
            'description': {'es': title_es, 'en': title_en},
            'score': score, 'bps_evaluated': len(findings),
            'status': status, 'findings': findings
        }
    
    def _calculate_question_score(self, findings):
        if not findings: return 0.0
        score_map = {'COMPLIANT': 100.0, 'NON_COMPLIANT': 0.0, 'PENDING_REVIEW': 50.0, 'PARTIAL_COMPLIANT': 50.0}
        return round(sum(score_map.get(f['status'], 0.0) for f in findings) / len(findings), 2)
    
    def _calculate_pillar_score(self, questions):
        if not questions: return 0.0
        total_weighted = sum(q['score'] * q['bps_evaluated'] for q in questions)
        total_bps = sum(q['bps_evaluated'] for q in questions)
        return round(total_weighted / total_bps, 2) if total_bps > 0 else 0.0
    
    def _calculate_distributions(self, questions):
        compliance = {'compliant': 0, 'non_compliant': 0, 'pending_review': 0}
        severity = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        for q in questions:
            for f in q['findings']:
                s = f['status'].lower()
                if s == 'compliant': compliance['compliant'] += 1
                elif s == 'non_compliant': compliance['non_compliant'] += 1
                else: compliance['pending_review'] += 1
                sev = f['severity'].lower()
                if sev in severity: severity[sev] += 1
        return compliance, severity
