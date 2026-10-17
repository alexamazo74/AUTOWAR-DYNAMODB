"""
Configuración compartida de pytest para la suite de pruebas de AutoWAR.

Ajusta sys.path para poder importar:
  - El paquete `autowar_common` (que en producción vive en el layer común,
    bajo lambda/layers/common/python/).
  - Los módulos del evaluador de seguridad (lambda/evaluators/security/),
    que usan imports planos como `from all_bp_evaluations import *`.

Mock de sesión boto3 FIEL
--------------------------
El código de producción usa cláusulas como
`except client.exceptions.NoSuchEntityException:`. Un mock casero que no expone
`.exceptions` provoca un `AttributeError` falso-positivo (y así fallaba el
`_DenyingClient` anterior). Para ser fieles, construimos clientes boto3 REALES
(con credenciales ficticias y región fija) y los envolvemos en un proxy
`ScriptedClient` que:
  - delega `client.exceptions` (y cualquier atributo no-operación) al cliente
    real, preservando las clases de excepción reales (p.ej.
    `NoSuchEntityException` del cliente iam);
  - intercepta las operaciones de API devolviendo una respuesta guionada o
    lanzando un `ClientError` guionado (AccessDenied por defecto).

Nunca se invoca una operación real contra AWS: el proxy resuelve todo con el
"guion" (scripts) o con deny-by-default.

Fixtures expuestas:
  - `security_handler`: importa (y recarga) el módulo handler.py del evaluador.
  - `denying_session`: sesión donde TODA operación falla con AccessDenied, pero
    `client.exceptions.<X>` existe. Mantiene nombre y semántica previos.
  - `scripted_session`: factory para construir sesiones con respuestas/errores
    por servicio y operación (rutas COMPLIANT/NON_COMPLIANT/PENDING_REVIEW).
"""

import os
import sys

import boto3
import pytest
from botocore.exceptions import ClientError

# --- Rutas del proyecto ---
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMMON_LAYER = os.path.join(REPO_ROOT, "lambda", "layers", "common", "python")
SECURITY_DIR = os.path.join(REPO_ROOT, "lambda", "evaluators", "security")

# El layer común expone el paquete `autowar_common`.
if COMMON_LAYER not in sys.path:
    sys.path.insert(0, COMMON_LAYER)

# El evaluador de seguridad usa imports planos (`from all_bp_evaluations import *`,
# `from autowar_common...`), así que su carpeta debe estar en sys.path.
if SECURITY_DIR not in sys.path:
    sys.path.insert(0, SECURITY_DIR)


# ---------------------------------------------------------------------------
# Entorno: credenciales/region ficticias para no leer credenciales reales.
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True, scope="session")
def _fake_aws_env():
    """Fija credenciales y región ficticias durante toda la sesión de pruebas.

    boto3 construye los clientes sin validar credenciales hasta la primera
    llamada real (que en estos tests nunca ocurre, porque el proxy la
    intercepta). Fijar estas variables evita que boto3 intente leer un perfil o
    las credenciales reales del entorno.
    """
    previous = {}
    env = {
        "AWS_DEFAULT_REGION": "us-east-1",
        "AWS_ACCESS_KEY_ID": "testing",
        "AWS_SECRET_ACCESS_KEY": "testing",
        "AWS_SESSION_TOKEN": "testing",
    }
    for key, value in env.items():
        previous[key] = os.environ.get(key)
        os.environ[key] = value
    try:
        yield
    finally:
        for key, old in previous.items():
            if old is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = old


@pytest.fixture
def security_handler():
    """Importa el módulo handler.py del evaluador de seguridad.

    Se importa dentro de la fixture (no a nivel de módulo) para que el ajuste
    de sys.path de arriba ya esté aplicado.
    """
    import importlib

    import handler as security_handler_module  # noqa: WPS433 (import local intencional)

    importlib.reload(security_handler_module)
    return security_handler_module


