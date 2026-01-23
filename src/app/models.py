from pydantic import BaseModel
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


class EvaluationRequest(BaseModel):
    evaluation_id: str
    question_id: str


class SecurityEvaluation(BaseModel):
    id: str
    evaluation_id: str
    question_id: str
    pillar: str = 'Security'
    scoring: Dict[str, Any]
    validation_results: Dict[str, Any]
    resources_evaluated: List[Dict[str, Any]]
    evaluated_at: str
    status: str


# Nuevos modelos para riesgos y remediación
class RiskAssessment(BaseModel):
    bp_id: str
    severity: str  # 'critical', 'high', 'medium', 'low'
    probability: str  # 'high', 'medium', 'low'
    impact_business: str  # 'high', 'medium', 'low'
    impact_technical: str  # 'high', 'medium', 'low'
    description: str
    affected_resources: List[str]
    mitigation_priority: int  # 1-10
    industry_context: Optional[str] = None


class RemediationStep(BaseModel):
    step_id: str
    bp_id: str
    title: str
    description: str
    effort: str  # 'low', 'medium', 'high'
    impact: str  # 'high', 'medium', 'low'
    time_estimate: str  # 'hours', 'days', 'weeks'
    cost_estimate: Optional[str] = None
    required_skills: List[str]
    validation_criteria: str
    priority: int  # 1-10


class RemediationPlan(BaseModel):
    question_id: str
    total_steps: int
    estimated_effort: str
    estimated_cost: Optional[str] = None
    steps: List[RemediationStep]
    prerequisites: List[str]
    success_criteria: str


class IndustryBenchmark(BaseModel):
    industry: str
    pillar: str
    question_id: str
    bp_id: Optional[str] = None
    average_score: float
    recommended_threshold: float
    risk_multipliers: Dict[str, float]
    last_updated: str


class ClientProfile(BaseModel):
    client_id: str
    name: str
    industry: str
    region: str
    size: str  # 'small', 'medium', 'large', 'enterprise'
    compliance_requirements: List[str]
    risk_tolerance: str  # 'low', 'medium', 'high'
    contact_info: Dict[str, Any]
