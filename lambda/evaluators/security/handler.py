"""
Security Pillar Evaluator Lambda
Evaluates 11 Security questions with 63 Best Practices
"""

import json
import boto3
import os
from datetime import datetime
from typing import Dict, List, Any
from botocore.exceptions import ClientError
import importlib.util

# Import from common layer
import sys
import os
sys.path.append('/opt/python')
from autowar_common.credentials_manager import CredentialsManager

# Load bp_descriptions dynamically to avoid import conflicts
bp_desc_path = os.path.join(os.path.dirname(__file__), 'bp_descriptions.py')
spec = importlib.util.spec_from_file_location("security_bp_descriptions", bp_desc_path)
bp_desc_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bp_desc_module)
SECURITY_BP_DESCRIPTIONS = bp_desc_module.SECURITY_BP_DESCRIPTIONS

# Import all BP evaluations
from all_bp_evaluations import *


def aggregate_multi_region_results(results: List[Dict]) -> Dict:
    """Aggregates results from multiple regions into a single pillar result"""
    if not results:
        return {}
    
    # Start with first result as base
    aggregated = results[0].copy()
    aggregated['regions'] = [r.get('region', 'unknown') for r in results]
    aggregated['multi_region'] = True
    
    # Aggregate questions - merge findings from all regions
    all_questions = {}
    
    for result in results:
        region = result.get('region', 'unknown')
        for question in result.get('questions', []):
            q_id = question['question_id']
            if q_id not in all_questions:
                all_questions[q_id] = {
                    'question_id': q_id,
                    'title': question['title'],
                    'description': question['description'],
                    'findings_by_region': {},
                    'all_findings': []
                }
            
            # Store findings by region
            all_questions[q_id]['findings_by_region'][region] = question['findings']
            
            # Add region info to each finding
            for finding in question['findings']:
                finding_with_region = finding.copy()
                finding_with_region['region'] = region
                all_questions[q_id]['all_findings'].append(finding_with_region)
    
    # Calculate aggregated scores
    aggregated_questions = []
    for q_id, q_data in all_questions.items():
        all_findings = q_data['all_findings']
        
        score_map = {'COMPLIANT': 100.0, 'NON_COMPLIANT': 0.0, 'PENDING_REVIEW': 50.0}
        total_score = sum(score_map.get(f['status'], 0.0) for f in all_findings)
        avg_score = round(total_score / len(all_findings), 2) if all_findings else 0.0
        
        statuses = [f['status'] for f in all_findings]
        if any(s == 'NON_COMPLIANT' for s in statuses):
            overall_status = 'NON_COMPLIANT'
        elif all(s == 'COMPLIANT' for s in statuses):
            overall_status = 'COMPLIANT'
        else:
            overall_status = 'PENDING_REVIEW'
        
        aggregated_questions.append({
            'question_id': q_id,
            'title': q_data['title'],
            'description': q_data['description'],
            'score': avg_score,
            'bps_evaluated': len(all_findings),
            'status': overall_status,
            'findings': all_findings,
            'findings_by_region': q_data['findings_by_region']
        })
    
    aggregated['questions'] = aggregated_questions
    aggregated['total_findings'] = sum(len(q['findings']) for q in aggregated_questions)
    aggregated['total_best_practices'] = sum(q['bps_evaluated'] for q in aggregated_questions)
    
    total_weighted_score = sum(q['score'] * q['bps_evaluated'] for q in aggregated_questions)
    total_bps = sum(q['bps_evaluated'] for q in aggregated_questions)
    aggregated['overall_score'] = round(total_weighted_score / total_bps, 2) if total_bps > 0 else 0.0
    
    compliance_dist = {'compliant': 0, 'non_compliant': 0, 'pending_review': 0}
    severity_dist = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
    
    for question in aggregated_questions:
        for finding in question['findings']:
            status = finding['status'].lower()
            if status == 'compliant':
                compliance_dist['compliant'] += 1
            elif status == 'non_compliant':
                compliance_dist['non_compliant'] += 1
            else:
                compliance_dist['pending_review'] += 1
            
            severity = finding['severity'].lower()
            if severity in severity_dist:
                severity_dist[severity] += 1
    
    aggregated['compliance_distribution'] = compliance_dist
    aggregated['severity_distribution'] = severity_dist
    
    return aggregated


