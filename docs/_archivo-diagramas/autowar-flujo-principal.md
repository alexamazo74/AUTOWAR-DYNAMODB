# AutoWAR (AWS Well-Architected Analyzer) — Flujo principal

Diagrama: `autowar-flujo-principal.drawio` (export PNG: `autowar-flujo-principal.drawio.png`)
Versión: v1 — 2026-10-16 — AWS Solutions GFourmis
Alcance: refleja el **estado actual del código** del proyecto `auto-war`, no una arquitectura objetivo.

## Descripción del flujo

El flujo principal cubre desde que el consultor carga las credenciales del cliente hasta que
obtiene el resultado del análisis de seguridad SEC01.

1. **① Credenciales** — El Analista / Consultor AWS ingresa en el frontend el nombre del
   cliente, la región y las credenciales AWS del cliente (access key, secret, token opcional).
2. **② HTTPS /validate** — El frontend (`frontend/index.html` + `script.js`) envía los datos al
   endpoint `POST /api/validate-credentials` del backend Flask (`backend/app.py`).
3. **③ get_caller_identity** — El backend valida la identidad contra **AWS STS**. Si es válida,
   habilita el botón de análisis en la UI.
4. **④ HTTPS /analyze-sec01** — El Analista dispara el análisis; el frontend llama a
   `POST /api/analyze-sec01`.
5. **⑤ invoca análisis** — El endpoint invoca el **motor de análisis** `WAFSecurityAnalyzer`
   (`backend/waf_analyzer.py`), que evalúa SEC01 best practices BP01–BP08.
6. **⑥ inventario (describe/list)** — El motor inventaria los recursos de la **cuenta AWS del
   cliente** en modo solo lectura: IAM (usuarios, roles, root, MFA), EC2, RDS, Lambda, S3,
   CloudTrail y Organizations.
7. **⑦ persistir resultado** — El resultado (score, hallazgos, riesgos, remediación) se guarda en
   **DynamoDB** (tabla `AutoWAR-WAFAnalysis`).
8. **⑨ resultados** — El resultado vuelve al frontend y se muestra en la pestaña Resultados.

> El paso **⑧ "resumen asistido (futuro)"** hacia **Amazon Bedrock** aparece punteado: está
> previsto en `.env` (`BEDROCK_MODEL_ID`) pero **aún no está integrado** en el flujo.

## Gaps importantes reflejados en el diagrama (líneas punteadas)

- **Backend simulado vs motor real:** hoy `POST /api/analyze-sec01` en `app.py` devuelve datos
  **simulados**; el motor `WAFSecurityAnalyzer` ya está implementado pero aún no está conectado
  al endpoint. Los pasos ⑤, ⑥ y ⑦ representan el flujo previsto una vez conectado.
- **Persistencia:** la tabla DynamoDB existe (via `infrastructure/dynamodb_setup.py`) pero el
  flujo todavía no escribe en ella.
- **Bedrock:** integración de IA generativa para resúmenes, pendiente.

## Servicios / componentes

| Componente | Rol en el flujo |
|------------|-----------------|
| Analista / Consultor AWS | Usuario que opera la herramienta |
| Frontend web estático | UI de captura y visualización (`frontend/`) |
| Backend API Flask | Expone `/validate-credentials` y `/analyze-sec01` (`backend/app.py`) |
| WAFSecurityAnalyzer | Motor de análisis SEC01 BP01–BP08 (`backend/waf_analyzer.py`) |
| AWS STS | Valida la identidad de las credenciales del cliente |
| Cuenta AWS del cliente | IAM, EC2, RDS, Lambda, S3, CloudTrail, Organizations (solo lectura) |
| DynamoDB `AutoWAR-WAFAnalysis` | Persistencia de resultados de análisis |
| Amazon Bedrock | Resúmenes asistidos por IA (futuro, no integrado) |

## Decisiones de diseño del diagrama

- El backend se dibuja dentro de un grupo "EC2 / local" porque hoy es un servidor Flask (no hay
  API Gateway ni Lambda como front del API; las figuras tipo Lambda se usan solo para representar
  los dos endpoints de forma visual).
- La cuenta del cliente se aísla en un grupo rosa para dejar claro que el acceso es de **solo
  lectura** y pertenece a un contexto distinto al de la herramienta.
- Las líneas punteadas marcan lo que **aún no está integrado**, para que el diagrama no sugiera
  más madurez de la real.

---

# Página 2 — Arquitectura objetivo (6 pilares + mejoras)

Export PNG: `autowar-arquitectura-objetivo.drawio.png`
Alcance: arquitectura **objetivo** propuesta (no el estado actual). Cubre los 6 pilares del
Well-Architected Framework y las mejoras sugeridas respecto a lo que hoy existe.

## Flujo objetivo

