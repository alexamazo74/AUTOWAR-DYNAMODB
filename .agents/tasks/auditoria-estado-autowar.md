# Auditoría de Estado — AutoWAR (AWS Well-Architected Analyzer)

**Tipo:** Revisión de SOLO LECTURA (no se modificó código del proyecto).
**Fecha:** generado automáticamente.
**Raíz del proyecto:** `C:\AAM\Varios\internal-aws-solutions\GFourmis\solutions\auto-war`
**Alcance:** 6 evaluadores de pilares, pilar de Seguridad en detalle, 4 specs de Kiro, estado de pruebas, CDK/despliegue, barrido del resto y recomendación final.

---

## Resumen ejecutivo (respuesta corta)

- **Seguridad y Cost están realmente implementados** con llamadas reales a APIs de AWS (boto3). Lo que decían los `tasks.md` es correcto para estos dos pilares.
- **Security está completo**: 11 preguntas (SEC01–SEC11), **63 Best Practices**, todas cableadas a funciones de evaluación reales. 61 funciones viven en `all_bp_evaluations.py` + 2 inline en `handler.py`. Usa **43 servicios AWS distintos** vía 140+ llamadas boto3. No hay TODOs reales ni `NotImplementedError`. Las apariciones de `PENDING_REVIEW` son veredictos legítimos de "cumplimiento parcial" o manejo de errores de permisos, no placeholders.
- **Cost está completo**: 0 usos de `_create_pending` en su handler; evaluaciones reales en todas las preguntas COST01–COST11.
- **Performance está parcialmente real**: tiene evaluaciones boto3 reales para las primeras preguntas (PERF01–PERF04) pero **todas las preguntas también caen a `_create_pending`** por BPs no implementadas; aún no es un pilar "real" completo.
- **Reliability, Operational Excellence y Sustainability son 100% placeholder** (`_create_pending` → `PENDING_REVIEW`), sin una sola llamada boto3 en sus handlers.
- **NO existe ninguna suite de pruebas automatizadas.** No hay archivos `test_*.py`, `conftest.py`, ni `pytest.ini`/`tox.ini` en el proyecto (fuera de dependencias). `pytest`, `pytest-asyncio` y `moto` están declarados en `requirements.txt` pero no se usan. Los specs describen decenas de property tests/unit tests que **no están implementados**.
- **CDK**: un único stack en código, `AutoWARStack` (`cdk-new/`), hardcodeado a la cuenta `102080400524` / `us-east-1`. **No existe la carpeta `cdk/` antigua** mencionada en el README. El segundo stack en la cuenta (`AutoWarStack`, "war" en minúscula) es casi con certeza un **despliegue legado/huérfano** de una versión anterior, no reproducible desde el código actual.
- **Orden recomendado para "pulir Seguridad"**: terminar `refinar-remediaciones-seguridad` (tareas 12 y 13) + crear la suite de pruebas con moto (que no existe) → luego continuar `implement-real-bp-evaluations` desde la tarea 3 (Performance) en adelante.

---

## 1. Estado de los 6 evaluadores

Carpeta: `lambda/evaluators/{security,cost,performance,reliability,operational_excellence,sustainability}/handler.py` + `lambda/evaluators/unified_handler.py`.

El router `unified_handler.py` carga dinámicamente el `handler.py` del pilar pedido (`event.pathParameters.pillar`), ejecuta su `lambda_handler`, y si viene de Step Functions comprime el resultado (gzip+base64) y lo guarda en DynamoDB para evitar el límite de 256 KB.

### Métrica objetiva por pilar (conteo sobre `handler.py`)

| Pilar | `self.session.client` | `_create_pending` | bloques `try` | Veredicto |
|---|---|---|---|---|
| **cost** | 36 | **0** | 38 | **Real / completo** |
| **security** | (ver nota) | 0 en `handler.py`† | — | **Real / completo (63 BP)** |
| **performance** | 7 | 6 | 6 | **Parcial** (real en PERF01–04, resto pending) |
| **reliability** | **0** | 14 | 2 | **Placeholder total** |
| **operational_excellence** | **0** | 12 | 2 | **Placeholder total** |
| **sustainability** | **0** | 7 | 2 | **Placeholder total** |

