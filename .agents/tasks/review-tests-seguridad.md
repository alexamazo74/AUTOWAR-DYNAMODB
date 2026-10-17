# Suite de pruebas del pilar de Seguridad con mock boto3 fiel

El commit `d7f281c` añade una suite pytest completa para el pilar de Security de AutoWAR (11 preguntas SEC01..SEC11, 63 BPs) que corre sin cuenta AWS real. El cambio central es un mock de sesión boto3 fiel (`ScriptedSession`/`ScriptedClient`) que construye clientes boto3 reales y los envuelve en un proxy: así `client.exceptions.<X>` resuelve a las clases de excepción reales del servicio y las cláusulas `except client.exceptions.NoSuchEntityException` dejan de romper con `AttributeError` (ese era el fallo del `_DenyingClient` previo). Sobre esa base se construyen tests estructurales por-BP, rutas explícitas para las tres BPs priorizadas, un patrón parametrizado reutilizable, un test de integración opcional auto-skippeable, y la documentación de 4 bugs reales de producción marcados `xfail`. El objetivo del trabajo fue tests, y no se tocó código de producción de los evaluadores.

Watch for: la única desviación material respecto al plan es que el mock resultó demasiado fiel y destapó 4 bugs reales de producción (3 `UnboundLocalError` ante AccessDenied + 1 `description` vacía); están documentados con archivo:línea y marcados `xfail`, no en rojo (confirmed). Un comentario de docstring en `test_security_structure.py` dice "60 sanas / 3 con bug" cuando son 59 sanas / 4 con bug (confirmed, cosmético). La evidencia de ejecución se obtuvo con `pytest.main()` en proceso en lugar del subproceso `python -m pytest` por un problema de truncado de terminal del equipo (confirmed, declarado por el coder; no bloqueante).

**Verdict**: APPROVED

## High-level view

El mock fiel es la pieza que hace viable todo lo demás. En vez de un cliente casero sin `.exceptions`, se construye el cliente boto3 real (cacheado, con credenciales ficticias de un fixture autouse) y se envuelve en un proxy que delega `exceptions` al cliente real e intercepta cada operación con un "guion" por servicio/operación (respuesta, error o `raise` de una excepción ya instanciada), con deny-by-default. Nunca se llama a AWS real. Esto satisface el criterio 1 de forma directa y verificable: el único `.exceptions.<X>` del pilar es `NoSuchEntityException` en iam (líneas 749 y 770 de `all_bp_evaluations.py`), y la ruta se ejercita explícitamente en `test_sec02_bp01_no_password_policy_uses_nosuchentity`.

La cobertura tiene dos niveles. El estructural recorre las 63 BPs individualmente bajo `denying_session` y valida contrato de finding, enums, unicidad de IDs, scores en [0,100] y distribuciones que suman 63. El por-BP cubre SEC01-BP01, SEC01-BP02 y SEC02-BP01 con rutas COMPLIANT/NON_COMPLIANT/PENDING_REVIEW/AccessDenied, más un patrón parametrizado para extender. `test_calculations.py` queda intacto con sus 11 tests puros.

Los 4 bugs reales son la novedad frente al plan, que anticipaba que no habría bugs. El equipo respetó el protocolo: no corrigió producción, documentó cada bug en `bugs-encontrados-seguridad.md` con archivo:línea y fix propuesto, y marcó los tests que los evidencian como `xfail` con `raises` específico y `reason` apuntando al doc. La invariante de 63 findings se preserva porque las BPs con crash se sustituyen por el finding degradado que `_handle_permission_error` habría producido.

El test de integración está marcado `@pytest.mark.integration`, se deselecciona en el modo por defecto (`-m "not integration"`) y se auto-salta vía `sts.get_caller_identity()` si no hay credenciales, así que nunca toca la cuenta en una corrida normal ni falla sin credenciales. `pytest.ini` y `run-tests.ps1` se respetan sin cambios, y `tests/README.md` documenta los tres comandos.

<details>
<summary>Issues (3)</summary>

1. **Docstring con conteo incorrecto** — El docstring de `test_security_structure.py` dice "60 sanas / 3 con bug"; son 59 sanas y 4 con bug (SEC10-BP08 también se xfailea en el test parametrizado). Corregir el comentario. No bloqueante, cosmético.
2. **Evidencia obtenida en proceso, no por subproceso** — El resumen de pytest (90 passed, 8 xfailed, 1 deselected) se capturó con `pytest.main()` por truncado de terminal, no con el comando mandatorio `python -m pytest`. El coder lo declara y es el mismo venv/pytest.ini; verificable re-corriendo el comando en una terminal normal. No bloqueante.
3. **4 bugs reales de producción pendientes de fix** — SEC02-BP05/SEC07-BP02/SEC09-BP01 (`UnboundLocalError` ante AccessDenied) y SEC10-BP08 (`description` vacía por clave ausente). Documentados y xfail. Fuera del alcance de este trabajo (tests), pero deben abrirse como trabajo de producción: con permisos parciales estos bugs rompen `evaluate()` → 500.

