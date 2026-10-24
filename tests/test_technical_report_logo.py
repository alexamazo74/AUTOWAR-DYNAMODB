"""
Prueba de REGRESION del logo en el reporte TECNICO (XLSX) - FEAT-002, BUG 2.

El reporte tecnico incrusta el logo de GFourmis en la hoja 'Resumen' con
openpyxl, que delega en Pillow (PIL) para procesar la imagen. El bug reportado:
el layer 'reports' empaquetado NO contenia Pillow, asi que en Lambda openpyxl no
podia incrustar la imagen y el XLSX salia SIN logo.

Dos angulos de prueba, ambos ejecutables en Windows (el entorno de CI/dev):

  1) test_resumen_xlsx_contiene_logo_embebido: prueba la LOGICA del handler.
     Genera el XLSX con el interprete actual (Pillow disponible para el proceso)
     y verifica que el logo quede embebido en la hoja 'Resumen'. Reproduce el
     camino feliz que en Lambda usara el Pillow del layer. Si el handler no
     incrustara el logo (bug de codigo), esta prueba fallaria.

  2) test_pillow_del_layer_es_binario_linux_para_lambda: prueba el ARTEFACTO.
     El layer debe traer Pillow con binarios NATIVOS para el runtime Lambda
     (Linux, manylinux2014_x86_64 / cp311), no ruedas de Windows. Afirma que el
     modulo de extension _imaging del PIL del layer existe como .so (ELF Linux),
     no como .pyd (Windows). Esto captura directamente la causa raiz: antes el
     layer no tenia Pillow; un layer con ruedas de Windows tampoco serviria en
     Lambda. NOTA: el .so de Linux NO se puede importar en el interprete Windows
     de los tests (por eso no se intenta), pero su presencia y formato SI se
     verifican de forma portable.

Afirmaciones adicionales:
  (b) resolve_asset_path('gfourmis-logo.png') devuelve una ruta y existe.

Con el layer ORIGINAL (sin Pillow) ambas pruebas de layer fallaban; tras
reconstruir el layer con ruedas manylinux/cp311 pasan.
"""

import glob
import importlib.util
import os
import sys
import zipfile
from io import BytesIO

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TECHNICAL_DIR = os.path.join(REPO_ROOT, "lambda", "report_generator_technical")
LAYER_PYTHON = os.path.join(REPO_ROOT, "lambda", "layers", "reports", "python")
LOGO_NAME = "gfourmis-logo.png"


