"""
Prueba de REGRESIÓN: los nombres de servicio usados en session.client('...')
dentro de los evaluadores deben ser nombres OFICIALES de botocore.

Contexto del bug: las pruebas previas usaban MagicMock para session.client, que
acepta CUALQUIER cadena sin validar. Por eso un nombre inválido como
'elasticloadbalancing' (el correcto es 'elbv2') pasó desapercibido y reventaba
en producción con UnknownServiceError. Esta prueba NO usa mocks: obtiene la
lista oficial de servicios de botocore y afirma que cada literal extraído de los
evaluadores está en ella.

FALLARÍA si se reintrodujera 'elasticloadbalancing' (o cualquier nombre que
botocore no conozca) y PASA con los nombres corregidos (p.ej. 'elbv2').
"""

import glob
import os
import re

import botocore.session

# Raíz del repo y carpeta de evaluadores.
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVALUATORS_GLOB = os.path.join(REPO_ROOT, "lambda", "evaluators", "**", "*.py")

# Captura el literal de servicio en .client('xxx') / .client("xxx"),
# admitiendo espacios y argumentos extra (p.ej. .client('s3', region_name=...)).
_CLIENT_LITERAL = re.compile(r"\.client\(\s*['\"]([a-zA-Z0-9_\-]+)['\"]")


def _official_service_names():
    """Lista oficial de nombres de servicio reconocidos por botocore."""
    return set(botocore.session.get_session().get_available_services())


def _iter_client_literals():
    """Recorre los archivos de evaluadores y extrae (archivo, nombre_servicio)."""
    for path in glob.glob(EVALUATORS_GLOB, recursive=True):
        with open(path, encoding="utf-8") as fh:
            source = fh.read()
        for match in _CLIENT_LITERAL.finditer(source):
            yield os.path.relpath(path, REPO_ROOT), match.group(1)


def test_performance_evaluator_files_exist():
    """Sanidad: los archivos clave del evaluador de performance existen y se
    escanean (evita un falso verde si el glob no encontrara nada)."""
    scanned = {path for path, _ in _iter_client_literals()}
    perf_handler = os.path.join("lambda", "evaluators", "performance", "handler.py")
    perf_bps = os.path.join("lambda", "evaluators", "performance", "all_bp_evaluations.py")
    assert os.path.exists(os.path.join(REPO_ROOT, perf_bps)), (
        "No existe all_bp_evaluations.py del pilar de performance"
    )
    # all_bp_evaluations.py contiene los session.client(...) del pilar.
    assert perf_bps in scanned, (
        f"El escaneo no cubrió {perf_bps}; literales encontrados en: {sorted(scanned)}"
    )
    # handler.py puede o no tener literales; solo verificamos que exista.
    assert os.path.exists(os.path.join(REPO_ROOT, perf_handler)), (
        "No existe handler.py del pilar de performance"
    )


def test_all_client_service_names_are_official():
    """Cada nombre de servicio en session.client('...') debe ser oficial de botocore."""
    official = _official_service_names()
    invalid = [
        (path, name)
        for path, name in _iter_client_literals()
        if name not in official
    ]
    assert not invalid, (
        "Nombres de servicio inválidos (no reconocidos por botocore) en los "
        f"evaluadores: {invalid}. Usar el nombre oficial (p.ej. 'elbv2' en lugar "
        "de 'elasticloadbalancing')."
    )
