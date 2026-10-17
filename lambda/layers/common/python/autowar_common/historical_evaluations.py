"""
Historical Evaluations DynamoDB Operations
Provides helper functions for storing and retrieving historical evaluations
"""

import os
import boto3
from datetime import datetime
from typing import List, Dict, Optional
from decimal import Decimal
import json

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb')
TABLE_NAME = os.environ.get('HISTORICAL_TABLE', 'AutoWAR-Evaluations')


def decimal_to_float(obj):
    """Convert Decimal objects to float for JSON serialization"""
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: decimal_to_float(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [decimal_to_float(item) for item in obj]
    return obj


def float_to_decimal(obj):
    """Convert float objects to Decimal for DynamoDB storage"""
    if isinstance(obj, float):
        return Decimal(str(obj))
    elif isinstance(obj, dict):
        return {k: float_to_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [float_to_decimal(item) for item in obj]
    return obj


def put_evaluation(account_id: str, evaluation_data: dict) -> dict:
    """
    Store an evaluation in DynamoDB
    
    Args:
        account_id: AWS account ID
        evaluation_data: Complete evaluation data including pillarScores, bestPractices, metadata
    
    Returns:
        dict: Stored item with accountId and timestamp
    
    Requirements: 1.4, 1.5, 8.3
    """
    table = dynamodb.Table(TABLE_NAME)
    
    # Generate timestamp
    timestamp = datetime.utcnow().isoformat() + 'Z'
    
    # Prepare item
    item = {
        'accountId': account_id,
        'timestamp': timestamp,
        **float_to_decimal(evaluation_data)
    }
    
    # Store in DynamoDB
    table.put_item(Item=item)
    
    return {
        'accountId': account_id,
        'timestamp': timestamp
    }


def get_evaluation(account_id: str, timestamp: str) -> Optional[dict]:
    """
    Retrieve a specific evaluation from DynamoDB
    
    Args:
        account_id: AWS account ID
        timestamp: Evaluation timestamp (ISO 8601)
    
    Returns:
        dict: Evaluation data or None if not found
    
    Requirements: 2.4, 8.3
    """
    table = dynamodb.Table(TABLE_NAME)
    
    response = table.get_item(
        Key={
            'accountId': account_id,
            'timestamp': timestamp
        }
    )
    
    item = response.get('Item')
    if item:
        return decimal_to_float(item)
    return None


def get_most_recent_evaluation(account_id: str) -> Optional[dict]:
    """
    Retrieve the most recent evaluation for an account
    
    Args:
        account_id: AWS account ID
    
    Returns:
        dict: Most recent evaluation data or None if not found
    
    Requirements: 1.3
    """
    table = dynamodb.Table(TABLE_NAME)
    
    response = table.query(
        KeyConditionExpression='accountId = :account_id',
        ExpressionAttributeValues={
            ':account_id': account_id
        },
        ScanIndexForward=False,  # Descending order (most recent first)
        Limit=1
    )
    
    items = response.get('Items', [])
    if items:
        return decimal_to_float(items[0])
    return None


def query_evaluations(
    account_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> List[dict]:
    """
    Query evaluations for an account with optional date range filtering
    
    Args:
        account_id: AWS account ID
        start_date: Optional start date (ISO 8601)
        end_date: Optional end date (ISO 8601)
    
    Returns:
        list: List of evaluations ordered by timestamp descending
    
    Requirements: 2.1, 2.2, 2.3
    """
    table = dynamodb.Table(TABLE_NAME)
    
    # Build query expression
    key_condition = 'accountId = :account_id'
    expression_values = {':account_id': account_id}
    
    if start_date and end_date:
        key_condition += ' AND #ts BETWEEN :start_date AND :end_date'
        expression_values[':start_date'] = start_date
        expression_values[':end_date'] = end_date
    elif start_date:
        key_condition += ' AND #ts >= :start_date'
        expression_values[':start_date'] = start_date
    elif end_date:
        key_condition += ' AND #ts <= :end_date'
        expression_values[':end_date'] = end_date
    
    query_params = {
        'KeyConditionExpression': key_condition,
        'ExpressionAttributeValues': expression_values,
        'ScanIndexForward': False  # Descending order
    }
    
    # Add ExpressionAttributeNames if timestamp filtering is used
    if start_date or end_date:
        query_params['ExpressionAttributeNames'] = {'#ts': 'timestamp'}
    
    response = table.query(**query_params)
    
    items = response.get('Items', [])
    return [decimal_to_float(item) for item in items]