def lambda_handler(event, context):
    """
    Main handler for Security pillar evaluation
    """
    # CORS headers for all responses
    cors_headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,X-Session-ID',
        'Access-Control-Allow-Methods': 'POST,OPTIONS'
    }
    
    try:
        # Extract session_id from headers (case-insensitive)
        headers = event.get('headers', {})
        session_id = headers.get('X-Session-ID') or headers.get('x-session-id')
        
        if not session_id:
            return {
                'statusCode': 401,
                'headers': cors_headers,
                'body': json.dumps({'error': 'Missing X-Session-ID header'})
            }
        
        # Check for recent cached evaluation in DynamoDB (last 5 minutes)
        dynamodb = boto3.resource('dynamodb')
        table_name = os.environ.get('DYNAMODB_TABLE')
        if table_name:
            table = dynamodb.Table(table_name)
            import time
            from boto3.dynamodb.conditions import Key
            
            # Query for recent security evaluations
            response = table.query(
                KeyConditionExpression=Key('session_id').eq(session_id) & Key('evaluation_id').begins_with('security#'),
                ScanIndexForward=False,  # Most recent first
                Limit=1
            )
            
            if response.get('Items'):
                latest_eval = response['Items'][0]
                eval_timestamp = int(latest_eval['evaluation_id'].split('#')[1])
                current_time = int(time.time())
                
                # If evaluation is less than 5 minutes old, return cached result
                if (current_time - eval_timestamp) < 300:  # 300 seconds = 5 minutes
                    print(f"Returning cached evaluation from {current_time - eval_timestamp} seconds ago")
                    return {
                        'statusCode': 200,
                        'headers': cors_headers,
                        'body': json.dumps(latest_eval['data'], default=str)
                    }
        
        # Get credentials from session
        creds_manager = CredentialsManager()
        credentials = creds_manager.get_session_credentials(session_id)
        
        if not credentials:
            return {
                'statusCode': 401,
                'headers': cors_headers,
                'body': json.dumps({'error': 'Session expired or invalid'})
            }
        
        # Get regions from credentials (support multi-region)
        regions = credentials.get('regions', [credentials.get('region', 'us-east-1')])
        
        # Evaluate Security pillar across all regions
        all_results = []
        
        if len(regions) > 1:
            # Multi-region: evaluate in parallel using threads
            from concurrent.futures import ThreadPoolExecutor, as_completed
            
            def evaluate_region(region):
                session = boto3.Session(
                    aws_access_key_id=credentials['access_key_id'],
                    aws_secret_access_key=credentials['secret_access_key'],
                    aws_session_token=credentials.get('session_token'),
                    region_name=region
                )
                evaluator = SecurityEvaluator(session, region)
                return evaluator.evaluate()
            
            with ThreadPoolExecutor(max_workers=min(len(regions), 4)) as executor:
                futures = {executor.submit(evaluate_region, r): r for r in regions}
                for future in as_completed(futures):
                    try:
                        result = future.result()
                        all_results.append(result)
                    except Exception as e:
                        print(f"Error evaluating region {futures[future]}: {str(e)}")
        else:
            # Single region: evaluate directly
            region = regions[0] if regions else 'us-east-1'
            session = boto3.Session(
                aws_access_key_id=credentials['access_key_id'],
                aws_secret_access_key=credentials['secret_access_key'],
                aws_session_token=credentials.get('session_token'),
                region_name=region
            )
            evaluator = SecurityEvaluator(session, region)
            all_results.append(evaluator.evaluate())
        
        # If single region, return as before
        if len(all_results) == 1:
            final_result = all_results[0]
        else:
            # If multiple regions, aggregate results
            final_result = aggregate_multi_region_results(all_results)
        
        # Save to DynamoDB (no TTL - keep historical data)
        if table_name:
            from decimal import Decimal
            
            # Convert floats to Decimal for DynamoDB
            def convert_floats(obj):
                if isinstance(obj, float):
                    return Decimal(str(obj))
                elif isinstance(obj, dict):
                    return {k: convert_floats(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_floats(item) for item in obj]
                return obj
            
            table.put_item(
                Item={
                    'session_id': session_id,
                    'evaluation_id': f'security#{int(time.time())}',
                    'pillar_id': 'security',
                    'timestamp': final_result['timestamp'],
                    'data': convert_floats(json.loads(json.dumps(final_result, default=str)))
                }
            )
        
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps(final_result, default=str)
        }
        
    except Exception as e:
        print(f"Error evaluating Security pillar: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'statusCode': 500,
            'headers': cors_headers,
            'body': json.dumps({'error': f'Evaluation failed: {str(e)}'})
        }


