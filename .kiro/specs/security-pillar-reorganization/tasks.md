# Plan de Implementación: AutoWAR - Sistema Multi-Pilar

## Visión General

Este plan implementa la plataforma AutoWAR de evaluación del AWS Well-Architected Framework con arquitectura serverless. El sistema evalúa 6 pilares (Security, Reliability, Performance, Cost, Operational Excellence, Sustainability) consultando APIs de AWS reales para generar hallazgos con evidencia técnica.

La implementación sigue un enfoque incremental: infraestructura → backend → frontend → testing, asegurando que cada componente se integre correctamente antes de avanzar.

## Tareas

- [x] 1. Configurar infraestructura serverless con CDK
  - Crear stack de CDK con S3, CloudFront, API Gateway, Lambda, DynamoDB, Secrets Manager, KMS
  - Configurar permisos IAM para Lambdas (acceso a Secrets Manager, DynamoDB, KMS)
  - Configurar CORS en API Gateway para permitir requests desde CloudFront
  - Desplegar stack y verificar que todos los recursos se crean correctamente
  - _Requirements: 1.1, 1.2, 6.4, 7.7_

- [ ]* 1.1 Escribir property test para validación de estructura de infraestructura
  - **Property 3: Pillar Data Structure Completeness**
  - **Validates: Requirements 1.2, 7.1**

- [x] 2. Implementar Credential Validator Lambda
  - [x] 2.1 Crear función Lambda que valide credenciales con STS GetCallerIdentity
    - Aceptar input: access_key_id, secret_access_key, session_token (opcional), account_id, regions (lista)
    - Validar formato de regiones con regex `^[a-z]{2}-[a-z]+-\d$`
    - Llamar a `sts:GetCallerIdentity` con las credenciales proporcionadas
    - Si válidas: generar UUID para session_id, cifrar credenciales con KMS, guardar en Secrets Manager con TTL de 1 hora
    - Si inválidas: retornar HTTP 401 con mensaje descriptivo
    - _Requirements: 6.1, 6.2, 6.3, 6.4_
  
  - [ ]* 2.2 Escribir property test para validación de input de credenciales
    - **Property 18: Credential Input Validation**
    - **Validates: Requirements 6.1**
  
  - [ ]* 2.3 Escribir unit tests para manejo de errores de credenciales
    - Test: Credenciales inválidas retornan HTTP 401
    - Test: Credenciales válidas retornan session_id y expires_at
    - Test: Formato de región inválido retorna error descriptivo
    - _Requirements: 6.3_

- [x] 3. Implementar modelos de datos y funciones de cálculo
  - [x] 3.1 Crear dataclasses para Finding, Question, Pillar en Python
    - Definir Finding con campos: bp, description, status, severity, finding, evidence, remediation, risk
    - Definir Question con campos: question_id, title, description, score, bps_evaluated, status, findings
    - Definir Pillar con campos: pillar_id, region, regions, multi_region, pillar_name, description, overall_score, total_findings, total_best_practices, timestamp, questions, compliance_distribution, severity_distribution
    - Implementar validación de enums para status (COMPLIANT, NON_COMPLIANT, PENDING_REVIEW) y severity (CRITICAL, HIGH, MEDIUM, LOW)
    - _Requirements: 3.3, 3.4, 3.5, 9.1, 9.3, 9.4, 9.5_
  
  - [x] 3.2 Implementar funciones de cálculo de scores
    - `calculate_question_score(findings)`: Calcular score de pregunta como promedio ponderado (COMPLIANT=100, NON_COMPLIANT=0, PENDING_REVIEW=50)
    - `calculate_pillar_score(questions)`: Calcular score de pilar como promedio ponderado por número de BPs
    - `determine_question_status(findings)`: Determinar estado de pregunta basado en estados de findings
    - `calculate_distributions(questions)`: Calcular distribuciones de compliance y severity
    - _Requirements: 2.8, 4.1, 4.2, 4.3, 4.4, 4.5_
  
  - [ ]* 3.3 Escribir property tests para cálculo de scores
    - **Property 1: Question Score Calculation Consistency**
    - **Property 2: Pillar Score Calculation Consistency**
    - **Property 20: Score Range Invariant**
    - **Validates: Requirements 2.8, 4.1, 4.2, 4.3**
  
  - [ ]* 3.4 Escribir property tests para estructura de datos
    - **Property 4: Question Data Structure Completeness**
    - **Property 5: Finding Data Structure Completeness**
    - **Property 6: Status Enumeration Validation**
    - **Property 7: Severity Enumeration Validation**
    - **Validates: Requirements 3.3, 3.4, 3.5, 9.1, 9.3, 9.4, 9.5**
  
  - [ ]* 3.5 Escribir property tests para distribuciones
    - **Property 14: Compliance Distribution Accuracy**
    - **Property 15: Severity Distribution Accuracy**
    - **Validates: Requirements 4.4, 4.5**