def _load_technical_handler():
    """Importa el handler tecnico de forma aislada (como test_executive_report).

    autowar_common (del layer comun) ya esta en sys.path gracias a conftest.
    Se anade el layer reports para resolver assets; Pillow lo aporta el venv del
    proceso actual (en Lambda lo aportara el layer).
    """
    if LAYER_PYTHON not in sys.path:
        sys.path.insert(0, LAYER_PYTHON)
    if TECHNICAL_DIR not in sys.path:
        sys.path.insert(0, TECHNICAL_DIR)
    handler_path = os.path.join(TECHNICAL_DIR, "handler.py")
    spec = importlib.util.spec_from_file_location("technical_report_handler", handler_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def technical_handler():
    return _load_technical_handler()


def _synthetic_evaluation_data():
    best_practices = [
        {"bpId": "SEC01-BP01", "pilar": "security", "status": "NON_COMPLIANT",
         "severity": "CRITICAL", "description": "MFA en usuario root",
         "finding": "El usuario root no tiene MFA", "evidence": "ev",
         "remediation": "rem", "risk": "riesgo", "questionTitle": "Gestion de identidades"},
        {"bpId": "SEC02-BP01", "pilar": "security", "status": "COMPLIANT",
         "severity": "LOW", "description": "Politica IAM minima",
         "finding": "ok", "evidence": "ev", "remediation": "rem", "risk": "riesgo",
         "questionTitle": "Permisos"},
        {"bpId": "PERF01-BP01", "pilar": "performance", "status": "NON_COMPLIANT",
         "severity": "MEDIUM", "description": "Diversidad de instancias",
         "finding": "limitada", "evidence": "ev", "remediation": "rem", "risk": "riesgo",
         "questionTitle": "Seleccion de computo"},
    ]
    return {
        "metadata": {"accountId": "123456789012"},
        "pillarScores": {"security": 50.0, "performance": 0.0},
        "bestPractices": best_practices,
    }


def _xlsx_has_images(xlsx_bytes):
    """True si el .xlsx contiene al menos una imagen embebida (xl/media/)."""
    with zipfile.ZipFile(BytesIO(xlsx_bytes)) as zf:
        return any(name.startswith("xl/media/") for name in zf.namelist())


def test_resolve_asset_path_encuentra_el_logo(technical_handler):
    """(b) resolve_asset_path('gfourmis-logo.png') resuelve a un archivo existente."""
    path = technical_handler.resolve_asset_path(LOGO_NAME)
    assert path is not None, f"resolve_asset_path('{LOGO_NAME}') devolvio None"
    assert os.path.exists(path), f"La ruta resuelta no existe: {path}"


def test_resumen_xlsx_contiene_logo_embebido(technical_handler):
    """(a) la hoja 'Resumen' del XLSX tecnico embebe el logo cuando Pillow existe.

    Prueba la logica del handler (openpyxl + XLImage + add_image). Si el handler
    no incrustara el logo, no habria entradas xl/media/ en el .xlsx.
    """
    pytest.importorskip(
        "PIL",
        reason="Pillow no disponible para el interprete de los tests; el handler "
               "lo usa via openpyxl para embeber el logo (en Lambda lo aporta el layer).",
    )

    data = _synthetic_evaluation_data()
    selected = ["security", "performance"]

    content = technical_handler.generate_technical_report(
        data, selected, "123456789012", "2025-01-01T00:00:00Z", None
    )

    assert isinstance(content, (bytes, bytearray))
    assert len(content) > 0, "El reporte tecnico no debe venir vacio"
    assert _xlsx_has_images(bytes(content)), (
        "La hoja 'Resumen' del XLSX tecnico NO contiene imagenes embebidas: el "
        "logo no se incrusto. El handler debe incrustar gfourmis-logo.png via "
        "openpyxl.drawing.image.Image + ws.add_image."
    )


def test_pillow_del_layer_es_binario_linux_para_lambda():
    """El Pillow del layer debe traer binarios para el runtime Lambda (Linux).

    openpyxl incrusta imagenes via Pillow, cuyo modulo de extension es _imaging.
    En el layer destinado a Lambda, _imaging debe estar compilado para Linux
    (archivo .so, ELF), no para Windows (.pyd). Esta prueba es portable: verifica
    presencia y formato del binario SIN importarlo (el .so Linux no carga en el
    interprete Windows de los tests).

    Con el layer ORIGINAL (sin Pillow) esta prueba fallaba: no habia carpeta PIL.
    """
    pil_dir = os.path.join(LAYER_PYTHON, "PIL")
    assert os.path.isdir(pil_dir), (
        f"El layer no contiene PIL/ en {LAYER_PYTHON}. Reconstruye el layer con "
        f"ruedas manylinux2014_x86_64/cp311 (pip install --platform ... o Docker "
        f"public.ecr.aws/lambda/python:3.11)."
    )

    # Binario de extension _imaging (nombre varia por plataforma/ABI).
    so_files = glob.glob(os.path.join(pil_dir, "_imaging*.so"))
    pyd_files = glob.glob(os.path.join(pil_dir, "_imaging*.pyd"))

    assert so_files, (
        "No se encontro el binario Linux _imaging*.so en el PIL del layer. "
        f"Encontrados .pyd (Windows)={pyd_files}. El layer debe construirse para "
        f"el runtime Lambda (Linux), no con ruedas de Windows."
    )

    # Confirmar que el .so es un ELF (magic bytes 0x7f 'E' 'L' 'F').
    with open(so_files[0], "rb") as fh:
        magic = fh.read(4)
    assert magic == b"\x7fELF", (
        f"El binario {os.path.basename(so_files[0])} no es un ELF de Linux "
        f"(magic={magic!r}); el layer no sirve para el runtime Lambda."
    )
