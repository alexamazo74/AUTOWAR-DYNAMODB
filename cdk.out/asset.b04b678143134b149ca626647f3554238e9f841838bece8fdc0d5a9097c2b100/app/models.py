from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List


class ResourceTarget(BaseModel):
    type: str
    name: str
    extra: Optional[Dict[str, Any]] = None


class EvaluationIn(BaseModel):
    client_id: str
    account_id: Optional[str] = None
    region: Optional[str] = None
    start_ts: Optional[int] = None
    end_ts: Optional[int] = None
    pillar_scores: Optional[Dict[str, float]] = None
    summary: Optional[str] = None
    targets: Optional[List[ResourceTarget]] = None


class EvaluationOut(EvaluationIn):
    evaluationId: str
    created_at: int
    score_total: Optional[float] = None
    status: str = 'PENDING'
