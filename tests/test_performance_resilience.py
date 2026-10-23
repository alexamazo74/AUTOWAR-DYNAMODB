"""
Prueba de REGRESIÓN de resiliencia del pilar de Performance.

Contexto del bug: botocore.exceptions.UnknownServiceError hereda de
BotoCoreError, NO de ClientError. Un `except ClientError` NO lo captura, así que
un nombre de servicio inválido (o un servicio que lanza esa excepción) hacía que
la excepción escapara de la BP, tumbara PerformanceEvaluator.evaluate() y dejara
el pilar entero sin resultados (por eso Rendimiento no aparecía en el dashboard).

El fix (FEAT-001 parte b) envuelve cada BP en PerformanceEvaluator._safe_eval,
que atrapa CUALQUIER excepción y delega en _handle_permission_error ->
PENDING_REVIEW. Esta prueba construye una sesión OFFLINE cuyo .client('elbv2')
lanza UnknownServiceError y para el resto devuelve clientes que fallan toda
operación con ClientError (AccessDenied) SIN tocar la red. Afirma que evaluate():
  (a) no propaga la excepción;
  (b) devuelve 5 questions con 32 BPs en total;
  (c) el/los BP afectados quedan en PENDING_REVIEW.

Con el código viejo (sin _safe_eval) la UnknownServiceError escaparía y el test
fallaría. NOTA: a diferencia del mock fiel de conftest (ScriptedSession), aquí
NO se usan clientes boto3 reales, porque el evaluador de performance usa
paginadores y esos sí ejecutarían llamadas reales de red contra AWS.
"""

import importlib.util
import os
import sys

import pytest
from botocore.exceptions import ClientError, UnknownServiceError

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PERFORMANCE_DIR = os.path.join(REPO_ROOT, "lambda", "evaluators", "performance")

# Servicio que, al pedirse, simula el fallo de nombre inválido original.
_FAILING_SERVICE = "elbv2"


def _load_performance_handler():
    """Importa el handler del pilar de performance de forma aislada.

    Tanto security como performance tienen un módulo `all_bp_evaluations`; para
    evitar colisiones con el que ya cargó conftest para security, se carga
    `all_bp_evaluations` desde la ruta del pilar de performance bajo su nombre
    canónico (que el handler espera con `import all_bp_evaluations`).
    """
    if PERFORMANCE_DIR not in sys.path:
        sys.path.insert(0, PERFORMANCE_DIR)

    bp_path = os.path.join(PERFORMANCE_DIR, "all_bp_evaluations.py")
    spec_bp = importlib.util.spec_from_file_location("all_bp_evaluations", bp_path)
    bp_module = importlib.util.module_from_spec(spec_bp)
    sys.modules["all_bp_evaluations"] = bp_module
    spec_bp.loader.exec_module(bp_module)

    handler_path = os.path.join(PERFORMANCE_DIR, "handler.py")
    spec_h = importlib.util.spec_from_file_location("performance_handler", handler_path)
    handler_module = importlib.util.module_from_spec(spec_h)
    spec_h.loader.exec_module(handler_module)
    return handler_module


def _access_denied(operation):
    """Construye un ClientError de AccessDenied para una operación dada."""
    return ClientError(
        {"Error": {"Code": "AccessDenied", "Message": f"stub deny ({operation})"}},
        operation,
    )


class _DenyingPaginator:
    """Paginador falso: iterar lanza ClientError (sin red)."""

    def __init__(self, operation):
        self._operation = operation

    def paginate(self, *args, **kwargs):
        raise _access_denied(self._operation)


class _DenyingClient:
    """Cliente offline: toda operación y todo paginador fallan con ClientError.

    No realiza NINGUNA llamada de red. Reproduce el camino "sin permisos / sin
    datos" de forma determinista, que es justo lo que el evaluador degrada a
    PENDING_REVIEW/NOT_APPLICABLE.
    """

    def get_paginator(self, operation):
        return _DenyingPaginator(operation)

    def get_waiter(self, *args, **kwargs):
        raise _access_denied("get_waiter")

    def __getattr__(self, name):
        # Cualquier operación de API (snake_case) falla con AccessDenied.
        def _operation(*args, **kwargs):
            raise _access_denied(name)

        return _operation


