"""
Evaluation Orchestrator Lambda
Initiates Step Functions execution for async evaluation
"""

import json
import os
import boto3
import uuid
from datetime import datetime

stepfunctions = boto3.client('stepfunctions')
dynamodb = boto3.resource('dynamodb')

STATE_MACHINE_ARN = os.environ.get('STATE_MACHINE_ARN')
EVALUATIONS_TABLE = os.environ.get('EVALUATIONS_TABLE')

def lambda_handler(event, context):
    """Start async evaluation via Step Functions"""
    
    cors_headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,X-Session-ID',
        'Access-Control-Allow-Methods': 'POST,OPTIONS'
    }
    
    try:
        # Get session ID from headers
        session_id = event.get('headers', {}).get('X-Session-ID') or \
                    event.get('headers', {}).get('x-session-id')
        
        if not session_id:
            return {
                'statusCode': 400,
                'headers': cors_headers,
                'body': json.dumps({'error': 'Missing X-Session-ID header'})
            }
        
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        
        # Generate evaluation ID
        evaluation_id = str(uuid.uuid4())
        
        # Prepare input for Step Functions
        sf_input = {
            'evaluation_id': evaluation_id,
            'session_id': session_id,
            'regions': body.get('regions', ['us-east-1']),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Start Step Functions execution
        response = stepfunctions.start_execution(
            stateMachineArn=STATE_MACHINE_ARN,
            name=f'eval-{evaluation_id}',
            input=json.dumps(sf_input)
        )
        
        # Store initial status in DynamoDB
        table = dynamodb.Table(EVALUATIONS_TABLE)
        table.put_item(
            Item={
                'session_id': session_id,
                'evaluation_id': evaluation_id,
                'status': 'IN_PROGRESS',
                'started_at': datetime.utcnow().isoformat(),
                'execution_arn': response['executionArn'],
                'progress': {
                    'security': 'IN_PROGRESS',
                    'performance': 'IN_PROGRESS',
                    'cost': 'IN_PROGRESS',
                    'reliability': 'IN_PROGRESS',
                    'operational_excellence': 'IN_PROGRESS',
                    'sustainability': 'IN_PROGRESS'
                },
                'ttl': int(datetime.utcnow().timestamp()) + 86400  # 24 hours
            }
        )
        
        return {
            'statusCode': 202,  # Accepted
            'headers': cors_headers,
            'body': json.dumps({
                'evaluation_id': evaluation_id,
                'status': 'IN_PROGRESS',
                'message': 'Evaluation started successfully'
            })
        }
        
    except Exception as e:
        print(f'Error starting evaluation: {str(e)}')
        import traceback
        traceback.print_exc()
        
        return {
            'statusCode': 500,
            'headers': cors_headers,
            'body': json.dumps({'error': str(e)})
        }
