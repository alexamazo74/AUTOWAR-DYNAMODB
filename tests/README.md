# Suite de pruebas — pilar de Seguridad (AutoWAR)

Pruebas automatizadas del evaluador del pilar de **Security** (11 preguntas SEC01..SEC11, 63 Best
Practices) que corren **sin cuenta AWS real**, usando un mock de sesión boto3 fiel.

## Cómo correr la suite

Desde la raíz del repo (`auto-war`):

```powershell
# Modo por defecto (mocks; omite integración). Recomendado.
.\run-tests.ps1

# Incluye además la prueba de integración contra la cuenta AWS real.
.\run-tests.ps1 -Integration
```

O directamente con el intérprete del venv del proyecto:

```powershell
# Equivalente al modo por defecto:
.venv\Scripts\python.exe -m pytest -q -m "not integration"

# Solo la prueba de integración (se auto-salta si no hay credenciales):
.venv\Scripts\python.exe -m pytest -q -m integration
```

`pytest.ini` define `testpaths = tests`, `addopts = -q --strict-markers` y el marcador `integration`.
`run-tests.ps1` usa el venv `.venv` si existe.

### Resultado esperado (modo por defecto)

`90 passed, 1 deselected, 8 xfailed`. Los `xfailed` corresponden a 4 bugs reales de producción
documentados (ver abajo); no son fallos.

## Estructura de la suite

| Archivo | Qué cubre |
|---|---|
| `conftest.py` | Mock fiel de sesión boto3 + fixtures (`denying_session`, `scripted_session`), ajuste de `sys.path`, registro de las 63 BPs (`iter_bp_invokers`). |
| `_helpers.py` | Constantes del contrato de findings y `assert_finding_contract`. |
| `test_calculations.py` | Funciones puras de scoring/distribuciones (`autowar_common.calculations`). |
| `test_security_structure.py` | Contrato del pilar recorriendo las 63 BPs individualmente. |
| `test_security_bps.py` | Rutas explícitas por BP (COMPLIANT / NON_COMPLIANT / PENDING_REVIEW / AccessDenied) + patrón parametrizado reutilizable. |
| `test_security_bugs.py` | Pruebas `xfail` que evidencian los bugs reales de producción. |
| `test_integration_security.py` | Integración opcional contra la cuenta real (marcador `integration`). |

## Diseño del mock fiel (por qué clientes reales + proxy)

Algunas BPs usan cláusulas como `except client.exceptions.NoSuchEntityException:`. Un mock casero que no
expone `.exceptions` provoca un `AttributeError` falso-positivo (así fallaba el `_DenyingClient` anterior).

El mock (`conftest.py`) construye **clientes boto3 reales** (con credenciales ficticias y región fija) y los
envuelve en un proxy `ScriptedClient` que:

- delega `client.exceptions` al cliente real → las clases de excepción reales existen (p.ej.
  `NoSuchEntityException` del cliente `iam`);
- intercepta cada operación de API devolviendo una respuesta guionada o lanzando un `ClientError`
  guionado. **Nunca** se llama a AWS real.

No se usó `moto` como base porque no cubre de forma uniforme los 43 servicios del pilar y no da control fino
para forzar AccessDenied por operación. Los clientes reales + proxy preservan `.exceptions` con fidelidad y
son rápidos (los clientes se cachean).

Fixtures:

- `denying_session`: toda operación lanza `AccessDenied`, pero `client.exceptions.<X>` existe. Ejercita la
  ruta "sin permisos / degradada" de cada BP.
- `scripted_session(scripts_by_service, deny_by_default=True)`: factory para declarar respuestas/errores por
  servicio y operación. Operaciones sin guion → `AccessDenied` por defecto.

Formato del guion por operación:

```python
scripts = {
    "iam": {
        "get_account_password_policy": {"response": {"PasswordPolicy": {...}}},
        "get_account_summary": {"error": ("AccessDenied", "msg")},
        "list_users": {"raise": <excepción_ya_instanciada>},   # p.ej. NoSuchEntityException real
        "list_mfa_devices": lambda **kw: {"MFADevices": []},    # callable
    },
}
```

## Cómo añadir un test por BP (patrón reutilizable)

1. Lee la función de la BP en `lambda/evaluators/security/all_bp_evaluations.py` (o el método inline en
   `handler.py` para SEC01-BP01/BP02) e identifica **qué operaciones** llama y en qué orden.
2. Decide la ruta a probar y construye el `scripts` necesario para alcanzarla (recuerda: lo no guionado
   lanza AccessDenied).
3. Invoca la BP:
   - función: `evaluate_secNN_bpMM(scripted_session(scripts), handle_error_func)`.
   - inline: `SecurityEvaluator(scripted_session(scripts), "us-east-1")._evaluate_sec01_bpMM()`.
4. **Ejecuta el test y observa el `status` REAL** que devuelve el código. Fija la aserción a ese status
   observado (no a uno asumido). Valida siempre `assert_finding_contract(finding, expected_bp=...)`.
5. Para extender el patrón parametrizado, añade una fila
   `(func_name, scripts, expected_status)` a `_PARAM_BPS` en `test_security_bps.py`
   (`expected_status=None` si solo quieres validar el contrato).

## Bugs reales de producción encontrados

El mock fiel reveló **4 bugs** (no se corrigió el código; el objetivo es TESTS). Están en
`.agents/tasks/bugs-encontrados-seguridad.md` con `archivo:línea`, causa y fix propuesto, y cada uno queda
marcado `xfail`:

- SEC02-BP05, SEC07-BP02, SEC09-BP01: `UnboundLocalError` ante AccessDenied (variable asignada dentro de un
  `try` interno y leída tras el `except`).
- SEC10-BP08: `description` vacía porque falta la clave `'SEC10-BP08'` en `SECURITY_BP_DESCRIPTIONS`.

Cuando se corrijan, los `xfail` pasarán a `xpass` (señal para endurecer los tests) y la suite estructural
podrá volver a basarse en `SecurityEvaluator.evaluate()` end-to-end.

## Prueba de integración

`test_integration_security.py` usa un `boto3.Session()` real, se auto-salta si `sts.get_caller_identity()`
falla (sin credenciales), y si hay credenciales valida el contrato de alto nivel (11 preguntas, 63 BPs,
scores en rango). Se omite en el modo por defecto. La región se puede fijar con la variable de entorno
`AUTOWAR_INTEGRATION_REGION` (por defecto `us-east-1`).