- [x] 4. Checkpoint - Verificar modelos y cálculos
  - Asegurar que todos los tests de modelos y cálculos pasen
  - Verificar que las validaciones de enums funcionen correctamente
  - Preguntar al usuario si hay dudas o ajustes necesarios

- [x] 5. Implementar Security Pillar Evaluator Lambda
  - [x] 5.1 Crear estructura base del evaluador de Security
    - Crear clase `SecurityEvaluator` con método `evaluate()` que retorna estructura de Pillar
    - Implementar métodos `_evaluate_sec01()` a `_evaluate_sec11()` para las 11 preguntas
    - Cada método debe retornar estructura de Question con findings
    - Implementar método `_handle_permission_error()` para marcar BPs como PENDING_REVIEW cuando hay errores de permisos
    - _Requirements: 1.2, 1.3, 2.1, 3.2, 6.6, 14.1, 14.2_
  
  - [x] 5.2 Implementar evaluaciones reales de BPs de Security
    - Implementar evaluación de SEC01-BP01 (Separate workloads using accounts) consultando Organizations API
    - Implementar evaluación de SEC01-BP02 (Secure root user) consultando IAM API
    - Implementar evaluación de SEC02-BP01 (Strong sign-in mechanisms) consultando IAM GetAccountPasswordPolicy
    - Implementar evaluaciones de SEC03 (Permissions management) consultando IAM APIs
    - Implementar evaluaciones de SEC04 (Detection) consultando CloudTrail y GuardDuty APIs
    - Implementar evaluaciones de SEC05 (Network protection) consultando VPC y Security Groups APIs
    - Implementar evaluaciones de SEC08 (Data at rest) consultando KMS y encryption settings
    - Para BPs sin implementación real, usar placeholder que retorna PENDING_REVIEW
    - _Requirements: 3.2, 3.7, 13.1_
  
  - [x] 5.3 Implementar manejo de errores y reintentos
    - Implementar retry logic con backoff exponencial (1s, 2s, 4s) para errores de red/timeout
    - Capturar `ClientError` de boto3 y determinar si es error de permisos (AccessDenied, UnauthorizedOperation)
    - Si error de permisos: marcar BP como PENDING_REVIEW con mensaje de error en evidence
    - Si error de red después de 3 reintentos: marcar BP como PENDING_REVIEW
    - Continuar evaluación de otras BPs incluso si algunas fallan
    - _Requirements: 6.6, 14.1, 14.2, 14.3, 14.6_
  
  - [x] 5.4 Implementar soporte multi-región
    - Modificar evaluador para aceptar lista de regiones
    - Evaluar cada región independientemente creando boto3.Session por región
    - Implementar función `aggregate_multi_region_results()` que combina resultados de múltiples regiones
    - Agregar campo `region` a cada finding para identificar de qué región proviene
    - Calcular scores agregados como promedio ponderado entre regiones
    - _Requirements: 6.7_
  
  - [ ]* 5.5 Escribir property test para agregación multi-región
    - **Property 13: Multi-Region Aggregation Correctness**
    - **Validates: Requirements 6.7**
  
  - [ ]* 5.6 Escribir unit tests para evaluador de Security
    - Test: Security pillar tiene exactamente 11 preguntas (SEC01-SEC11)
    - Test: Security pillar tiene exactamente 63 Best Practices totales
    - Test: Error de permisos marca BP como PENDING_REVIEW con error en evidence
    - Test: Evaluación parcial continúa cuando algunas BPs fallan
    - _Requirements: 2.1, 14.1, 14.6_