† Security hace sus llamadas boto3 en `all_bp_evaluations.py` (140+ `session.client`), no en `handler.py`. El handler solo orquesta y llama a las 61 funciones `evaluate_secNN_bpMM(...)`.

### Detalle por pilar

- **Cost (real).** `lambda/evaluators/cost/handler.py` (1323 líneas). Cada BP consulta APIs reales: IAM (`list_groups`, `list_roles`), Budgets (`describe_budgets`), Cost Explorer (`get_cost_and_usage`, `get_cost_forecast`, `get_anomaly_monitors`), CloudWatch dashboards, Trusted Advisor (`describe_trusted_advisor_checks`), Organizations, CodePipeline/CloudFormation, EC2/S3 para tagging, etc. Cero `_create_pending`.

- **Performance (parcial).** `lambda/evaluators/performance/handler.py` (445 líneas). Tiene evaluaciones reales con boto3 para:
  - PERF01-BP01: `ec2.describe_instances()` → diversidad de tipos de instancia.
  - PERF02-BP01: `ec2` + `lambda` → opciones de cómputo.
  - PERF03-BP01: `s3` + `dynamodb` + `rds` → almacenes de datos específicos.
  - PERF04-BP01: `ec2.describe_vpcs()` → requisitos de red.
  Pero **las 5 preguntas (PERF01–PERF05) rellenan sus BP restantes con `self._create_pending(...)`**, así que el pilar sigue devolviendo muchos `PENDING_REVIEW`.

- **Reliability / Operational Excellence / Sustainability (placeholder).** Sus handlers no tienen ninguna llamada `self.session.client`; cada `_evaluate_relNN/_opsNN/_susNN` hace un bucle que agrega `self._create_pending(f'...-BP{i:02d}')`. Todo devuelve `PENDING_REVIEW` con `finding: 'Manual review required'` (ver `sustainability/handler.py:266`, `operational_excellence/handler.py:320`).

**Conclusión vs. tasks.md:** confirmado. Security y Cost reales; Performance a medias; Reliability, Ops y Sustainability pendientes. (El spec `implement-real-bp-evaluations/requirements.md` lo dice explícitamente en su Introducción: *"Security … Already has real evaluations"*.)

---

## 2. Pilar de Seguridad en detalle

Archivos: `lambda/evaluators/security/handler.py` (841 líneas), `all_bp_evaluations.py` (4130 líneas), `bp_descriptions.py` (89 líneas).

### Cobertura de preguntas y BPs

`SecurityEvaluator.evaluate()` ejecuta las 11 preguntas. Reparto de BPs (según el cableado en `handler.py`):

| Pregunta | Tema | BPs | Dónde se evalúa |
|---|---|---|---|
| SEC01 | Operar de forma segura | 8 | BP01/BP02 inline en `handler.py`; BP03–BP08 en `all_bp_evaluations.py` |
| SEC02 | Gestión de identidades | 6 | `all_bp_evaluations.py` (BP01–BP06) |
| SEC03 | Gestión de permisos | 9 | `all_bp_evaluations.py` (BP01–BP09) |
| SEC04 | Detección e investigación | 4 | `all_bp_evaluations.py` (BP01–BP04) |
| SEC05 | Protección de red | 4 | `all_bp_evaluations.py` (BP01–BP04) |
| SEC06 | Protección de cómputo | 5 | `all_bp_evaluations.py` (BP01–BP05) |
| SEC07 | Clasificación de datos | 4 | `all_bp_evaluations.py` (BP01–BP04) |
| SEC08 | Datos en reposo | 4 | `all_bp_evaluations.py` (BP01–BP04) |
| SEC09 | Datos en tránsito | 3 | `all_bp_evaluations.py` (BP01–BP03) |
| SEC10 | Respuesta a incidentes | 8 | `all_bp_evaluations.py` (BP01–BP08) |
| SEC11 | Seguridad de aplicaciones | 8 | `all_bp_evaluations.py` (BP01–BP08) |
| **Total** | | **63** | 61 funciones externas + 2 inline |

