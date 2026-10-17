"""
Evaluation Status Lambda
Returns the current status of an async evaluation
"""

import json
import os
import boto3
import gzip
import base64

dynamodb = boto3.resource('dynamodb')
EVALUATIONS_TABLE = os.environ.get('EVALUATIONS_TABLE')

def lambda_handler(event, context):
    cors_headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,X-Session-ID',
        'Access-Control-Allow-Methods': 'GET,OPTIONS'
    }
    
    try:
        session_id = event.get('headers', {}).get('X-Session-ID') or \
                    event.get('headers', {}).get('x-session-id')
        
        if not session_id:
            return {'statusCode': 400, 'headers': cors_headers,
                    'body': json.dumps({'error': 'Missing X-Session-ID header'})}
        
        evaluation_id = event.get('pathParameters', {}).get('evaluation_id')
        if not evaluation_id:
            return {'statusCode': 400, 'headers': cors_headers,
                    'body': json.dumps({'error': 'Missing evaluation_id'})}
        
        table = dynamodb.Table(EVALUATIONS_TABLE)
        response = table.get_item(Key={'session_id': session_id, 'evaluation_id': evaluation_id})
        
        if 'Item' not in response:
            return {'statusCode': 404, 'headers': cors_headers,
                    'body': json.dumps({'error': 'Evaluation not found'})}
        
        item = response['Item']
        status = item.get('status', 'UNKNOWN')
        
        # Check Step Functions execution if still in progress
        if status == 'IN_PROGRESS' and item.get('execution_arn'):
            try:
                sfn_client = boto3.client('stepfunctions')
                execution = sfn_client.describe_execution(executionArn=item['execution_arn'])
                sfn_status = execution.get('status', '')
                if sfn_status in ('FAILED', 'TIMED_OUT', 'ABORTED'):
                    table.update_item(
                        Key={'session_id': session_id, 'evaluation_id': evaluation_id},
                        UpdateExpression='SET #s = :s',
                        ExpressionAttributeNames={'#s': 'status'},
                        ExpressionAttributeValues={':s': 'FAILED'}
                    )
                    status = 'FAILED'
            except Exception as e:
                print(f"Could not check Step Functions: {str(e)}")
        
        # Decompress results if needed
        results = item.get('results')
        if item.get('results_compressed') and results:
            try:
                compressed = base64.b64decode(results)
                decompressed = gzip.decompress(compressed)
                results = decompressed.decode('utf-8')
            except Exception as e:
                print(f"Error decompressing results: {str(e)}")
        
        result = {
            'evaluation_id': evaluation_id,
            'status': status,
            'started_at': item.get('started_at'),
            'completed_at': item.get('completed_at'),
            'progress': item.get('progress', {}),
            'results': results
        }
        
        return {'statusCode': 200, 'headers': cors_headers, 'body': json.dumps(result)}
        
    except Exception as e:
        print(f'Error: {str(e)}')
        import traceback; traceback.print_exc()
        return {'statusCode': 500, 'headers': cors_headers,
                'body': json.dumps({'error': str(e)})}
