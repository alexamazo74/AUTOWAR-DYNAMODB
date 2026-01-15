# Diseño de esquemas DynamoDB — AutoWAR

Resumen de la propuesta de claves primarias (PK), claves de ordenación (SK) y GSIs para las tablas listadas en el alcance. Está orientado a consultas comunes de la plataforma (por cliente, por evaluación, por recurso, por BP, por id único, por estado).

Notas generales:
- Todas las tablas usan `BILLING_MODE = PAY_PER_REQUEST`.
- Cuando se indican claves compuestas, usar el prefijo (por ejemplo `CLIENT#`, `EVAL#`) para evitar colisiones y facilitar consultas multi-entidad.
- Recomiendo usar `ttl` (atributo numérico UNIX epoch) para elementos temporales (e.g., evidencias de corta retención, notificaciones transitorias).
- Para secretos y credenciales sensibles, preferir AWS Secrets Manager y almacenar en la tabla solo un `secret_ref` o `secret_arn`.

---

## 1) `autowar-clients`
- PK: `CLIENT#<clientId>`
- SK: `META#<metaId>` (por ejemplo `META#profile`) — puede usarse `META#` fijo para un único item perfil por cliente
- Atributos: `name`, `industry`, `contact_emails`, `accounts` (lista de accountIds), `created_at`, `status`
- GSIs:
  - `industryIndex` -> PK: `industry`, SK: `created_at` (query clients por industria)
  - `statusIndex` -> PK: `status`, SK: `created_at` (para listar clientes activos/inactivos)
- Accesos típicos: obtener cliente por id, listar clientes por industria, buscar por status.

## 2) `autowar-evaluations`
- PK: `CLIENT#<clientId>`
- SK: `EVAL#<evaluationId>` (usar UUID o timestamp prefijado)
- Atributos: `evaluationId`, `accountId`, `region`, `start_ts`, `end_ts`, `score_total`, `pillar_scores` (map), `status`, `summary`, `created_by`
- GSIs:
  - `evaluationByIdIndex` -> PK: `evaluationId`, SK: `end_ts` (buscar evaluación por id)
  - `accountEvaluationsIndex` -> PK: `ACCOUNT#<accountId>`, SK: `end_ts` (listar evaluaciones por cuenta)
  - `statusIndex` -> PK: `status`, SK: `end_ts` (filtrar evaluaciones por estado)
- Accesos: listar evaluaciones por cliente, recuperar evaluación por id, histórico por cuenta o por periodo.

## 3) `autowar-waf-questions`
- PK: `QUESTION#<questionId>`
- SK: `VERSION#<version>` (permite versiones de la pregunta si hay cambios)
- Atributos: `question_text`, `pillar`, `weight`, `order`, `related_bps` (lista)
- GSI:
  - `pillarIndex` -> PK: `pillar`, SK: `order` (obtener preguntas por pilar en orden)
- Accesos: cargar preguntas para una evaluación, buscar pregunta por id.

## 4) `autowar-best-practices`
- PK: `BP#<bpId>`
- SK: `QUESTION#<questionId>` (si se relacionan BPs a preguntas) o `META#<meta>` para metadatos
- Atributos: `description`, `severity`, `remediation_steps` (lista/JSON), `references`
- GSI:
  - `questionIndex` -> PK: `questionId`, SK: `severity` (listar BPs por pregunta)
- Accesos: consultar BP por id, listar BPs por pregunta.

## 5) `autowar-aws-resources`
- PK: `CLIENT#<clientId>`
- SK: `RESOURCE#<resourceType>#<resourceId>` (por ejemplo `RESOURCE#EC2#i-0123...` o usar ARN)
- Atributos: `resourceArn`, `resourceType`, `accountId`, `region`, `discovered_at`, `config` (map)
- GSI:
  - `resourceArnIndex` -> PK: `resourceArn`, SK: `discovered_at` (buscar recurso por ARN)
  - `typeIndex` -> PK: `resourceType`, SK: `region` (consultas por tipo)
- Accesos: inventario por cliente; buscar evidencias/relación recurso → BP.

