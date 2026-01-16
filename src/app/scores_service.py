import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, List, Dict, Optional
from .aws_connector import get_table
from boto3.dynamodb.conditions import Key, Attr

SCORES_TABLE = "autowar-scores"


def _to_decimal_safe(v: Any) -> Any:
    try:
        return Decimal(str(v))
    except Exception:
        return v


def create_score(payload: Any) -> Dict[str, Any]:
    table = get_table(SCORES_TABLE)
    sid = str(uuid.uuid4())
    total = Decimal("0")
    scores_serialized = {}
    # compute simple total if possible and coerce numbers to Decimal for DynamoDB
    try:
        vals = []
        for k, val in payload.scores.items():
            d = _to_decimal_safe(val)
            scores_serialized[k] = d
            if isinstance(d, Decimal):
                vals.append(d)
        if vals:
            total = sum(vals, Decimal("0"))
    except Exception:
        total = Decimal("0")

    item: Dict[str, Any] = {
        "id": sid,
        "evaluation_id": payload.evaluation_id,
        "bp_id": payload.bp_id,
        "scores": scores_serialized,
        "total": total,
        "created_at": datetime.utcnow().isoformat(),
    }
    table.put_item(Item=item)
    # Convert Decimal total back to float for API responses
    resp_item: Dict[str, Any] = dict(item)
    try:
        resp_item["total"] = float(item["total"])
    except Exception:
        pass
    return resp_item


def get_score(score_id: str) -> Optional[Dict[str, Any]]:
    table = get_table(SCORES_TABLE)
    resp = table.get_item(Key={"id": score_id})
    item = resp.get("Item")
    if item and "total" in item:
        try:
            item["total"] = float(item["total"])
        except Exception:
            pass
    return item


def list_scores_for_evaluation(
    evaluation_id: str, limit: int = 50
) -> List[Dict[str, Any]]:
    table = get_table(SCORES_TABLE)
    # Prefer query against the GSI named 'evaluationIndex', fallback to scan
    try:
        resp = table.query(
            IndexName="evaluationIndex",
            KeyConditionExpression=Key("evaluation_id").eq(evaluation_id),
            Limit=limit,
        )
        items = resp.get("Items", [])
    except Exception:
        resp = table.scan(
            FilterExpression=Attr("evaluation_id").eq(evaluation_id), Limit=limit
        )
        items = resp.get("Items", [])

    # normalize totals
    for it in items:
        if "total" in it:
            try:
                it["total"] = float(it["total"])
            except Exception:
                pass
    return items[:limit]
