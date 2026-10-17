"""
Helpers compartidos para la suite de pruebas del pilar de Seguridad.

Centraliza las constantes del contrato de findings y la función de aserción
`assert_finding_contract`, para no duplicarlas entre
`test_security_structure.py` y `test_security_bps.py`.
"""

# Enums válidos del contrato de un finding (coinciden con autowar_common.models).
VALID_STATUS = {"COMPLIANT", "NON_COMPLIANT", "PENDING_REVIEW"}
VALID_SEVERITY = {"CRITICAL", "HIGH", "MEDIUM", "LOW"}

# Claves obligatorias de cada finding (dict) devuelto por una BP.
FINDING_KEYS = {
    "bp",
    "description",
    "status",
    "severity",
    "finding",
    "evidence",
    "remediation",
    "risk",
}

# Campos de texto que nunca deben estar vacíos.
TEXT_KEYS = ("description", "finding", "evidence", "remediation", "risk")

# Preguntas esperadas del pilar de Seguridad: SEC01..SEC11.
EXPECTED_QUESTIONS = [f"SEC{n:02d}" for n in range(1, 12)]

# Total de Best Practices evaluadas en el pilar.
EXPECTED_TOTAL_BPS = 63

# Reparto de BPs por pregunta (verificado en handler.py). Suma 63.
EXPECTED_BPS_PER_QUESTION = {
    "SEC01": 8,
    "SEC02": 6,
    "SEC03": 9,
    "SEC04": 4,
    "SEC05": 4,
    "SEC06": 5,
    "SEC07": 4,
    "SEC08": 4,
    "SEC09": 3,
    "SEC10": 8,
    "SEC11": 8,
}


def assert_finding_contract(finding, expected_bp=None):
    """Valida que un finding cumpla el contrato completo.

    - Tiene exactamente las claves obligatorias.
    - `status` y `severity` usan enums válidos.
    - Los campos de texto son cadenas no vacías.
    - (Opcional) el `bp` coincide con el esperado.
    """
    assert isinstance(finding, dict), f"El finding no es un dict: {type(finding)!r}"

    missing = FINDING_KEYS - set(finding.keys())
    assert not missing, f"{finding.get('bp')} sin campos: {missing}"

    assert finding["status"] in VALID_STATUS, (
        f"{finding['bp']} status inválido: {finding['status']}"
    )
    assert finding["severity"] in VALID_SEVERITY, (
        f"{finding['bp']} severity inválido: {finding['severity']}"
    )

    for key in TEXT_KEYS:
        value = finding[key]
        assert isinstance(value, str) and value.strip(), (
            f"{finding['bp']} campo vacío o no textual: {key}"
        )

    if expected_bp is not None:
        assert finding["bp"] == expected_bp, (
            f"BP inesperado: se esperaba {expected_bp}, se obtuvo {finding['bp']}"
        )