> Nota: el README menciona una versión antigua con solo 5 preguntas SEC y "mock AWS resources". Esa descripción está **desactualizada**: el código actual implementa las 11 preguntas con llamadas reales.

### Cómo evalúa (ejemplos verificados)

- **SEC01-BP01** (`handler.py:_evaluate_sec01_bp01`): `organizations.describe_organization()`, `list_accounts()`, `list_roots()`, `list_organizational_units_for_parent()`, `list_policies(Filter='SERVICE_CONTROL_POLICY')`. Deriva COMPLIANT/PENDING_REVIEW/NON_COMPLIANT según nº de cuentas, OUs, FeatureSet y SCPs.
- **SEC01-BP02** (`handler.py:_evaluate_sec01_bp02`): `iam.get_account_summary()` (MFA raíz, access keys raíz), `cloudtrail.lookup_events()` (actividad raíz 90 días), `list_virtual_mfa_devices()`. Marca CRITICAL si falta MFA raíz o hay access keys.
- **SEC02-BP01** (`all_bp_evaluations.py`): política de contraseñas (`get_account_password_policy`) — evalúa longitud, tipos de caracteres, expiración, reutilización.
- Servicios AWS consultados en `all_bp_evaluations.py` (43 distintos): `accessanalyzer, acm, autoscaling, cloudformation, cloudfront, cloudtrail, cloudwatch, codeartifact, codebuild, codecommit, codedeploy, codepipeline, config, directconnect, dynamodb, ec2, elbv2, events, fis, guardduty, iam, imagebuilder, inspector2, kms, lambda, logs, macie2, network-firewall, organizations, ram, rds, s3, s3control, secretsmanager, securityhub, servicecatalog, shield, sns, ssm, sso-admin, stepfunctions, sts, wafv2`.

### Calidad de remediaciones y evidencia

Alta. Cada finding retorna el contrato estándar `{bp, description, status, severity, finding, evidence, remediation, risk}`. Las remediaciones son multi-paso y accionables (p. ej. SEC01-BP02 lista 7 pasos concretos). La evidencia concatena datos técnicos reales (IDs de org/cuentas, conteos, flags). Los textos están en español.

### Gaps concretos para "pulir" Seguridad

1. **`bp_descriptions.py` incompleto** (89 líneas para 63 BPs). El spec `refinar-remediaciones-seguridad` tarea **12 está pendiente**: actualizar las 63 descripciones con el contenido oficial.
2. **Remediaciones de BPs PENDING no todas alineadas al Excel oficial** — es el objeto del spec `refinar-remediaciones-seguridad` (R1/R2/R3). La fuente `docs/Kiro/Seguridad.md` **sí existe** (no es bloqueo).
3. **Verificación de despliegue pendiente** (`refinar-remediaciones-seguridad` tareas 13.2 y 13.3): ejecutar evaluación completa y subir frontend.
4. **Cero cobertura de pruebas automatizadas** para Seguridad (ver sección 4). Hoy no hay forma de "probar completo y automático cada vez" como pide el usuario.
5. No se detectaron funciones que devuelvan siempre el mismo resultado ni `raise NotImplementedError`. El único "TODO" que aparece en grep es la palabra española "TODOS/todos" dentro de textos de remediación (falsos positivos).

---

## 3. Los 4 specs de Kiro (`.kiro/specs/`)