</details>

<details>
<summary>Details</summary>

## Mock fiel: clientes reales + proxy guionado

`ScriptedClient.__getattr__` devuelve `real_client.exceptions` para el atributo `exceptions`, resuelve las operaciones snake_case contra `meta.method_to_api_mapping` y delega el resto al cliente real. El guion por operación admite `{'response': ...}`, `{'error': ('Code','Msg')}`, `{'raise': <exc instanciada>}` o un callable, con `deny_by_default=True` que lanza `ClientError` AccessDenied para lo no guionado. Esto cumple el criterio 1: el conftest ya no usa `_DenyingClient` sin `.exceptions`, `denying_session` conserva nombre y semántica (todo AccessDenied) pero ahora sobre clientes reales, y `sys.path` inserta `COMMON_LAYER` (autowar_common) y `SECURITY_DIR` (confirmed, conftest.py líneas 43-56).

El caso crítico que justifica el diseño está probado end-to-end: `test_sec02_bp01_no_password_policy_uses_nosuchentity` (test_security_bps.py) instancia una `NoSuchEntityException` real del cliente iam y la inyecta vía `{'raise': ...}`, forzando la rama `except client.exceptions.NoSuchEntityException` de `evaluate_sec02_bp01` (confirmed, `all_bp_evaluations.py:749`). Con el mock casero previo esta rama lanzaba `AttributeError`; ahora resuelve y el finding sale `PENDING_REVIEW`. El test afirma el status real observado, no uno asumido.

El fixture autouse `_fake_aws_env` fija región y credenciales ficticias con save/restore del entorno previo, evitando que boto3 lea un perfil real al construir clientes. Los clientes reales se cachean por `(service, region)` a nivel de clase, lo que mantiene la construcción barata pese a crear clientes reales de ~43 servicios.

## Cobertura estructural y por-BP

El criterio 2 se cumple en `test_security_structure.py`: `test_pillar_has_eleven_questions` valida SEC01..SEC11 y el reparto exacto por pregunta (8,6,9,4,4,5,4,4,3,8,8 = 63); `test_each_bp_returns_valid_finding_under_access_denied` está parametrizado sobre las 63 BPs; `test_scores_within_range` valida [0,100]; y `test_distributions_match_finding_counts` comprueba que compliance y severity suman 63. El contrato se centraliza en `_helpers.assert_finding_contract` con los enums correctos (status ∈ {COMPLIANT,NON_COMPLIANT,PENDING_REVIEW}, severity ∈ {CRITICAL,HIGH,MEDIUM,LOW}) y campos de texto no vacíos. `test_calculations.py` conserva sus 11 tests (confirmed, git show del commit: 11 defs).

El criterio 3 se cumple en `test_security_bps.py`: SEC01-BP01 tiene COMPLIANT, PENDING_REVIEW, NON_COMPLIANT (single-account), rama "no Organizations" y AccessDenied degradado; SEC01-BP02 tiene COMPLIANT, NON_COMPLIANT/CRITICAL, PENDING_REVIEW (MFA virtual root) y AccessDenied → PENDING_REVIEW/MEDIUM; SEC02-BP01 tiene COMPLIANT, política débil, la ruta NoSuchEntity y AccessDenied. El patrón parametrizado `_PARAM_BPS` + `test_bp_scripted_happy_path` queda listo para extender (una fila por BP con `expected_status=None` para solo-contrato). Las 63 BPs quedan ejercitadas en ruta AccessDenied/degradada por el nivel estructural.

Nota de método bien aplicada: varios asserts fijan el status a un conjunto (`in {NON_COMPLIANT, PENDING_REVIEW}`) donde la lógica de producción no es determinista por los datos, en lugar de forzar un status asumido. Es defendible y coherente con la instrucción del plan de afirmar el status real observado.

## Los 4 bugs reales y por qué no están en rojo

