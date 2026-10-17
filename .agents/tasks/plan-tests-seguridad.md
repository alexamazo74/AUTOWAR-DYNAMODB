# Plan de implementación — Suite de pruebas automatizadas del pilar de Seguridad (AutoWAR)

Objetivo: dejar una suite pytest COMPLETA y VERDE para el pilar de Seguridad (11 preguntas SEC01..SEC11,
63 BPs), sin tocar código de producción de los evaluadores (salvo documentar bugs reales aparte). Trabajar
directamente en el repo local `c:\AAM\Varios\internal-aws-solutions\GFourmis\solutions\auto-war` (sin worktree).

## Contexto verificado durante la exploración (hechos, no suposiciones)

- Intérprete: `c:\AAM\Varios\internal-aws-solutions\GFourmis\solutions\auto-war\.venv\Scripts\python.exe`
  (Python 3.14, boto3 1.43, pytest 9.1, moto 5.2). No crear otro venv.
- Runner del proyecto: `run-tests.ps1` (por defecto `pytest -q -m "not integration"`; con `-Integration`
  corre todo). `pytest.ini` define `testpaths = tests`, `addopts = -q --strict-markers`, y el marker
  `integration`. Respetar ambos.
- Estado real al correr `pytest -q` HOY: **11 passed, 6 failed**. Los 11 que pasan son `test_calculations.py`.
  Los 6 que fallan son todos de `test_security_structure.py` y **todos** por la MISMA causa raíz:
  `evaluate_sec02_bp01` ejecuta `except client.exceptions.NoSuchEntityException:` y el mock casero
  `_DenyingClient` del `conftest.py` NO expone `.exceptions`, produciendo
  `AttributeError: 'function' object has no attribute 'NoSuchEntityException'`. Es un falso positivo del
  mock, no un bug de producción.
- Único uso de `.exceptions.<X>` en todo el pilar: `client.exceptions.NoSuchEntityException` en el cliente
  `iam` dentro de `evaluate_sec02_bp01` (all_bp_evaluations.py, líneas ~749 y ~770). No hay `get_paginator`.
- Contrato de cada finding (dict): claves `{bp, description, status, severity, finding, evidence,
  remediation, risk}`; `status ∈ {COMPLIANT, NON_COMPLIANT, PENDING_REVIEW}`;
  `severity ∈ {CRITICAL, HIGH, MEDIUM, LOW}`. Todos los campos de texto deben ser no vacíos.
- `bp_descriptions.py` → `SECURITY_BP_DESCRIPTIONS` tiene 63 claves, ninguna vacía (verificado). Esto importa
  para las rutas COMPLIANT, cuyo `description` sale de ese dict.
- `handler.SecurityEvaluator(session, region)` → `.evaluate()` orquesta las 11 preguntas. SEC01-BP01 y
  SEC01-BP02 son métodos inline (`_evaluate_sec01_bp01/_bp02`, clientes `organizations` e `iam`
  respectivamente); las otras 61 BPs son funciones `evaluate_secNN_bpMM(session, handle_error_func)`
  importadas de `all_bp_evaluations`.
- Reparto de BPs por pregunta (verificado en handler.py): SEC01=8, SEC02=6, SEC03=9, SEC04=4, SEC05=4,
  SEC06=5, SEC07=4, SEC08=4, SEC09=3, SEC10=8, SEC11=8. Total = 63.
- Las funciones de BP capturan `ClientError` del `try` externo y delegan en `handle_error_func`
  (`_handle_permission_error` → status `PENDING_REVIEW`, severity `MEDIUM`). Muchas además envuelven cada
  sub-llamada en `try/except ClientError` o `try/except Exception` y degradan a hallazgos
  `NON_COMPLIANT`/`PENDING_REVIEW`.

## Decisión de diseño (a): mock/fixture de sesión boto3 fiel

Problema central: el mock debe exponer `client.exceptions.<ClaseReal>` para que las cláusulas
`except client.exceptions.NoSuchEntityException` se resuelvan sin `AttributeError`, y además debe poder
simular tanto AccessDenied como respuestas con datos (rutas COMPLIANT/NON_COMPLIANT/PENDING_REVIEW).

Opciones evaluadas:
- **Mock casero** (actual `_DenyingClient`): descartado. No tiene `.exceptions`; es la causa de los 6 fallos.
- **moto 5.2**: útil para servicios soportados, pero (1) no cubre uniformemente los 43 servicios usados
  (p.ej. sso-admin, inspector2, macie2, servicecatalog, accessanalyzer tienen cobertura parcial o nula),
  (2) acopla los tests al estado interno de moto, y (3) no da control fino para forzar AccessDenied por
  operación. Reservarlo solo para el test de smoke IAM opcional si se desea, no como base.