### 3.1 `autowar-reporting-system`
**Propósito** (requirements/design): sistema de reportes — almacenamiento histórico (DynamoDB `AutoWAR-Evaluations`), bucket S3 de reportes, Report Manager Lambda (`/reports/list`, `/reports/generate`), generadores Ejecutivo (DOCX con python-docx + matplotlib) y Técnico (XLSX con openpyxl), y página frontend `reports.html`.
**Avance (`tasks.md`):** mayormente **completo**. Tareas 1–10 y 12 marcadas `[x]` (storage, report manager, ambos generadores, frontend, CDK). **Pendientes:** tarea 11 (manejo de errores transversal: 11.1–11.4) y tarea 13 (checkpoint final de tests). Los sub-tests `*` siguen sin hacerse.
**Aplica a Seguridad:** indirectamente (los reportes consumen la evaluación de Seguridad). No es prioridad para "pulir Seguridad".

### 3.2 `implement-real-bp-evaluations`
**Propósito:** reemplazar placeholders `PENDING_REVIEW` por evaluaciones reales boto3 en los pilares, en orden Cost → Performance → Reliability → Ops → Sustainability.
**Avance (`tasks.md`):** **Tarea 1 (Cost) completa** `[x]` (1.1–1.14 implementadas; tests `*` omitidos). **Tareas 2–15 pendientes** `[ ]`: Performance (3), Reliability (5), Operational Excellence (7), Sustainability (9), más módulos comunes de error (11), multi-región (12), property tests (13) e integración final (14–15).
**Aplica a Seguridad:** NO directamente (Security ya está hecho); es el spec para **continuar** después de pulir Seguridad.

### 3.3 `refinar-remediaciones-seguridad`
**Propósito:** refinar las 63 BPs de Seguridad — remediaciones precisas según la guía oficial (`docs/Kiro/Seguridad.md` / `Seguridad WAR y Como Evaluar.xlsx`), evidencia más completa y riesgos correctos en BPs PENDING.
**Avance (`tasks.md`):** tareas **1–11 completas** `[x]` (refinamiento de SEC01–SEC11). **Pendientes:** tarea **12** (actualizar las 63 descripciones en `bp_descriptions.py`) y tarea **13** parcial (`[-]`): 13.1 desplegar Lambda `[x]`, pero **13.2 ejecutar evaluación completa** `[ ]` y **13.3 subir frontend a S3 + invalidar CloudFront** `[ ]`.
**Aplica a Seguridad:** **ESTE es el spec principal para "pulir Seguridad".**

### 3.4 `security-pillar-reorganization`
**Propósito:** plan maestro de la plataforma multi-pilar (infra CDK → credential validator → modelos/cálculos → evaluador Security → otros 5 pilares → frontend i18n → despliegue). Es el spec "fundacional".
**Avance (`tasks.md`):** prácticamente **todo `[x]`** (tareas 1–18 marcadas completas, salvo los sub-tests `*` que quedaron sin implementar). Nota: afirma 7.1–7.5 (otros pilares) como completas, lo cual contradice el código real — esas tareas crearon las *clases* evaluadoras pero dejaron la mayoría de BPs como placeholder, trabajo que luego retomó `implement-real-bp-evaluations`.
**Aplica a Seguridad:** fundacional/histórico; no requiere acción nueva para pulir Seguridad.

### Orden recomendado de ejecución (para pulir Seguridad)
1. `refinar-remediaciones-seguridad` → tarea 12 + 13.2/13.3.
2. (Nuevo, no cubierto por ningún spec) crear suite de pruebas automatizadas con moto para Seguridad.
3. `implement-real-bp-evaluations` → desde tarea 3 (Performance) en adelante.

---

## 4. Estado de pruebas

**Hallazgo crítico: NO existe ninguna prueba automatizada en el proyecto.**