- [x] 6. Implementar Lambda handler para Security con cache
  - [x] 6.1 Crear función `lambda_handler` para Security pillar
    - Extraer session_id del header X-Session-ID
    - Recuperar credenciales de Secrets Manager usando session_id
    - Si no hay credenciales o sesión expirada: retornar HTTP 401
    - Verificar cache en DynamoDB (evaluaciones de últimos 5 minutos)
    - Si hay cache válido: retornar resultado cacheado
    - Si no hay cache: ejecutar evaluación con SecurityEvaluator
    - Guardar resultado en DynamoDB con partition key=session_id, sort key=security#{timestamp}
    - Retornar resultado con HTTP 200
    - _Requirements: 6.5, 7.1, 7.2, 12.3_
  
  - [ ]* 6.2 Escribir unit tests para lambda handler
    - Test: Session ID inválido retorna HTTP 401
    - Test: Cache válido (< 5 min) retorna resultado cacheado sin re-evaluar
    - Test: Sin cache ejecuta evaluación y guarda en DynamoDB
    - _Requirements: 6.5_

- [x] 7. Implementar evaluadores para los otros 5 pilares
  - [x] 7.1 Implementar Reliability Pillar Evaluator (13 preguntas, 37 BPs)
    - Crear clase `ReliabilityEvaluator` siguiendo misma estructura que SecurityEvaluator
    - Implementar evaluaciones de REL01 (Service Quotas) consultando Service Quotas API
    - Implementar evaluaciones de REL06 (Monitoring) consultando CloudWatch API
    - Implementar evaluaciones de REL09 (Backup) consultando AWS Backup API
    - Para BPs sin implementación, usar placeholder PENDING_REVIEW
    - _Requirements: 1.1, 2.2, 13.2_
  
  - [x] 7.2 Implementar Performance Efficiency Pillar Evaluator (5 preguntas, 32 BPs)
    - Crear clase `PerformanceEvaluator`
    - Implementar evaluaciones de PERF01 (Resource selection) consultando EC2 API
    - Implementar evaluaciones de PERF02 (Compute) consultando Lambda y EC2 APIs
    - Implementar evaluaciones de PERF03 (Storage) consultando S3, DynamoDB, RDS APIs
    - _Requirements: 1.1, 2.3, 13.3_
  
  - [x] 7.3 Implementar Cost Optimization Pillar Evaluator (10 preguntas, 28 BPs)
    - Crear clase `CostEvaluator`
    - Implementar evaluaciones de COST01 consultando Cost Explorer API
    - Implementar evaluaciones de COST02 consultando Budgets API
    - _Requirements: 1.1, 2.4, 13.4_
  
  - [x] 7.4 Implementar Operational Excellence Pillar Evaluator (16 preguntas, 42 BPs)
    - Crear clase `OperationalExcellenceEvaluator`
    - Implementar evaluaciones de OPS01 consultando CloudFormation API
    - Implementar evaluaciones de OPS02 consultando Systems Manager API
    - _Requirements: 1.1, 2.5, 13.5_
  
  - [x] 7.5 Implementar Sustainability Pillar Evaluator (6 preguntas, 18 BPs)
    - Crear clase `SustainabilityEvaluator`
    - Implementar evaluaciones de SUS01 consultando Compute Optimizer API
    - _Requirements: 1.1, 2.6, 13.6_
  
  - [ ]* 7.6 Escribir property test para consistencia estructural entre pilares
    - **Property 16: Data Structure Consistency Across Pillars**
    - **Validates: Requirements 1.6, 9.7**

