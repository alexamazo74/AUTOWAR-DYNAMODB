"""
Save Evaluation Results Lambda
Reads full pillar data from DynamoDB (compressed, saved by unified_handler) and assembles final result.
"""

import json
import os
import boto3
import gzip
import base64
from datetime import datetime
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
EVALUATIONS_TABLE = os.environ.get('EVALUATIONS_TABLE')


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


def lambda_handler(event, context):
    print(f"Received event keys: {list(event.keys())}")
    
    try:
        session_id = event.get('session_id')
        evaluation_id = event.get('evaluation_id')
        pillar_results_raw = event.get('pillar_results', [])
        started_at = event.get('timestamp')
        
        if not session_id or not evaluation_id:
            raise ValueError("Missing session_id or evaluation_id")
        
        table = dynamodb.Table(EVALUATIONS_TABLE)
        pillars_list = ['security', 'performance', 'cost', 'reliability', 'operational_excellence', 'sustainability']
        
        # Read full pillar data from DynamoDB (compressed by unified_handler)
        pillar_results = []
        for pillar_name in pillars_list:
            pillar_key = f'{evaluation_id}#pillar#{pillar_name}'
            try:
                response = table.get_item(Key={
                    'session_id': session_id,
                    'evaluation_id': pillar_key
                })
                if 'Item' in response:
                    item = response['Item']
                    
                    # Try compressed format first
                    compressed_b64 = item.get('compressed_data')
                    if compressed_b64:
                        compressed = base64.b64decode(compressed_b64)
                        decompressed = gzip.decompress(compressed)
                        pillar_data = json.loads(decompressed.decode('utf-8'))
                        print(f"Loaded {pillar_name}: {item.get('data_size', '?')} bytes (compressed: {item.get('compressed_size', '?')})")
                    else:
                        # Fallback to uncompressed pillar_data
                        pillar_data = item.get('pillar_data', {})
                        pillar_data = json.loads(json.dumps(pillar_data, cls=DecimalEncoder))
                        print(f"Loaded {pillar_name} (uncompressed)")
                    
                    pillar_results.append(pillar_data)
                    
                    # Clean up temporary item
                    try:
                        table.delete_item(Key={'session_id': session_id, 'evaluation_id': pillar_key})
                    except Exception:
                        pass
                else:
                    print(f"No DynamoDB data for {pillar_name}")
            except Exception as e:
                print(f"Error reading {pillar_name}: {str(e)}")
        
        # Fallback to Step Functions payload if DynamoDB read failed
        if len(pillar_results) == 0:
            print("Falling back to Step Functions payload")
            for result in pillar_results_raw:
                if isinstance(result, dict):
                    if 'statusCode' in result and 'body' in result:
                        body = result['body']
                        if isinstance(body, str):
                            body = json.loads(body)
                        pillar_results.append(body)
                    elif 'pillar_id' in result:
                        pillar_results.append(result)
        
        print(f"Total pillar results: {len(pillar_results)}")
        for p in pillar_results:
            if isinstance(p, dict):
                has_questions = 'questions' in p and len(p.get('questions', [])) > 0
                print(f"  {p.get('pillar_id', '?')}: score={p.get('overall_score', '?')}, has_questions={has_questions}")
        
        # Save final result
        results_json = json.dumps(pillar_results, cls=DecimalEncoder)
        
        # If results are too large for DynamoDB (>400KB), compress
        if len(results_json) > 350000:
            compressed = gzip.compress(results_json.encode('utf-8'))
            results_stored = base64.b64encode(compressed).decode('utf-8')
            is_compressed = True
            print(f"Results compressed: {len(results_json)} -> {len(results_stored)} bytes")
        else:
            results_stored = results_json
            is_compressed = False
        
        item = {
            'session_id': session_id,
            'evaluation_id': evaluation_id,
            'status': 'COMPLETED',
            'started_at': started_at,
            'completed_at': datetime.utcnow().isoformat(),
            'results': results_stored,
            'results_compressed': is_compressed,
            'progress': {
                'security': 'COMPLETED', 'performance': 'COMPLETED',
                'cost': 'COMPLETED', 'reliability': 'COMPLETED',
                'operational_excellence': 'COMPLETED', 'sustainability': 'COMPLETED'
            }
        }
        
        table.put_item(Item=item)
        print(f"Saved evaluation {evaluation_id} ({len(pillar_results)} pillars)")
        
        return {'statusCode': 200, 'body': json.dumps({'message': 'Results saved successfully'})}
        
    except Exception as e:
        print(f'Error: {str(e)}')
        import traceback; traceback.print_exc()
        raise e