class SecurityEvaluator:
    """Evaluates Security pillar (11 questions, 63 BPs)"""
    
    def __init__(self, session: boto3.Session, region: str = None):
        self.session = session
        self.region = region or session.region_name
        
    def evaluate(self) -> Dict[str, Any]:
        """Evaluates all 11 Security questions"""
        questions = []
        
        # Evaluate all 11 questions
        questions.append(self._evaluate_sec01())
        questions.append(self._evaluate_sec02())
        questions.append(self._evaluate_sec03())
        questions.append(self._evaluate_sec04())
        questions.append(self._evaluate_sec05())
        questions.append(self._evaluate_sec06())
        questions.append(self._evaluate_sec07())
        questions.append(self._evaluate_sec08())
        questions.append(self._evaluate_sec09())
        questions.append(self._evaluate_sec10())
        questions.append(self._evaluate_sec11())
        
        # Calculate pillar score
        pillar_score = self._calculate_pillar_score(questions)
        
        # Calculate distributions
        compliance_dist, severity_dist = self._calculate_distributions(questions)
        
        return {
            'pillar_id': 'security',
            'region': self.region,
            'pillar_name': {
                'es': 'Seguridad',
                'en': 'Security'
            },
            'description': {
                'es': 'Protección de información, sistemas y activos',
                'en': 'Protection of information, systems, and assets'
            },
            'overall_score': pillar_score,
            'total_findings': sum(len(q['findings']) for q in questions),
            'total_best_practices': sum(q['bps_evaluated'] for q in questions),
            'timestamp': datetime.utcnow().isoformat(),
            'questions': questions,
            'compliance_distribution': compliance_dist,
            'severity_distribution': severity_dist
        }
    
    def _evaluate_sec01(self) -> Dict[str, Any]:
        """SEC01: How do you securely operate your workload? (8 BPs)"""
        findings = []
        
        # SEC01-BP01: Separate workloads using accounts
        findings.append(self._evaluate_sec01_bp01())
        
        # SEC01-BP02: Secure account root user
        findings.append(self._evaluate_sec01_bp02())
        
        # SEC01-BP03 to BP08: Real evaluations
        findings.append(evaluate_sec01_bp03(self.session, self._handle_permission_error))
        findings.append(evaluate_sec01_bp04(self.session, self._handle_permission_error))
        findings.append(evaluate_sec01_bp05(self.session, self._handle_permission_error))
        findings.append(evaluate_sec01_bp06(self.session, self._handle_permission_error))
        findings.append(evaluate_sec01_bp07(self.session, self._handle_permission_error))
        findings.append(evaluate_sec01_bp08(self.session, self._handle_permission_error))
        
        return self._create_question('SEC01', findings, 
                                    'How do you securely operate your workload?',
                                    'Secure operation of workloads')
    
    def _evaluate_sec01_bp01(self) -> Dict[str, Any]:
        """SEC01-BP01: Cargas de trabajo separadas mediante cuentas
        Evalúa: AWS Organizations structure, OUs, SCPs, account isolation, workload separation
        """
        try:
            client = self.session.client('organizations')

            # 1. Verificar estructura de Organizations
            try:
                org = client.describe_organization()['Organization']
                org_id = org.get('Id', 'N/A')
                feature_set = org.get('FeatureSet', 'NONE')
            except ClientError:
                return {
                    'bp': 'SEC01-BP01',
                    'description': SECURITY_BP_DESCRIPTIONS.get('SEC01-BP01', ''),
                    'status': 'NON_COMPLIANT',
                    'severity': 'HIGH',
                    'finding': 'No se detectó AWS Organizations configurado. La cuenta opera de forma aislada sin arquitectura multi-cuenta.',
                    'evidence': 'AWS Organizations no está habilitado en esta cuenta.',
                    'remediation': (
                        'Implementar arquitectura multi-cuenta con AWS Organizations: '
                        '1) Crear organización con feature set ALL. '
                        '2) Diseñar estructura de OUs (Producción, Desarrollo, Staging, Seguridad, Shared Services). '
                        '3) Crear cuentas separadas por carga de trabajo y entorno. '
                        '4) Aplicar SCPs para establecer barreras de permisos. '
                        '5) Configurar AWS Control Tower para gobernanza centralizada.'
                    ),
                    'risk': 'Sin aislamiento de cuentas, un incidente de seguridad en una carga de trabajo puede afectar a todas las demás. El radio de explosión es máximo.'
                }

            # 2. Listar cuentas
            accounts = client.list_accounts()['Accounts']
            num_accounts = len(accounts)
            active_accounts = [a for a in accounts if a['Status'] == 'ACTIVE']

            # 3. Verificar OUs (estructura organizacional)
            roots = client.list_roots()['Roots']
            root_id = roots[0]['Id'] if roots else None
            ous = []
            if root_id:
                try:
                    ous_response = client.list_organizational_units_for_parent(ParentId=root_id)
                    ous = ous_response.get('OrganizationalUnits', [])
                except ClientError:
                    pass

            # 4. Verificar SCPs
            scps = []
            try:
                scps_response = client.list_policies(Filter='SERVICE_CONTROL_POLICY')
                scps = scps_response.get('Policies', [])
            except ClientError:
                pass

            # 5. Construir evidencia detallada
            account_names = [f"{a['Name']} ({a['Id']})" for a in active_accounts[:10]]
            ou_names = [f"{ou['Name']} ({ou['Id']})" for ou in ous[:10]]
            scp_names = [p['Name'] for p in scps if p['Name'] != 'FullAWSAccess']

            evidence_parts = [
                f"Organización: {org_id} (FeatureSet: {feature_set})",
                f"Cuentas activas: {len(active_accounts)} de {num_accounts} total",
                f"Cuentas: {', '.join(account_names[:5])}{'...' if len(account_names) > 5 else ''}",
                f"OUs de primer nivel: {len(ous)} ({', '.join(ou_names[:5])})" if ous else "OUs de primer nivel: 0",
                f"SCPs personalizadas: {len(scp_names)} ({', '.join(scp_names[:5])})" if scp_names else "SCPs personalizadas: 0 (solo FullAWSAccess)"
            ]
            evidence = ' | '.join(evidence_parts)

            # 6. Evaluar cumplimiento
            issues = []
            if num_accounts <= 1:
                issues.append('Cuenta única sin separación de cargas de trabajo')
            if len(ous) == 0:
                issues.append('Sin OUs definidas para organizar cuentas')
            if feature_set != 'ALL':
                issues.append(f'FeatureSet es {feature_set}, se requiere ALL para SCPs')
            if len(scp_names) == 0:
                issues.append('Sin SCPs personalizadas para barreras de permisos')

            if len(issues) == 0:
                return {
                    'bp': 'SEC01-BP01',
                    'description': SECURITY_BP_DESCRIPTIONS.get('SEC01-BP01', ''),
                    'status': 'COMPLIANT',
                    'severity': 'LOW',
                    'finding': f'Arquitectura multi-cuenta implementada con {len(active_accounts)} cuentas activas, {len(ous)} OUs y {len(scp_names)} SCPs personalizadas.',
                    'evidence': evidence,
                    'remediation': 'Estado actual cumple. Continuar monitoreando la estructura organizacional y revisar periódicamente la separación de cargas de trabajo.',
                    'risk': 'Bajo riesgo. La arquitectura multi-cuenta proporciona aislamiento adecuado.'
                }
            elif num_accounts > 1 and len(issues) <= 2:
                return {
                    'bp': 'SEC01-BP01',
                    'description': SECURITY_BP_DESCRIPTIONS.get('SEC01-BP01', ''),
                    'status': 'PENDING_REVIEW',
                    'severity': 'MEDIUM',
                    'finding': f'Arquitectura multi-cuenta parcialmente implementada. Hallazgos: {"; ".join(issues)}',
                    'evidence': evidence,
                    'remediation': (
                        'Completar la implementación de arquitectura multi-cuenta: '
                        '1) Crear OUs para separar entornos (Producción, Desarrollo, Staging). '
                        '2) Aplicar SCPs para restringir acciones no autorizadas. '
                        '3) Verificar que cada carga de trabajo tenga su propia cuenta. '
                        '4) Implementar AWS Control Tower para gobernanza automatizada. '
                        '5) Configurar etiquetas de asignación de costos por cuenta.'
                    ),
                    'risk': 'Riesgo medio. La separación parcial puede dejar cargas de trabajo sin aislamiento adecuado.'
                }
            else:
                return {
                    'bp': 'SEC01-BP01',
                    'description': SECURITY_BP_DESCRIPTIONS.get('SEC01-BP01', ''),
                    'status': 'NON_COMPLIANT',
                    'severity': 'HIGH',
                    'finding': f'Arquitectura multi-cuenta insuficiente. Hallazgos: {"; ".join(issues)}',
                    'evidence': evidence,
                    'remediation': (
                        'Implementar arquitectura multi-cuenta completa: '
                        '1) Habilitar AWS Organizations con FeatureSet ALL. '
                        '2) Diseñar estructura de OUs (Seguridad, Producción, Desarrollo, Staging, Shared Services, Sandbox). '
                        '3) Crear cuentas separadas para cada carga de trabajo y entorno. '
                        '4) Aplicar SCPs para establecer barreras de permisos organizacionales. '
                        '5) Configurar AWS Control Tower para gobernanza centralizada. '
                        '6) Implementar roles cross-account con privilegios mínimos. '
                        '7) Configurar separación de facturación y asignación de costos por cuenta.'
                    ),
                    'risk': 'Alto riesgo. Sin aislamiento adecuado de cuentas, un incidente de seguridad puede propagarse a todas las cargas de trabajo. El radio de explosión es máximo.'
                }
        except ClientError as e:
            return self._handle_permission_error('SEC01-BP01', e)

    
    def _evaluate_sec01_bp02(self) -> Dict[str, Any]:
        """SEC01-BP02: Proteger el usuario raíz de la cuenta y sus propiedades
        Evalúa: MFA root, access keys root, CloudTrail root activity, root usage monitoring, SCPs
        """
        try:
            client = self.session.client('iam')
            summary = client.get_account_summary()['SummaryMap']
            
            issues = []
            evidence_parts = []
            
            # 1. Verificar MFA en usuario raíz
            root_mfa = summary.get('AccountMFAEnabled', 0)
            evidence_parts.append(f"MFA raíz: {'Habilitado' if root_mfa else 'DESHABILITADO'}")
            if not root_mfa:
                issues.append('MFA no habilitado en usuario raíz')
            
            # 2. Verificar access keys del usuario raíz
            root_access_keys = summary.get('AccountAccessKeysPresent', 0)
            evidence_parts.append(f"Access keys raíz: {root_access_keys}")
            if root_access_keys > 0:
                issues.append(f'{root_access_keys} access key(s) activa(s) en usuario raíz')
            
            # 3. Verificar actividad reciente del usuario raíz via CloudTrail
            try:
                ct_client = self.session.client('cloudtrail')
                import datetime as dt
                root_events = ct_client.lookup_events(
                    LookupAttributes=[{'AttributeKey': 'Username', 'AttributeValue': 'root'}],
                    StartTime=dt.datetime.utcnow() - dt.timedelta(days=90),
                    MaxResults=5
                )
                root_activity_count = len(root_events.get('Events', []))
                evidence_parts.append(f"Actividad raíz (90 días): {root_activity_count} eventos")
                if root_activity_count > 0:
                    last_event = root_events['Events'][0]
                    evidence_parts.append(f"Último evento raíz: {last_event.get('EventName', 'N/A')} ({last_event.get('EventTime', 'N/A')})")
                    issues.append(f'Actividad reciente del usuario raíz detectada ({root_activity_count} eventos en 90 días)')
            except ClientError:
                evidence_parts.append("Actividad raíz: No se pudo verificar (CloudTrail)")
            
            # 4. Verificar MFA devices (virtual vs hardware)
            try:
                mfa_devices = client.list_virtual_mfa_devices()
                virtual_mfa = [d for d in mfa_devices.get('VirtualMFADevices', []) if 'root' in str(d.get('SerialNumber', '')).lower()]
                if virtual_mfa:
                    evidence_parts.append("Tipo MFA raíz: Virtual (se recomienda hardware)")
                    issues.append('MFA virtual en usuario raíz (se recomienda dispositivo hardware)')
            except ClientError:
                pass
            
            # 5. Verificar número de usuarios IAM (indicador de uso directo vs SSO)
            num_users = summary.get('Users', 0)
            evidence_parts.append(f"Usuarios IAM: {num_users}")
            
            evidence = ' | '.join(evidence_parts)
            
            # Evaluar severidad y estado
            if not root_mfa or root_access_keys > 0:
                return {
                    'bp': 'SEC01-BP02',
                    'description': SECURITY_BP_DESCRIPTIONS.get('SEC01-BP02', ''),
                    'status': 'NON_COMPLIANT',
                    'severity': 'CRITICAL',
                    'finding': f'Protección del usuario raíz insuficiente. Hallazgos críticos: {"; ".join(issues)}',
                    'evidence': evidence,
                    'remediation': (
                        'Proteger el usuario raíz de forma inmediata: '
                        '1) Habilitar MFA en el usuario raíz (preferiblemente dispositivo hardware FIDO2). '
                        '2) Eliminar TODAS las access keys del usuario raíz. '
                        '3) Configurar alarma de CloudWatch para detectar uso de API del usuario raíz. '
                        '4) Aplicar SCP para restringir acciones del usuario raíz en cuentas miembro. '
                        '5) Usar correo corporativo (no personal) para la cuenta raíz. '
                        '6) Almacenar credenciales raíz en bóveda segura con acceso controlado. '
                        '7) No usar el usuario raíz para tareas rutinarias.'
                    ),
                    'risk': 'Riesgo CRÍTICO. El usuario raíz tiene acceso administrativo completo e irrestricto. Sin MFA o con access keys activas, las credenciales comprometidas otorgan control total de la cuenta.'
                }
            elif len(issues) > 0:
                return {
                    'bp': 'SEC01-BP02',
                    'description': SECURITY_BP_DESCRIPTIONS.get('SEC01-BP02', ''),
                    'status': 'PENDING_REVIEW',
                    'severity': 'MEDIUM',
                    'finding': f'Protección del usuario raíz parcial. Hallazgos: {"; ".join(issues)}',
                    'evidence': evidence,
                    'remediation': (
                        'Completar la protección del usuario raíz: '
                        '1) Reemplazar MFA virtual por dispositivo hardware FIDO2 en cuentas de gestión. '
                        '2) Configurar alarma de CloudWatch para eventos de usuario raíz (ConsoleLogin, API calls). '
                        '3) Aplicar SCP "Disallow Actions as Root User" en cuentas miembro. '
                        '4) Revisar y eliminar cualquier uso rutinario del usuario raíz. '
                        '5) Documentar procedimiento de acceso de emergencia al usuario raíz.'
                    ),
                    'risk': 'Riesgo medio. El usuario raíz tiene protección básica pero requiere mejoras para cumplir con las mejores prácticas.'
                }
            else:
                return {
                    'bp': 'SEC01-BP02',
                    'description': SECURITY_BP_DESCRIPTIONS.get('SEC01-BP02', ''),
                    'status': 'COMPLIANT',
                    'severity': 'LOW',
                    'finding': 'Usuario raíz protegido correctamente. MFA habilitado, sin access keys, sin actividad reciente.',
                    'evidence': evidence,
                    'remediation': 'Estado actual cumple. Continuar monitoreando la actividad del usuario raíz y mantener MFA activo.',
                    'risk': 'Bajo riesgo. El usuario raíz está adecuadamente protegido.'
                }
        except ClientError as e:
            return self._handle_permission_error('SEC01-BP02', e)
    
    def _evaluate_sec02(self) -> Dict[str, Any]:
        """SEC02: How do you manage identities for people and machines? (6 BPs)"""
        findings = []
        
        # SEC02-BP01: Use strong sign-in mechanisms
        findings.append(evaluate_sec02_bp01(self.session, self._handle_permission_error))
        
        # SEC02-BP02 to BP06: Real evaluations
        findings.append(evaluate_sec02_bp02(self.session, self._handle_permission_error))
        findings.append(evaluate_sec02_bp03(self.session, self._handle_permission_error))
        findings.append(evaluate_sec02_bp04(self.session, self._handle_permission_error))
        findings.append(evaluate_sec02_bp05(self.session, self._handle_permission_error))
        findings.append(evaluate_sec02_bp06(self.session, self._handle_permission_error))
        
        return self._create_question('SEC02', findings,
                                    'How do you manage identities for people and machines?',
                                    'Identity and access management')
    
    
    # Placeholder methods for remaining questions (SEC03-SEC11)
    def _evaluate_sec03(self) -> Dict[str, Any]:
        """SEC03: How do you manage permissions for people and machines? (9 BPs)"""
        findings = []
        
        # All 9 BPs with real evaluations
        findings.append(evaluate_sec03_bp01(self.session, self._handle_permission_error))
        findings.append(evaluate_sec03_bp02(self.session, self._handle_permission_error))
        findings.append(evaluate_sec03_bp03(self.session, self._handle_permission_error))
        findings.append(evaluate_sec03_bp04(self.session, self._handle_permission_error))
        findings.append(evaluate_sec03_bp05(self.session, self._handle_permission_error))
        findings.append(evaluate_sec03_bp06(self.session, self._handle_permission_error))
        findings.append(evaluate_sec03_bp07(self.session, self._handle_permission_error))
        findings.append(evaluate_sec03_bp08(self.session, self._handle_permission_error))
        findings.append(evaluate_sec03_bp09(self.session, self._handle_permission_error))
        
        return self._create_question('SEC03', findings,
                                    'How do you manage permissions for people and machines?',
                                    'Permission management')
    
    def _evaluate_sec04(self) -> Dict[str, Any]:
        """SEC04: How do you detect and investigate security events? (4 BPs)"""
        findings = []
        
        # All 4 BPs with real evaluations
        findings.append(evaluate_sec04_bp01(self.session, self._handle_permission_error))
        findings.append(evaluate_sec04_bp02(self.session, self._handle_permission_error))
        findings.append(evaluate_sec04_bp03(self.session, self._handle_permission_error))
        findings.append(evaluate_sec04_bp04(self.session, self._handle_permission_error))
        
        return self._create_question('SEC04', findings,
                                    'How do you detect and investigate security events?',
                                    'Detection and investigation')
    
    def _evaluate_sec05(self) -> Dict[str, Any]:
        """SEC05: How do you protect your network resources? (4 BPs)"""
        findings = []
        
        # All 4 BPs with real evaluations
        findings.append(evaluate_sec05_bp01(self.session, self._handle_permission_error))
        findings.append(evaluate_sec05_bp02(self.session, self._handle_permission_error))
        findings.append(evaluate_sec05_bp03(self.session, self._handle_permission_error))
        findings.append(evaluate_sec05_bp04(self.session, self._handle_permission_error))
        
        return self._create_question('SEC05', findings,
                                    'How do you protect your network resources?',
                                    'Network protection')
    
    def _evaluate_sec06(self) -> Dict[str, Any]:
        """SEC06: How do you protect your compute resources? (5 BPs)"""
        findings = []
        
        # All 5 BPs with real evaluations
        findings.append(evaluate_sec06_bp01(self.session, self._handle_permission_error))
        findings.append(evaluate_sec06_bp02(self.session, self._handle_permission_error))
        findings.append(evaluate_sec06_bp03(self.session, self._handle_permission_error))
        findings.append(evaluate_sec06_bp04(self.session, self._handle_permission_error))
        findings.append(evaluate_sec06_bp05(self.session, self._handle_permission_error))
        
        return self._create_question('SEC06', findings,
                                    'How do you protect your compute resources?',
                                    'Compute protection')
    
    def _evaluate_sec07(self) -> Dict[str, Any]:
        """SEC07: How do you classify your data? (4 BPs)"""
        findings = []
        
        # All 4 BPs with real evaluations
        findings.append(evaluate_sec07_bp01(self.session, self._handle_permission_error))
        findings.append(evaluate_sec07_bp02(self.session, self._handle_permission_error))
        findings.append(evaluate_sec07_bp03(self.session, self._handle_permission_error))
        findings.append(evaluate_sec07_bp04(self.session, self._handle_permission_error))
        
        return self._create_question('SEC07', findings,
                                    'How do you classify your data?',
                                    'Data classification')
    
    def _evaluate_sec08(self) -> Dict[str, Any]:
        """SEC08: How do you protect your data at rest? (4 BPs)"""
        findings = []
        
        # All 4 BPs with real evaluations
        findings.append(evaluate_sec08_bp01(self.session, self._handle_permission_error))
        findings.append(evaluate_sec08_bp02(self.session, self._handle_permission_error))
        findings.append(evaluate_sec08_bp03(self.session, self._handle_permission_error))
        findings.append(evaluate_sec08_bp04(self.session, self._handle_permission_error))
        
        return self._create_question('SEC08', findings,
                                    'How do you protect your data at rest?',
                                    'Data at rest protection')
    
    def _evaluate_sec09(self) -> Dict[str, Any]:
        """SEC09: How do you protect your data in transit? (3 BPs)"""
        findings = []
        
        # All 3 BPs with real evaluations
        findings.append(evaluate_sec09_bp01(self.session, self._handle_permission_error))
        findings.append(evaluate_sec09_bp02(self.session, self._handle_permission_error))
        findings.append(evaluate_sec09_bp03(self.session, self._handle_permission_error))
        
        return self._create_question('SEC09', findings,
                                    'How do you protect your data in transit?',
                                    'Data in transit protection')
    
    def _evaluate_sec10(self) -> Dict[str, Any]:
        """SEC10: How do you anticipate, respond to, and recover from incidents? (8 BPs)"""
        findings = []
        
        # All 8 BPs with real evaluations
        findings.append(evaluate_sec10_bp01(self.session, self._handle_permission_error))
        findings.append(evaluate_sec10_bp02(self.session, self._handle_permission_error))
        findings.append(evaluate_sec10_bp03(self.session, self._handle_permission_error))
        findings.append(evaluate_sec10_bp04(self.session, self._handle_permission_error))
        findings.append(evaluate_sec10_bp05(self.session, self._handle_permission_error))
        findings.append(evaluate_sec10_bp06(self.session, self._handle_permission_error))
        findings.append(evaluate_sec10_bp07(self.session, self._handle_permission_error))
        findings.append(evaluate_sec10_bp08(self.session, self._handle_permission_error))
        
        return self._create_question('SEC10', findings,
                                    'How do you anticipate, respond to, and recover from incidents?',
                                    'Incident response')
    
    def _evaluate_sec11(self) -> Dict[str, Any]:
        """SEC11: How do you incorporate and validate the security properties of applications? (8 BPs)"""
        findings = []
        
        # All 8 BPs with real evaluations
        findings.append(evaluate_sec11_bp01(self.session, self._handle_permission_error))
        findings.append(evaluate_sec11_bp02(self.session, self._handle_permission_error))
        findings.append(evaluate_sec11_bp03(self.session, self._handle_permission_error))
        findings.append(evaluate_sec11_bp04(self.session, self._handle_permission_error))
        findings.append(evaluate_sec11_bp05(self.session, self._handle_permission_error))
        findings.append(evaluate_sec11_bp06(self.session, self._handle_permission_error))
        findings.append(evaluate_sec11_bp07(self.session, self._handle_permission_error))
        findings.append(evaluate_sec11_bp08(self.session, self._handle_permission_error))
        
        return self._create_question('SEC11', findings,
                                    'How do you incorporate and validate security properties?',
                                    'Application security')
    
    # Helper methods
    def _create_question(self, question_id: str, findings: List[Dict], 
                        title_en: str, title_es: str) -> Dict[str, Any]:
        """Creates a question object with calculated score"""
        score = self._calculate_question_score(findings)
        status = self._determine_question_status(findings)
        
        return {
            'question_id': question_id,
            'title': {
                'es': title_es,
                'en': title_en
            },
            'description': {
                'es': title_es,
                'en': title_en
            },
            'score': score,
            'bps_evaluated': len(findings),
            'status': status,
            'findings': findings
        }
    
    def _calculate_question_score(self, findings: List[Dict]) -> float:
        """Calculates score for a question based on BP statuses"""
        if not findings:
            return 0.0
        
        score_map = {
            'COMPLIANT': 100.0,
            'NON_COMPLIANT': 0.0,
            'PENDING_REVIEW': 50.0
        }
        
        total_score = sum(score_map.get(f['status'], 0.0) for f in findings)
        return round(total_score / len(findings), 2)
    
    def _calculate_pillar_score(self, questions: List[Dict]) -> float:
        """Calculates overall pillar score"""
        if not questions:
            return 0.0
        
        total_weighted_score = 0.0
        total_bps = 0
        
        for question in questions:
            num_bps = question['bps_evaluated']
            question_score = question['score']
            total_weighted_score += question_score * num_bps
            total_bps += num_bps
        
        return round(total_weighted_score / total_bps if total_bps > 0 else 0.0, 2)
    
    def _determine_question_status(self, findings: List[Dict]) -> str:
        """Determines overall status of a question"""
        statuses = [f['status'] for f in findings]
        
        if all(s == 'COMPLIANT' for s in statuses):
            return 'COMPLIANT'
        elif any(s == 'NON_COMPLIANT' for s in statuses):
            return 'NON_COMPLIANT'
        else:
            return 'PENDING_REVIEW'
    
    def _calculate_distributions(self, questions: List[Dict]) -> tuple:
        """Calculates compliance and severity distributions"""
        compliance_dist = {
            'compliant': 0,
            'non_compliant': 0,
            'pending_review': 0
        }
        
        severity_dist = {
            'critical': 0,
            'high': 0,
            'medium': 0,
            'low': 0
        }
        
        for question in questions:
            for finding in question['findings']:
                status = finding['status'].lower()
                if status == 'compliant':
                    compliance_dist['compliant'] += 1
                elif status == 'non_compliant':
                    compliance_dist['non_compliant'] += 1
                else:
                    compliance_dist['pending_review'] += 1
                
                severity = finding['severity'].lower()
                if severity in severity_dist:
                    severity_dist[severity] += 1
        
        return compliance_dist, severity_dist
    
    def _handle_permission_error(self, bp_id: str, error: ClientError) -> Dict[str, Any]:
        """Handles AWS permission errors gracefully"""
        error_code = error.response['Error']['Code']
        error_message = error.response['Error']['Message']
        
        return {
            'bp': bp_id,
            'description': SECURITY_BP_DESCRIPTIONS.get(bp_id, ''),
            'status': 'PENDING_REVIEW',
            'severity': 'MEDIUM',
            'finding': 'Unable to evaluate due to insufficient permissions',
            'evidence': f'Access Denied: {error_code} - {error_message}',
            'remediation': 'Grant required IAM permissions to evaluation role',
            'risk': 'Cannot determine compliance status'
        }
