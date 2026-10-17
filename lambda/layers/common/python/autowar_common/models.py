"""
Data models for AutoWAR
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Literal


# Type aliases for validation
Status = Literal["COMPLIANT", "NON_COMPLIANT", "PENDING_REVIEW"]
Severity = Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"]


@dataclass
class AWSCredentials:
    """AWS credentials for evaluation"""
    access_key_id: str
    secret_access_key: str
    account_id: str
    region: str
    session_token: Optional[str] = None


@dataclass
class Finding:
    """
    Finding from Best Practice evaluation.
    
    Requirements: 3.3, 3.4, 3.5, 9.1, 9.3, 9.4, 9.5
    """
    bp: str  # Best Practice ID (e.g., "SEC01-BP01")
    description: str  # BP description
    status: Status
    severity: Severity
    finding: str  # Description of the finding
    evidence: str  # Technical evidence (ARNs, IDs, configs)
    remediation: str  # Recommended action
    risk: str  # Risk description
    
    def __post_init__(self):
        """Validate enum values and non-empty strings"""
        # Validate status enum
        valid_statuses = ["COMPLIANT", "NON_COMPLIANT", "PENDING_REVIEW"]
        if self.status not in valid_statuses:
            raise ValueError(f"Invalid status: {self.status}. Must be one of {valid_statuses}")
        
        # Validate severity enum
        valid_severities = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
        if self.severity not in valid_severities:
            raise ValueError(f"Invalid severity: {self.severity}. Must be one of {valid_severities}")
        
        # Validate non-empty strings
        if not self.bp or not self.bp.strip():
            raise ValueError("bp cannot be empty")
        if not self.description or not self.description.strip():
            raise ValueError("description cannot be empty")
        if not self.finding or not self.finding.strip():
            raise ValueError("finding cannot be empty")
        if not self.evidence or not self.evidence.strip():
            raise ValueError("evidence cannot be empty")
        if not self.remediation or not self.remediation.strip():
            raise ValueError("remediation cannot be empty")
        if not self.risk or not self.risk.strip():
            raise ValueError("risk cannot be empty")
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)


@dataclass
class Question:
    """
    Question from a pillar with associated findings.
    
    Requirements: 2.7, 7.2, 9.6
    """
    question_id: str  # Question ID (e.g., "SEC01", "REL02")
    title: Dict[str, str]  # {"es": "...", "en": "..."}
    description: Dict[str, str]  # {"es": "...", "en": "..."}
    score: float  # 0-100
    bps_evaluated: int
    status: Status
    findings: List[Finding] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate question data"""
        # Validate status enum
        valid_statuses = ["COMPLIANT", "NON_COMPLIANT", "PENDING_REVIEW"]
        if self.status not in valid_statuses:
            raise ValueError(f"Invalid status: {self.status}. Must be one of {valid_statuses}")
        
        # Validate score range
        if not (0.0 <= self.score <= 100.0):
            raise ValueError(f"Score must be between 0 and 100, got {self.score}")
        
        # Validate bps_evaluated
        if self.bps_evaluated < 0:
            raise ValueError(f"bps_evaluated must be non-negative, got {self.bps_evaluated}")
        
        # Validate bilingual content
        if not isinstance(self.title, dict) or 'es' not in self.title or 'en' not in self.title:
            raise ValueError("title must be a dict with 'es' and 'en' keys")
        if not isinstance(self.description, dict) or 'es' not in self.description or 'en' not in self.description:
            raise ValueError("description must be a dict with 'es' and 'en' keys")
        
        # Validate non-empty strings
        if not self.question_id or not self.question_id.strip():
            raise ValueError("question_id cannot be empty")
        if not self.title['es'].strip() or not self.title['en'].strip():
            raise ValueError("title translations cannot be empty")
        if not self.description['es'].strip() or not self.description['en'].strip():
            raise ValueError("description translations cannot be empty")
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        # Convert Finding objects to dicts
        data['findings'] = [f.to_dict() if hasattr(f, 'to_dict') else f for f in self.findings]
        return data


@dataclass
class Pillar:
    """
    Pillar evaluation result with all questions and findings.
    
    Requirements: 1.2, 7.1
    """
    pillar_id: str  # "security", "reliability", etc.
    region: str  # Single region (e.g., "us-east-1")
    pillar_name: Dict[str, str]  # {"es": "Seguridad", "en": "Security"}
    description: Dict[str, str]  # {"es": "...", "en": "..."}
    overall_score: float  # 0-100
    total_findings: int
    total_best_practices: int
    timestamp: str  # ISO 8601
    questions: List[Question]
    compliance_distribution: Dict[str, int]  # {"compliant": 10, "non_compliant": 5, "pending_review": 3}
    severity_distribution: Dict[str, int]  # {"critical": 2, "high": 5, "medium": 8, "low": 3}
    regions: Optional[List[str]] = None  # Multi-region support
    multi_region: bool = False
    
    def __post_init__(self):
        """Validate pillar data"""
        # Validate score range
        if not (0.0 <= self.overall_score <= 100.0):
            raise ValueError(f"overall_score must be between 0 and 100, got {self.overall_score}")
        
        # Validate counts
        if self.total_findings < 0:
            raise ValueError(f"total_findings must be non-negative, got {self.total_findings}")
        if self.total_best_practices < 0:
            raise ValueError(f"total_best_practices must be non-negative, got {self.total_best_practices}")
        
        # Validate bilingual content
        if not isinstance(self.pillar_name, dict) or 'es' not in self.pillar_name or 'en' not in self.pillar_name:
            raise ValueError("pillar_name must be a dict with 'es' and 'en' keys")
        if not isinstance(self.description, dict) or 'es' not in self.description or 'en' not in self.description:
            raise ValueError("description must be a dict with 'es' and 'en' keys")
        
        # Validate non-empty strings
        if not self.pillar_id or not self.pillar_id.strip():
            raise ValueError("pillar_id cannot be empty")
        if not self.region or not self.region.strip():
            raise ValueError("region cannot be empty")
        if not self.timestamp or not self.timestamp.strip():
            raise ValueError("timestamp cannot be empty")
        if not self.pillar_name['es'].strip() or not self.pillar_name['en'].strip():
            raise ValueError("pillar_name translations cannot be empty")
        if not self.description['es'].strip() or not self.description['en'].strip():
            raise ValueError("description translations cannot be empty")
        
        # Validate distributions
        if not isinstance(self.compliance_distribution, dict):
            raise ValueError("compliance_distribution must be a dict")
        if not isinstance(self.severity_distribution, dict):
            raise ValueError("severity_distribution must be a dict")
        
        # Validate multi-region consistency
        if self.multi_region and not self.regions:
            raise ValueError("regions must be provided when multi_region is True")
        if self.regions and not self.multi_region:
            self.multi_region = True  # Auto-correct
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        # Convert Question objects to dicts
        data['questions'] = [q.to_dict() if hasattr(q, 'to_dict') else q for q in self.questions]
        return data