- Búsqueda de `test_*.py`, `*_test.py`, `conftest.py` fuera de dependencias (`cdk.out`, `.venv`, `node_modules`, `site-packages`): **0 resultados**.
- No hay `pytest.ini`, `tox.ini`, `noxfile.py`, `Makefile`, ni scripts `.ps1/.sh/.bat` en la raíz. El README menciona `start-servers.ps1` y `pytest -q`, pero **ese script y esas pruebas no están en el repo**.
- `requirements.txt` declara `pytest>=7.0.0`, `pytest-asyncio>=0.21.0`, `moto>=4.2.0` — infraestructura preparada pero **sin usar**.
- Los `tasks.md` listan abundantes property tests (hypothesis) y unit tests, todos marcados como sub-tareas opcionales `[ ]*` y **ninguno implementado**.

**¿Cubren Seguridad?** No. No hay cobertura de ningún pilar.

**¿Comando para correr todo?** No existe hoy.

**Qué falta para una suite que corra "completa y automática" para Seguridad:**
1. Crear carpeta `tests/` con `conftest.py` y fixtures moto (mock de IAM, Organizations, EC2, S3, KMS, GuardDuty, Config, CloudTrail, etc.).
2. Unit tests por BP: montar estado AWS con moto y afirmar `status`/`severity`/`evidence` esperados (incluyendo rutas COMPLIANT, NON_COMPLIANT y PENDING_REVIEW por AccessDenied).
3. Test estructural: Security tiene exactamente 11 preguntas y 63 BPs; contrato de finding completo.
4. Property tests (hypothesis) para `calculate_question_score` / `calculate_pillar_score` / distribuciones (ya especificados en los specs).
5. Un comando único reproducible (p. ej. `pytest -q` o un `run-tests.ps1`) y, opcionalmente, un job CI (`.github/`).
6. Vía de integración opcional contra cuenta real (marcador `@pytest.mark.integration` que use credenciales STS AssumeRole, saltable por defecto).

> Nota de moto: varias APIs que usa Security tienen soporte parcial o nulo en moto (p. ej. Trusted Advisor, Security Hub, Access Analyzer, FIS). Para esas BPs conviene mockear a nivel de cliente boto3 (stubber/monkeypatch) en vez de moto.

---

## 5. CDK / Despliegue

Archivos: `cdk-new/app.py`, `cdk-new/stacks/autowar_stack.py` (637 líneas), `cdk-new/cdk.json`, `cdk-new/requirements.txt` (`aws-cdk-lib==2.100.0`).

### Recursos que define el stack `AutoWARStack`
- **KMS** key (`alias/autowar-secrets`) para cifrar credenciales.
- **Frontend:** bucket S3 (cifrado S3_MANAGED) + CloudFront con OAI, `REDIRECT_TO_HTTPS`, SPA error responses.
- **DynamoDB:** `AutoWAR-Evaluations` (cache de evaluaciones) + tabla histórica (`historical_evaluations_table`), cifrado AWS_MANAGED.
- **S3 reports bucket.**
- **Lambda Layers:** `CommonLayer` (`../lambda/layers/common`) y `ReportsLayer` (`../lambda/layers/reports` — openpyxl/python-docx/matplotlib).
- **Lambdas:** CredentialValidator, UnifiedEvaluator (10 min, 1024 MB), StoreEvaluation, EvaluationOrchestrator, EvaluationStatus, ReportManager (+ generadores ejecutivo/técnico).
- **API Gateway** REST (`AutoWAR API`) con throttling, logging INFO, tracing y CORS abierto.
- **Step Functions:** `sfn.Parallel` que evalúa los 6 pilares en paralelo, con `Catch` por pilar, y una state machine `evaluation_state_machine`.
- **IAM** con permisos acotados a `arn:aws:secretsmanager:*:*:secret:autowar/sessions/*`, KMS encrypt/decrypt, grants a DynamoDB.

### Empaquetado de Lambdas y layers
Vía `lambda_.Code.from_asset("../lambda/<fn>")` y `LayerVersion(code=Code.from_asset("../lambda/layers/<layer>"))`. CDK sube el contenido tal cual (no hay bundling custom visible). Runtime `PYTHON_3_11`.