- **Clientes boto3 REALES + override de métodos** (elegido como base): crear un `boto3.Session` real
  (con credenciales ficticias y región fija), y para cada `service_name` construir el cliente real con
  `session.client(service_name, ...)`. El cliente real YA expone `client.exceptions.<X>` nativo
  (incluye `NoSuchEntityException` para iam). Luego se envuelve ese cliente real en un proxy que:
  - delega `__getattr__('exceptions')` al cliente real (y cualquier atributo no-operación),
  - intercepta las operaciones de API (métodos) devolviendo una respuesta configurable o lanzando
    un `ClientError` configurable (p.ej. AccessDenied) según un "guion" (scripted responses) por operación.
  Esto preserva fielmente `.exceptions` sin llamar a AWS real (nunca se invoca la operación real).
- **botocore Stubber** (elegido como complemento, para casos de respuesta "feliz" exacta): para los tests
  COMPLIANT/NON_COMPLIANT de BPs priorizadas donde interesa validar el mapeo de datos→status, usar
  `botocore.stub.Stubber` sobre un cliente real (Stubber también preserva `client.exceptions`). Stubber
  valida el shape de la respuesta contra el modelo del servicio, lo que da fidelidad alta.

Diseño concreto de las fixtures (todas en `tests/conftest.py`):

1. `fake_session` base: una clase `ScriptedSession` que recibe un `dict` de "guiones" por servicio y por
   operación. Su `.client(service_name)` construye el cliente boto3 REAL una vez (cacheado), y lo envuelve
   en `ScriptedClient`:
   - `ScriptedClient.__getattr__(name)`: si `name == 'exceptions'` → devuelve `real_client.exceptions`
     (clases de excepción reales); si `name` es una operación conocida → devuelve un callable que consulta
     el guion; en otro caso delega en `real_client`.
   - El callable de operación: si el guion dice "deny" → `raise real_client.exceptions.<X>(...)` o un
     `ClientError` AccessDenied genérico (según se configure); si el guion da una respuesta → la devuelve
     tal cual; si no hay guion para esa operación → por defecto lanza `ClientError` AccessDenied (modo
     "deny-by-default", que replica el comportamiento de la sesión actual pero SIN romper `.exceptions`).
   Credenciales ficticias y `region_name='us-east-1'` para que `session.client(...)` real no requiera
   credenciales válidas (boto3 crea el cliente sin validarlas hasta la primera llamada, que nunca ocurre).
2. `denying_session` (reescrita, misma firma que la fixture existente para no romper
   `test_security_structure.py`): un `ScriptedSession` en modo "deny-by-default" sin guiones. Resultado:
   toda operación lanza AccessDenied PERO `client.exceptions.NoSuchEntityException` existe → las 6 pruebas
   estructurales pasan y cada BP cae a su rama de error/pending con finding válido.
3. Helper de construcción de guiones `scripted_session(scripts: dict)` (fixture factory) para los tests por
   BP: permite declarar, por servicio y operación, `response=<dict>` o `error=('Code','Msg')`.

Por grupo de servicios: no se requiere lógica distinta por servicio para el modo deny-by-default (el proxy
es genérico). Para IAM (único con `.exceptions.<X>` real usado) basta con que el proxy exponga
`real_client.exceptions`, lo cual cubre `NoSuchEntityException`. Para los servicios sin dependencia de
`.exceptions`, el proxy genérico es suficiente. moto queda fuera del camino principal.

## Decisión de diseño (b): cómo corregir conftest.py

- Mantener el ajuste de `sys.path` (COMMON_LAYER y SECURITY_DIR) y la fixture `security_handler`
  (import + reload dentro de la fixture) tal como están: funcionan.
- Reemplazar `_DenyingClient` y `FakeDenyingSession` por el `ScriptedSession`/`ScriptedClient` descritos.
  Conservar el NOMBRE de la fixture `denying_session` y su semántica (todo AccessDenied) para no reescribir
  `test_security_structure.py`.
- Añadir las fixtures nuevas: `scripted_session` (factory) y utilidades para construir respuestas.
- Fijar región y credenciales ficticias vía variables de entorno dentro de un fixture autouse de sesión
  (`AWS_DEFAULT_REGION=us-east-1`, `AWS_ACCESS_KEY_ID=testing`, `AWS_SECRET_ACCESS_KEY=testing`,
  `AWS_SESSION_TOKEN=testing`) para evitar que boto3 intente leer credenciales del entorno real.