El mock fiel destapó un patrón repetido: una variable (`old_keys`, `buckets`, `cert_list`) se asigna dentro de un `try` interno; si la primera llamada lanza `ClientError`, el `except` no la asigna y una lectura posterior lanza `UnboundLocalError`, que el `try/except ClientError` externo de la BP no atrapa. El efecto real es que, con permisos parciales, la BP no degrada a un finding sino que aborta `SecurityEvaluator.evaluate()` → 500 en el Lambda. BUG-4 es distinto: `SEC10-BP08` no está en `SECURITY_BP_DESCRIPTIONS` (confirmed: el dict solo define SEC10-BP01..BP07), así que la `description` sale vacía y viola el contrato del finding.

El criterio 6 se cumple: los 4 están en `bugs-encontrados-seguridad.md` con archivo:línea y fix propuesto, y los tests que los evidencian (`test_security_bugs.py` + el parametrizado de SEC10-BP08 en estructura) están en `xfail` con `raises` tipado (`UnboundLocalError`/`AssertionError`) y `reason` apuntando al doc. En `test_security_structure.py`, `_collect_findings` captura la excepción de las 3 BPs con crash y sustituye por el finding degradado esperado, con un assert de que la BP esté en `CRASH_BUGGY_BPS` (una excepción no documentada haría fallar el test, lo que es correcto: no enmascara crashes nuevos). `strict=False` en los xfail es la elección adecuada aquí para que un futuro fix produzca `xpass` sin romper la suite.

## Integración opcional y runner

El criterio 4 se cumple: `test_integration_security.py` tiene una única prueba `@pytest.mark.integration`, el modo por defecto corre `-m "not integration"` (vía `run-tests.ps1` y evidencia: 1 deselected), y aun con `-m integration` se auto-salta tras un `sts.get_caller_identity()` fallido (evidencia: 1 skipped, 98 deselected, RC 0). No toca la cuenta en corrida normal.

El criterio 5 se cumple: `pytest.ini` (testpaths=tests, addopts `-q --strict-markers`, marker integration) y `run-tests.ps1` (venv `.venv`, `-Integration` conmuta el filtro) se respetan sin cambios, y `tests/README.md` documenta los tres comandos (`pytest -q`, `run-tests.ps1`, `run-tests.ps1 -Integration`), la estructura, el diseño del mock y el protocolo de bugs.

## Evidencia de suite verde

`evidencia-tests-seguridad.md` reporta `90 passed, 1 deselected, 8 xfailed, 3 warnings, RC 0` en modo por defecto y `1 skipped, 98 deselected, RC 0` en modo integración. 0 failures. El documento declara con transparencia que el resumen se obtuvo con `pytest.main()` en proceso porque el subproceso `python -m pytest` se truncaba en este equipo (devolvía RC -1 antes de volcar el resumen) — el mismo síntoma que observé al correr `git diff` en esta review. Es el mismo venv y `pytest.ini`, así que la evidencia es creíble; la instrucción prohíbe re-correr la suite completa y no hay una duda específica que justifique un spot-check adicional más allá de los ya hechos (conteo de tests de calculations, existencia de NoSuchEntityException y ausencia de SEC10-BP08), todos confirmados.

## Alcance del diff

El `git diff main` del árbol de trabajo muestra miles de borrados por la migración/copia del repo (no parte de este trabajo). El cambio a revisar es el commit `d7f281c`, que toca solo `tests/` (8 archivos nuevos + conftest) y 2 docs en `.agents/tasks/`. No hay cambios de producción empaquetados en el commit (confirmed, git show --stat).

</details>

<details>
<summary>Mapa de archivos (commit d7f281c)</summary>

- `tests/conftest.py` — mock fiel `ScriptedSession`/`ScriptedClient`, fixtures `denying_session`/`scripted_session`, `iter_bp_invokers`, autouse de credenciales, sys.path.
- `tests/_helpers.py` — constantes del contrato y `assert_finding_contract`.
- `tests/test_calculations.py` — 11 tests puros de scoring (intacto).
- `tests/test_security_structure.py` — contrato de pilar por-BP, invariantes, scores, distribuciones.
- `tests/test_security_bps.py` — rutas explícitas SEC01-BP01/BP02/SEC02-BP01 + patrón parametrizado.
- `tests/test_security_bugs.py` — 4 tests xfail que evidencian los bugs reales.
- `tests/test_integration_security.py` — integración opcional auto-skippeable.
- `tests/README.md` — comandos, estructura, diseño del mock, protocolo de bugs.
- `.agents/tasks/bugs-encontrados-seguridad.md` — 4 bugs con archivo:línea y fix.
- `.agents/tasks/evidencia-tests-seguridad.md` — comando y resumen de pytest.

Diff completo: `git -C c:\AAM\Varios\internal-aws-solutions\GFourmis\solutions\auto-war show d7f281c`

</details>
