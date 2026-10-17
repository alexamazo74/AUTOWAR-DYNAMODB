"""
Operational Excellence Pillar Evaluator Lambda
Evaluates 11 Operational Excellence questions with 31 Best Practices
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
spec = importlib.util.spec_from_file_location("operational_excellence_bp_descriptions", bp_desc_path)
bp_desc_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bp_desc_module)
OPERATIONAL_EXCELLENCE_BP_DESCRIPTIONS = bp_desc_module.OPERATIONAL_EXCELLENCE_BP_DESCRIPTIONS


def lambda_handler(event, context):
    """Main handler for Operational Excellence pillar evaluation"""
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
            
            # Query for recent operational_excellence evaluations
            response = table.query(
                KeyConditionExpression=Key('session_id').eq(session_id) & Key('evaluation_id').begins_with('operational_excellence#'),
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
        
        creds_manager = CredentialsManager()
        credentials = creds_manager.get_session_credentials(session_id)
        
        if not credentials:
            return {
                'statusCode': 401,
                'headers': cors_headers,
                'body': json.dumps({'error': 'Session expired or invalid'})
            }
        
        regions = credentials.get('regions', [credentials.get('region', 'us-east-1')])
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
                evaluator = OperationalExcellenceEvaluator(session, region)
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
            evaluator = OperationalExcellenceEvaluator(session, region)
            all_results.append(evaluator.evaluate())
        
        # Aggregate if multiple regions
        if len(all_results) == 1:
            final_result = all_results[0]
        else:
            final_result = all_results[0]
            final_result['regions'] = [r.get('region') for r in all_results]
            final_result['multi_region'] = True
        
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
                    'evaluation_id': f'operational_excellence#{int(time.time())}',
                    'pillar_id': 'operational_excellence',
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
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'statusCode': 500,
            'headers': cors_headers,
            'body': json.dumps({'error': f'Evaluation failed: {str(e)}'})
        }


class OperationalExcellenceEvaluator:
    """Evaluates Operational Excellence pillar (11 questions, 31 BPs)"""
    
    def __init__(self, session: boto3.Session, region: str = None):
        self.session = session
        self.region = region or session.region_name
        
    def evaluate(self) -> Dict[str, Any]:
        """Evaluates all 11 Operational Excellence questions"""
        questions = [
            self._evaluate_ops01(),
            self._evaluate_ops02(),
            self._evaluate_ops03(),
            self._evaluate_ops04(),
            self._evaluate_ops05(),
            self._evaluate_ops06(),
            self._evaluate_ops07(),
            self._evaluate_ops08(),
            self._evaluate_ops09(),
            self._evaluate_ops10(),
            self._evaluate_ops11()
        ]
        
        pillar_score = self._calculate_pillar_score(questions)
        compliance_dist, severity_dist = self._calculate_distributions(questions)
        
        return {
            'pillar_id': 'operational_excellence',
            'region': self.region,
            'pillar_name': {'es': 'Excelencia Operativa', 'en': 'Operational Excellence'},
            'description': {'es': 'Ejecutar y monitorear sistemas para entregar valor de negocio', 'en': 'Run and monitor systems to deliver business value'},
            'overall_score': pillar_score,
            'total_findings': sum(len(q['findings']) for q in questions),
            'total_best_practices': sum(q['bps_evaluated'] for q in questions),
            'timestamp': datetime.utcnow().isoformat(),
            'questions': questions,
            'compliance_distribution': compliance_dist,
            'severity_distribution': severity_dist
        }
    
    def _evaluate_ops01(self) -> Dict[str, Any]:
        """OPS01: How do you determine what your priorities are? (6 BPs)"""
        findings = []
        
        for i in range(1, 7):
            findings.append(self._create_pending(f'OPS01-BP{i:02d}'))
        
        return self._create_question('OPS01', findings,
            'How do you determine what your priorities are?', 'Determinación de prioridades')
    
    def _evaluate_ops02(self) -> Dict[str, Any]:
        """OPS02: How do you structure your organization to support your business outcomes? (2 BPs)"""
        findings = []
        
        for i in range(1, 3):
            findings.append(self._create_pending(f'OPS02-BP{i:02d}'))
        
        return self._create_question('OPS02', findings,
            'How do you structure your organization to support your business outcomes?', 'Estructura organizacional')
    
    def _evaluate_ops03(self) -> Dict[str, Any]:
        """OPS03: How does your organizational culture support your business outcomes? (3 BPs)"""
        findings = []
        
        for i in range(1, 4):
            findings.append(self._create_pending(f'OPS03-BP{i:02d}'))
        
        return self._create_question('OPS03', findings,
            'How does your organizational culture support your business outcomes?', 'Cultura organizacional')
    
    def _evaluate_ops04(self) -> Dict[str, Any]:
        """OPS04: How do you implement observability in your workload? (4 BPs)"""
        findings = []
        
        for i in range(1, 5):
            findings.append(self._create_pending(f'OPS04-BP{i:02d}'))
        
        return self._create_question('OPS04', findings,
            'How do you implement observability in your workload?', 'Implementación de observabilidad')
    
    def _evaluate_ops05(self) -> Dict[str, Any]:
        """OPS05: How do you reduce defects, ease remediation, and improve flow into production? (4 BPs)"""
        findings = []
        
        for i in range(1, 5):
            findings.append(self._create_pending(f'OPS05-BP{i:02d}'))
        
        return self._create_question('OPS05', findings,
            'How do you reduce defects, ease remediation, and improve flow into production?', 'Reducción de defectos y mejora del flujo')
    
    def _evaluate_ops06(self) -> Dict[str, Any]:
        """OPS06: How do you mitigate deployment risks? (4 BPs)"""
        findings = []
        
        for i in range(1, 5):
            findings.append(self._create_pending(f'OPS06-BP{i:02d}'))
        
        return self._create_question('OPS06', findings,
            'How do you mitigate deployment risks?', 'Mitigación de riesgos de despliegue')
    
    def _evaluate_ops07(self) -> Dict[str, Any]:
        """OPS07: How do you know that you are ready to support a workload? (2 BPs)"""
        findings = []
        
        for i in range(1, 3):
            findings.append(self._create_pending(f'OPS07-BP{i:02d}'))
        
        return self._create_question('OPS07', findings,
            'How do you know that you are ready to support a workload?', 'Preparación para soportar workload')
    
    def _evaluate_ops08(self) -> Dict[str, Any]:
        """OPS08: How do you utilize workload observability in your organization? (2 BPs)"""
        findings = []
        
        for i in range(1, 3):
            findings.append(self._create_pending(f'OPS08-BP{i:02d}'))
        
        return self._create_question('OPS08', findings,
            'How do you utilize workload observability in your organization?', 'Utilización de observabilidad')
    
    def _evaluate_ops09(self) -> Dict[str, Any]:
        """OPS09: How do you understand the health of your operations? (2 BPs)"""
        findings = []
        
        for i in range(1, 3):
            findings.append(self._create_pending(f'OPS09-BP{i:02d}'))
        
        return self._create_question('OPS09', findings,
            'How do you understand the health of your operations?', 'Salud de las operaciones')
    
    def _evaluate_ops10(self) -> Dict[str, Any]:
        """OPS10: How do you manage workload and operations events? (1 BP)"""
        findings = []
        
        findings.append(self._create_pending('OPS10-BP01'))
        
        return self._create_question('OPS10', findings,
            'How do you manage workload and operations events?', 'Gestión de eventos')
    
    def _evaluate_ops11(self) -> Dict[str, Any]:
        """OPS11: How do you evolve operations? (1 BP)"""
        findings = []
        
        findings.append(self._create_pending('OPS11-BP01'))
        
        return self._create_question('OPS11', findings,
            'How do you evolve operations?', 'Evolución de operaciones')
    
    def _create_pending(self, bp_id: str) -> Dict[str, Any]:
        return {
            'bp': bp_id,
            'description': OPERATIONAL_EXCELLENCE_BP_DESCRIPTIONS.get(bp_id, 'Manual review required'),
            'status': 'PENDING_REVIEW',
            'severity': 'MEDIUM',
            'finding': 'Manual review required',
            'evidence': f'{bp_id} requires manual review',
            'remediation': 'Review AWS Well-Architected documentation',
            'risk': 'Unable to determine'
        }
    
    def _create_question(self, question_id: str, findings: List[Dict],
                        title_en: str, title_es: str) -> Dict[str, Any]:
        score = self._calculate_question_score(findings)
        status = 'COMPLIANT' if all(f['status'] == 'COMPLIANT' for f in findings) else \
                 'NON_COMPLIANT' if any(f['status'] == 'NON_COMPLIANT' for f in findings) else 'PENDING_REVIEW'
        
        return {
            'question_id': question_id,
            'title': {'es': title_es, 'en': title_en},
            'description': {'es': title_es, 'en': title_en},
            'score': score,
            'bps_evaluated': len(findings),
            'status': status,
            'findings': findings
        }
    
    def _calculate_question_score(self, findings: List[Dict]) -> float:
        if not findings:
            return 0.0
        score_map = {'COMPLIANT': 100.0, 'NON_COMPLIANT': 0.0, 'PENDING_REVIEW': 50.0}
        total = sum(score_map.get(f['status'], 0.0) for f in findings)
        return round(total / len(findings), 2)
    
    def _calculate_pillar_score(self, questions: List[Dict]) -> float:
        if not questions:
            return 0.0
        total_weighted = sum(q['score'] * q['bps_evaluated'] for q in questions)
        total_bps = sum(q['bps_evaluated'] for q in questions)
        return round(total_weighted / total_bps if total_bps > 0 else 0.0, 2)
    
    def _calculate_distributions(self, questions: List[Dict]) -> tuple:
        compliance_dist = {'compliant': 0, 'non_compliant': 0, 'pending_review': 0}
        severity_dist = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        
        for q in questions:
            for f in q['findings']:
                status = f['status'].lower()
                if status == 'compliant':
                    compliance_dist['compliant'] += 1
                elif status == 'non_compliant':
                    compliance_dist['non_compliant'] += 1
                else:
                    compliance_dist['pending_review'] += 1
                
                severity = f['severity'].lower()
                if severity in severity_dist:
                    severity_dist[severity] += 1
        
        return compliance_dist, severity_dist