- [x] 8. Checkpoint - Verificar evaluadores de todos los pilares
  - Ejecutar evaluación de cada pilar con credenciales de prueba
  - Verificar que todos los pilares retornan estructura consistente
  - Verificar que cache de DynamoDB funciona correctamente
  - Preguntar al usuario si hay dudas o ajustes necesarios

- [x] 9. Implementar sistema multiidioma (i18n.js)
  - [x] 9.1 Crear archivo i18n.js con diccionarios de traducción
    - Definir objeto `translations` con claves 'es' y 'en'
    - Incluir traducciones para nombres de pilares (Security→Seguridad, Reliability→Confiabilidad, etc.)
    - Incluir traducciones para estados (COMPLIANT→CUMPLE, NON_COMPLIANT→NO CUMPLE, PENDING_REVIEW→PENDIENTE)
    - Incluir traducciones para severidades (CRITICAL→CRÍTICO, HIGH→ALTO, MEDIUM→MEDIO, LOW→BAJO)
    - Incluir traducciones para términos de UI (dashboard, analyst, findings, evidence, remediation, risk)
    - _Requirements: 5.1, 5.2, 5.8, 10.1, 10.4, 10.8_
  
  - [x] 9.2 Implementar funciones de traducción
    - `translate(key, lang)`: Retorna traducción de una clave en el idioma especificado, fallback a inglés si no existe
    - `translateBP(bp, lang)`: Traduce campos de un BP (finding, risk, remediation, evidence)
    - `detectLanguage()`: Detecta idioma preferido de localStorage o navegador
    - `setLanguage(lang)`: Guarda idioma en localStorage
    - _Requirements: 5.5, 5.7, 10.2, 10.3, 10.7_
  
  - [ ]* 9.3 Escribir property tests para sistema de traducción
    - **Property 10: Translation Function Correctness**
    - **Property 11: Bilingual Content Availability**
    - **Property 12: Translation Consistency Across Pillars**
    - **Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5, 5.8, 10.3, 10.4, 10.6, 10.7**

- [x] 10. Implementar formulario de credenciales (index.html + app.js)
  - [x] 10.1 Crear formulario HTML con campos para credenciales AWS
    - Campos: Access Key ID, Secret Access Key, Session Token (opcional), Account ID, Regions (comma-separated)
    - Botón "Validar Credenciales"
    - Área de status para mostrar mensajes de éxito/error
    - _Requirements: 6.1_
  
  - [x] 10.2 Implementar lógica de validación y envío
    - Validar que todos los campos requeridos estén completos
    - Parsear regiones desde input comma-separated a array
    - Validar formato de regiones con regex
    - POST a `/credentials/validate` con credenciales
    - Si éxito: Guardar session_id en sessionStorage, redirigir a dashboard.html
    - Si error: Mostrar mensaje de error descriptivo
    - _Requirements: 6.1, 6.3, 7.3_
  
  - [ ]* 10.3 Escribir unit tests para formulario de credenciales
    - Test: Campos vacíos muestran error de validación
    - Test: Formato de región inválido muestra error
    - Test: Credenciales válidas guardan session_id y redirigen
    - _Requirements: 6.1, 6.3_

