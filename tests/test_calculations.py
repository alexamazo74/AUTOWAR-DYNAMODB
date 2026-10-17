"""
Pruebas de las funciones puras de cálculo (autowar_common.calculations).

No requieren AWS. Validan el scoring por pregunta/pilar, la determinación de
estado y las distribuciones, que son el núcleo del contrato de resultados.
"""

from autowar_common.calculations import (
    calculate_distributions,
    calculate_pillar_score,
    calculate_question_score,
    determine_question_status,
)
from autowar_common.models import Finding, Question


def _finding(status="COMPLIANT", severity="LOW", bp="SEC01-BP01"):
    return Finding(
        bp=bp,
        description="desc",
        status=status,
        severity=severity,
        finding="hallazgo",
        evidence="evidencia",
        remediation="remediacion",
        risk="riesgo",
    )


def _question(score, bps, findings=None):
    return Question(
        question_id="SEC01",
        title={"es": "t", "en": "t"},
        description={"es": "d", "en": "d"},
        score=score,
        bps_evaluated=bps,
        status="COMPLIANT",
        findings=findings or [],
    )


# --- calculate_question_score ---

def test_question_score_empty_is_zero():
    assert calculate_question_score([]) == 0.0


def test_question_score_all_compliant_is_100():
    findings = [_finding("COMPLIANT"), _finding("COMPLIANT", bp="SEC01-BP02")]
    assert calculate_question_score(findings) == 100.0


def test_question_score_all_non_compliant_is_0():
    findings = [_finding("NON_COMPLIANT"), _finding("NON_COMPLIANT", bp="SEC01-BP02")]
    assert calculate_question_score(findings) == 0.0


def test_question_score_mixed_average():
    # COMPLIANT(100) + NON_COMPLIANT(0) + PENDING_REVIEW(50) = 150 / 3 = 50
    findings = [
        _finding("COMPLIANT"),
        _finding("NON_COMPLIANT", bp="SEC01-BP02"),
        _finding("PENDING_REVIEW", bp="SEC01-BP03"),
    ]
    assert calculate_question_score(findings) == 50.0


# --- calculate_pillar_score (promedio ponderado por nº de BPs) ---

def test_pillar_score_weighted_average():
    questions = [_question(80.0, 5), _question(60.0, 3)]
    # (80*5 + 60*3) / 8 = (400 + 180) / 8 = 72.5
    assert calculate_pillar_score(questions) == 72.5


def test_pillar_score_empty_is_zero():
    assert calculate_pillar_score([]) == 0.0


# --- determine_question_status ---

def test_status_all_compliant():
    findings = [_finding("COMPLIANT"), _finding("COMPLIANT", bp="SEC01-BP02")]
    assert determine_question_status(findings) == "COMPLIANT"


def test_status_any_non_compliant():
    findings = [_finding("COMPLIANT"), _finding("NON_COMPLIANT", bp="SEC01-BP02")]
    assert determine_question_status(findings) == "NON_COMPLIANT"


def test_status_pending_when_mix_without_non_compliant():
    findings = [_finding("COMPLIANT"), _finding("PENDING_REVIEW", bp="SEC01-BP02")]
    assert determine_question_status(findings) == "PENDING_REVIEW"


def test_status_empty_is_pending():
    assert determine_question_status([]) == "PENDING_REVIEW"


# --- calculate_distributions ---

def test_distributions_counts():
    findings = [
        _finding("COMPLIANT", "LOW"),
        _finding("NON_COMPLIANT", "CRITICAL", bp="SEC01-BP02"),
        _finding("PENDING_REVIEW", "MEDIUM", bp="SEC01-BP03"),
    ]
    question = _question(50.0, 3, findings)
    compliance, severity = calculate_distributions([question])
    assert compliance == {"compliant": 1, "non_compliant": 1, "pending_review": 1}
    assert severity == {"critical": 1, "high": 0, "medium": 1, "low": 1}
