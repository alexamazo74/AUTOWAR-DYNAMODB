"""
Credential Validator Lambda
Validates AWS credentials and creates session
"""

import json
import logging
import os
from autowar_common.credentials_manager import CredentialsManager
from autowar_common.historical_evaluations import get_most_recent_evaluation

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    """
    Validates AWS credentials and creates temporary session
    
    Input:
    {
        "access_key_id": "...",
        "secret_access_key": "...",
        "session_token": "..." (optional),
        "account_id": "...",
        "region": "...",
        "action": "new_evaluation" | "load_recent" (optional, default: "new_evaluation")
    }
    
    Output:
    {
        "session_id": "uuid",
        "expires_at": "ISO timestamp",
        "account_id": "...",
        "action": "new_evaluation" | "load_recent",
        "evaluation_data": {...} (only if action is "load_recent")
    }
    """
    try:
        # Parse request body
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', event)
        
        # Get action parameter (default to "new_evaluation")
        action = body.get('action', 'new_evaluation')
        
        # Validate action parameter
        if action not in ['new_evaluation', 'load_recent']:
            raise ValueError(f"Invalid action: {action}. Must be 'new_evaluation' or 'load_recent'")
        
        logger.info(f"Validating credentials for account: {body.get('account_id')}, action: {action}")
        
        # Create credentials manager
        manager = CredentialsManager()
        
        # Validate and create session
        session_info = manager.validate_and_create_session(body)
        
        # Get user information from STS
        user_info = manager.get_user_info(body)
        
        logger.info(f"Session created: {session_info['session_id']}")
        
        # Handle action
        response_data = {
            'status': 'validated',
            'action': action,
            'user_info': user_info,
            **session_info
        }
        
        if action == 'load_recent':
            # Query most recent evaluation
            account_id = body.get('account_id')
            evaluation_data = get_most_recent_evaluation(account_id)
            
            if evaluation_data:
                response_data['evaluation_data'] = evaluation_data
                logger.info(f"Loaded recent evaluation for account {account_id}: {evaluation_data.get('timestamp')}")
            else:
                logger.info(f"No recent evaluation found for account {account_id}")
                response_data['evaluation_data'] = None
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(response_data)
        }
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        return {
            'statusCode': 401,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Invalid AWS credentials',
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
