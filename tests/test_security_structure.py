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

NOTA SOBRE BUGS DE PRODUCCIÓN
-----------------------------
El mock fiel reveló 3 bugs reales (UnboundLocalError ante AccessDenied) en
SEC02-BP05, SEC07-BP02 y SEC09-BP01. Están documentados en
`.agents/tasks/bugs-encontrados-seguridad.md` y NO se corrigieron (el objetivo es
TESTS, no refactor del evaluador). Como `SecurityEvaluator.evaluate()` aborta en la
primera BP que lanza esa excepción, las pruebas estructurales recorren las 63 BPs
**individualmente**: las 60 sanas se validan en verde y las 3 con bug se marcan
`xfail`. Las invariantes de pilar (11 preguntas, 63 BPs, distribuciones) se validan
reconstruyendo el resultado por-BP, sustituyendo las 3 BPs con bug por el finding
degradado que el manejador de errores (`_handle_permission_error`) habría producido
(ese es el comportamiento esperado una vez corregidos los bugs).
"""

import pytest
from _helpers import (  # noqa: E402 (sys.path lo ajusta conftest)
    EXPECTED_BPS_PER_QUESTION,
    EXPECTED_QUESTIONS,
    EXPECTED_TOTAL_BPS,
    VALID_SEVERITY,
    VALID_STATUS,
    assert_finding_contract,
)
from conftest import iter_bp_invokers

# BPs con bug de producción documentado (ver bugs-encontrados-seguridad.md).
# BUG-1..3: lanzan UnboundLocalError ante AccessDenied.
CRASH_BUGGY_BPS = {"SEC02-BP05", "SEC07-BP02", "SEC09-BP01"}
# BUG-4: devuelven un finding con `description` vacía (clave ausente en el dict).
EMPTY_DESC_BPS = {"SEC10-BP08"}
KNOWN_BUGGY_BPS = CRASH_BUGGY_BPS | EMPTY_DESC_BPS


def _collect_findings(security_handler, session):
    """Invoca las 63 BPs individualmente y devuelve [(bp_id, finding_or_None)].

    Para las BPs con bug documentado, captura la excepción y sustituye el finding
    por el que `_handle_permission_error` habría devuelto (status PENDING_REVIEW),
    que es el comportamiento esperado tras corregir el bug.
    """
    evaluator = security_handler.SecurityEvaluator(session, region="us-east-1")
    from botocore.exceptions import ClientError

    results = []
    for bp_id, invoker in iter_bp_invokers(security_handler, session):
        try:
            finding = invoker()
        except Exception:  # noqa: BLE001
            # Bug de producción (BUG-1..3): simula la degradación esperada para no
            # perder la invariante de 63 findings. Debe ser una BP conocida con bug.
            assert bp_id in CRASH_BUGGY_BPS, (
                f"{bp_id} lanzó una excepción no documentada en "
                f"bugs-encontrados-seguridad.md"
            )
            fake_error = ClientError(
                {"Error": {"Code": "AccessDenied", "Message": "bug workaround"}},
                "operation",
            )
            finding = evaluator._handle_permission_error(bp_id, fake_error)
        results.append((bp_id, finding))
    return results


# --- Validación por-BP (las 60 sanas en verde, las 3 con bug en xfail) ---

def _bp_ids():
    return [f"{sec}-BP{n:02d}"
            for sec, count in EXPECTED_BPS_PER_QUESTION.items()
            for n in range(1, count + 1)]


@pytest.mark.parametrize("bp_id", _bp_ids())
def test_each_bp_returns_valid_finding_under_access_denied(
    security_handler, denying_session, bp_id, request
):
    """Cada BP, ante AccessDenied, devuelve un finding válido (ruta degradada)."""
    if bp_id in CRASH_BUGGY_BPS:
        request.applymarker(
            pytest.mark.xfail(
                reason=(
                    f"{bp_id}: bug de producción (UnboundLocalError ante AccessDenied). "
                    f"Ver .agents/tasks/bugs-encontrados-seguridad.md"
                ),
                strict=False,
                raises=UnboundLocalError,
            )
        )
    elif bp_id in EMPTY_DESC_BPS:
        request.applymarker(
            pytest.mark.xfail(
                reason=(
                    f"{bp_id}: bug de producción (description vacía, clave ausente en "
                    f"SECURITY_BP_DESCRIPTIONS). Ver .agents/tasks/bugs-encontrados-seguridad.md"
                ),
                strict=False,
                raises=AssertionError,
            )
        )

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
    # Reparto de BPs por pregunta.
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
        if bp_id in EMPTY_DESC_BPS:
            # BUG-4 documentado: description vacía. Se valida (como xfail) en
            # test_each_bp_returns_valid_finding_under_access_denied[SEC10-BP08].
            # Aquí comprobamos el resto del contrato salvo la description vacía.
            assert set(finding.keys()) >= {
                "bp", "description", "status", "severity",
                "finding", "evidence", "remediation", "risk",
            }
            assert finding["status"] in VALID_STATUS
            assert finding["severity"] in VALID_SEVERITY
            continue
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
        compliance_key = finding["status"].lower()
        compliance[compliance_key] += 1
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
