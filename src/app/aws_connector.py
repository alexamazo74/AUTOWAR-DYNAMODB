import os
import boto3

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

_dynamo_resource = None


def _get_resource():
    global _dynamo_resource
    if _dynamo_resource is None:
        _dynamo_resource = boto3.resource("dynamodb", region_name=AWS_REGION)
    return _dynamo_resource


def get_table(table_name: str):
    """Return a DynamoDB Table resource for the given table name."""
    resource = _get_resource()
    return resource.Table(table_name)


# Simple helper for reading an item by id
def get_item(table_name: str, item_id: str):
    table = get_table(table_name)
    resp = table.get_item(Key={"id": item_id})
    return resp.get("Item")