# ---------------------------------------------------------------------------
# Mock fiel: clientes boto3 reales + proxy guionado.
# ---------------------------------------------------------------------------

# Sentinela para "no hay guion para esta operación".
_UNSET = object()


class ScriptedClient:
    """Proxy sobre un cliente boto3 REAL que guiona sus operaciones.

    `scripts` es un dict {operation_name: directiva}, donde `operation_name` es
    el nombre snake_case de la operación boto3 (p.ej. 'get_account_summary') y
    la directiva es:
      - {'response': <dict>}  -> la operación devuelve ese dict tal cual.
      - {'error': ('Code', 'Message')} -> la operación lanza un ClientError con
        ese Code/Message.
      - {'raise': <excepción_ya_instanciada>} -> la operación relanza esa
        excepción (útil para excepciones modeladas como NoSuchEntityException).
      - un callable -> se llama con (*args, **kwargs) y se devuelve su resultado.

    `deny_by_default`: si no hay guion para una operación invocada, lanza
    AccessDenied (True) o un ClientError genérico. Esto reproduce el camino
    "sin permisos / sin datos" sin romper `.exceptions`.
    """

    def __init__(self, real_client, scripts, deny_by_default=True):
        # Se usa object.__setattr__ para no colisionar con __getattr__.
        object.__setattr__(self, "_real_client", real_client)
        object.__setattr__(self, "_scripts", scripts or {})
        object.__setattr__(self, "_deny_by_default", deny_by_default)

    def __getattr__(self, name):
        real_client = object.__getattribute__(self, "_real_client")

        # Preservar las clases de excepción reales del servicio.
        if name == "exceptions":
            return real_client.exceptions

        # ¿Es una operación de API del servicio? (meta.method_to_api_mapping
        # contiene las operaciones snake_case disponibles.)
        method_map = real_client.meta.method_to_api_mapping
        if name in method_map:
            return self._make_operation(name)

        # Cualquier otro atributo (meta, waiters, etc.) se delega al cliente real.
        return getattr(real_client, name)

    def _make_operation(self, name):
        scripts = object.__getattribute__(self, "_scripts")
        deny_by_default = object.__getattribute__(self, "_deny_by_default")

        def _operation(*args, **kwargs):
            directive = scripts.get(name, _UNSET)

            if directive is _UNSET:
                if deny_by_default:
                    raise ClientError(
                        {
                            "Error": {
                                "Code": "AccessDenied",
                                "Message": f"stubbed deny ({name})",
                            }
                        },
                        name,
                    )
                raise ClientError(
                    {
                        "Error": {
                            "Code": "InvalidAction",
                            "Message": f"sin guion para la operación {name}",
                        }
                    },
                    name,
                )

            if callable(directive):
                return directive(*args, **kwargs)

            if "raise" in directive:
                raise directive["raise"]

            if "error" in directive:
                code, message = directive["error"]
                raise ClientError(
                    {"Error": {"Code": code, "Message": message}}, name
                )

            if "response" in directive:
                return directive["response"]

            raise AssertionError(
                f"Directiva de guion inválida para {name}: {directive!r}"
            )

        return _operation


class ScriptedSession:
    """Sesión boto3 falsa que entrega `ScriptedClient` por servicio.

    `scripts_by_service` es {service_name: {operation: directiva}}. Los clientes
    reales se cachean por servicio para reusar sus modelos y `.exceptions`.
    """

    # Caché de clase para clientes boto3 reales (compartida entre instancias),
    # porque construirlos tiene un costo no trivial y son inmutables aquí.
    _real_client_cache = {}

    def __init__(self, scripts_by_service=None, region_name="us-east-1", deny_by_default=True):
        self.scripts_by_service = scripts_by_service or {}
        self.region_name = region_name
        self._deny_by_default = deny_by_default

    @classmethod
    def _get_real_client(cls, service_name, region_name):
        key = (service_name, region_name)
        if key not in cls._real_client_cache:
            real_session = boto3.Session(region_name=region_name)
            cls._real_client_cache[key] = real_session.client(service_name)
        return cls._real_client_cache[key]

    def client(self, service_name, *_args, **kwargs):
        region = kwargs.get("region_name", self.region_name)
        real_client = self._get_real_client(service_name, region)
        scripts = self.scripts_by_service.get(service_name, {})
        return ScriptedClient(
            real_client, scripts, deny_by_default=self._deny_by_default
        )