## Decisión de diseño (c): cobertura de BPs por pregunta y rutas

Dos niveles de cobertura, para equilibrar completitud y mantenibilidad:

- Nivel ESTRUCTURAL (ya existe, debe quedar verde con el mock corregido): `test_security_structure.py`
  recorre las 63 BPs con `denying_session` y valida contrato, unicidad de IDs, rangos de score y
  distribuciones. Esto ya ejercita la ruta AccessDenied/degradada de las 63 BPs.
- Nivel POR-BP (nuevo), priorizando SEC01-BP01, SEC01-BP02, SEC02-BP01 con rutas explícitas:
  - **SEC01-BP01** (`organizations`, método inline): COMPLIANT (org FeatureSet=ALL, >1 cuenta activa, OUs,
    SCPs personalizadas), NON_COMPLIANT (sin Organizations → `describe_organization` lanza ClientError
    interno), PENDING_REVIEW (multi-cuenta parcial: cuentas pero sin OUs/SCPs), y AccessDenied (deny en
    `organizations` → finding NON_COMPLIANT "No se detectó AWS Organizations" por el except interno, o
    PENDING_REVIEW si el deny ocurre en el try externo — verificar la rama exacta al escribir el test y
    afirmar el status real observado, no uno asumido).
  - **SEC01-BP02** (`iam` + `cloudtrail`, inline): NON_COMPLIANT/CRITICAL (summary con
    `AccountMFAEnabled=0` o `AccountAccessKeysPresent>0`), COMPLIANT (MFA=1, sin access keys, sin actividad
    root), PENDING_REVIEW (MFA ok pero MFA virtual root detectado), AccessDenied en `iam.get_account_summary`
    → `_handle_permission_error` (PENDING_REVIEW/MEDIUM).
  - **SEC02-BP01** (`iam` + `sso-admin`): es la BP que hoy rompe el mock. Cubrir: AccessDenied real que
    debe entrar por `except client.exceptions.NoSuchEntityException` (sin password policy) → añade issue
    "Sin política de contraseñas"; NON_COMPLIANT/CRITICAL (password policy débil); COMPLIANT (policy fuerte
    min_length>=14, todos los char types, max_age<=90, reuse>=12, y sin usuarios con consola sin MFA);
    PENDING_REVIEW (policy intermedia). Guionar `get_account_password_policy`, `get_account_summary`,
    `list_users`, `list_mfa_devices`, `get_login_profile` y `sso-admin.list_instances`.
  - Resto de SEC01 (BP03-BP08) y SEC02 (BP02-BP06): al menos un test de ruta AccessDenied/degradada por BP
    (cubierto por el nivel estructural) + 1 test "feliz" (COMPLIANT o el status esperado) por BP donde el
    guion sea razonable. Priorizar BP03..BP08 de SEC01 y BP02..BP06 de SEC02 con un test "feliz" cada una.
  - SEC03..SEC11: cobertura estructural garantizada (deny-by-default) para las 63 BPs. Añadir tests
    "felices" por BP siguiendo el patrón reutilizable (abajo), al menos para una BP representativa por
    pregunta en esta iteración, dejando el patrón listo para extender al resto. El criterio de aceptación
    de completitud es: las 63 BPs ejercitadas en ruta AccessDenied/degradada (estructural) + rutas
    COMPLIANT/NON_COMPLIANT/PENDING_REVIEW explícitas para SEC01-BP01, SEC01-BP02 y SEC02-BP01, + al menos
    un test "feliz" por cada BP de SEC01 y SEC02.

Nota de método: para CADA ruta "feliz", al escribir el test se ejecuta primero y se afirma el status
realmente devuelto por el código de producción (leyendo la lógica de la BP), nunca un status asumido. Si
el código no permite alcanzar cierto status con datos válidos, se documenta y se omite esa rama (no se
fuerza).

## Decisión de diseño (d): patrón reutilizable para extender a más BPs

- Helper `assert_finding_contract(finding)`: valida claves, enums y campos no vacíos (reutiliza las
  constantes de `test_security_structure.py`, extraídas a un módulo `tests/_helpers.py` o fixtures en
  conftest para no duplicar).
- Patrón por BP en `tests/test_security_bps.py` (nuevo), parametrizado con `pytest.mark.parametrize`:
  tabla `(bp_func_name, scripts, expected_status, expected_severity_opt)`; cada fila construye
  `scripted_session(scripts)`, invoca `evaluate_secNN_bpMM(session, evaluator._handle_permission_error)`
  (o el método inline vía `SecurityEvaluator`), y afirma `assert_finding_contract` + `status`
  (y `severity` cuando sea determinista). Para las dos BPs inline, instanciar
  `SecurityEvaluator(scripted_session, 'us-east-1')` y llamar al método.