1. **① HTTPS** — Analista y Cliente acceden al frontend servido por **CloudFront + S3**.
2. **② token** — Autenticación con **Cognito**; el frontend obtiene un token.
3. **③ API** — Llamadas al **API Gateway** (REST) con autorizador Cognito.
4. **④ inicia** — Una **Lambda API** (orquestador / BFF) inicia la ejecución.
5. **⑤ fan-out por pilar** — **Step Functions** orquesta un análisis por cada pilar WAF, con una
   Lambda dedicada por pilar: Seguridad (SEC), Confiabilidad (REL), Excelencia operativa (OPS),
   Rendimiento (PERF), Costos (COST) y Sostenibilidad (SUS). **Amazon Bedrock** genera resumen e
   insights priorizados.
6. **⑥ AssumeRole + inventario** — Las Lambdas asumen un rol cross-account (**STS AssumeRole**,
   solo lectura) para inventariar la(s) cuenta(s) del cliente mediante **acceso directo a las
   APIs** (`describe`/`list`): Organizations y recursos EC2/RDS/S3/IAM/CloudTrail... Las
   credenciales se gestionan con **Secrets Manager** y el cifrado con **KMS** (no se envían
   credenciales en el POST).
   **No se asume que el cliente tenga Security Hub, Trusted Advisor ni Config habilitados, ni
   soporte Business/Enterprise** (lo normal es que no los tenga): AutoWAR implementa por su
   cuenta los checks equivalentes que esos servicios aportarían.
7. **⑦ resultados** — Los resultados se persisten en **DynamoDB** (resultados + reglas).
8. **⑨ informe** — Los informes exportables se guardan en **S3**.

Observabilidad transversal con **CloudWatch** (logs, métricas, alarmas) y despliegue por
**IaC (CloudFormation / CDK)**.

## Mejoras sugeridas (vs estado actual)

1. Cubrir los **6 pilares** WAF, no solo Seguridad (SEC01).
2. **API Gateway + Cognito** en vez de Flask abierto; autorizador por token.
3. **STS AssumeRole cross-account + Secrets Manager**: no enviar credenciales en el POST.
4. **Step Functions** para orquestar un análisis por pilar (paralelo, reintentos).
5. Integrar **Bedrock** para resumen gerencial/técnico e insights priorizados.
6. Persistir resultados en **DynamoDB** e informes exportables en **S3**.
7. **Observabilidad** con CloudWatch y despliegue por **IaC** (CDK/CFN).
8. **Cifrado con KMS** en reposo y en tránsito.
9. **No depender de Security Hub / Trusted Advisor / Config del cliente** (no suelen tenerlos
   habilitados ni soporte Business). AutoWAR debe implementar por su cuenta los checks
   equivalentes que esos servicios aportarían. Ver sección "Checks que AutoWAR debe cubrir por su
   cuenta" más abajo.

## Checks que AutoWAR debe cubrir por su cuenta (reemplazo de servicios AWS no asumidos)

Como no se asume que el cliente tenga Security Hub, Trusted Advisor ni Config, AutoWAR debe
implementar directamente contra las APIs (`describe`/`list`) el equivalente a lo que esos
servicios entregarían:

- **Equivalente a Security Hub (Seguridad):** root sin MFA, access keys de root, usuarios IAM sin
  MFA, políticas con permisos amplios (`*:*`), buckets S3 públicos o sin cifrado, security groups
  con puertos críticos abiertos (22/3389/1433/3306) a 0.0.0.0/0, RDS público, EBS sin cifrado,
  CloudTrail habilitado, rotación de claves KMS, VPC Flow Logs.
- **Equivalente a Trusted Advisor — Costos (COST):** instancias EC2/RDS ociosas o infrautilizadas,
  volúmenes EBS no asociados, Elastic IPs sin usar, oportunidades de Savings Plans / Reserved
  Instances, recursos sobredimensionados.
- **Equivalente a Trusted Advisor — Confiabilidad (REL):** recursos en una sola AZ, ausencia de
  Multi-AZ en RDS, falta de backups/snapshots, ausencia de Auto Scaling, single points of failure.
- **Equivalente a Trusted Advisor — Rendimiento (PERF):** tipos de instancia desactualizados,
  oportunidades de migrar a Graviton, configuraciones subóptimas.
- **Equivalente a Trusted Advisor — Límites de servicio:** consumo cercano a cuotas (service
  quotas) por servicio y región.
- **Excelencia operativa (OPS) y Sostenibilidad (SUS):** tags consistentes, uso de IaC, logging y
  monitoreo; para SUS, eficiencia de recursos y apagado de recursos ociosos.

> El archivo `.drawio` contiene ambas páginas: "AutoWAR - Flujo principal" (actual) y
> "AutoWAR - Arquitectura objetivo". El export PNG por línea de comandos en Windows solo genera
> la página activa; para regenerar la página 2 se exportó por separado.
