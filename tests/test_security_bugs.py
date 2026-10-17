"""
Pruebas que EVIDENCIAN bugs reales de producción del pilar de Seguridad.

Estos bugs se descubrieron al construir el mock de sesión boto3 fiel. NO se
corrige el código de producción (el objetivo es TESTS). Cada prueba está marcada
`xfail` apuntando a `.agents/tasks/bugs-encontrados-seguridad.md`. Cuando el bug
se corrija, la prueba pasará a `xpass` (señal para endurecerla).

Resumen de bugs:
  - BUG-1 SEC02-BP05: UnboundLocalError 'old_keys' ante AccessDenied.
  - BUG-2 SEC07-BP02: UnboundLocalError 'buckets' ante AccessDenied en S3.
  - BUG-3 SEC09-BP01: UnboundLocalError 'cert_list' ante AccessDenied en ACM.
  - BUG-4 SEC10-BP08: description vacía (clave ausente en SECURITY_BP_DESCRIPTIONS).
"""

import pytest
from _helpers import assert_finding_contract

import all_bp_evaluations as bp  # noqa: E402 (sys.path lo ajusta conftest)

BUGS_DOC = ".agents/tasks/bugs-encontrados-seguridad.md"


def _handle(bp_id, error):
    """Reproduce la firma de handle_error_func que esperan las BPs."""
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


@pytest.mark.xfail(
    reason=f"BUG-1 SEC02-BP05 UnboundLocalError ante AccessDenied. Ver {BUGS_DOC}",
    raises=UnboundLocalError,
    strict=False,
)
def test_sec02_bp05_access_denied_bug(denying_session):
    """SEC02-BP05 debería degradar a un finding válido cuando no hay permisos
    para generar el credential report; en su lugar lanza UnboundLocalError."""
    finding = bp.evaluate_sec02_bp05(denying_session, _handle)
    assert_finding_contract(finding, expected_bp="SEC02-BP05")


@pytest.mark.xfail(
    reason=f"BUG-2 SEC07-BP02 UnboundLocalError ante AccessDenied. Ver {BUGS_DOC}",
    raises=UnboundLocalError,
    strict=False,
)
def test_sec07_bp02_access_denied_bug(denying_session):
    """SEC07-BP02 debería degradar cuando S3 no es accesible; en su lugar lanza
    UnboundLocalError porque `buckets` queda sin asignar."""
    finding = bp.evaluate_sec07_bp02(denying_session, _handle)
    assert_finding_contract(finding, expected_bp="SEC07-BP02")


@pytest.mark.xfail(
    reason=f"BUG-3 SEC09-BP01 UnboundLocalError ante AccessDenied. Ver {BUGS_DOC}",
    raises=UnboundLocalError,
    strict=False,
)
def test_sec09_bp01_access_denied_bug(denying_session):
    """SEC09-BP01 debería degradar cuando ACM no es accesible; en su lugar lanza
    UnboundLocalError porque `cert_list` queda sin asignar."""
    finding = bp.evaluate_sec09_bp01(denying_session, _handle)
    assert_finding_contract(finding, expected_bp="SEC09-BP01")


@pytest.mark.xfail(
    reason=f"BUG-4 SEC10-BP08 description vacía (clave ausente). Ver {BUGS_DOC}",
    raises=AssertionError,
    strict=False,
)
def test_sec10_bp08_empty_description_bug(denying_session):
    """SEC10-BP08 devuelve un finding con `description` vacía porque falta la
    clave 'SEC10-BP08' en SECURITY_BP_DESCRIPTIONS."""
    finding = bp.evaluate_sec10_bp08(denying_session, _handle)
    assert_finding_contract(finding, expected_bp="SEC10-BP08")