- Documentar en `tests/README.md` cómo añadir una fila nueva (qué operaciones guionar, cómo leer la lógica
  de la BP para elegir el `expected_status`).

## Decisión de diseño (e): test de integración opcional

- Archivo `tests/test_integration_security.py` con una única prueba marcada `@pytest.mark.integration`
  que: crea un `boto3.Session()` REAL (credenciales del entorno/perfil), instancia
  `SecurityEvaluator(session, region)`, llama `.evaluate()` y afirma el contrato de alto nivel
  (11 preguntas, 63 findings, scores en rango). Se SALTA por defecto porque `run-tests.ps1` y el modo por
  defecto corren `-m "not integration"`. Añadir `skip` adicional si no hay credenciales
  (`pytest.skip("sin credenciales AWS")` tras un `sts.get_caller_identity()` en try/except) para que
  incluso con `-Integration` no falle en equipos sin cuenta.

## Decisión de diseño (f): tests/README.md

- Documentar: cómo correr (`.\run-tests.ps1`, `.\run-tests.ps1 -Integration`, o
  `.venv\Scripts\python.exe -m pytest`), estructura de la suite, el diseño del mock fiel (por qué clientes
  reales + proxy y no mock casero), el patrón para añadir tests por BP, y cómo se gestionan los bugs
  reales encontrados (archivo `bugs-encontrados-seguridad.md`, marca xfail/skip).

## Protocolo de bugs de producción

Si al escribir un test se descubre que una BP, ante AccessDenied real, lanzaría una excepción NO capturada
(p.ej. un `except client.exceptions.X` donde `X` no cubre el `Code` real, o una sub-llamada fuera de
try/except), NO arreglar el código. Documentar en
`c:\AAM\Varios\internal-aws-solutions\GFourmis\solutions\auto-war\.agents\tasks\bugs-encontrados-seguridad.md`
con `archivo:línea`, descripción y fix propuesto, y marcar el test que lo evidencia como `xfail`/`skip`
con `reason` apuntando al bug. (Observación: el único `.exceptions.<X>` del pilar es
`NoSuchEntityException` en iam; con clientes reales se resuelve sin romper, así que no se anticipa bug ahí.)

---

# Implementation Plan

- [ ] 1. Extraer helpers de contrato a un módulo compartido.
      Crear `tests/_helpers.py` con `VALID_STATUS`, `VALID_SEVERITY`, `FINDING_KEYS`,
      `EXPECTED_QUESTIONS`, `EXPECTED_TOTAL_BPS`, `EXPECTED_BPS_PER_QUESTION` (SEC01=8,SEC02=6,SEC03=9,
      SEC04=4,SEC05=4,SEC06=5,SEC07=4,SEC08=4,SEC09=3,SEC10=8,SEC11=8) y la función
      `assert_finding_contract(finding)` que valida claves, enums y campos de texto no vacíos.
      Files: `tests/_helpers.py`
      Verify: `.venv\Scripts\python.exe -m pytest -q -m "not integration"` — no debe romper nada
      (la suite sigue en 11 passed + 6 failed hasta el paso 2).

- [ ] 2. Reescribir el mock de sesión en `conftest.py` con clientes boto3 reales + proxy guionado.
      Implementar `ScriptedClient` (delegando `exceptions` al cliente real y guionando operaciones) y
      `ScriptedSession` (modo deny-by-default). Reescribir `denying_session` conservando nombre y
      semántica (todo AccessDenied) sobre `ScriptedSession`. Añadir fixture factory `scripted_session`
      y un fixture `autouse` de sesión que fije `AWS_DEFAULT_REGION`/credenciales ficticias. Conservar
      `security_handler` y el ajuste de `sys.path`.
      Files: `tests/conftest.py`
      Verify: `.venv\Scripts\python.exe -m pytest -q tests/test_security_structure.py` — los 6 tests
      estructurales ahora PASAN (ya no hay `AttributeError` de `.exceptions`).

- [ ] 3. Confirmar que la base queda verde tras corregir el mock.
      Sin cambios de código nuevos; corre toda la suite por defecto.
      Files: (ninguno)
      Verify: `.\run-tests.ps1` (o `.venv\Scripts\python.exe -m pytest -q -m "not integration"`) —
      resultado esperado: 17 passed (11 de calculations + 6 estructurales), 0 failed.

