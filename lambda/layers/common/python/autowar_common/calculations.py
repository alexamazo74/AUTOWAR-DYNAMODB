"""
Score calculation functions for AutoWAR.

Requirements: 2.8, 4.1, 4.2, 4.3, 4.4, 4.5
"""

from typing import List, Dict
from .models import Finding, Question


def calculate_question_score(findings: List[Finding]) -> float:
    """
    Calculate question score as weighted average of finding statuses.
    
    COMPLIANT = 100, NON_COMPLIANT = 0, PENDING_REVIEW = 50
    
    Args:
        findings: List of Finding objects
        
    Returns:
        Score between 0.0 and 100.0, rounded to 2 decimal places
        
    Requirements: 4.2, 4.3
    
    Example:
        >>> findings = [
        ...     Finding(status="COMPLIANT", ...),
        ...     Finding(status="NON_COMPLIANT", ...),
        ...     Finding(status="PENDING_REVIEW", ...)
        ... ]
        >>> calculate_question_score(findings)
        50.0
    """
    if not findings:
        return 0.0
    
    score_map = {
        "COMPLIANT": 100.0,
        "NON_COMPLIANT": 0.0,
        "PENDING_REVIEW": 50.0
    }
    
    total_score = sum(score_map[f.status] for f in findings)
    return round(total_score / len(findings), 2)


def calculate_pillar_score(questions: List[Question]) -> float:
    """
    Calculate pillar score as weighted average of question scores.
    
    Each question is weighted by its number of BPs evaluated.
    
    Args:
        questions: List of Question objects
        
    Returns:
        Score between 0.0 and 100.0, rounded to 2 decimal places
        
    Requirements: 4.1
    
    Example:
        >>> questions = [
        ...     Question(score=80.0, bps_evaluated=5, ...),
        ...     Question(score=60.0, bps_evaluated=3, ...)
        ... ]
        >>> calculate_pillar_score(questions)
        72.5
    """
    if not questions:
        return 0.0
    
    total_weighted_score = sum(q.score * q.bps_evaluated for q in questions)
    total_bps = sum(q.bps_evaluated for q in questions)
    
    if total_bps == 0:
        return 0.0
    
    return round(total_weighted_score / total_bps, 2)


def determine_question_status(findings: List[Finding]) -> str:
    """
    Determine question status based on finding statuses.
    
    Rules:
    - If all findings are COMPLIANT -> COMPLIANT
    - If any finding is NON_COMPLIANT -> NON_COMPLIANT
    - Otherwise -> PENDING_REVIEW
    
    Args:
        findings: List of Finding objects
        
    Returns:
        Status string: "COMPLIANT", "NON_COMPLIANT", or "PENDING_REVIEW"
        
    Requirements: 2.8
    
    Example:
        >>> findings = [Finding(status="COMPLIANT", ...), Finding(status="COMPLIANT", ...)]
        >>> determine_question_status(findings)
        'COMPLIANT'
    """
    if not findings:
        return "PENDING_REVIEW"
    
    statuses = [f.status for f in findings]
    
    # If all compliant
    if all(s == "COMPLIANT" for s in statuses):
        return "COMPLIANT"
    
    # If any non-compliant
    if any(s == "NON_COMPLIANT" for s in statuses):
        return "NON_COMPLIANT"
    
    # Otherwise pending review
    return "PENDING_REVIEW"


def calculate_distributions(questions: List[Question]) -> tuple[Dict[str, int], Dict[str, int]]:
    """
    Calculate compliance and severity distributions from questions.
    
    Args:
        questions: List of Question objects with findings
        
    Returns:
        Tuple of (compliance_distribution, severity_distribution)
        - compliance_distribution: {"compliant": int, "non_compliant": int, "pending_review": int}
        - severity_distribution: {"critical": int, "high": int, "medium": int, "low": int}
        
    Requirements: 4.4, 4.5
    
    Example:
        >>> questions = [Question(findings=[...], ...)]
        >>> compliance, severity = calculate_distributions(questions)
        >>> compliance
        {'compliant': 5, 'non_compliant': 3, 'pending_review': 2}
    """
    compliance_distribution = {
        "compliant": 0,
        "non_compliant": 0,
        "pending_review": 0
    }
    
    severity_distribution = {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0
    }
    
    # Iterate through all findings in all questions
    for question in questions:
        for finding in question.findings:
            # Count compliance status
            status_key = finding.status.lower()
            if status_key in compliance_distribution:
                compliance_distribution[status_key] += 1
            
            # Count severity
            severity_key = finding.severity.lower()
            if severity_key in severity_distribution:
                severity_distribution[severity_key] += 1
    
    return compliance_distribution, severity_distribution
