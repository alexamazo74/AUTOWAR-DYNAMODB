# Bugs reales de producción encontrados — pilar de Seguridad

> **ESTADO: los 4 bugs fueron CORREGIDOS** (2026-10-16). Esta sección documenta los bugs tal como se
> descubrieron y el fix aplicado a cada uno. Las pruebas que antes los evidenciaban como `xfail` son
> ahora pruebas de regresión en verde (ver `tests/test_security_bugs.py`), y la suite completa pasa
> `98 passed, 1 skipped, 0 failed`.

Estos bugs fueron descubiertos al construir la suite de pruebas con un mock de sesión boto3 FIEL
(clientes reales + proxy que preserva `client.exceptions`). Inicialmente NO se corrigió el código
(el objetivo de la tarea de testing era solo TESTS); una vez validada la suite, se aplicaron los fixes
propuestos (abajo, en cada bug) y se verificó que la suite queda verde.

Patrón común a los 3 bugs: una variable se asigna **dentro** de un `try` interno; si la **primera**
llamada AWS de ese `try` lanza `ClientError` (p.ej. `AccessDenied` por permisos parciales de la rol de
evaluación), el `except` interno **no** asigna esa variable, y una lectura posterior fuera del `try`
produce `UnboundLocalError` — una excepción **no capturada** que aborta la evaluación del pilar completo
(el `try/except ClientError` externo de la BP no atrapa `UnboundLocalError`).

Impacto real: con permisos parciales (un servicio denegado) la BP no degrada a un finding
`PENDING_REVIEW`/`NON_COMPLIANT`, sino que lanza una excepción que rompe `SecurityEvaluator.evaluate()`
y, por tanto, la respuesta HTTP del Lambda (acaba en el `except Exception` genérico → 500).

---

## BUG-1 — SEC02-BP05: `UnboundLocalError: old_keys`

- Archivo: `lambda/evaluators/security/all_bp_evaluations.py`
- Línea del fallo: ~1173 (`severity = 'HIGH' if old_keys > 3 or no_mfa_console > 3 else 'MEDIUM'`)
- Variables en riesgo: `old_keys`, `unused_users`, `no_mfa_console` (asignadas dentro del `try` que empieza
  en `client.generate_credential_report()`).

Causa: si `generate_credential_report()` o `get_credential_report()` lanzan `ClientError` (p.ej.
AccessDenied), el `except ClientError` añade un issue a `issues` pero deja `old_keys`/`no_mfa_console` sin
asignar. Como `issues` queda no vacío, el flujo entra en la rama `else`, que lee `old_keys` →
`UnboundLocalError`.

Fix APLICADO: `old_keys`, `unused_users` y `no_mfa_console` se inicializan a 0 antes del `try` interno.

Test de regresión: `tests/test_security_bugs.py::test_sec02_bp05_access_denied_degrades` (verde).

---

## BUG-2 — SEC07-BP02: `UnboundLocalError: buckets`

- Archivo: `lambda/evaluators/security/all_bp_evaluations.py`
- Línea del fallo: ~2869 (segundo bloque, `for bucket in buckets[:15]:`)
- Variable en riesgo: `buckets` (asignada dentro del primer `try` con `s3.list_buckets()`).

Causa: si `s3.list_buckets()` lanza `ClientError` (p.ej. AccessDenied), el `except ClientError` del primer
bloque solo añade evidencia, pero `buckets` nunca se asigna. El segundo bloque ("S3 public access block")
itera `for bucket in buckets[:15]` → `UnboundLocalError`.

Fix APLICADO: `buckets = []` se inicializa antes del primer `try`, de forma que el segundo bloque opera
sobre una lista vacía cuando S3 no es accesible.

Test de regresión: `tests/test_security_bugs.py::test_sec07_bp02_access_denied_degrades` (verde).

---

## BUG-3 — SEC09-BP01: `UnboundLocalError: cert_list`

- Archivo: `lambda/evaluators/security/all_bp_evaluations.py`
- Línea del fallo: ~3315 (rama COMPLIANT, `f'...con {len(cert_list)} certificados ACM.'`)
- Variable en riesgo: `cert_list` (asignada dentro del `try` con `acm.list_certificates()`).

Causa: si `acm.list_certificates()` lanza `ClientError` (p.ej. AccessDenied), el `except ClientError` solo
añade evidencia y **no** añade ningún issue. Con `issues` vacío, el flujo entra en la rama COMPLIANT, que
lee `len(cert_list)` → `UnboundLocalError`. (Además, degradar a COMPLIANT cuando ACM no es accesible es un
problema de criterio secundario: no se puede afirmar cumplimiento sin datos.)

Fix APLICADO: `cert_list = []` se inicializa antes del `try`, y cuando ACM es inaccesible se añade un issue
para que la BP NO reporte COMPLIANT sin datos (degrada a PENDING_REVIEW/NON_COMPLIANT).

Test de regresión: `tests/test_security_bugs.py::test_sec09_bp01_access_denied_degrades` (verde).

---

## BUG-4 — SEC10-BP08: `description` vacía (clave ausente en SECURITY_BP_DESCRIPTIONS)

- Archivo: `lambda/evaluators/security/bp_descriptions.py` (falta la clave `'SEC10-BP08'`).
- Afecta a: `lambda/evaluators/security/all_bp_evaluations.py:3833` (y la rama de error en :3848 vía
  `handle_error_func`), que hacen `SECURITY_BP_DESCRIPTIONS.get('SEC10-BP08', '')`.

Causa: la función `evaluate_sec10_bp08` existe (SEC10 tiene 8 BPs) y su docstring es "Establecer un marco
para aprender de los incidentes", pero el diccionario `SECURITY_BP_DESCRIPTIONS` solo define SEC10-BP01..
SEC10-BP07. Al no existir la clave `SEC10-BP08`, el campo `description` del finding queda como cadena vacía
`''` en TODAS las rutas (COMPLIANT, PENDING_REVIEW y error). Esto viola el contrato del finding (todos los
campos de texto deben ser no vacíos) y, de hecho, `autowar_common.models.Finding.__post_init__` lanzaría
`ValueError("description cannot be empty")` si este finding se construyera como `Finding`.

A diferencia de BUG-1..3, SEC10-BP08 **no** lanza una excepción: devuelve un dict con `description=''`.

Fix APLICADO: se añadió la clave `'SEC10-BP08': 'Establish a framework to learn from incidents'` en
`bp_descriptions.py`.

Test de regresión: `tests/test_security_bugs.py::test_sec10_bp08_has_description` (verde), y la BP se
valida junto a las otras 62 en `test_each_bp_returns_valid_finding_under_access_denied[SEC10-BP08]`.

---

## Efecto sobre la suite estructural

Como `SecurityEvaluator.evaluate()` orquesta las 63 BPs en secuencia y aborta en la primera que lanza
`UnboundLocalError` (BUG-1..3), no es posible validar el contrato del pilar completo recorriendo
`evaluate()` mientras existan estos bugs. Para no dejar la suite en rojo (y seguir validando las 59 BPs
sanas), las pruebas estructurales recorren las 63 BPs **individualmente**: las 59 sanas se validan en verde
y las 4 con bug (BUG-1..4) se marcan `xfail` apuntando a este documento. Cuando se corrijan, los `xfail`
pasarán a `xpass` (señal para endurecer los tests) y la suite estructural podrá volver a basarse en
`evaluate()` end-to-end.

Resumen: 4 bugs reales = 3 `UnboundLocalError` (SEC02-BP05, SEC07-BP02, SEC09-BP01) + 1 `description`
vacía (SEC10-BP08).
