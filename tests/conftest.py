"""
Configuración compartida de pytest para la suite de pruebas de AutoWAR.

Ajusta sys.path para poder importar:
  - El paquete `autowar_common` (que en producción vive en el layer común,
    bajo lambda/layers/common/python/).
  - Los módulos del evaluador de seguridad (lambda/evaluators/security/),
    que usan imports planos como `from all_bp_evaluations import *`.

Mock de sesión boto3 FIEL (100% en memoria, sin clientes boto3 reales)
----------------------------------------------------------------------
El código de producción usa cláusulas como
`except client.exceptions.NoSuchEntityException:`. Un mock casero que no expone
`.exceptions` provoca un `AttributeError` falso-positivo (y así fallaba el
`_DenyingClient` anterior).

Durante un tiempo se resolvió construyendo clientes boto3 REALES solo para
exponer sus `.exceptions`. Eso reintroducía un problema peor: construir y
ejercitar decenas de clientes boto3 reales por corrida (las 63 BPs del pilar,
parametrizadas) agota recursos nativos de botocore en Windows y el proceso de
pytest MUERE sin resumen ni traceback (crash nativo no determinista, siempre
alrededor de la BP ~30-40). Una suite que crashea no cumple el objetivo del
usuario (que las pruebas automáticas detecten los bugs sin pruebas funcionales).

Por eso el mock es ahora 100% en memoria, igual que el `_DenyingClient` del
pilar de performance (ver tests/test_performance_resilience.py): NUNCA se
construye un cliente boto3 real. El proxy `ScriptedClient`:
  - expone `client.exceptions.<X>` como una clase de excepción generada al vuelo
    (subclase de `botocore.exceptions.ClientError`), de modo que
    `except client.exceptions.NoSuchEntityException:` es un tipo válido y NO
    provoca AttributeError;
  - intercepta las operaciones de API devolviendo una respuesta guionada o
    lanzando un `ClientError` guionado (AccessDenied por defecto);
  - ofrece `get_paginator(op)` por robustez (paginador guionado por la misma
    operación), aunque el pilar de seguridad no usa paginadores.

Nota sobre identidad de clases de excepción: botocore crea una clase
`NoSuchEntityException` DISTINTA por cada instancia de cliente, así que una
`NoSuchEntityException` construida por el test (desde su propio cliente) nunca
fue `is`-igual a la del cliente de producción. El comportamiento observado (y
verificado) es que esa excepción NO entra en el `except` interno por clase y es
capturada por el `except ClientError` externo de la BP; el mock en memoria
preserva exactamente ese comportamiento.

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


def _load_security_bp_module():
    """Carga `all_bp_evaluations` DEL PILAR DE SEGURIDAD y lo deja en sys.modules.

    Tanto security como performance tienen un módulo `all_bp_evaluations`. Otras
    suites (p.ej. test_performance_resilience) inyectan su propio
    `sys.modules['all_bp_evaluations']` y, al no restaurarlo, dejaban envenenada
    la caché: el handler de seguridad hacía `from all_bp_evaluations import *` y
    recogía el módulo equivocado, provocando un AttributeError
    (`module 'handler' has no attribute 'SecurityEvaluator'`).

    Esta función (re)carga SIEMPRE el módulo desde SECURITY_DIR y lo fija como
    `sys.modules['all_bp_evaluations']`, de modo que el import del handler de
    seguridad sea determinista sin importar el orden de los tests.
    """
    import importlib.util

    bp_path = os.path.join(SECURITY_DIR, "all_bp_evaluations.py")
    spec = importlib.util.spec_from_file_location("all_bp_evaluations", bp_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["all_bp_evaluations"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def security_handler():
    """Carga el módulo handler.py DEL PILAR DE SEGURIDAD de forma determinista.

    Tanto security como performance tienen un `handler.py` en su carpeta, y ambas
    carpetas están en sys.path. Un simple `import handler` resuelve al primero que
    aparezca en sys.path: cuando la suite de performance inserta su carpeta en
    sys.path[0], ese `import handler` acababa resolviendo al handler de
    performance, y la fixture devolvía el módulo equivocado (de ahí el
    AttributeError: module 'handler' has no attribute 'SecurityEvaluator').

    Para blindar el seam cargamos el handler SIEMPRE desde su ruta explícita en
    SECURITY_DIR, tras fijar `sys.modules['all_bp_evaluations']` al módulo del
    pilar de seguridad (el handler hace `from all_bp_evaluations import *`).
    """
    import importlib.util

    _load_security_bp_module()

    handler_path = os.path.join(SECURITY_DIR, "handler.py")
    spec = importlib.util.spec_from_file_location("handler", handler_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["handler"] = module
    spec.loader.exec_module(module)
    return module


# ---------------------------------------------------------------------------
# Mock 100% en memoria: proxy guionado SIN clientes boto3 reales.
# ---------------------------------------------------------------------------

# Sentinela para "no hay guion para esta operación".
_UNSET = object()


class _ScriptedExceptions:
    """Namespace `client.exceptions` falso, en memoria.

    Cada atributo (`NoSuchEntityException`, etc.) se resuelve, al vuelo, a una
    subclase de `botocore.exceptions.ClientError` generada y cacheada por nombre.
    Así `except client.exceptions.NoSuchEntityException:` es siempre un tipo
    válido (no provoca AttributeError) sin construir un cliente boto3 real.

    No se busca identidad con la clase real de botocore: una excepción real
    `NoSuchEntityException` construida por el test tampoco era `is`-igual a la
    del cliente de producción (botocore crea una clase distinta por instancia de
    cliente), de modo que ese `except` interno nunca la capturaba por clase y la
    BP caía a su `except ClientError` externo. Este mock preserva ese mismo
    comportamiento porque las subclases generadas también heredan de ClientError.
    """

    def __init__(self):
        object.__setattr__(self, "_cache", {})

    def __getattr__(self, name):
        cache = object.__getattribute__(self, "_cache")
        klass = cache.get(name)
        if klass is None:
            klass = type(name, (ClientError,), {})
            cache[name] = klass
        return klass


class _ScriptedPaginator:
    """Paginador guionado por la operación subyacente (sin red).

    El pilar de seguridad no usa paginadores, pero se ofrece por robustez para
    cualquier BP que lo intente: delega en la misma directiva de la operación.
    """

    def __init__(self, operation_callable):
        self._operation_callable = operation_callable

    def paginate(self, *args, **kwargs):
        result = self._operation_callable(*args, **kwargs)
        return iter([result])


class ScriptedClient:
    """Cliente boto3 falso (100% en memoria) que guiona sus operaciones.

    NUNCA construye un cliente boto3 real: toda operación se resuelve con el
    "guion" (scripts) o con deny-by-default. `scripts` es un dict
    {operation_name: directiva}, donde `operation_name` es el nombre snake_case
    de la operación boto3 (p.ej. 'get_account_summary') y la directiva es:
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

    def __init__(self, scripts, deny_by_default=True):
        # Se usa object.__setattr__ para no colisionar con __getattr__.
        object.__setattr__(self, "_scripts", scripts or {})
        object.__setattr__(self, "_deny_by_default", deny_by_default)
        object.__setattr__(self, "_exceptions", _ScriptedExceptions())

    def __getattr__(self, name):
        # `client.exceptions.<X>` -> namespace de excepciones en memoria.
        if name == "exceptions":
            return object.__getattribute__(self, "_exceptions")

        # `client.get_paginator('op')` -> paginador guionado por esa operación.
        if name == "get_paginator":
            def _get_paginator(operation_name, *_a, **_k):
                return _ScriptedPaginator(self._make_operation(operation_name))

            return _get_paginator

        # Cualquier otro atributo se trata como una operación de API.
        return self._make_operation(name)

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

    `scripts_by_service` es {service_name: {operation: directiva}}. Es 100% en
    memoria: no construye ni cachea clientes boto3 reales (eso agotaba recursos
    nativos y tumbaba pytest en Windows). Cada `.client(...)` devuelve un
    `ScriptedClient` ligero con los guiones del servicio pedido.
    """

    def __init__(self, scripts_by_service=None, region_name="us-east-1", deny_by_default=True):
        self.scripts_by_service = scripts_by_service or {}
        self.region_name = region_name
        self._deny_by_default = deny_by_default

    def client(self, service_name, *_args, **_kwargs):
        scripts = self.scripts_by_service.get(service_name, {})
        return ScriptedClient(scripts, deny_by_default=self._deny_by_default)


@pytest.fixture
def denying_session():
    """Sesión boto3 falsa donde toda llamada AWS falla con AccessDenied.

    Expone `client.exceptions.<X>` en memoria (subclase de ClientError), de modo
    que las cláusulas `except client.exceptions.NoSuchEntityException` se
    resuelven sin AttributeError y cada BP cae a su rama de error/pending con un
    finding válido y completo, sin construir clientes boto3 reales.
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
    bp_module = _load_security_bp_module()

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
