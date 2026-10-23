# AutoWAR (AWS Well-Architected Analyzer) — Arquitectura

Diagrama: `AutoWAR-Arquitectura.drawio` (3 páginas)
Versión: v3 — 2026-10-16 — AWS Solutions GFourmis
Cuenta de referencia desplegada: 102080400524 / us-east-1

Este documento consolida la arquitectura de AutoWAR en tres vistas y reemplaza a los diagramas
previos (`AutoWAR_Arquitectura.drawio`, `AutoWAR_Arquitectura_v2.drawio` y
`autowar-flujo-principal.drawio`), que quedaron archivados en `docs/_archivo-diagramas/`.

---

## Página 1 — As-Is (estado real desplegado)

Refleja lo que **hoy** está desplegado como serverless con CDK, verificado contra el código en
`lambda/` y el stack `cdk-new/stacks/autowar_stack.py`.

Flujo:

1. El analista entrega credenciales AWS del cliente y región en el frontend (CloudFront + S3).
2. `POST /credentials/validate` → Lambda `CredentialValidator` valida con STS y guarda la sesión
   **cifrada con KMS en Secrets Manager** (TTL 1 hora).
3. `POST /evaluate/start` → Lambda `EvaluationOrchestrator` inicia **Step Functions**.
4. Step Functions ejecuta un estado **Parallel** con 6 ramas; cada rama invoca la **misma** Lambda
   `UnifiedEvaluator` con `pathParameters.pillar` distinto (no son 6 Lambdas separadas).
5. Cada evaluación accede a la cuenta del cliente en **solo lectura** (`describe`/`list`) usando
   las claves de la sesión. Guarda su resultado comprimido (gzip+base64) en DynamoDB.
6. `SaveEvaluationResults` consolida en la tabla histórica (`AutoWAR-Evaluations`, con PITR).
7. El frontend hace **polling** a `GET /evaluate/status/{id}` cada 5 s.
8. Reportes técnico/ejecutivo (openpyxl/python-docx) se generan bajo demanda y se guardan en S3.

### Estado de implementación por pilar (verificado en código)

| Pilar | Estado | Detalle |
|-------|--------|---------|
| Security (SEC) | ✅ Real | 11 preguntas, 63 BPs evaluadas contra APIs AWS |
| Cost (COST) | ✅ Real | Todas las BPs con llamadas reales (`iam`, `ce`, `budgets`, `ec2`, ...) |
| Performance (PERF) | 🟡 Parcial | Solo `BP01` real (ec2/lambda/s3/rds/vpc); el resto `PENDING_REVIEW` |
| Reliability (REL) | 🔴 Placeholder | Estructura 13 preguntas / 37 BPs, todo `_create_pending` |
| Operational Excellence (OPS) | 🔴 Placeholder | Todo `_create_pending` |
| Sustainability (SUS) | 🔴 Placeholder | Todo `_create_pending` |

### Componentes reales no mostrados en diagramas previos

Lambdas: `CredentialValidator`, `StoreEvaluation`, `EvaluationOrchestrator`, `EvaluationStatus`,
`SaveEvaluationResults`, `ReportManager`, `TechnicalReport`, `ExecutiveReport`.
Datos: DynamoDB Evaluations (TTL) + DynamoDB Historical (PITR), S3 Reports (ciclo de vida 30 días),
Secrets Manager (sesiones), KMS (rotación habilitada).

---

## Página 2 — To-Be (objetivo)

Arquitectura objetivo aprobada en la conversación de diseño. Añade sobre el As-Is:

1. **Portal Hub + Cognito federado** — la entrada es desde el Hub de GFourmis, que emite un JWT
   firmado (OIDC) con el acuerdo de integración. Cognito valida la federación.
2. **Entitlements** — Lambda Authorizer en API Gateway + tabla DynamoDB de entitlements; enforcement
   en doble capa (frontend oculta, backend rechaza).
3. **STS AssumeRole cross-account + ExternalId** — reemplaza el guardado de claves de larga
   duración del cliente. El rol es de solo lectura en la cuenta del cliente.