### Comando de deploy
Desde `cdk-new/`: instalar deps (`pip install -r requirements.txt`) y `cdk deploy` (requiere `cdk bootstrap` previo). El entorno está **hardcodeado** en `app.py` a `account="102080400524"`, `region="us-east-1"`.

### Sobre los DOS stacks en la cuenta (`AutoWARStack` vs `AutoWarStack`)
- El código actual define **un único** stack con id `"AutoWARStack"` (WAR en mayúsculas) — `app.py:13` y `class AutoWARStack` en `autowar_stack.py:25`.
- **No existe la carpeta `cdk/` antigua** que menciona el README (verificado: `Test-Path cdk` → False); solo existe `cdk-new/`.
- Por tanto, la hipótesis más probable: **`AutoWarStack` (minúscula) es un stack legado/huérfano** desplegado por una iteración anterior del proyecto (el README habla de un `cdk/` previo y de `AutoWarUserPoolId`/`AutoWarUserPoolClientId` con esa capitalización). No es reproducible desde el código actual y conviene revisarlo en CloudFormation para decidir si se elimina. **Esto es una verificación de solo lectura; no se tocó la cuenta.**

---

## 6. Barrido de alto nivel del resto

| Pieza | Ruta | Qué hace | Estado aparente |
|---|---|---|---|
| Credential Validator | `lambda/credential_validator/handler.py` (116 líneas) | Valida credenciales con STS, cifra con KMS, guarda sesión en Secrets Manager; soporta `action` new/load (reporting) | Implementado |
| Evaluation Orchestrator | `lambda/evaluation_orchestrator/handler.py` (97 líneas) | Lee `X-Session-ID`, genera `evaluation_id`, arranca Step Functions, guarda estado `IN_PROGRESS` en DynamoDB con TTL 24h | Implementado |
| Evaluation Status | `lambda/evaluation_status/` | Consulta estado de la evaluación | Presente |
| Store / Save Evaluation | `lambda/store_evaluation/`, `lambda/save_evaluation_results/` | Persisten resultados | Presentes |
| Report Manager | `lambda/report_manager/handler.py` (222 líneas) | Rutas `/reports/list` y `/reports/generate`; invoca generadores; firma URLs S3 | Implementado |
| Report Generator Ejecutivo | `lambda/report_generator_executive/` (401 líneas) | DOCX con python-docx + gráficos matplotlib | Implementado |
| Report Generator Técnico | `lambda/report_generator_technical/` (548 líneas) | XLSX con openpyxl, formato condicional | Implementado |
| Capa común | `lambda/layers/common/python/autowar_common/` | `models.py` (dataclasses Finding/Question/Pillar), `calculations.py` (scores/distribuciones), `credentials_manager.py` (STS/KMS/Secrets), `evaluation_builder.py`, `report_storage.py`, `historical_evaluations.py` | Implementado |

El flujo de credenciales sigue el patrón documentado: AssumeRole preferido (STS) y claves de acceso como fallback guardadas en Secrets Manager + KMS; validación con `sts:GetCallerIdentity`.

**Documentación fuente:** `docs/Kiro/Seguridad.md` y `docs/Kiro/Optimización de Costos.md` existen (guías "¿Cómo evaluar?"), más los Excel originales en `docs/` (`Seguridad WAR y Como Evaluar.xlsx`, `Costos WAR...`, etc.).

---

## 7. Recomendación final (plan ordenado)

