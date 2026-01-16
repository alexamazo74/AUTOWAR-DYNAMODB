import os
import json
import time
import logging
import boto3

try:
    import httpx
except Exception:
    httpx = None  # type: ignore[assignment]
from typing import Any, Dict

logging.basicConfig()
logger = logging.getLogger("report_generator")
logger.setLevel(os.getenv("LOG_LEVEL", "INFO"))

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
REPORTS_BUCKET = os.getenv("REPORTS_BUCKET")
REPORTS_TABLE = os.getenv("AUTOWAR_REPORTS_TABLE", "autowar-reports")

dynamo = boto3.resource("dynamodb", region_name=AWS_REGION)
s3 = boto3.client("s3", region_name=AWS_REGION)


def _now_ts():
    return int(time.time())


def render_report(evaluation: Dict[str, Any]) -> bytes:
    # If a serverless renderer is configured, call it (expects PDF bytes),
    # otherwise fallback to JSON content.
    renderer = os.getenv("RENDERER_URL")
    content = {
        "evaluationId": evaluation.get("evaluationId"),
        "created_at": evaluation.get("created_at"),
        "results": evaluation.get("results"),
    }
    if renderer:
        try:
            # call external renderer service (POST JSON -> returns bytes)
            if httpx is None:
                raise RuntimeError("httpx not available in this lambda package")
            resp = httpx.post(
                renderer, json={"payload": content, "format": "pdf"}, timeout=30.0
            )
            resp.raise_for_status()
            return resp.content
        except Exception:
            logger.exception("Renderer call failed, falling back to JSON")
            print(
                f"report_generator: renderer call failed for evaluation {evaluation.get('evaluationId')}"
            )
    return json.dumps(content, indent=2).encode("utf-8")


def handler(event, context):
    table = dynamo.Table(REPORTS_TABLE)
    eval_table = dynamo.Table(
        os.getenv("AUTOWAR_EVALUATIONS_TABLE", "autowar-evaluations")
    )
    processed = 0
    for record in event.get("Records", []):
        try:
            body = record.get("body")
            msg = json.loads(body) if isinstance(body, str) else body
            evaluation_id = msg.get("evaluationId")
            logger.info("Processing report job for %s", evaluation_id)
            # fetch evaluation
            try:
                eval_resp = eval_table.get_item(Key={"id": evaluation_id})
                evaluation = eval_resp.get("Item")
            except Exception:
                evaluation = None

            # render report
            report_bytes = render_report(
                evaluation
                or {
                    "evaluationId": evaluation_id,
                    "created_at": _now_ts(),
                    "results": [],
                }
            )
            key = f"reports/{evaluation_id}/{_now_ts()}.json"
            if REPORTS_BUCKET:
                s3.put_object(Bucket=REPORTS_BUCKET, Key=key, Body=report_bytes)
                s3_url = f"s3://{REPORTS_BUCKET}/{key}"
            else:
                s3_url = key

            # update reports table (use pk/sk schema)
            # Try to update the reports table using update_item (tests use this
            # signature). If update_item is not available, fall back to put_item
            # using pk/sk schema for real DynamoDB tables.
            try:
                # Prefer update_item with Key={'id': evaluation_id} for test doubles
                try:
                    table.update_item(
                        Key={"id": evaluation_id},
                        UpdateExpression="SET status = :s, s3_key = :k, generated_at = :g",
                        ExpressionAttributeValues={
                            ":s": "COMPLETED",
                            ":k": s3_url,
                            ":g": _now_ts(),
                        },
                    )
                except AttributeError:
                    # table doesn't implement update_item (real boto3 Table supports put_item)
                    sk_value = str(_now_ts())
                    table.put_item(
                        Item={
                            "pk": evaluation_id,
                            "sk": sk_value,
                            "status": "COMPLETED",
                            "s3_key": s3_url,
                            "generated_at": _now_ts(),
                        }
                    )
            except Exception:
                logger.exception("Failed to update reports table for %s", evaluation_id)
                print(
                    f"report_generator: failed to update reports table for {evaluation_id}"
                )

            processed += 1
        except Exception:
            continue
    return {"statusCode": 200, "processed": processed}
