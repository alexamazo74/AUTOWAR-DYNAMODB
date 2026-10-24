"""
Prueba de REGRESIÓN del generador de reporte EJECUTIVO (DOCX).

Dos bugs que cubre (FEAT-002):
  1) matplotlib intentaba escribir su caché de configuración en HOME al
     importarse; en el filesystem de solo lectura de Lambda eso reventaba el
     import. El fix fija MPLCONFIGDIR a un directorio escribible ANTES de
     importar matplotlib (os.environ.setdefault). Aquí fijamos MPLCONFIGDIR a un
     tmp dir ANTES de importar el handler para reproducir el entorno restringido.
  2) Si una gráfica fallaba al construirse, tumbaba la generación completa del
     DOCX (por eso el reporte ejecutivo fallaba con "No se recibió la URL").
     El fix (_safe_chart) tolera el fallo de una gráfica y genera el reporte sin
     ella.

Afirmaciones:
  (a) generate_executive_report(...) devuelve bytes > 0;
  (b) el DOCX contiene imágenes (inline_shapes o entradas word/media/ en el zip);
  (c) si una gráfica lanza una excepción, el reporte igual se genera (bytes > 0).
"""

import importlib.util
import json
import os
import sys
import tempfile
import zipfile
from io import BytesIO

import pytest

# IMPORTANTE: fijar MPLCONFIGDIR a un tmp dir ANTES de importar el handler
# (que a su vez importa matplotlib). Reproduce el entorno de solo lectura de
# Lambda sin reventar el import.
_MPL_TMPDIR = tempfile.mkdtemp(prefix="mplconfig_test_")
os.environ["MPLCONFIGDIR"] = _MPL_TMPDIR

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXECUTIVE_DIR = os.path.join(REPO_ROOT, "lambda", "report_generator_executive")


