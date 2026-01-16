import time
import uuid
import json
from typing import List, Optional, Dict, Any
from boto3.dynamodb.conditions import Key
from .aws_connector import get_table
from .models import EvaluationIn
from .validators import run_validators_for_evaluation
import boto3
import os

SQS_QUEUE_URL = os.getenv("AUTOWAR_EVAL_QUEUE_URL")

_sqs = None


def _get_sqs():
    global _sqs
    if _sqs is None:
        _sqs = boto3.client("sqs")
    return _sqs


TABLE_NAME = "autowar-evaluations"


def create_evaluation(data: EvaluationIn) -> Dict[str, Any]:
    evaluation_id = str(uuid.uuid4())
    ts = int(time.time())
    item = data.dict()
    item.update(
        {
            "id": evaluation_id,
            "evaluationId": evaluation_id,
            "created_at": ts,
            "status": "PENDING",
        }
    )
    table = get_table(TABLE_NAME)
    table.put_item(Item=item)
    # Enqueue evaluation for asynchronous processing if queue URL configured
    try:
        if SQS_QUEUE_URL:
            sqs = _get_sqs()
            payload = {"evaluationId": evaluation_id, "item": item}
            sqs.send_message(QueueUrl=SQS_QUEUE_URL, MessageBody=json.dumps(payload))
        else:
            # fallback to synchronous validators if no queue configured
            targets = item.get("targets")
            results = run_validators_for_evaluation(
                targets or [],
                region=item.get("region"),
                account_id=item.get("account_id"),
            )
            if results:
                item["results"] = results
                item["status"] = "COMPLETED"
                table.put_item(Item=item)
    except Exception:
        # leave as PENDING if enqueue or validators fail
        pass
    return item


def get_evaluation(evaluation_id: str) -> Optional[Dict[str, Any]]:
    table = get_table(TABLE_NAME)
    resp = table.get_item(Key={"id": evaluation_id})
    return resp.get("Item")


def list_evaluations_for_client(client_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    table = get_table(TABLE_NAME)
    try:
        resp = table.query(
            IndexName="clientIndex",
            KeyConditionExpression=Key("client_id").eq(client_id),
            Limit=limit,
            ScanIndexForward=False,
        )
        return resp.get("Items", [])
    except Exception:
        # fallback to scan (less efficient) if index not present
        resp = table.scan(FilterExpression=Key("client_id").eq(client_id), Limit=limit)
        return resp.get("Items", [])