## 6) `autowar-remediation-tracking`
- PK: `CLIENT#<clientId>`
- SK: `REMEDIATION#<remediationId>`
- Atributos: `bpId`, `evaluationId`, `description`, `status` (OPEN/IN_PROGRESS/CLOSED), `assigned_to`, `created_at`, `updated_at`, `resolution_notes`
- GSI:
  - `statusIndex` -> PK: `status`, SK: `created_at` (listar remediaciones abiertas)
  - `assignedIndex` -> PK: `assigned_to`, SK: `updated_at` (tareas por responsable)
- Accesos: listar remediaciones por cliente, por estado, por responsable.

## 7) `autowar-automation-config`
- PK: `CLIENT#<clientId>`
- SK: `CONFIG#<configName>`
- Atributos: `type` (schedule|webhook|lambda), `schedule` (cron spec), `enabled`, `config_json`
- GSI opcional: none required; consultas por cliente son la más común
- Accesos: leer/configurar automatizaciones por cliente.

## 8) `autowar-risks`
- PK: `CLIENT#<clientId>`
- SK: `RISK#<riskId>`
- Atributos: `title`, `description`, `severity`, `likelihood`, `impact`, `relatedBPs` (lista), `created_at`
- GSI:
  - `severityIndex` -> PK: `severity`, SK: `created_at` (filtrar por severidad global)
- Accesos: listar riesgos por cliente y priorizarlos.

## 9) `autowar-analysis-history`
- PK: `CLIENT#<clientId>`
- SK: `ANALYSIS#<analysisId>` (puede ser evaluaciónId o snapshot timestamp)
- Atributos: `snapshot` (referencia o JSON), `metrics`, `created_at`
- GSI opcional: `createdAtIndex` -> PK: `created_at` para consultas temporales globales
- Accesos: reconstruir análisis históricos; comparar snapshots.

## 10) `autowar-comparative-analysis`
- PK: `CLIENT#<clientId>`
- SK: `COMPARE#<comparisonId>`
- Atributos: `baseline_id`, `comparisons` (map), `generated_at`
- GSI: `baselineIndex` -> PK: `baseline_id`, SK: `generated_at`
- Accesos: resultados comparativos solicitados por cliente.

## 11) `autowar-periodic-results`
- PK: `CLIENT#<clientId>`
- SK: `PERIOD#<YYYY-MM>` (ej. `PERIOD#2026-01`)
- Atributos: `summary`, `score_total`, `pillar_scores`, `generated_at`, `report_ref`
- GSI: `periodIndex` -> PK: `period` (si se quiere listar por periodo global)
- Accesos: informe periódico por cliente.

## 12) `autowar-evidence-technical`
- PK: `CLIENT#<clientId>`
- SK: `EVID#<evidenceId>`
- Atributos: `resourceArn`, `questionId`, `bpId`, `s3_key`, `captured_at`, `captured_by`, `metadata`
- GSIs:
  - `resourceArnIndex` -> PK: `resourceArn`, SK: `captured_at`
  - `questionIndex` -> PK: `questionId`, SK: `captured_at`
- TTL recomendado para evidencias temporales (`ttl` attribute) si aplica
- Accesos: listar evidencias por recurso, por pregunta o por BP.

## 13) `autowar-ai-prompts-results`
- PK: `PROMPT#<promptId>`
- SK: `RESULT#<resultId>`
- Atributos: `prompt_text`, `model`, `response`, `tokens_used`, `confidence`, `created_at`, `input_refs` (list)
- GSI:
  - `promptHashIndex` -> PK: `prompt_hash`, SK: `created_at` (buscar respuestas por prompt reproducible)
- Accesos: historial de prompts, re-ejecución y auditoría de IA.

## 14) `autowar-industry-benchmarks`
- PK: `INDUSTRY#<industryName>`
- SK: `METRIC#<metricId>`
- Atributos: `metric_name`, `baseline_value`, `percentile`, `updated_at`
- Accesos: comparar cliente contra baseline de su industria.

