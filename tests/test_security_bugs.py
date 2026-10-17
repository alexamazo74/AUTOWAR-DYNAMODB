"""
Pruebas de REGRESIÓN de bugs reales de producción del pilar de Seguridad.

Estos 4 bugs se descubrieron al construir el mock de sesión boto3 fiel y fueron
CORREGIDOS (ver .agents/tasks/bugs-encontrados-seguridad.md). Estas pruebas
verifican el comportamiento correcto tras el fix y previenen que los bugs
reaparezcan (regresión). Antes del fix fallaban (xfail); ahora deben pasar en verde.

Bugs corregidos:
  - BUG-1 SEC02-BP05: UnboundLocalError 'old_keys'/'unused_users'/'no_mfa_console'
    ante AccessDenied -> se inicializan antes del try interno.
  - BUG-2 SEC07-BP02: UnboundLocalError 'buckets' ante AccessDenied en S3 ->
    `buckets = []` antes del try.
  - BUG-3 SEC09-BP01: UnboundLocalError 'cert_list' ante AccessDenied en ACM ->
    `cert_list = []` antes del try + degradar (no COMPLIANT) si ACM es inaccesible.
  - BUG-4 SEC10-BP08: description vacía (clave ausente) -> añadida en
    SECURITY_BP_DESCRIPTIONS.
"""

from _helpers import assert_finding_contract

import all_bp_evaluations as bp  # noqa: E402 (sys.path lo ajusta conftest)

BUGS_DOC = ".agents/tasks/bugs-encontrados-seguridad.md"


def _handle(bp_id, error):
    """Reproduce la firma de handle_error_func que esperan las BPs.

    En las BPs correctamente escritas, el ClientError de una API individual se
    captura en un try interno y NO llega aquí; este callback solo se invoca si el
    try/except ClientError externo atrapa el error. Devuelve un finding válido.
    """
    return {
        "bp": bp_id,
        "description": "x",
        "status": "PENDING_REVIEW",
        "severity": "MEDIUM",
        "finding": "x",
        "evidence": "x",
        "remediation": "x",
        "risk": "x",
    }


def test_sec02_bp05_access_denied_degrades(denying_session):
    """BUG-1 corregido: SEC02-BP05 degrada a un finding válido cuando no hay
    permisos para generar el credential report (ya no lanza UnboundLocalError)."""
    finding = bp.evaluate_sec02_bp05(denying_session, _handle)
    assert_finding_contract(finding, expected_bp="SEC02-BP05")


def test_sec07_bp02_access_denied_degrades(denying_session):
    """BUG-2 corregido: SEC07-BP02 degrada cuando S3 no es accesible
    (ya no lanza UnboundLocalError por `buckets` sin asignar)."""
    finding = bp.evaluate_sec07_bp02(denying_session, _handle)
    assert_finding_contract(finding, expected_bp="SEC07-BP02")


def test_sec09_bp01_access_denied_degrades(denying_session):
    """BUG-3 corregido: SEC09-BP01 degrada cuando ACM no es accesible
    (ya no lanza UnboundLocalError por `cert_list` sin asignar) y NO reporta
    COMPLIANT sin datos."""
    finding = bp.evaluate_sec09_bp01(denying_session, _handle)
    assert_finding_contract(finding, expected_bp="SEC09-BP01")
    # Sin acceso a ACM no se puede afirmar cumplimiento.
    assert finding["status"] != "COMPLIANT", (
        "SEC09-BP01 no debe reportar COMPLIANT cuando ACM es inaccesible"
    )


def test_sec10_bp08_has_description(denying_session):
    """BUG-4 corregido: SEC10-BP08 ahora tiene description no vacía
    (clave añadida en SECURITY_BP_DESCRIPTIONS)."""
    finding = bp.evaluate_sec10_bp08(denying_session, _handle)
    assert_finding_contract(finding, expected_bp="SEC10-BP08")
    assert finding["description"].strip(), (
        "SEC10-BP08 debe tener description no vacía"
    )