def _load_executive_handler():
    """Importa el handler del generador ejecutivo de forma aislada.

    autowar_common (del layer común) ya está en sys.path gracias a conftest.
    NO se añade el layer 'reports' (no existe en el repo); las dependencias
    (python-docx, matplotlib) vienen del venv.
    """
    if EXECUTIVE_DIR not in sys.path:
        sys.path.insert(0, EXECUTIVE_DIR)
    handler_path = os.path.join(EXECUTIVE_DIR, "handler.py")
    spec = importlib.util.spec_from_file_location("executive_report_handler", handler_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def executive_handler():
    return _load_executive_handler()


def _synthetic_evaluation_data():
    """Construye evaluation_data sintético con varios pilares y estados."""
    best_practices = [
        # Seguridad
        {"bpId": "SEC01-BP01", "pilar": "security", "status": "NON_COMPLIANT",
         "severity": "CRITICAL", "description": "MFA en usuario root",
         "finding": "El usuario root no tiene MFA habilitado"},
        {"bpId": "SEC02-BP01", "pilar": "security", "status": "NON_COMPLIANT",
         "severity": "HIGH", "description": "Bucket S3 público",
         "finding": "Bucket con acceso público detectado"},
        {"bpId": "SEC03-BP01", "pilar": "security", "status": "COMPLIANT",
         "severity": "LOW", "description": "Política IAM mínima",
         "finding": "Políticas con privilegio mínimo"},
        # Rendimiento
        {"bpId": "PERF01-BP01", "pilar": "performance", "status": "NON_COMPLIANT",
         "severity": "MEDIUM", "description": "Diversidad de tipos de instancia",
         "finding": "Diversidad limitada de tipos de instancia"},
        {"bpId": "PERF04-BP04", "pilar": "performance", "status": "PENDING_REVIEW",
         "severity": "MEDIUM", "description": "Balanceo de carga",
         "finding": "No se pudo evaluar automáticamente"},
        {"bpId": "PERF02-BP06", "pilar": "performance", "status": "NOT_APPLICABLE",
         "severity": "LOW", "description": "Aceleradores de hardware",
         "finding": "No aplica"},
        # Costo
        {"bpId": "COST01-BP01", "pilar": "cost", "status": "COMPLIANT",
         "severity": "LOW", "description": "Propiedad de optimización de costos",
         "finding": "Grupo FinOps presente"},
        {"bpId": "COST02-BP01", "pilar": "cost", "status": "NON_COMPLIANT",
         "severity": "MEDIUM", "description": "Recursos ociosos",
         "finding": "Instancias ociosas detectadas"},
    ]
    return {
        "metadata": {"accountId": "123456789012"},
        "pillarScores": {"security": 33.3, "performance": 25.0, "cost": 50.0},
        "bestPractices": best_practices,
    }


def _docx_has_images(docx_bytes):
    """True si el DOCX contiene al menos una imagen embebida (word/media/)."""
    with zipfile.ZipFile(BytesIO(docx_bytes)) as zf:
        return any(name.startswith("word/media/") for name in zf.namelist())


def test_generate_executive_report_devuelve_bytes_con_imagenes(executive_handler):
    """(a) devuelve bytes > 0 y (b) el DOCX contiene imágenes (gráficas)."""
    data = _synthetic_evaluation_data()
    selected = ["security", "performance", "cost"]

    content = executive_handler.generate_executive_report(
        data, selected, "123456789012", "2025-01-01T00:00:00Z", None
    )

    assert isinstance(content, (bytes, bytearray))
    assert len(content) > 0, "El reporte ejecutivo no debe venir vacío"
    assert _docx_has_images(bytes(content)), (
        "El DOCX ejecutivo debe contener imágenes (gráficas embebidas)"
    )


def test_mplconfigdir_apunta_a_tmp(executive_handler):
    """El handler respeta el MPLCONFIGDIR fijado (entorno restringido)."""
    # setdefault no sobreescribe el valor que fijamos antes del import.
    assert os.environ["MPLCONFIGDIR"] == _MPL_TMPDIR


def test_reporte_se_genera_aunque_una_grafica_falle(executive_handler, monkeypatch):
    """(c) Si una gráfica lanza excepción, el reporte igual se genera (bytes > 0)."""
    def _boom(*args, **kwargs):
        raise RuntimeError("fallo simulado al construir la gráfica")

    # Romper una de las gráficas incrustadas en el resumen ejecutivo.
    monkeypatch.setattr(executive_handler, "chart_scores_por_pilar", _boom)

    data = _synthetic_evaluation_data()
    selected = ["security", "performance", "cost"]

    content = executive_handler.generate_executive_report(
        data, selected, "123456789012", "2025-01-01T00:00:00Z", None
    )

    assert isinstance(content, (bytes, bytearray))
    assert len(content) > 0, (
        "El reporte debe generarse aun si una gráfica falla (sin esa gráfica)"
    )


def test_lambda_handler_camino_completo_devuelve_signed_url(executive_handler, monkeypatch):
    """Ejercita el camino COMPLETO de lambda_handler que produce la URL.

    Reproduce el BUG 3 ("No se recibió la URL del reporte"): si el import de
    matplotlib fallara o si generate_executive_report / la inserción del logo
    lanzaran una excepción, el handler devolvería statusCode 500 SIN 'signedUrl'
    y este test fallaría. Mockeamos upload_report y generate_signed_url para no
    tocar S3; así la única forma de obtener 200 + 'signedUrl' es que el DOCX
    (logo + charts) se genere de principio a fin.
    """
    captured = {}

    def _fake_upload_report(account_id, evaluation_timestamp, report_type, content, extension):
        # El contenido que llega aquí es el DOCX ya generado por el handler.
        captured["content"] = bytes(content)
        captured["extension"] = extension
        captured["report_type"] = report_type
        return f"reports/{account_id}/{evaluation_timestamp}/{report_type}.{extension}"

    def _fake_generate_signed_url(s3_key, expiration_seconds=3600):
        captured["s3_key"] = s3_key
        return f"https://signed.example/{s3_key}?expires={expiration_seconds}"

    monkeypatch.setattr(executive_handler, "upload_report", _fake_upload_report)
    monkeypatch.setattr(executive_handler, "generate_signed_url", _fake_generate_signed_url)

    event = {
        "accountId": "123456789012",
        "evaluationTimestamp": "2025-01-01T00:00:00Z",
        "evaluationData": _synthetic_evaluation_data(),
        "selectedPilares": ["security", "performance", "cost"],
    }

    resp = executive_handler.lambda_handler(event, None)

    assert resp["statusCode"] == 200, (
        f"El camino completo del handler debe devolver 200, devolvió "
        f"{resp['statusCode']}: {resp.get('body')}"
    )
    body = json.loads(resp["body"])
    assert "signedUrl" in body, "El body debe contener 'signedUrl'"
    assert body["signedUrl"].startswith("https://"), "La URL firmada debe ser una URL válida"
    assert body["s3Key"] == captured.get("s3_key")

    # El DOCX subido debe ser un documento real con imágenes (logo + charts).
    assert captured.get("extension") == "docx"
    assert captured.get("report_type") == "executive"
    assert _docx_has_images(captured["content"]), (
        "El DOCX subido debe contener imágenes (logo + gráficas embebidas)"
    )


def test_lambda_handler_sin_matplotlib_en_layer_falla_import():
    """Opcional: reproduce fielmente el Runtime.ImportModuleError del BUG 3.

    Importa el handler con sys.path limitado al layer 'reports' + layer común
    (SIN el venv). Si matplotlib NO está presente en el layer 'reports', el
    import a nivel de módulo falla con ImportError/ModuleNotFoundError, que es
    exactamente lo que Lambda reportaba como Runtime.ImportModuleError.

    Nota: cuando el layer YA fue reconstruido con matplotlib (FEAT-002), sus
    binarios son nativos de Linux (manylinux) y NO son importables en Windows,
    por lo que este test se omite (skip): el camino feliz del handler ya queda
    cubierto por el resto de la suite, que usa el matplotlib del venv.
    """
    reports_python = os.path.join(REPO_ROOT, "lambda", "layers", "reports", "python")
    common_python = os.path.join(REPO_ROOT, "lambda", "layers", "common", "python")
    if not os.path.isdir(reports_python):
        pytest.skip("El layer 'reports' no está empaquetado en el repo")

    if os.path.isdir(os.path.join(reports_python, "matplotlib")):
        pytest.skip(
            "El layer 'reports' ya incluye matplotlib (FEAT-002); sus binarios "
            "Linux no son importables en Windows, no se puede ejercitar el import local"
        )

    handler_path = os.path.join(EXECUTIVE_DIR, "handler.py")
    saved_path = list(sys.path)
    saved_modules = dict(sys.modules)
    # Quitar módulos ya cacheados que resolverían desde el venv.
    for name in list(sys.modules):
        if name == "matplotlib" or name.startswith("matplotlib."):
            del sys.modules[name]
    try:
        sys.path = [EXECUTIVE_DIR, reports_python, common_python]
        spec = importlib.util.spec_from_file_location(
            "executive_report_handler_layeronly", handler_path
        )
        module = importlib.util.module_from_spec(spec)
        # El layer NO tiene matplotlib: debe reproducirse el fallo de import.
        with pytest.raises((ImportError, ModuleNotFoundError)):
            spec.loader.exec_module(module)
    finally:
        sys.path = saved_path
        sys.modules.clear()
        sys.modules.update(saved_modules)