## 15) `autowar-notifications-log`
- PK: `CLIENT#<clientId>`
- SK: `NOTIF#<notifId>`
- Atributos: `channel`, `payload_ref` (S3 o JSON), `status`, `sent_at`, `attempts`
- GSI:
  - `statusIndex` -> PK: `status`, SK: `sent_at`
- Accesos: revisar historiales de notificación y reintentos.

## 16) `autowar-user-management`
- PK: `USER#<userId>`
- SK: `META#<meta>` (ej. `META#profile`)
- Atributos: `email`, `name`, `roles` (lista), `last_login`, `status`
- GSI:
  - `emailIndex` -> PK: `email`, SK: `userId` (buscar usuario por email)
- Nota: no almacenar contraseñas en claro — recomendar Cognito o Secrets Manager para auth.

## 17) `autowar-aws-credentials`
- PK: `CLIENT#<clientId>`
- SK: `CRED#<credId>`
- Atributos: `credential_type` (role|access_keys), `role_arn`, `secret_ref` (ARN en Secrets Manager), `expiry`, `created_at`, `status`
- GSI:
  - `statusIndex` -> PK: `status`, SK: `expiry` (encontrar credenciales expiring/expired)
- Nota: almacena sólo referencias cifradas a secrets, no claves en texto plano.

Detalles del formato actual (metadatos que guarda el backend)

Cuando se crea un registro de credenciales via el endpoint `/credentials` el backend inserta un item en `autowar-aws-credentials` cuyo contenido varía ligeramente según el flujo usado. A continuación se describen los campos esperados y ejemplos.

Campos comunes
- `id` (string): identificador único del registro (UUID)
- `client_id` (string): id del cliente al que pertenecen las credenciales
- `created_at` (number): epoch timestamp de creación
- `type` (string): `role` o `keys`
- `status` (string): estado administrativo, p.ej. `ACTIVE`, `EXPIRED`, `REVOKED`

Flujo AssumeRole (preferido)
- `role_arn` (string): ARN del role proporcionado por el cliente
- `caller_identity` (map): resultado de `sts:GetCallerIdentity` al asumir el role, p.ej. `{ "Account": "1234...", "Arn": "arn:aws:iam::...", "UserId": "..." }`

Ejemplo (AssumeRole):

{
  "id": "6f1d2a9e-...",
  "client_id": "client-123",
  "created_at": 1700000000,
  "type": "role",
  "role_arn": "arn:aws:iam::111122223333:role/AutoWARReadOnly",
  "caller_identity": { "Account": "111122223333", "Arn": "arn:aws:sts::...", "UserId": "..." },
  "status": "ACTIVE"
}

Flujo claves (fallback)
- `secret_arn` (string|null): ARN del secreto en Secrets Manager que contiene `access_key_id`, `secret_access_key` y opcional `session_token`. Si `save_secret=false` este campo puede ser `null` y no se guarda la clave.
- `caller_identity` (map): resultado de `sts:GetCallerIdentity` usando las claves proporcionadas.

Ejemplo (keys):

{
  "id": "9b2f3c4d-...",
  "client_id": "client-456",
  "created_at": 1700001000,
  "type": "keys",
  "secret_arn": "arn:aws:secretsmanager:us-east-1:111122223333:secret:autowar/client-456/abcd1234",
  "caller_identity": { "Account": "222233334444", "Arn": "arn:aws:iam::222233334444:user/some-user", "UserId": "..." },
  "status": "ACTIVE"
}

Notas operativas
- No almacenar claves en texto plano en DynamoDB ni en registros de logs.
- Para `type=role` se guarda `role_arn` y `caller_identity`; el backend obtiene credenciales temporales en tiempo de ejecución mediante `sts:AssumeRole` cuando se lanza un análisis.
- Para `type=keys` se recomienda guardar las claves en Secrets Manager y referenciarlas desde `secret_arn`.
- Añadir campos extra (por ejemplo `expiry` o `last_used_at`) es posible y útil para gestión/rotación.

---

## Tablas opcionales recomendadas

### `autowar-reports`
- PK: `CLIENT#<clientId>`
- SK: `REPORT#<reportId>`
- Atributos: `evaluationId`, `s3_key`, `report_type` (executive|technical), `generated_at`, `generated_by`
- GSI: `evaluationIndex` -> PK: `evaluationId`, SK: `generated_at`
- Uso: metadatos y enlaces a objetos S3.