- [x] 11. Implementar dashboard (dashboard.html + dashboard.js)
  - [x] 11.1 Crear interfaz de dashboard con loading y grid de pilares
    - Mostrar loading spinner con texto de progreso durante evaluación
    - Grid de 6 cards (2x3) para mostrar pilares
    - Cada card muestra: nombre del pilar, score con color, total de BPs, total de hallazgos, badges de severidad
    - _Requirements: 1.7, 7.5_
  
  - [x] 11.2 Implementar lógica de evaluación secuencial de pilares
    - Verificar session_id en sessionStorage, redirigir a index.html si no existe
    - Evaluar los 6 pilares secuencialmente con POST a `/evaluate/{pillar}`
    - Actualizar texto de loading con progreso (1/6, 2/6, etc.)
    - Incluir header X-Session-ID en todas las requests
    - Manejar errores de evaluación mostrando mensaje descriptivo
    - _Requirements: 1.1, 1.4, 7.1, 7.8_
  
  - [x] 11.3 Implementar renderizado de cards de pilares
    - Crear card por cada pilar con datos de evaluación
    - Aplicar color a score según rango (verde ≥80, amarillo ≥60, rojo <60)
    - Mostrar badges de severidad solo si hay hallazgos de ese nivel
    - Click en card guarda datos del pilar en sessionStorage y navega a analyst.html
    - _Requirements: 1.7, 4.4, 4.5_
  
  - [ ]* 11.4 Escribir unit tests para dashboard
    - Test: Session ID inválido redirige a index.html
    - Test: Evaluación exitosa renderiza 6 cards de pilares
    - Test: Click en card guarda datos y navega a analyst.html
    - _Requirements: 1.7_

- [x] 12. Implementar vista de analista (analyst.html + analyst.js)
  - [x] 12.1 Crear layout con sidebar de preguntas y panel principal
    - Sidebar izquierdo: Lista de preguntas con question_id, título, y score
    - Panel principal: Resumen de pregunta seleccionada + tabla de hallazgos
    - Resumen muestra: score, número de BPs, estado general, timestamp
    - _Requirements: 8.1, 8.2, 8.3_
  
  - [x] 12.2 Implementar tabla de hallazgos con todas las columnas
    - Columnas: BP ID + Description, Status (badge), Severity (badge), Finding, Risk, Remediation, Evidence
    - Resaltar filas con severidad CRITICAL (fondo rojo claro) y HIGH (fondo naranja claro)
    - Mostrar badges de estado con colores (verde=CUMPLE, rojo=NO CUMPLE, amarillo=PENDIENTE)
    - Mostrar badges de severidad con colores (rojo=CRÍTICO, naranja=ALTO, amarillo=MEDIO, azul=BAJO)
    - _Requirements: 8.4, 8.5, 8.10_
  
  - [x] 12.3 Implementar navegación entre preguntas
    - Click en pregunta del sidebar actualiza panel principal
    - Resaltar pregunta activa en sidebar
    - Cargar datos del pilar desde sessionStorage
    - Si no hay datos, redirigir a dashboard.html
    - _Requirements: 8.2, 8.3, 8.9_
  
  - [ ]* 12.4 Escribir unit tests para vista de analista
    - Test: Sin datos de pilar en sessionStorage redirige a dashboard
    - Test: Click en pregunta actualiza panel principal
    - Test: Hallazgos CRITICAL y HIGH se resaltan visualmente
    - _Requirements: 8.2, 8.5_

- [x] 13. Integrar sistema multiidioma en frontend
  - [x] 13.1 Agregar selector de idioma en todas las vistas
    - Agregar dropdown o toggle para seleccionar español/inglés
    - Guardar selección en localStorage
    - Actualizar todas las traducciones visibles al cambiar idioma
    - _Requirements: 5.6, 5.7, 8.8_
  
  - [x] 13.2 Aplicar traducciones a dashboard y vista de analista
    - Traducir nombres de pilares según idioma seleccionado
    - Traducir estados y severidades en badges
    - Traducir términos de UI (dashboard, analyst, findings, etc.)
    - _Requirements: 5.1, 5.2, 5.5, 8.8_
  
  - [ ]* 13.3 Escribir unit tests para integración de i18n
    - Test: Cambio de idioma actualiza todas las traducciones
    - Test: Idioma se persiste en localStorage
    - Test: Idioma se restaura al recargar página
    - _Requirements: 5.6, 5.7, 12.1, 12.2_

