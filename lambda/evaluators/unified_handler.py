"""
Unified Evaluator Handler
Routes to appropriate pillar evaluator
"""

import json
import sys
import os
import importlib.util
import boto3
import gzip
import base64

def lambda_handler(event, context):
    """Routes to appropriate pillar evaluator"""
    
    # Get pillar from path
    pillar = event.get('pathParameters', {}).get('pillar', 'security')
    
    # Check if called from Step Functions (has evaluation_id in body)
    is_step_functions = False
    evaluation_id = None
    session_id_from_event = None
    try:
        body_str = event.get('body', '{}')
        if isinstance(body_str, str) and body_str:
            body_data = json.loads(body_str)
            evaluation_id = body_data.get('evaluation_id')
            session_id_from_event = body_data.get('session_id')
            is_step_functions = evaluation_id is not None
    except (json.JSONDecodeError, TypeError):
        pass
    
    cors_headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,X-Session-ID',
        'Access-Control-Allow-Methods': 'POST,OPTIONS'
    }
    
    try:
        base_dir = os.path.dirname(__file__)
        pillar_dir = os.path.join(base_dir, pillar)
        handler_path = os.path.join(pillar_dir, 'handler.py')
        
        if not os.path.exists(handler_path):
            return {'statusCode': 404, 'headers': cors_headers,
                    'body': json.dumps({'error': f'Pillar {pillar} not implemented'})}
        
        original_sys_path = sys.path.copy()
        
        try:
            sys.path.insert(0, pillar_dir)
            if base_dir not in sys.path:
                sys.path.insert(0, base_dir)
            
            spec = importlib.util.spec_from_file_location(f"{pillar}_handler", handler_path)
            handler_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(handler_module)
            
            result = handler_module.lambda_handler(event, context)
            
            # If called from Step Functions, save full result to S3
            # and return only a small summary to avoid 256KB Step Functions limit
            if is_step_functions and result.get('statusCode') == 200:
                try:
                    table_name = os.environ.get('DYNAMODB_TABLE') or os.environ.get('EVALUATIONS_TABLE')
                    if table_name and evaluation_id and session_id_from_event:
                        full_body = result.get('body', '{}')
                        if isinstance(full_body, str):
                            full_body_parsed = json.loads(full_body)
                        else:
                            full_body_parsed = full_body
                        
                        # Compress and store in DynamoDB as base64-encoded gzip
                        full_json = json.dumps(full_body_parsed, default=str)
                        compressed = gzip.compress(full_json.encode('utf-8'))
                        compressed_b64 = base64.b64encode(compressed).decode('utf-8')
                        
                        dynamodb = boto3.resource('dynamodb')
                        table = dynamodb.Table(table_name)
                        
                        table.put_item(Item={
                            'session_id': session_id_from_event,
                            'evaluation_id': f'{evaluation_id}#pillar#{pillar}',
                            'compressed_data': compressed_b64,
                            'data_size': len(full_json),
                            'compressed_size': len(compressed_b64)
                        })
                        
                        print(f"Saved {pillar}: {len(full_json)} bytes -> {len(compressed_b64)} bytes compressed")
                        
                        # Return small summary for Step Functions
                        summary = {
                            'statusCode': 200,
                            'headers': cors_headers,
                            'body': json.dumps({
                                'pillar_id': full_body_parsed.get('pillar_id', pillar),
                                'overall_score': full_body_parsed.get('overall_score', 0),
                                'total_findings': full_body_parsed.get('total_findings', 0),
                                'total_best_practices': full_body_parsed.get('total_best_practices', 0),
                                'pillar_name': full_body_parsed.get('pillar_name', {}),
                                'compliance_distribution': full_body_parsed.get('compliance_distribution', {}),
                                'severity_distribution': full_body_parsed.get('severity_distribution', {}),
                                'stored_in_dynamodb': True
                            })
                        }
                        return summary
                except Exception as save_err:
                    print(f"Warning: Could not save to DynamoDB: {str(save_err)}")
            
            return result
            
        finally:
            sys.path = original_sys_path
        
    except Exception as e:
        print(f"Error loading pillar {pillar}: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'statusCode': 500, 'headers': cors_headers,
                'body': json.dumps({'error': f'Failed to load pillar: {str(e)}'})}