Ejemplo y detalles operativos
- `id` (string): uuid del registro (opcional si se usa `pk`/`sk` como identificador)
- `client_id` (string): id del cliente
- `evaluationId` (string): id de la evaluación asociada
- `s3_key` (string): ruta en S3 al artefacto (p.ej. `autowar/client-123/reports/report-2026-01-01-exec.pdf`)
- `report_type` (string): `executive` o `technical`
- `generated_at` (number): epoch timestamp
- `generated_by` (string): id del proceso/usuario que generó el reporte
- `size` (number, opcional): bytes del objeto en S3
- `format` (string, opcional): `pdf`|`xlsx`|`csv`

Ejemplo (autowar-reports):

{
  "id": "report-0001",
  "client_id": "client-123",
  "evaluationId": "6f1d2a9e-...",
  "s3_key": "autowar/client-123/reports/6f1d2a9e-exec.pdf",
  "report_type": "executive",
  "generated_at": 1700002000,
  "generated_by": "worker-01",
  "size": 245678,
  "format": "pdf"
}

### `autowar-audit-log`
- PK: `ENTITY#<entityId>` (puede ser `USER#...` o `EVAL#...`)
- SK: `AUDIT#<timestamp>` (orden temporal descendente posible usando inverted timestamp)
- Atributos: `action`, `actor_id`, `details`, `ip`, `created_at`
- GSI: `actionIndex` -> PK: `action`, SK: `created_at`
- Uso: auditoría de operaciones a nivel de app (complementa CloudTrail).

Ejemplo y campos recomendados
- `id` (string): uuid del evento (opcional)
- `entity_id` (string): id de la entidad afectada (ej. `EVAL#6f1d2a9e-...` o `CLIENT#client-123`)
- `action` (string): operación registrada (p.ej. `ASSUME_ROLE`, `CREATE_EVALUATION`, `STORE_REPORT`)
- `actor_id` (string): quien inició la acción (user id o sistema)
- `details` (map|string): detalles libres o estructurados sobre la acción (error messages, parameters)
- `ip` (string, opcional): dirección IP desde la que se realizó la acción
- `created_at` (number): epoch timestamp
- `severity` (string, opcional): `INFO`|`WARN`|`ERROR`

Ejemplo (autowar-audit-log):

{
  "id": "audit-0001",
  "entity_id": "CLIENT#client-123",
  "action": "ASSUME_ROLE",
  "actor_id": "user-operator-1",
  "details": { "role_arn": "arn:aws:iam::111122223333:role/AutoWARReadOnly", "result": "Success" },
  "ip": "203.0.113.10",
  "created_at": 1700003000,
  "severity": "INFO"
}

Notas operativas
- Registrar en `autowar-audit-log` cada `AssumeRole`, `GetCallerIdentity` válido, y acciones CRUD críticas para facilitar investigación y auditoría por cliente.
- Considerar exportar logs sensibles a un sistema de logging central (OpenSearch/CloudWatch) con retención y acceso controlado.

---

## Recomendaciones operativas
- Mantener `autowar-evaluations` como tabla central para operaciones CRUD de análisis.
- Usar `autowar-aws-resources` y `autowar-evidence-technical` para enlazar recursos concretos (ARNs) con BPs y preguntas.
- Indexar `evaluationId` para lectura rápida por referencia desde reports, remediations y evidence.
- Guardar artefactos binarios (PDF/Excel) en S3 y referenciarlos desde `autowar-reports`.
- Usar Secrets Manager para `secret_ref` almacenados en `autowar-aws-credentials`.

Si quieres, puedo ahora:
- A) Generar los esquemas PK/SK/GSI como código CDK (añadir `autowar-reports` y `autowar-audit-log`),
- B) Implementar en el backend el endpoint CRUD para `autowar-evaluations` usando los patrones anteriores, o
- C) Crear pruebas unitarias para los modelos y conectores.

Elige A/B/C o pide otra acción.
