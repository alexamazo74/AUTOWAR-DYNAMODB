import os
import json
import boto3
from typing import Any, Dict

from src.app.validators.manager import run_validators_for_evaluation

AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
EVAL_TABLE = os.getenv('AUTOWAR_EVALUATIONS_TABLE', 'autowar-evaluations')
EVIDENCE_TABLE = os.getenv('AUTOWAR_EVIDENCE_TABLE', 'autowar-evidence-technical')
REPORT_QUEUE_URL = os.getenv('AUTOWAR_REPORT_QUEUE_URL')

_sqs = None
def _get_sqs():
    global _sqs
    if _sqs is None:
        _sqs = boto3.client('sqs')
    return _sqs

dynamo = boto3.resource('dynamodb', region_name=AWS_REGION)


def _now_ts():
    import time

    return int(time.time())


def handler(event, context):
    eval_table = dynamo.Table(EVAL_TABLE)
    evidence_table = dynamo.Table(EVIDENCE_TABLE)
    processed = 0
    for record in event.get('Records', []):
        try:
            body = record.get('body')
            if isinstance(body, str):
                msg = json.loads(body)
            else:
                msg = body
            evaluation_id = msg.get('evaluationId') or msg.get('id')
            item = msg.get('item') or msg

            # run validators
            targets = item.get('targets') or []
            results = run_validators_for_evaluation(targets, region=item.get('region'), account_id=item.get('account_id'))

            # persist results into evaluation item
            eval_table.update_item(
                Key={'id': evaluation_id},
                UpdateExpression='SET #s = :s, results = :r, completed_at = :c',
                ExpressionAttributeNames={'#s': 'status'},
                ExpressionAttributeValues={':s': 'COMPLETED', ':r': results, ':c': _now_ts()},
            )

            # write per-target evidence entries
            for r in results:
                evidence_item = {
                    'id': f"{evaluation_id}#{r.get('name')}#{_now_ts()}",
                    'evaluation_id': evaluation_id,
                    'validator': r.get('name'),
                    'resource': r.get('resource'),
                    'status': r.get('status'),
                    'details': r.get('details'),
                    'created_at': _now_ts(),
                }
                try:
                    evidence_table.put_item(Item=evidence_item)
                except Exception:
                    pass

            # persist a minimal report metadata record
            try:
                reports_table = dynamo.Table(os.getenv('AUTOWAR_REPORTS_TABLE', 'autowar-reports'))
                report_item = {
                    'id': evaluation_id,
                    'evaluation_id': evaluation_id,
                    'status': 'PENDING',
                    'created_at': _now_ts(),
                }
                reports_table.put_item(Item=report_item)
            except Exception:
                pass

            # enqueue report generation job if configured
            try:
                if REPORT_QUEUE_URL:
                    sqs = _get_sqs()
                    payload = {'evaluationId': evaluation_id}
                    sqs.send_message(QueueUrl=REPORT_QUEUE_URL, MessageBody=json.dumps(payload))
            except Exception:
                pass

            processed += 1
        except Exception:
            continue

    return {'statusCode': 200, 'processed': processed}
