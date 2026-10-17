"""
Pruebas estructurales del evaluador del pilar de Seguridad.

Verifican el contrato de la plataforma (independiente de los datos reales de AWS):
  - El pilar produce exactamente 11 preguntas (SEC01..SEC11).
  - El total de Best Practices evaluadas es 63.
  - Cada finding cumple el contrato {bp, description, status, severity,
    finding, evidence, remediation, risk} con enums válidos.
  - Los scores están en el rango [0, 100] y las distribuciones cuadran.

Se usa una sesión boto3 falsa (denying_session) para no depender de la cuenta
real: todas las llamadas AWS fallan con AccessDenied, pero `client.exceptions.<X>`
existe (mock fiel), de modo que cada BP cae a su rama de error/pending y devuelve
un finding válido y completo.

Los 4 bugs de producción que el mock fiel reveló (SEC02-BP05, SEC07-BP02,
SEC09-BP01, SEC10-BP08) fueron CORREGIDOS; por eso las 63 BPs se validan ahora de
forma uniforme en verde. La regresión específica de cada bug se cubre además en
tests/test_security_bugs.py.
"""

from _helpers import (  # noqa: E402 (sys.path lo ajusta conftest)
    EXPECTED_BPS_PER_QUESTION,
    EXPECTED_QUESTIONS,
    EXPECTED_TOTAL_BPS,
    VALID_SEVERITY,
    VALID_STATUS,
    assert_finding_contract,
)
import pytest
from conftest import iter_bp_invokers


def _collect_findings(security_handler, session):
    """Invoca las 63 BPs individualmente y devuelve [(bp_id, finding)].

    Tras corregir los bugs, ninguna BP lanza excepción ante AccessDenied: todas
    devuelven un finding degradado válido.
    """
    results = []
    for bp_id, invoker in iter_bp_invokers(security_handler, session):
        results.append((bp_id, invoker()))
    return results


def _bp_ids():
    return [f"{sec}-BP{n:02d}"
            for sec, count in EXPECTED_BPS_PER_QUESTION.items()
            for n in range(1, count + 1)]


# --- Validación por-BP: las 63 ante AccessDenied devuelven finding válido ---

@pytest.mark.parametrize("bp_id", _bp_ids())
def test_each_bp_returns_valid_finding_under_access_denied(
    security_handler, denying_session, bp_id
):
    """Cada BP, ante AccessDenied, devuelve un finding válido (ruta degradada),
    sin lanzar excepción."""
    invokers = dict(iter_bp_invokers(security_handler, denying_session))
    finding = invokers[bp_id]()
    assert_finding_contract(finding, expected_bp=bp_id)


# --- Invariantes de pilar (reconstruidas por-BP) ---

def test_pillar_has_sixty_three_best_practices(security_handler, denying_session):
    results = _collect_findings(security_handler, denying_session)
    assert len(results) == EXPECTED_TOTAL_BPS, (
        f"Se esperaban {EXPECTED_TOTAL_BPS} BPs, se obtuvo {len(results)}"
    )


def test_pillar_has_eleven_questions(security_handler, denying_session):
    results = _collect_findings(security_handler, denying_session)
    seen_questions = []
    for bp_id, _finding in results:
        q = bp_id.split("-")[0]
        if q not in seen_questions:
            seen_questions.append(q)
    assert seen_questions == EXPECTED_QUESTIONS, (
        f"Se esperaban 11 preguntas SEC01..SEC11, se obtuvo: {seen_questions}"
    )
    counts = {}
    for bp_id, _finding in results:
        q = bp_id.split("-")[0]
        counts[q] = counts.get(q, 0) + 1
    assert counts == EXPECTED_BPS_PER_QUESTION, (
        f"Reparto de BPs por pregunta inesperado: {counts}"
    )


def test_every_finding_has_full_contract(security_handler, denying_session):
    results = _collect_findings(security_handler, denying_session)
    for bp_id, finding in results:
        assert_finding_contract(finding, expected_bp=bp_id)


def test_bp_ids_are_unique_and_well_formed(security_handler, denying_session):
    results = _collect_findings(security_handler, denying_session)
    bp_ids = [bp_id for bp_id, _ in results]
    assert len(bp_ids) == len(set(bp_ids)), "Hay BP IDs duplicados"
    for bp_id in bp_ids:
        assert bp_id.startswith("SEC"), f"BP ID con prefijo inesperado: {bp_id}"
        assert "-BP" in bp_id, f"BP ID mal formado: {bp_id}"


def test_distributions_match_finding_counts(security_handler, denying_session):
    results = _collect_findings(security_handler, denying_session)

    compliance = {"compliant": 0, "non_compliant": 0, "pending_review": 0}
    severity = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for _bp_id, finding in results:
        assert finding["status"] in VALID_STATUS
        assert finding["severity"] in VALID_SEVERITY
        compliance[finding["status"].lower()] += 1
        severity[finding["severity"].lower()] += 1

    total_comp = sum(compliance.values())
    assert total_comp == EXPECTED_TOTAL_BPS, (
        f"La distribución de cumplimiento suma {total_comp}, "
        f"se esperaban {EXPECTED_TOTAL_BPS}"
    )
    total_sev = sum(severity.values())
    assert total_sev == EXPECTED_TOTAL_BPS, (
        f"La distribución de severidad suma {total_sev}, "
        f"se esperaban {EXPECTED_TOTAL_BPS}"
    )


def test_scores_within_range(security_handler, denying_session):
    """El score por pregunta y de pilar, calculado sobre los findings por-BP,
    está en [0, 100]."""
    results = _collect_findings(security_handler, denying_session)
    score_map = {"COMPLIANT": 100.0, "NON_COMPLIANT": 0.0, "PENDING_REVIEW": 50.0}

    by_question = {}
    for bp_id, finding in results:
        q = bp_id.split("-")[0]
        by_question.setdefault(q, []).append(finding)

    total_weighted = 0.0
    total_bps = 0
    for q, findings in by_question.items():
        q_score = sum(score_map.get(f["status"], 0.0) for f in findings) / len(findings)
        assert 0.0 <= q_score <= 100.0, f"{q} score fuera de rango: {q_score}"
        total_weighted += q_score * len(findings)
        total_bps += len(findings)

    overall = total_weighted / total_bps if total_bps else 0.0
    assert 0.0 <= overall <= 100.0
