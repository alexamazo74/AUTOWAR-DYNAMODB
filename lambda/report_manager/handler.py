"""
Report Manager Lambda
Handles report generation requests and evaluation queries
"""

import json
import logging
import os
import boto3
from autowar_common.historical_evaluations import query_evaluations, get_evaluation

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize Lambda client
lambda_client = boto3.client('lambda')


def lambda_handler(event, context):
    """
    Routes to appropriate handler based on HTTP method and path
    
    GET /reports/list - List evaluations
    POST /reports/generate - Generate report
    """
    try:
        http_method = event.get('httpMethod', 'GET')
        path = event.get('path', '')
        
        cors_headers = {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
        }
        
        # Handle OPTIONS for CORS
        if http_method == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': cors_headers,
                'body': ''
            }
        
        # Route to appropriate handler
        if http_method == 'GET' and 'list' in path:
            return handle_list_evaluations(event, cors_headers)
        elif http_method == 'POST' and 'generate' in path:
            return handle_generate_report(event, cors_headers)
        else:
            return {
                'statusCode': 404,
                'headers': cors_headers,
                'body': json.dumps({'error': 'Not found'})
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


def handle_list_evaluations(event, cors_headers):
    """
    Handle GET /reports/list
    Query parameters: accountId, startDate (optional), endDate (optional)
    """
    try:
        # Get query parameters
        params = event.get('queryStringParameters', {}) or {}
        account_id = params.get('accountId')
        start_date = params.get('startDate')
        end_date = params.get('endDate')
        
        if not account_id:
            return {
                'statusCode': 400,
                'headers': cors_headers,
                'body': json.dumps({'error': 'accountId is required'})
            }
        
        logger.info(f"Listing evaluations for account: {account_id}")
        
        # Query evaluations
        evaluations = query_evaluations(account_id, start_date, end_date)
        
        # Format response (return summary info only)
        evaluations_summary = []
        for evaluation in evaluations:
            evaluations_summary.append({
                'accountId': evaluation.get('accountId'),
                'timestamp': evaluation.get('timestamp'),
                'pillarScores': evaluation.get('pillarScores', {}),
                'totalBestPractices': evaluation.get('metadata', {}).get('totalBestPractices', 0),
                'totalFindings': evaluation.get('metadata', {}).get('totalFindings', 0)
            })
        
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps({
                'evaluations': evaluations_summary
            })
        }
        
    except Exception as e:
        logger.error(f"Error listing evaluations: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': cors_headers,
            'body': json.dumps({
                'error': 'Failed to list evaluations',
                'message': str(e)
            })
        }


def handle_generate_report(event, cors_headers):
    """
    Handle POST /reports/generate
    Body: {accountId, evaluationTimestamp, pilares, reportType}
    """
    try:
        # Parse request body
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', {})
        
        account_id = body.get('accountId')
        evaluation_timestamp = body.get('evaluationTimestamp')
        pilares = body.get('pilares', [])
        report_type = body.get('reportType')
        
        # Validate request
        if not account_id:
            return {
                'statusCode': 400,
                'headers': cors_headers,
                'body': json.dumps({'error': 'accountId is required'})
            }
        
        if not evaluation_timestamp:
            return {
                'statusCode': 400,
                'headers': cors_headers,
                'body': json.dumps({'error': 'evaluationTimestamp is required'})
            }
        
        if not pilares or len(pilares) == 0:
            return {
                'statusCode': 400,
                'headers': cors_headers,
                'body': json.dumps({'error': 'At least one pilar must be selected'})
            }
        
        if report_type not in ['executive', 'technical']:
            return {
                'statusCode': 400,
                'headers': cors_headers,
                'body': json.dumps({'error': 'reportType must be "executive" or "technical"'})
            }
        
        logger.info(f"Generating {report_type} report for account {account_id}, evaluation {evaluation_timestamp}")
        
        # Retrieve evaluation data
        evaluation_data = get_evaluation(account_id, evaluation_timestamp)
        
        if not evaluation_data:
            return {
                'statusCode': 404,
                'headers': cors_headers,
                'body': json.dumps({'error': 'Evaluation not found'})
            }
        
        # Prepare payload for report generator
        payload = {
            'accountId': account_id,
            'evaluationTimestamp': evaluation_timestamp,
            'evaluationData': evaluation_data,
            'selectedPilares': pilares
        }
        
        # Determine which Lambda to invoke
        function_name = os.environ.get('TECHNICAL_REPORT_FUNCTION') if report_type == 'technical' else os.environ.get('EXECUTIVE_REPORT_FUNCTION')
        
        # Invoke report generator Lambda
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        
        # Parse response
        response_payload = json.loads(response['Payload'].read())
        
        if response['StatusCode'] != 200:
            raise Exception(f"Report generator failed: {response_payload}")
        
        # Extract result from response body
        result_body = json.loads(response_payload.get('body', '{}'))
        
        # Si el generador no devolvio una URL firmada el reporte fallo (p.ej.
        # el generador reviento y devolvio 500 con un mensaje de error). En ese
        # caso devolvemos un 500 real con el mensaje del generador, en vez de un
        # 200 con reportUrl null que confunde al frontend.
        if not result_body.get('signedUrl'):
            error_message = (
                result_body.get('message')
                or result_body.get('error')
                or 'Generador no devolvió URL'
            )
            logger.error(f"Report generator did not return a signedUrl: {error_message}")
            return {
                'statusCode': 500,
                'headers': cors_headers,
                'body': json.dumps({
                    'error': 'Failed to generate report',
                    'message': error_message
                })
            }
        
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps({
                'reportUrl': result_body.get('signedUrl'),
                'expiresIn': result_body.get('expiresIn', 3600),
                'reportKey': result_body.get('s3Key')
            })
        }
        
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': cors_headers,
            'body': json.dumps({
                'error': 'Failed to generate report',
                'message': str(e)
            })
        }