- [ ] 4. Tests por-BP priorizados: SEC01-BP01, SEC01-BP02, SEC02-BP01 con rutas explícitas.
      Crear `tests/test_security_bps.py`. Para cada una, usar `scripted_session`/`SecurityEvaluator`
      e implementar las rutas COMPLIANT, NON_COMPLIANT, PENDING_REVIEW y AccessDenied descritas en la
      decisión (c). Afirmar `assert_finding_contract` + `status` (y `severity` donde sea determinista),
      verificando el status REAL del código antes de fijar la aserción. SEC02-BP01 debe incluir el caso
      que entra por `except client.exceptions.NoSuchEntityException` (sin password policy).
      Files: `tests/test_security_bps.py`
      Verify: `.venv\Scripts\python.exe -m pytest -q tests/test_security_bps.py` — todos los nuevos
      tests de estas 3 BPs pasan.

- [ ] 5. Extender tests "felices" al resto de SEC01 (BP03-BP08) y SEC02 (BP02-BP06) con el patrón
      parametrizado, y una BP representativa por cada SEC03..SEC11.
      Añadir filas parametrizadas en `tests/test_security_bps.py` (tabla
      `(bp_func, scripts, expected_status[, expected_severity])`). Si alguna BP revela un bug de
      producción (excepción no capturada ante deny real), NO arreglar: documentar en
      `.agents/tasks/bugs-encontrados-seguridad.md` (archivo:línea, descripción, fix propuesto) y marcar
      ese test `xfail`/`skip` con `reason`.
      Files: `tests/test_security_bps.py`, (si aplica) `.agents/tasks/bugs-encontrados-seguridad.md`
      Verify: `.venv\Scripts\python.exe -m pytest -q -m "not integration"` — toda la suite verde
      (los `xfail` cuentan como xfailed, no como failed).

- [ ] 6. Añadir el test de integración opcional marcado `integration`.
      Crear `tests/test_integration_security.py` con una prueba `@pytest.mark.integration` que usa un
      `boto3.Session()` real, se auto-salta si no hay credenciales (try `sts.get_caller_identity()`),
      instancia `SecurityEvaluator`, llama `.evaluate()` y afirma contrato de alto nivel (11 preguntas,
      63 findings, scores en rango).
      Files: `tests/test_integration_security.py`
      Verify: `.\run-tests.ps1` NO ejecuta este test (queda deselected por `-m "not integration"`);
      `.venv\Scripts\python.exe -m pytest -q -m integration` lo recoge y, sin credenciales, lo marca
      skipped (no failed).

- [ ] 7. Escribir `tests/README.md`.
      Documentar cómo correr la suite (los 3 comandos), la estructura de archivos, el diseño del mock
      fiel (clientes reales + proxy, por qué no mock casero ni moto como base, cómo se preserva
      `client.exceptions`), el patrón para añadir un test por BP, el marker `integration`, y el protocolo
      de bugs (`bugs-encontrados-seguridad.md`, xfail/skip). En español, con nombres de servicios AWS en
      inglés.
      Files: `tests/README.md`
      Verify: lectura manual; y `.\run-tests.ps1` sigue verde tras el paso (sin regresiones).

- [ ] 8. Verificación final completa de la suite.
      Correr el runner por defecto y con integración para confirmar el estado final y que no hay
      ficheros temporales ni artefactos sueltos dentro del root del repo.
      Files: (ninguno)
      Verify: `.\run-tests.ps1` → todo verde (passed + xfailed/skipped, 0 failed);
      `.\run-tests.ps1 -Integration` → integración skipped si no hay credenciales, resto verde.

## Supuestos y vacíos (declarados)

- Se asume que boto3 construye los clientes reales sin validar credenciales hasta la primera llamada a la
  API (comportamiento estándar). Si en algún entorno fallara la construcción de un cliente concreto, el
  fixture `autouse` con credenciales ficticias lo cubre; si aún así fallara un servicio exótico, se
  construye su proxy sobre un cliente de un servicio equivalente que exponga las mismas excepciones (solo
  iam necesita `.exceptions.<X>` real, el resto no depende de `.exceptions`).
- "Completo" se define como: 63 BPs ejercitadas en ruta deny/degradada (estructural) + rutas explícitas
  para las 3 BPs priorizadas + un test "feliz" por BP de SEC01 y SEC02 + una BP representativa por
  SEC03..SEC11. Ampliar a test "feliz" por cada una de las 63 BPs queda como extensión directa del patrón
  (paso 5), no bloqueante para la suite verde.
- No se modifica código de producción de los evaluadores; cualquier bug real se documenta y se marca el
  test como xfail/skip (protocolo arriba).
