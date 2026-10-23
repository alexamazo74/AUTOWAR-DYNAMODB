"""
Prueba de REGRESION del logo en el reporte TECNICO (XLSX) - FEAT-002, BUG 2.

El reporte tecnico incrusta el logo de GFourmis en la hoja 'Resumen' con
openpyxl, que delega en Pillow (PIL) para procesar la imagen. Si el layer
'reports' NO contiene PIL, openpyxl no puede embeber la imagen y el XLSX sale
SIN logo (el bug reportado por el usuario).

Reto de aislamiento
-------------------
El venv de desarrollo (Windows) SI tiene Pillow/matplotlib/numpy instalados,
asi que ejecutar la generacion dentro del propio proceso de pytest usaria el PIL
del venv y la imagen se embeberia SIEMPRE, enmascarando el bug del layer. Para
probar FIELMENTE el contrato del LAYER, la generacion del XLSX corre en un
SUBPROCESO aislado:

  - python -S (sin site-packages del venv),
  - con sys.path = [ layer reports/python, report_generator_technical,
    common/python ] y NADA del venv,
  - stubbeando autowar_common.report_storage (que importa boto3 a nivel de
    modulo y no esta disponible sin site) para poder importar el handler.

Asi PIL solo existe si el LAYER lo contiene. El subproceso genera el .xlsx; el
proceso padre (con su venv) lo abre y verifica que haya imagenes embebidas.

Afirmaciones:
  (a) la hoja 'Resumen' del XLSX tiene al menos una imagen embebida
      (entradas en xl/media/ del zip del .xlsx);
  (b) resolve_asset_path('gfourmis-logo.png') devuelve una ruta y existe.

Debe FALLAR con el layer ACTUAL (sin Pillow: no se embebe la imagen) y PASAR
tras reconstruir el layer con Docker (public.ecr.aws/lambda/python:3.11).
"""

import os
import subprocess
import sys
import tempfile
import zipfile

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TECHNICAL_DIR = os.path.join(REPO_ROOT, "lambda", "report_generator_technical")
LAYER_PYTHON = os.path.join(REPO_ROOT, "lambda", "layers", "reports", "python")
COMMON_LAYER = os.path.join(REPO_ROOT, "lambda", "layers", "common", "python")
LOGO_NAME = "gfourmis-logo.png"


# Script que corre EN EL SUBPROCESO aislado. Construye evaluation_data
# sintetico, importa el handler tecnico usando SOLO el layer reports para
# openpyxl/PIL (stubbeando report_storage), genera el XLSX y lo escribe a disco.
_CHILD_SCRIPT = r'''
import importlib.util
import os
import sys
import types

LAYER_PYTHON = sys.argv[1]
TECHNICAL_DIR = sys.argv[2]
OUT_PATH = sys.argv[3]

# sys.path controlado: el layer reports debe proveer openpyxl + PIL.
sys.path.insert(0, LAYER_PYTHON)
sys.path.insert(0, TECHNICAL_DIR)

# Stub de autowar_common.report_storage: el handler lo importa a nivel de modulo
# (y este arrastra boto3, no disponible con -S). No se usa en la generacion.
pkg = types.ModuleType("autowar_common")
pkg.__path__ = []
mod = types.ModuleType("autowar_common.report_storage")
mod.upload_report = lambda *a, **k: "stub-key"
mod.generate_signed_url = lambda *a, **k: "https://stub.invalid/url"
pkg.report_storage = mod
sys.modules["autowar_common"] = pkg
sys.modules["autowar_common.report_storage"] = mod

handler_path = os.path.join(TECHNICAL_DIR, "handler.py")
spec = importlib.util.spec_from_file_location("technical_report_handler", handler_path)
handler = importlib.util.module_from_spec(spec)
spec.loader.exec_module(handler)

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
evaluation_data = {
    "metadata": {"accountId": "123456789012"},
    "pillarScores": {"security": 50.0, "performance": 0.0},
    "bestPractices": best_practices,
}
selected = ["security", "performance"]

content = handler.generate_technical_report(
    evaluation_data, selected, "123456789012", "2025-01-01T00:00:00Z", None
)
with open(OUT_PATH, "wb") as fh:
    fh.write(content)
'''


def _xlsx_has_images(xlsx_path):
    """True si el .xlsx contiene al menos una imagen embebida (xl/media/)."""
    with zipfile.ZipFile(xlsx_path) as zf:
        return any(name.startswith("xl/media/") for name in zf.namelist())


def test_resolve_asset_path_encuentra_el_logo():
    """(b) resolve_asset_path('gfourmis-logo.png') resuelve a un archivo existente.

    Se importa el handler de forma aislada (como test_executive_report.py),
    anadiendo el layer reports a sys.path. Esta parte no depende de PIL.
    """
    import importlib.util

    if LAYER_PYTHON not in sys.path:
        sys.path.insert(0, LAYER_PYTHON)
    if TECHNICAL_DIR not in sys.path:
        sys.path.insert(0, TECHNICAL_DIR)

    handler_path = os.path.join(TECHNICAL_DIR, "handler.py")
    spec = importlib.util.spec_from_file_location("technical_report_handler_rp", handler_path)
    handler = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(handler)

    path = handler.resolve_asset_path(LOGO_NAME)
    assert path is not None, f"resolve_asset_path('{LOGO_NAME}') devolvio None"
    assert os.path.exists(path), f"La ruta resuelta no existe: {path}"


def test_resumen_xlsx_contiene_logo_embebido(tmp_path):
    """(a) la hoja 'Resumen' tiene imagen embebida usando el PIL DEL LAYER.

    Corre la generacion del XLSX en un subproceso aislado (python -S) cuyo
    sys.path usa SOLO el layer reports para openpyxl/PIL. Si el layer no tiene
    Pillow, openpyxl no puede embeber el logo y el XLSX sale SIN imagenes.
    """
    out_path = os.path.join(str(tmp_path), "technical_report.xlsx")

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, encoding="utf-8"
    ) as script_file:
        script_file.write(_CHILD_SCRIPT)
        script_path = script_file.name

    try:
        # -S: ignora site-packages del venv -> PIL/openpyxl solo desde el layer.
        result = subprocess.run(
            [sys.executable, "-S", script_path, LAYER_PYTHON, TECHNICAL_DIR, out_path],
            capture_output=True,
            text=True,
        )
    finally:
        os.unlink(script_path)

    assert result.returncode == 0 and os.path.exists(out_path), (
        "El subproceso no genero el XLSX usando solo el layer reports. "
        "Probablemente faltan dependencias en el layer (openpyxl/PIL). "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )

    assert _xlsx_has_images(out_path), (
        "La hoja 'Resumen' del XLSX tecnico NO contiene imagenes embebidas: "
        "el logo no se incrusto porque el layer reports no tiene Pillow (PIL). "
        "Reconstruye el layer con Docker (public.ecr.aws/lambda/python:3.11)."
    )