4. **Los 6 pilares completos** con evaluación real.
5. **Amazon Bedrock** para resumen e insights por dominio, con Guardrails y VPC endpoint.
6. **WAF** delante de CloudFront/API Gateway (AWS Managed Rules + rate limiting).
7. **Observabilidad y resiliencia** — alarmas CloudWatch, X-Ray, SQS DLQ; HA multi-AZ nativo del
   serverless; DR con PITR + versionado S3 + backups (RPO/RTO a definir).

---

## Página 3 — Flujo Hub + Entitlements

Explica el mecanismo de integración y la tabla de brechas As-Is → To-Be.

### Acuerdo de integración (claims del JWT)

- `pillars`: lista de pilares habilitados (1, varios o todos)
- `reports`: técnico y/o ejecutivo
- `history`: acceso a históricos (sí/no)
- `remediations`: presentar remediaciones (sí/no)
- `inventory_architecture`: inventario de recursos + arquitectura actual (sí/no)
- `recommended_architecture`: arquitectura recomendada (sí/no)
- `accounts`: **allow-list** de cuentas AWS que se pueden analizar
- `valid_until`: vigencia del acuerdo (días/horas)
- extensible: nuevas funcionalidades siguen el mismo patrón (habilitado/pagado por acuerdo)

### Reglas clave

- AutoWAR **solo** permite analizar las cuentas de la `allow-list` del Hub.
- El Hub **no** envía credenciales de acceso; el usuario provee el acceso a la cuenta vía
  AssumeRole antes de ejecutar cualquier función.
- El acuerdo se **persiste** en DynamoDB por su vigencia (TTL = `valid_until`).
- Enforcement en **doble capa**: UI (UX) + Lambda Authorizer (seguridad).

### Puntos a decidir en comité de arquitectura

1. Mecanismo exacto de federación Hub→AutoWAR (OIDC/JWT recomendado; alternativas SAML o API
   servidor-a-servidor).
2. RPO/RTO objetivo para DR.
3. Alcance de Bedrock (solo resumen gerencial/técnico vs evaluación asistida por IA).

---

## Exportación de imágenes (PNG)

En este entorno no hay draw.io CLI ni la app de escritorio instalada, por lo que los PNG no se
regeneran automáticamente. Para exportarlos:

- Abrir `AutoWAR-Arquitectura.drawio` en draw.io (desktop o app.diagrams.net).
- Menú **Archivo → Exportar como → PNG**, repetir por cada página (As-Is, To-Be, Flujo Hub).

Alternativa por línea de comandos (si se instala el CLI de draw.io):

```
drawio -x -f png -p 0 -o AutoWAR-AsIs.png     AutoWAR-Arquitectura.drawio
drawio -x -f png -p 1 -o AutoWAR-ToBe.png     AutoWAR-Arquitectura.drawio
drawio -x -f png -p 2 -o AutoWAR-FlujoHub.png AutoWAR-Arquitectura.drawio
```

---

## Costos (actualizado para el To-Be)

Modelo de costos en `AutoWAR-Estimacion-Costos.xlsx` (hojas con formulas encadenadas y celdas
editables). Incluye los componentes nuevos del To-Be: WAF, Cognito, Lambda Authorizer y la tabla
DynamoDB de entitlements (ademas de Bedrock, que ya estaba modelado).

Ordenes de magnitud (escenario base, us-east-1):

- **Costo por analisis**: ~US$0.06 (Bedrock Haiku) a ~US$0.14 (Bedrock Sonnet).
- **Costo mensual (200 analisis)**: ~US$31 (Haiku) a ~US$46 (Sonnet).
- El To-Be agrega ~US$8/mes fijos por WAF (1 web ACL + 3 reglas) y Cognito ~US$0 en volumen bajo
  (dentro de capa gratis Essentials), creciendo con los MAU.

Estimacion en la calculadora de AWS (To-Be, 200 analisis/mes, modelo Sonnet):
`https://calculator.aws/#/estimate?id=a2ab4d09438706b2e4a1ebaf9c3cf5d1a462ab8a`

Nota de modelado: en la calculadora, Bedrock se parametriza por tasa (requests/min x horas/dia)
con tokens por request; se ajustaron los tokens por request para que el total mensual de tokens
coincida con el volumen real (3M entrada / 0.8M salida por mes). El Excel es el modelo
autoritativo (parametriza Bedrock directamente por tokens).