class _OfflineFailingSession:
    """Sesión boto3 falsa y OFFLINE.

    - .client(_FAILING_SERVICE) lanza UnknownServiceError (reproduce el nombre
      de servicio inválido original: botocore no lo reconoce).
    - .client(cualquier otro) devuelve un _DenyingClient que no toca la red.
    """

    def __init__(self, failing_service, region_name="us-east-1"):
        self._failing_service = failing_service
        self.region_name = region_name

    def client(self, service_name, *args, **kwargs):
        if service_name == self._failing_service:
            raise UnknownServiceError(
                service_name=service_name,
                known_service_names=["elbv2", "ec2", "s3"],
            )
        return _DenyingClient()


@pytest.fixture
def performance_handler():
    """Carga el handler de performance y restaura sys.modules['all_bp_evaluations'].

    `_load_performance_handler` inyecta su propio `all_bp_evaluations` en
    sys.modules (performance y security comparten ese nombre de módulo). Si no se
    restaura, deja envenenada la caché para suites posteriores (p.ej. security).
    El teardown devuelve la entrada previa (o la elimina) para blindar el seam.
    """
    previous_bp = sys.modules.get("all_bp_evaluations")
    try:
        yield _load_performance_handler()
    finally:
        if previous_bp is not None:
            sys.modules["all_bp_evaluations"] = previous_bp
        else:
            sys.modules.pop("all_bp_evaluations", None)


def _build_evaluator(performance_handler):
    session = _OfflineFailingSession(_FAILING_SERVICE)
    return performance_handler.PerformanceEvaluator(session, region="us-east-1")


def test_evaluate_no_propaga_unknown_service_error(performance_handler):
    """evaluate() no debe propagar la UnknownServiceError de un servicio inválido."""
    evaluator = _build_evaluator(performance_handler)
    # Con el bug viejo (sin _safe_eval) esto lanzaría UnknownServiceError.
    result = evaluator.evaluate()
    assert isinstance(result, dict)


def test_evaluate_devuelve_5_questions_y_32_bps(performance_handler):
    """evaluate() devuelve 5 questions con 32 BPs en total pese al fallo de un servicio."""
    evaluator = _build_evaluator(performance_handler)
    result = evaluator.evaluate()

    questions = result["questions"]
    assert len(questions) == 5, "El pilar de performance debe tener 5 preguntas"

    total_bps = sum(q["bps_evaluated"] for q in questions)
    assert total_bps == 32, f"Se esperaban 32 BPs en total, se obtuvieron {total_bps}"
    assert result["total_best_practices"] == 32


def test_bp_afectado_queda_pending_review(performance_handler):
    """El/los BP que dependen del servicio que falla quedan en PENDING_REVIEW."""
    evaluator = _build_evaluator(performance_handler)
    result = evaluator.evaluate()

    all_findings = [f for q in result["questions"] for f in q["findings"]]

    pending = [f for f in all_findings if f["status"] == "PENDING_REVIEW"]
    assert pending, (
        "Al fallar un servicio con UnknownServiceError, el/los BP afectados "
        "deben degradar a PENDING_REVIEW"
    )

    # PERF04-BP04 lista load balancers vía elbv2 (session.client('elbv2')),
    # el servicio que lanza UnknownServiceError. Debe existir y degradar.
    bp04 = next((f for f in all_findings if f["bp"] == "PERF04-BP04"), None)
    assert bp04 is not None, "PERF04-BP04 debe estar presente en los resultados"
    assert bp04["status"] == "PENDING_REVIEW", (
        f"PERF04-BP04 debe quedar PENDING_REVIEW al fallar elbv2, no {bp04['status']}"
    )