### Fase A — Pulir Seguridad
1. **Crear la suite de pruebas de Seguridad (bloqueante para "probar siempre").** No existe hoy. Montar `tests/` con moto + stubber boto3, unit tests por BP (rutas COMPLIANT/NON_COMPLIANT/PENDING), test estructural (11 preguntas / 63 BPs), property tests de scoring, y un comando único (`pytest -q` o `run-tests.ps1`). Añadir marcador `integration` opcional contra cuenta real. *(No mapea a ningún spec existente — recomiendo añadirlo como tarea nueva dentro de `refinar-remediaciones-seguridad` o un spec de testing.)*
2. **`refinar-remediaciones-seguridad` tarea 12:** completar las 63 descripciones en `bp_descriptions.py` desde `docs/Kiro/Seguridad.md`.
3. **`refinar-remediaciones-seguridad` tareas 13.2 y 13.3:** ejecutar evaluación completa de Seguridad contra la cuenta y verificar; subir frontend a S3 e invalidar CloudFront.
4. (Opcional) Alinear remediaciones/riesgos de BPs PENDING restantes con la guía oficial (R2/R3 del spec).

### Fase B — Continuar pilares
5. **`implement-real-bp-evaluations` tarea 3 (Performance):** completar las BPs que hoy caen a `_create_pending` (ElastiCache, ELBv2, etc.).
6. Tareas 5 (Reliability), 7 (Operational Excellence), 9 (Sustainability): hoy 100% placeholder, requieren implementación completa.
7. Tareas 11 (manejo de errores común), 12 (multi-región), 13–15 (property/integration tests, validación final).

### Fase C — Reportes y limpieza
8. `autowar-reporting-system` tareas 11 (manejo de errores) y 13 (checkpoint de tests).
9. **Investigar y resolver el stack huérfano `AutoWarStack`** en la cuenta (revisar en CloudFormation; decidir borrado tras confirmar que no está en uso). Acción destructiva → requiere confirmación explícita del usuario.

### Riesgos / bloqueos detectados
- **Sin pruebas automatizadas:** cualquier refinamiento de Seguridad hoy se valida solo manualmente. Es el mayor riesgo para la meta del usuario ("probar completo y automático cada vez").
- **Soporte parcial de moto** para APIs como Trusted Advisor, Security Hub, Access Analyzer, FIS → usar stubs boto3 en esas BPs.
- **Entorno CDK hardcodeado** (cuenta/región en `app.py`): dificulta despliegues multi-cuenta; considerar parametrizar vía contexto/variables de entorno.
- **README desactualizado** (habla de 5 preguntas SEC, "mock AWS resources" y carpeta `cdk/`): puede inducir a error; conviene actualizarlo.
- **Inconsistencia documental** entre `security-pillar-reorganization` (marca otros pilares como completos) y el código real (placeholders). La fuente de verdad del avance real de pilares es `implement-real-bp-evaluations/tasks.md`.
- **Dos tablas DynamoDB y stacks duplicados** en la cuenta pueden generar confusión/costos; revisar al resolver el stack huérfano.

---

### Anexo — Evidencia de archivos clave
- `lambda/evaluators/unified_handler.py` — router dinámico + compresión a DynamoDB.
- `lambda/evaluators/security/handler.py:279` — `class SecurityEvaluator`; `_evaluate_sec01`..`_evaluate_sec11`.
- `lambda/evaluators/security/all_bp_evaluations.py` — 61 funciones `evaluate_secNN_bpMM`, 140+ `session.client`, 43 servicios AWS.
- `lambda/evaluators/{reliability,operational_excellence,sustainability}/handler.py` — solo `_create_pending` (0 boto3).
- `lambda/evaluators/performance/handler.py` — real en PERF01–04 BP01, resto `_create_pending`.
- `lambda/evaluators/cost/handler.py` — 0 `_create_pending`.
- `cdk-new/app.py` / `cdk-new/stacks/autowar_stack.py:25` — único stack `AutoWARStack`, cuenta 102080400524/us-east-1.
- `requirements.txt` — pytest/moto declarados; sin tests en el repo.
- `.kiro/specs/*/tasks.md` — estados de avance citados en la sección 3.
- `docs/Kiro/Seguridad.md` — guía oficial "¿Cómo evaluar?" (existe).

_Content was rephrased for compliance with licensing restrictions where source text was summarized._
