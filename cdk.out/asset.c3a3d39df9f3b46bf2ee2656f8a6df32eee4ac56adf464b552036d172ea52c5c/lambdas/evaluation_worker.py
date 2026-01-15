import os
import json
import logging
import boto3
from typing import Any, Dict

from app.validators.manager import run_validators_for_evaluation

LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
logging.basicConfig()
logger = logging.getLogger('evaluation_worker')
logger.setLevel(LOG_LEVEL)

AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
EVAL_TABLE = os.getenv('AUTOWAR_EVALUATIONS_TABLE', 'autowar-evaluations')
EVIDENCE_TABLE = os.getenv('AUTOWAR_EVIDENCE_TABLE', 'autowar-evidence-technical')
REPORT_QUEUE_URL = os.getenv('AUTOWAR_REPORT_QUEUE_URL')

_sqs = None
def _get_sqs():
    global _sqs
    if _sqs is None:
        _sqs = boto3.client('sqs', region_name=AWS_REGION)
    return _sqs

dynamo = boto3.resource('dynamodb', region_name=AWS_REGION)


def _now_ts():
    import time

    return int(time.time())


def handler(event, context):
    eval_table = dynamo.Table(EVAL_TABLE)
    evidence_table = dynamo.Table(EVIDENCE_TABLE)
    processed = 0

    logger.info('Handler invoked with %d records', len(event.get('Records', [])))

    for record in event.get('Records', []):
        body = record.get('body')
        try:
            logger.debug('Raw record body: %s', body)
            if isinstance(body, str):
                msg = json.loads(body)
            else:
                msg = body

            logger.info('Processing message: %s', json.dumps(msg if isinstance(msg, dict) else {'id': str(msg)}))

            evaluation_id = msg.get('evaluationId') or msg.get('id')
            item = msg.get('item') or msg

            if not evaluation_id:
                logger.warning('Skipping message with no evaluationId: %s', msg)
                continue

            # run validators
            targets = item.get('targets') or []
            try:
                results = run_validators_for_evaluation(targets, region=item.get('region'), account_id=item.get('account_id'))
            except Exception:
                logger.exception('Validator execution failed for evaluation %s', evaluation_id)
                results = []

            # persist results into evaluation item
            try:
                eval_table.update_item(
                    Key={'id': evaluation_id},
                    UpdateExpression='SET #s = :s, results = :r, completed_at = :c',
                    ExpressionAttributeNames={'#s': 'status'},
                    ExpressionAttributeValues={':s': 'COMPLETED', ':r': results, ':c': _now_ts()},
                )
            except Exception:
                logger.exception('Failed to update evaluation item %s', evaluation_id)

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
                    logger.exception('Failed to write evidence item for %s', evaluation_id)

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
                logger.exception('Failed to write report metadata for %s', evaluation_id)

            # enqueue report generation job if configured
            try:
                if REPORT_QUEUE_URL:
                    sqs = _get_sqs()
                    payload = {'evaluationId': evaluation_id}
                    resp = sqs.send_message(QueueUrl=REPORT_QUEUE_URL, MessageBody=json.dumps(payload))
                    logger.info('Enqueued report job %s for evaluation %s', resp.get('MessageId'), evaluation_id)
                else:
                    logger.debug('No REPORT_QUEUE_URL configured; skipping enqueue for %s', evaluation_id)
            except Exception:
                logger.exception('Failed to enqueue report job for %s', evaluation_id)

            processed += 1
        except Exception:
            logger.exception('Unhandled exception processing record: %s', body)
            continue

    logger.info('Handler completed, processed=%d', processed)
    return {'statusCode': 200, 'processed': processed}
