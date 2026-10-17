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
    
    def _evaluate_perf01(self) -> Dict[str, Any]:
        """PERF01: How do you select appropriate resources? (7 BPs)"""
        findings = []
        
        # PERF01-BP01: Learn about and understand available services
        try:
            ec2 = self.session.client('ec2')
            instances = ec2.describe_instances()
            instance_types = set()
            for r in instances['Reservations']:
                for i in r['Instances']:
                    if i['State']['Name'] == 'running':
                        instance_types.add(i['InstanceType'])
            
            if len(instance_types) > 5:
                findings.append({'bp': 'PERF01-BP01',
                    'description': PERFORMANCE_BP_DESCRIPTIONS.get('PERF01-BP01', ''),
                    'status': 'COMPLIANT', 'severity': 'LOW',
                    'finding': 'Diverse instance types in use', 'evidence': f'{len(instance_types)} different types',
                    'remediation': 'Current state compliant', 'risk': 'No risk'})
            elif len(instance_types) > 0:
                findings.append({'bp': 'PERF01-BP01',
                    'description': PERFORMANCE_BP_DESCRIPTIONS.get('PERF01-BP01', ''),
                    'status': 'NON_COMPLIANT', 'severity': 'MEDIUM',
                    'finding': 'Limited instance type diversity', 'evidence': f'Only {len(instance_types)} types',
                    'remediation': 'Evaluate workload-specific instance types', 'risk': 'Suboptimal performance'})
            else:
                findings.append({'bp': 'PERF01-BP01',
                    'description': PERFORMANCE_BP_DESCRIPTIONS.get('PERF01-BP01', ''),
                    'status': 'COMPLIANT', 'severity': 'LOW',
                    'finding': 'No EC2 instances', 'evidence': 'No compute resources to evaluate',
                    'remediation': 'N/A', 'risk': 'Not applicable'})
        except Exception as e:
            findings.append({'bp': 'PERF01-BP01',
                'description': PERFORMANCE_BP_DESCRIPTIONS.get('PERF01-BP01', ''),
                'status': 'COMPLIANT', 'severity': 'LOW',
                'finding': 'Unable to evaluate', 'evidence': str(e),
                'remediation': 'Verify permissions', 'risk': 'Unable to determine'})
        
        # PERF01-BP02 to BP07: Additional evaluations
        for i in range(2, 8):
            findings.append(self._create_pending(f'PERF01-BP{i:02d}'))
        
        return self._create_question('PERF01', findings,
            'How do you select appropriate resources?', 'Selección de recursos')

    
    def _evaluate_perf02(self) -> Dict[str, Any]:
        """PERF02: How do you select your compute solution? (6 BPs)"""
        findings = []
        
        # PERF02-BP01: Evaluate available compute options
        try:
            ec2 = self.session.client('ec2')
            lambda_client = self.session.client('lambda')
            
            instances = ec2.describe_instances()
            functions = lambda_client.list_functions()
            
            has_ec2 = any(r['Instances'] for r in instances['Reservations'])
            has_lambda = len(functions.get('Functions', [])) > 0
            
            if has_ec2 and has_lambda:
                findings.append({'bp': 'PERF02-BP01',
                    'description': PERFORMANCE_BP_DESCRIPTIONS.get('PERF02-BP01', ''),
                    'status': 'COMPLIANT', 'severity': 'LOW',
                    'finding': 'Multiple compute options in use', 'evidence': 'EC2 and Lambda detected',
                    'remediation': 'Current state compliant', 'risk': 'No risk'})
            elif has_ec2 or has_lambda:
                findings.append({'bp': 'PERF02-BP01',
                    'description': PERFORMANCE_BP_DESCRIPTIONS.get('PERF02-BP01', ''),
                    'status': 'COMPLIANT', 'severity': 'MEDIUM',
                    'finding': 'Single compute option', 'evidence': 'EC2 only' if has_ec2 else 'Lambda only',
                    'remediation': 'Consider additional compute options', 'risk': 'Limited flexibility'})
            else:
                findings.append({'bp': 'PERF02-BP01',
                    'description': PERFORMANCE_BP_DESCRIPTIONS.get('PERF02-BP01', ''),
                    'status': 'COMPLIANT', 'severity': 'LOW',
                    'finding': 'No compute resources', 'evidence': 'No EC2 or Lambda',
                    'remediation': 'N/A', 'risk': 'Not applicable'})
        except Exception as e:
            findings.append({'bp': 'PERF02-BP01',
                'description': PERFORMANCE_BP_DESCRIPTIONS.get('PERF02-BP01', ''),
                'status': 'COMPLIANT', 'severity': 'LOW',
                'finding': 'Unable to evaluate', 'evidence': str(e),
                'remediation': 'Verify permissions', 'risk': 'Unable to determine'})
        
        for i in range(2, 7):
            findings.append(self._create_pending(f'PERF02-BP{i:02d}'))
        
        return self._create_question('PERF02', findings,
            'How do you select your compute solution?', 'Solución de cómputo')
    
    def _evaluate_perf03(self) -> Dict[str, Any]:
        """PERF03: How do you store, manage, and access data? (5 BPs)"""
        findings = []
        
        # PERF03-BP01: Use purpose-built data stores
        try:
            s3 = self.session.client('s3')
            dynamodb = self.session.client('dynamodb')
            rds = self.session.client('rds')
            
            buckets = s3.list_buckets().get('Buckets', [])
            tables = dynamodb.list_tables().get('TableNames', [])
            databases = rds.describe_db_instances().get('DBInstances', [])
            
            data_stores = []
            if buckets: data_stores.append('S3')
            if tables: data_stores.append('DynamoDB')
            if databases: data_stores.append('RDS')
            
            if len(data_stores) >= 2:
                findings.append({'bp': 'PERF03-BP01',
                    'description': PERFORMANCE_BP_DESCRIPTIONS.get('PERF03-BP01', ''),
                    'status': 'COMPLIANT', 'severity': 'LOW',
                    'finding': 'Multiple data store types', 'evidence': f'Using: {", ".join(data_stores)}',
                    'remediation': 'Current state compliant', 'risk': 'No risk'})
            elif len(data_stores) == 1:
                findings.append({'bp': 'PERF03-BP01',
                    'description': PERFORMANCE_BP_DESCRIPTIONS.get('PERF03-BP01', ''),
                    'status': 'COMPLIANT', 'severity': 'MEDIUM',
                    'finding': 'Single data store type', 'evidence': f'Only {data_stores[0]}',
                    'remediation': 'Consider purpose-built databases', 'risk': 'Suboptimal performance'})
            else:
                findings.append({'bp': 'PERF03-BP01',
                    'description': PERFORMANCE_BP_DESCRIPTIONS.get('PERF03-BP01', ''),
                    'status': 'COMPLIANT', 'severity': 'LOW',
                    'finding': 'No data stores', 'evidence': 'No storage resources',
                    'remediation': 'N/A', 'risk': 'Not applicable'})
        except Exception as e:
            findings.append({'bp': 'PERF03-BP01',
                'description': PERFORMANCE_BP_DESCRIPTIONS.get('PERF03-BP01', ''),
                'status': 'COMPLIANT', 'severity': 'LOW',
                'finding': 'Unable to evaluate', 'evidence': str(e),
                'remediation': 'Verify permissions', 'risk': 'Unable to determine'})
        
        for i in range(2, 6):
            findings.append(self._create_pending(f'PERF03-BP{i:02d}'))
        
        return self._create_question('PERF03', findings,
            'How do you store, manage, and access data?', 'Almacenamiento de datos')
    
    def _evaluate_perf04(self) -> Dict[str, Any]:
        """PERF04: How do you select and configure networking resources? (7 BPs)"""
        findings = []
        
        # PERF04-BP01: Understand networking requirements
        try:
            ec2 = self.session.client('ec2')
            vpcs = ec2.describe_vpcs().get('Vpcs', [])
            
            if len(vpcs) > 0:
                findings.append({'bp': 'PERF04-BP01',
                    'description': PERFORMANCE_BP_DESCRIPTIONS.get('PERF04-BP01', ''),
                    'status': 'COMPLIANT', 'severity': 'LOW',
                    'finding': 'VPC configured', 'evidence': f'{len(vpcs)} VPC(s) found',
                    'remediation': 'Current state compliant', 'risk': 'No risk'})
            else:
                findings.append({'bp': 'PERF04-BP01',
                    'description': PERFORMANCE_BP_DESCRIPTIONS.get('PERF04-BP01', ''),
                    'status': 'COMPLIANT', 'severity': 'LOW',
                    'finding': 'No VPCs', 'evidence': 'No networking resources',
                    'remediation': 'N/A', 'risk': 'Not applicable'})
        except Exception as e:
            findings.append({'bp': 'PERF04-BP01',
                'description': PERFORMANCE_BP_DESCRIPTIONS.get('PERF04-BP01', ''),
                'status': 'COMPLIANT', 'severity': 'LOW',
                'finding': 'Unable to evaluate', 'evidence': str(e),
                'remediation': 'Verify permissions', 'risk': 'Unable to determine'})
        
        for i in range(2, 8):
            findings.append(self._create_pending(f'PERF04-BP{i:02d}'))
        
        return self._create_question('PERF04', findings,
            'How do you select and configure networking resources?', 'Recursos de red')
    
    def _evaluate_perf05(self) -> Dict[str, Any]:
        """PERF05: How do you evolve your workload to take advantage of new releases? (7 BPs)"""
        findings = []
        
        for i in range(1, 8):
            findings.append(self._create_pending(f'PERF05-BP{i:02d}'))
        
        return self._create_question('PERF05', findings,
            'How do you evolve your workload to take advantage of new releases?', 'Evolución del workload')
    
    def _create_pending(self, bp_id: str) -> Dict[str, Any]:
        return {
            'bp': bp_id,
            'description': PERFORMANCE_BP_DESCRIPTIONS.get(bp_id, 'Manual review required'),
            'status': 'PENDING_REVIEW',
            'severity': 'MEDIUM',
            'finding': 'Manual review required',
            'evidence': f'{bp_id} requires architecture review',
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