- [x] 14. Checkpoint - Verificar integración frontend-backend
  - Ejecutar flujo completo: ingresar credenciales → evaluar pilares → ver dashboard → navegar a analista
  - Verificar que todas las traducciones funcionan correctamente
  - Verificar que cache de evaluaciones funciona (re-evaluar dentro de 5 min retorna cache)
  - Preguntar al usuario si hay dudas o ajustes necesarios

- [x] 15. Implementar manejo de errores en frontend
  - [x] 15.1 Manejar errores de sesión expirada
    - Detectar HTTP 401 en responses de evaluación
    - Limpiar sessionStorage
    - Redirigir a index.html con mensaje "Sesión expirada"
    - _Requirements: 7.4, 12.5_
  
  - [x] 15.2 Manejar errores de evaluación
    - Detectar HTTP 500 o errores de red
    - Mostrar mensaje de error descriptivo en dashboard
    - Permitir reintentar evaluación
    - _Requirements: 7.4_
  
  - [ ]* 15.3 Escribir unit tests para manejo de errores
    - Test: HTTP 401 limpia sessionStorage y redirige a index
    - Test: HTTP 500 muestra mensaje de error sin redirigir
    - Test: Error de red muestra mensaje de retry
    - _Requirements: 7.4, 12.5_

- [x] 16. Implementar property tests para propiedades adicionales
  - [ ]* 16.1 Escribir property test para BP ID format
    - **Property 8: BP ID Format Validation**
    - **Validates: Requirements 3.1**
  
  - [ ]* 16.2 Escribir property test para valores especiales de BPs compliant
    - **Property 9: Compliant BP Special Values**
    - **Validates: Requirements 3.6**
  
  - [ ]* 16.3 Escribir property test para determinación de estado de pregunta
    - **Property 17: Question Status Determination**
    - **Validates: Requirements 2.8**
  
  - [ ]* 16.4 Escribir property test para convención de naming JSON
    - **Property 19: JSON Field Naming Convention**
    - **Validates: Requirements 9.2**

- [x] 17. Desplegar aplicación a AWS
  - [x] 17.1 Compilar frontend y subir a S3
    - Ejecutar `npm run build` en directorio frontend-new
    - Subir contenido de dist/ a bucket S3 de frontend
    - Invalidar cache de CloudFront
    - _Requirements: 11.1, 11.2_
  
  - [x] 17.2 Desplegar Lambdas actualizadas
    - Empaquetar código de Lambdas con dependencias
    - Actualizar funciones Lambda en AWS
    - Verificar que todas las Lambdas se despliegan correctamente
    - _Requirements: 11.5, 11.7_
  
  - [x] 17.3 Verificar despliegue completo
    - Acceder a URL de CloudFront
    - Ejecutar flujo completo de evaluación
    - Verificar que todos los pilares se evalúan correctamente
    - _Requirements: 11.1, 11.5, 11.6_

- [x] 18. Checkpoint final - Verificar sistema completo
  - Ejecutar todos los property tests (mínimo 100 iteraciones cada uno)
  - Ejecutar todos los unit tests
  - Verificar cobertura de tests (objetivo: 80%+)
  - Ejecutar evaluación completa de los 6 pilares con credenciales reales
  - Verificar que todas las 20 propiedades de correctitud se cumplen
  - Preguntar al usuario si hay ajustes finales necesarios

## Notas

- Las tareas marcadas con `*` son opcionales y pueden omitirse para un MVP más rápido
- Cada tarea referencia los requerimientos específicos que implementa para trazabilidad
- Los checkpoints aseguran validación incremental y permiten detectar problemas temprano
- Los property tests validan propiedades universales con mínimo 100 iteraciones
- Los unit tests validan ejemplos específicos, casos borde y condiciones de error
- La implementación sigue el orden: infraestructura → backend → frontend → testing → despliegue

