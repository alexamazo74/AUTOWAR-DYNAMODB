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