@pytest.fixture
def denying_session():
    """Sesión boto3 falsa donde toda llamada AWS falla con AccessDenied.

    A diferencia del mock casero anterior, expone `client.exceptions.<X>` real,
    de modo que las cláusulas `except client.exceptions.NoSuchEntityException`
    se resuelven sin AttributeError y cada BP cae a su rama de error/pending con
    un finding válido y completo.
    """
    return ScriptedSession(deny_by_default=True)


def _bp_id_from_func_name(func_name):
    """Convierte 'evaluate_sec02_bp01' -> 'SEC02-BP01'."""
    # func_name = evaluate_secNN_bpMM
    parts = func_name.split("_")  # ['evaluate', 'secNN', 'bpMM']
    sec = parts[1].upper()  # 'SECNN'
    bp = parts[2].upper()  # 'BPMM'
    return f"{sec}-{bp}"


def iter_bp_invokers(security_handler, session):
    """Devuelve una lista [(bp_id, invoker)] para las 63 BPs del pilar.

    - Las 61 BPs implementadas como funciones `evaluate_secNN_bpMM(session, handle)`
      en `all_bp_evaluations` se invocan con (session, evaluator._handle_permission_error).
    - Las 2 BPs inline (SEC01-BP01, SEC01-BP02) se invocan vía los métodos del
      `SecurityEvaluator`.

    `invoker` es un callable sin argumentos que ejecuta la BP y devuelve el finding.
    El orden sigue el de `handler.evaluate()` por pregunta y número de BP.
    """
    import all_bp_evaluations as bp_module

    evaluator = security_handler.SecurityEvaluator(session, region="us-east-1")

    invokers = []
    for sec in range(1, 12):
        n_bps = {
            1: 8, 2: 6, 3: 9, 4: 4, 5: 4, 6: 5, 7: 4, 8: 4, 9: 3, 10: 8, 11: 8,
        }[sec]
        for bp_num in range(1, n_bps + 1):
            func_name = f"evaluate_sec{sec:02d}_bp{bp_num:02d}"
            bp_id = f"SEC{sec:02d}-BP{bp_num:02d}"

            if sec == 1 and bp_num == 1:
                invokers.append((bp_id, evaluator._evaluate_sec01_bp01))
                continue
            if sec == 1 and bp_num == 2:
                invokers.append((bp_id, evaluator._evaluate_sec01_bp02))
                continue

            func = getattr(bp_module, func_name)

            def _make(fn):
                return lambda: fn(session, evaluator._handle_permission_error)

            invokers.append((bp_id, _make(func)))

    return invokers


@pytest.fixture
def scripted_session():
    """Factory para construir una `ScriptedSession` con guiones por servicio.

    Uso:
        session = scripted_session({
            "iam": {
                "get_account_password_policy": {"response": {"PasswordPolicy": {...}}},
                "get_account_summary": {"response": {"SummaryMap": {...}}},
                "list_users": {"response": {"Users": []}},
            },
            "sso-admin": {"list_instances": {"response": {"Instances": []}}},
        })

    Operaciones sin guion lanzan AccessDenied por defecto (deny_by_default=True),
    salvo que se pase deny_by_default=False.
    """

    def _factory(scripts_by_service=None, deny_by_default=True):
        return ScriptedSession(
            scripts_by_service=scripts_by_service,
            deny_by_default=deny_by_default,
        )

    return _factory
