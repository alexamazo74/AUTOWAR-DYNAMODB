"""
Store Evaluation Lambda
Stores complete evaluation in historical DynamoDB table
"""

import json
import logging
from autowar_common.historical_evaluations import put_evaluation
from autowar_common.evaluation_builder import build_evaluation_data

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    """
    Store a complete evaluation in DynamoDB
    
    Input:
    {
        "account_id": "...",
        "pillar_results": {
            "security": {...},
            "reliability": {...},
            ...
        }
    }
    
    Output:
    {
        "accountId": "...",
        "timestamp": "ISO 8601"
    }
    """
    try:
        # Parse request body
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', event)
        
        account_id = body.get('account_id')
        pillar_results = body.get('pillar_results', {})
        
        if not account_id:
            raise ValueError("account_id is required")
        
        if not pillar_results:
            raise ValueError("pillar_results is required")
        
        logger.info(f"Storing evaluation for account: {account_id}")
        
        # Build evaluation data
        evaluation_data = build_evaluation_data(pillar_results, account_id)
        
        # Store in DynamoDB
        result = put_evaluation(account_id, evaluation_data)
        
        logger.info(f"Evaluation stored: {result['timestamp']}")
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'status': 'stored',
                **result
            })
        }
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        return {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Invalid request',
                'message': str(e)
            })
        }
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e)
            })
        }
