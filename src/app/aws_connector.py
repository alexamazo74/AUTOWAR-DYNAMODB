import os
import boto3
from boto3.dynamodb.conditions import Key
from typing import List, Dict, Any

AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')

_dynamo_resource = None

def _get_resource():
    global _dynamo_resource
    if _dynamo_resource is None:
        _dynamo_resource = boto3.resource('dynamodb', region_name=AWS_REGION)
    return _dynamo_resource

def get_table(table_name: str):
    """Return a DynamoDB Table resource for the given table name."""
    resource = _get_resource()
    return resource.Table(table_name)

class AWSConnector:
    """Connector for AWS services"""

    def __init__(self):
        self.region = AWS_REGION

    async def get_resources_by_service(self, service: str) -> List[Dict[str, Any]]:
        """Mock implementation - in real implementation would query AWS APIs"""
        # For testing, return mock data
        if service == 'iam':
            return [
                {
                    'service': 'iam',
                    'type': 'user',
                    'user_name': 'test-user',
                    'access_keys': [],
                    'mfa_enabled': True
                },
                {
                    'service': 'iam',
                    'type': 'role',
                    'role_name': 'test-role'
                }
            ]
        elif service == 'cloudtrail':
            return [
                {
                    'service': 'cloudtrail',
                    'trail_name': 'test-trail',
                    'is_logging': True,
                    'is_multi_region_trail': True
                }
            ]
        return []
def get_item(table_name: str, item_id: str):
    table = get_table(table_name)
    resp = table.get_item(Key={'id': item_id})
    return resp.get('Item')
