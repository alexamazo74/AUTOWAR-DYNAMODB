"""
Prueba de CONTRATO del layer 'reports' (FEAT-002, BUG 2).

El layer 'reports' se empaqueta con lambda_.Code.from_asset(...), que copia el
directorio tal cual (NO corre pip). Por eso lambda/layers/reports/python/ DEBE
contener, precompiladas, todas las dependencias declaradas en requirements.txt.

Esta prueba lee requirements.txt y afirma que, para cada paquete declarado,
existe su carpeta/modulo de import dentro de python/. Incluye numpy como
dependencia transitiva OBLIGATORIA de matplotlib.

Debe FALLAR con el layer ACTUAL (faltan PIL/, matplotlib/, numpy/) y PASAR tras
reconstruir el layer con Docker (imagen public.ecr.aws/lambda/python:3.11) via
BundlingOptions de CDK o build-layer.sh.
"""

import os
import re

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORTS_LAYER = os.path.join(REPO_ROOT, "lambda", "layers", "reports")
LAYER_PYTHON = os.path.join(REPORTS_LAYER, "python")
REQUIREMENTS = os.path.join(REPORTS_LAYER, "requirements.txt")

# Mapeo nombre pip -> nombre de import (carpeta/modulo dentro de python/).
PIP_TO_IMPORT = {
    "openpyxl": "openpyxl",
    "python-docx": "docx",
    "matplotlib": "matplotlib",
    "Pillow": "PIL",
}

# Dependencias transitivas obligatorias que tambien deben estar en el layer.
# numpy es imprescindible para que matplotlib importe.
REQUIRED_TRANSITIVE = ["numpy"]


def _parse_requirements():
    """Devuelve la lista de nombres de paquete declarados en requirements.txt."""
    names = []
    with open(REQUIREMENTS, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # Separar nombre de la especificacion de version (==, >=, etc.).
            name = re.split(r"[=<>!~ ]", line, maxsplit=1)[0].strip()
            if name:
                names.append(name)
    return names


def _import_module_exists(import_name):
    """True si existe python/<import_name>/ o python/<import_name>.py."""
    pkg_dir = os.path.join(LAYER_PYTHON, import_name)
    module_file = os.path.join(LAYER_PYTHON, import_name + ".py")
    return os.path.isdir(pkg_dir) or os.path.isfile(module_file)


def test_requirements_file_existe():
    assert os.path.isfile(REQUIREMENTS), (
        f"No se encontro requirements.txt del layer en {REQUIREMENTS}"
    )


def test_layer_python_dir_existe():
    assert os.path.isdir(LAYER_PYTHON), (
        f"No existe el directorio empaquetado del layer: {LAYER_PYTHON}"
    )


@pytest.mark.parametrize("pip_name", _parse_requirements())
def test_cada_paquete_de_requirements_esta_en_el_layer(pip_name):
    """Cada paquete de requirements.txt debe tener su modulo de import en python/."""
    import_name = PIP_TO_IMPORT.get(pip_name, pip_name)
    assert _import_module_exists(import_name), (
        f"El paquete '{pip_name}' (import '{import_name}') declarado en "
        f"requirements.txt NO esta en {LAYER_PYTHON}. Reconstruye el layer "
        f"(Docker: public.ecr.aws/lambda/python:3.11) con build-layer.sh o "
        f"BundlingOptions de CDK."
    )


@pytest.mark.parametrize("import_name", REQUIRED_TRANSITIVE)
def test_dependencias_transitivas_obligatorias_en_el_layer(import_name):
    """numpy (transitiva de matplotlib) debe estar presente en el layer."""
    assert _import_module_exists(import_name), (
        f"La dependencia transitiva obligatoria '{import_name}' NO esta en "
        f"{LAYER_PYTHON}. matplotlib no puede importar sin numpy. Reconstruye "
        f"el layer con Docker (public.ecr.aws/lambda/python:3.11)."
    )
