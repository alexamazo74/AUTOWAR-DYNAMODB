"""
Prueba de integración OPCIONAL del pilar de Seguridad contra una cuenta AWS real.

Está marcada `@pytest.mark.integration`, por lo que:
  - `run-tests.ps1` (modo por defecto) y `pytest -m "not integration"` la OMITEN.
  - `run-tests.ps1 -Integration` / `pytest -m integration` la recogen.

Aun recogiéndola, se auto-salta si no hay credenciales AWS válidas (p.ej. en un
equipo sin cuenta), de modo que NUNCA falla por ausencia de credenciales.

NO ejecuta integración por defecto ni toca la cuenta AWS en la suite estándar.
"""

import os

import pytest

INTEGRATION_REGION = os.environ.get("AUTOWAR_INTEGRATION_REGION", "us-east-1")
EXPECTED_TOTAL_BPS = 63
EXPECTED_QUESTIONS = 11


@pytest.mark.integration
def test_security_evaluator_against_real_account(security_handler):
    """Corre SecurityEvaluator contra la cuenta real y valida el contrato de alto
    nivel del resultado (11 preguntas, 63 BPs, scores en rango)."""
    import boto3
    from botocore.exceptions import BotoCoreError, ClientError, NoCredentialsError

    # Usar una sesión real (credenciales del entorno/perfil). Importante: NO fijar
    # credenciales ficticias aquí; el fixture autouse las fija para el resto de la
    # suite, pero para integración se requieren credenciales reales.
    session = boto3.Session(region_name=INTEGRATION_REGION)

    try:
        sts = session.client("sts")
        sts.get_caller_identity()
    except (NoCredentialsError, ClientError, BotoCoreError) as exc:
        pytest.skip(f"Sin credenciales AWS válidas para integración: {exc}")

    evaluator = security_handler.SecurityEvaluator(session, region=INTEGRATION_REGION)
    result = evaluator.evaluate()

    assert result["pillar_id"] == "security"
    assert len(result["questions"]) == EXPECTED_QUESTIONS
    assert result["total_best_practices"] == EXPECTED_TOTAL_BPS
    assert 0.0 <= result["overall_score"] <= 100.0

    total_findings = sum(len(q["findings"]) for q in result["questions"])
    assert total_findings == EXPECTED_TOTAL_BPS
