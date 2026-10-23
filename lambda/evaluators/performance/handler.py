"""
Performance Efficiency Pillar Evaluator Lambda
Evaluates 5 Performance questions with 32 Best Practices
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
sys.path.append('/opt/python')
from autowar_common.credentials_manager import CredentialsManager

# Load bp_descriptions dynamically to avoid import conflicts
bp_desc_path = os.path.join(os.path.dirname(__file__), 'bp_descriptions.py')
spec = importlib.util.spec_from_file_location("performance_bp_descriptions", bp_desc_path)
bp_desc_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bp_desc_module)
PERFORMANCE_BP_DESCRIPTIONS = bp_desc_module.PERFORMANCE_BP_DESCRIPTIONS

# Import all BP evaluations (pillar_dir is inserted into sys.path by unified_handler)
from all_bp_evaluations import *


def lambda_handler(event, context):
    """Main handler for Performance Efficiency pillar evaluation"""
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
            
            # Query for recent performance evaluations
            response = table.query(
                KeyConditionExpression=Key('session_id').eq(session_id) & Key('evaluation_id').begins_with('performance#'),
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
                evaluator = PerformanceEvaluator(session, region)
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
            evaluator = PerformanceEvaluator(session, region)
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
                    'evaluation_id': f'performance#{int(time.time())}',
                    'pillar_id': 'performance',
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


class PerformanceEvaluator:
    """Evaluates Performance Efficiency pillar (5 questions, 32 BPs)"""
    
    def __init__(self, session: boto3.Session, region: str = None):
        self.session = session
        self.region = region or session.region_name

        
    def evaluate(self) -> Dict[str, Any]:
        """Evaluates all 5 Performance questions"""
        questions = [
            self._evaluate_perf01(),
            self._evaluate_perf02(),
            self._evaluate_perf03(),
            self._evaluate_perf04(),
            self._evaluate_perf05()
        ]
        
        pillar_score = self._calculate_pillar_score(questions)
        compliance_dist, severity_dist = self._calculate_distributions(questions)
        
        return {
            'pillar_id': 'performance',
            'region': self.region,
            'pillar_name': {'es': 'Eficiencia del Rendimiento', 'en': 'Performance Efficiency'},
            'description': {'es': 'Uso eficiente de recursos de computación', 'en': 'Efficient use of computing resources'},
            'overall_score': pillar_score,
            'total_findings': sum(len(q['findings']) for q in questions),
            'total_best_practices': sum(q['bps_evaluated'] for q in questions),
            'timestamp': datetime.utcnow().isoformat(),
            'questions': questions,
            'compliance_distribution': compliance_dist,
            'severity_distribution': severity_dist
        }
    
    def _safe_eval(self, bp_id: str, func) -> Dict[str, Any]:
        """Ejecuta la evaluación de un BP de forma resiliente.

        Si el BP lanza CUALQUIER excepción (incluidas las que no son ClientError,
        como UnknownServiceError de botocore), se delega a _handle_permission_error
        para devolver un finding PENDING_REVIEW. Así ningún BP individual tumba el
        pilar completo.
        """
        try:
            return func(self.session, self._handle_permission_error)
        except Exception as e:
            return self._handle_permission_error(bp_id, e)

    def _evaluate_perf01(self) -> Dict[str, Any]:
        """PERF01: How do you select appropriate resources? (7 BPs)"""
        findings = [
            self._safe_eval('PERF01-BP01', evaluate_perf01_bp01),
            self._safe_eval('PERF01-BP02', evaluate_perf01_bp02),
            self._safe_eval('PERF01-BP03', evaluate_perf01_bp03),
            self._safe_eval('PERF01-BP04', evaluate_perf01_bp04),
            self._safe_eval('PERF01-BP05', evaluate_perf01_bp05),
            self._safe_eval('PERF01-BP06', evaluate_perf01_bp06),
            self._safe_eval('PERF01-BP07', evaluate_perf01_bp07),
        ]
        return self._create_question('PERF01', findings,
            'How do you select appropriate resources?', 'Selección de recursos')

    def _evaluate_perf02(self) -> Dict[str, Any]:
        """PERF02: How do you select your compute solution? (6 BPs)"""
        findings = [
            self._safe_eval('PERF02-BP01', evaluate_perf02_bp01),
            self._safe_eval('PERF02-BP02', evaluate_perf02_bp02),
            self._safe_eval('PERF02-BP03', evaluate_perf02_bp03),
            self._safe_eval('PERF02-BP04', evaluate_perf02_bp04),
            self._safe_eval('PERF02-BP05', evaluate_perf02_bp05),
            self._safe_eval('PERF02-BP06', evaluate_perf02_bp06),
        ]
        return self._create_question('PERF02', findings,
            'How do you select your compute solution?', 'Solución de cómputo')
    
    def _evaluate_perf03(self) -> Dict[str, Any]:
        """PERF03: How do you store, manage, and access data? (5 BPs)"""
        findings = [
            self._safe_eval('PERF03-BP01', evaluate_perf03_bp01),
            self._safe_eval('PERF03-BP02', evaluate_perf03_bp02),
            self._safe_eval('PERF03-BP03', evaluate_perf03_bp03),
            self._safe_eval('PERF03-BP04', evaluate_perf03_bp04),
            self._safe_eval('PERF03-BP05', evaluate_perf03_bp05),
        ]
        return self._create_question('PERF03', findings,
            'How do you store, manage, and access data?', 'Almacenamiento de datos')
    
    def _evaluate_perf04(self) -> Dict[str, Any]:
        """PERF04: How do you select and configure networking resources? (7 BPs)"""
        findings = [
            self._safe_eval('PERF04-BP01', evaluate_perf04_bp01),
            self._safe_eval('PERF04-BP02', evaluate_perf04_bp02),
            self._safe_eval('PERF04-BP03', evaluate_perf04_bp03),
            self._safe_eval('PERF04-BP04', evaluate_perf04_bp04),
            self._safe_eval('PERF04-BP05', evaluate_perf04_bp05),
            self._safe_eval('PERF04-BP06', evaluate_perf04_bp06),
            self._safe_eval('PERF04-BP07', evaluate_perf04_bp07),
        ]
        return self._create_question('PERF04', findings,
            'How do you select and configure networking resources?', 'Recursos de red')
    
    def _evaluate_perf05(self) -> Dict[str, Any]:
        """PERF05: How do you evolve your workload to take advantage of new releases? (7 BPs)"""
        findings = [
            self._safe_eval('PERF05-BP01', evaluate_perf05_bp01),
            self._safe_eval('PERF05-BP02', evaluate_perf05_bp02),
            self._safe_eval('PERF05-BP03', evaluate_perf05_bp03),
            self._safe_eval('PERF05-BP04', evaluate_perf05_bp04),
            self._safe_eval('PERF05-BP05', evaluate_perf05_bp05),
            self._safe_eval('PERF05-BP06', evaluate_perf05_bp06),
            self._safe_eval('PERF05-BP07', evaluate_perf05_bp07),
        ]
        return self._create_question('PERF05', findings,
            'How do you evolve your workload to take advantage of new releases?', 'Evolución del workload')
    
    def _handle_permission_error(self, bp_id: str, error: ClientError) -> Dict[str, Any]:
        """Maneja errores de permisos/excepciones de AWS devolviendo PENDING_REVIEW (nunca COMPLIANT)."""
        try:
            error_code = error.response['Error']['Code']
            error_message = error.response['Error']['Message']
        except (AttributeError, KeyError, TypeError):
            error_code = 'UnknownError'
            error_message = str(error)
        
        return {
            'bp': bp_id,
            'description': PERFORMANCE_BP_DESCRIPTIONS.get(bp_id, ''),
            'status': 'PENDING_REVIEW',
            'severity': 'MEDIUM',
            'finding': 'No se pudo evaluar automáticamente (permisos insuficientes)',
            'evidence': f'Access Denied: {error_code} - {error_message}',
            'remediation': 'Verificar permisos de solo lectura para el servicio correspondiente',
            'risk': 'No se pudo determinar el cumplimiento'
        }
    
    def _create_question(self, question_id: str, findings: List[Dict],
                        title_en: str, title_es: str) -> Dict[str, Any]:
        score = self._calculate_question_score(findings)
        status = self._determine_question_status(findings)
        applicable_bps = sum(1 for f in findings if f['status'] != 'NOT_APPLICABLE')
        
        return {
            'question_id': question_id,
            'title': {'es': title_es, 'en': title_en},
            'description': {'es': title_es, 'en': title_en},
            'score': score,
            'bps_evaluated': len(findings),
            'applicable_bps': applicable_bps,
            'status': status,
            'findings': findings
        }
    
    def _determine_question_status(self, findings: List[Dict]) -> str:
        """Estado de la pregunta excluyendo NOT_APPLICABLE del juicio."""
        applicable = [f for f in findings if f['status'] != 'NOT_APPLICABLE']
        if not applicable:
            # Todas NOT_APPLICABLE (o sin findings)
            return 'NOT_APPLICABLE' if findings else 'COMPLIANT'
        if any(f['status'] == 'NON_COMPLIANT' for f in applicable):
            return 'NON_COMPLIANT'
        if all(f['status'] == 'COMPLIANT' for f in applicable):
            return 'COMPLIANT'
        return 'PENDING_REVIEW'
    
    def _calculate_question_score(self, findings: List[Dict]) -> float:
        """Promedia solo los BPs aplicables; NOT_APPLICABLE se excluye del cálculo."""
        score_map = {'COMPLIANT': 100.0, 'NON_COMPLIANT': 0.0, 'PENDING_REVIEW': 50.0}
        applicable = [f for f in findings if f['status'] != 'NOT_APPLICABLE']
        if not applicable:
            # Sin BPs aplicables (todas NA) -> no penalizar
            return 100.0
        total = sum(score_map.get(f['status'], 0.0) for f in applicable)
        return round(total / len(applicable), 2)
    
    def _calculate_pillar_score(self, questions: List[Dict]) -> float:
        """Promedio ponderado por BPs aplicables (excluye NOT_APPLICABLE del peso)."""
        if not questions:
            return 0.0
        total_weighted = sum(q['score'] * q.get('applicable_bps', q['bps_evaluated']) for q in questions)
        total_applicable = sum(q.get('applicable_bps', q['bps_evaluated']) for q in questions)
        if total_applicable == 0:
            return 100.0
        return round(total_weighted / total_applicable, 2)
    
    def _calculate_distributions(self, questions: List[Dict]) -> tuple:
        compliance_dist = {'compliant': 0, 'non_compliant': 0, 'pending_review': 0, 'not_applicable': 0}
        severity_dist = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        
        for q in questions:
            for f in q['findings']:
                status = f['status'].lower()
                if status == 'compliant':
                    compliance_dist['compliant'] += 1
                elif status == 'non_compliant':
                    compliance_dist['non_compliant'] += 1
                elif status == 'not_applicable':
                    compliance_dist['not_applicable'] += 1
                else:
                    compliance_dist['pending_review'] += 1
                
                severity = f['severity'].lower()
                if severity in severity_dist:
                    severity_dist[severity] += 1
        
        return compliance_dist, severity_dist
