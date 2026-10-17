# Documento de Diseño - AutoWAR: Plataforma de Evaluación AWS Well-Architected Framework

## Visión General

AutoWAR es una plataforma serverless de evaluación del AWS Well-Architected Framework que analiza infraestructuras AWS reales contra los 6 pilares fundamentales. El sistema conecta directamente con APIs de AWS para obtener evidencia técnica real, evalúa el cumplimiento de Best Practices, y genera hallazgos con remediaciones específicas.

La arquitectura sigue un patrón serverless con:
- Frontend: React + Vite servido desde S3 + CloudFront
- Backend: AWS Lambda + API Gateway
- Almacenamiento: DynamoDB para evaluaciones, Secrets Manager para credenciales
- Evaluación: Lambdas especializadas por pilar que consultan APIs de AWS

El sistema soporta evaluación multi-región, multiidioma (español/inglés), y proporciona vistas diferenciadas para analistas técnicos y ejecutivos.

## Arquitectura

### Componentes Principales

```
┌─────────────────────────────────────────────────────────────────┐
│                         CloudFront CDN                          │
│                    (Distribución Global)                        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      S3 Bucket (Frontend)                       │
│              React + Vite SPA (index, dashboard,                │
│                    analyst, client views)                       │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                        API Gateway REST                         │
│  /credentials/validate  |  /evaluate/{pillar}                  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                ┌────────────┴────────────┐
                ▼                         ▼
┌───────────────────────────┐  ┌──────────────────────────────────┐
│ Credential Validator      │  │  Pillar Evaluator Lambdas        │
│ Lambda                    │  │  - Security (11Q, 63BP)          │
│ - Valida con STS          │  │  - Reliability (13Q, 37BP)       │
│ - Crea session en Secrets │  │  - Performance (5Q, 32BP)        │
│ - Retorna session_id      │  │  - Cost (10Q, 28BP)              │
└───────────────────────────┘  │  - Operational (16Q, 42BP)       │
                               │  - Sustainability (6Q, 18BP)     │
                               └──────────┬───────────────────────┘
                                          │
                    ┌─────────────────────┼─────────────────────┐
                    ▼                     ▼                     ▼
         ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
         │ Secrets Manager  │  │   DynamoDB       │  │  AWS APIs        │
         │ (Credenciales)   │  │ (Evaluaciones)   │  │ (IAM, EC2, S3,   │
         │ TTL: 1 hora      │  │ Cache: 5 min     │  │  CloudTrail...)  │
         └──────────────────┘  └──────────────────┘  └──────────────────┘
```

### Flujo de Evaluación

1. **Autenticación**: Usuario ingresa credenciales AWS → Credential Validator valida con STS → Crea sesión en Secrets Manager → Retorna session_id
2. **Evaluación**: Frontend solicita evaluación de pilar → API Gateway enruta a Lambda evaluador → Lambda obtiene credenciales de Secrets Manager → Consulta APIs de AWS → Genera hallazgos → Guarda en DynamoDB → Retorna resultados
3. **Visualización**: Frontend recibe datos → Renderiza dashboard con scores → Usuario navega a vista de analista → Muestra preguntas y BPs con evidencia técnica

### Decisiones de Arquitectura

**Serverless sobre EC2/ECS**: Evaluaciones son esporádicas y de corta duración (2-5 min). Lambda proporciona escalabilidad automática y costo por uso.

**DynamoDB sobre RDS**: Datos de evaluación son documentos JSON sin relaciones complejas. DynamoDB ofrece mejor rendimiento para lecturas/escrituras de documentos completos.

**Secrets Manager sobre Parameter Store**: Credenciales AWS requieren rotación automática y cifrado con KMS. Secrets Manager proporciona TTL automático y mejor auditoría.

**Multi-región en evaluación**: Recursos AWS pueden estar en múltiples regiones. Sistema evalúa todas las regiones especificadas y agrega resultados.

**Cache de 5 minutos**: Evaluaciones son costosas (múltiples llamadas a APIs AWS). Cache reduce latencia y costos para evaluaciones repetidas.

## Componentes e Interfaces

### 1. Credential Validator Lambda

**Responsabilidad**: Validar credenciales AWS y crear sesiones seguras.

**Interfaz de Entrada**:
```python
{
    "access_key_id": str,
    "secret_access_key": str,
    "session_token": Optional[str],
    "account_id": str,
    "regions": List[str]  # ["us-east-1", "eu-west-1"]
}
```

**Interfaz de Salida**:
```python
{
    "session_id": str,  # UUID
    "expires_at": str,  # ISO 8601 timestamp
    "account_id": str,
    "regions": List[str]
}
```

**Lógica**:
1. Validar credenciales con `sts:GetCallerIdentity`
2. Generar UUID para session_id
3. Cifrar credenciales con KMS
4. Almacenar en Secrets Manager con nombre `autowar/sessions/{session_id}`
5. Configurar TTL de 1 hora
6. Retornar session_id y metadata

**Manejo de Errores**:
- Credenciales inválidas → HTTP 401 con mensaje descriptivo
- Error de red/timeout → HTTP 500 con retry sugerido
- Permisos insuficientes → HTTP 403 con permisos faltantes

### 2. Pillar Evaluator Lambdas

**Responsabilidad**: Evaluar Best Practices de un pilar consultando APIs de AWS.

**Interfaz de Entrada** (Headers):
```
X-Session-ID: {session_id}
```

**Interfaz de Salida**:
```python
{
    "pillar_id": str,  # "security", "reliability", etc.
    "region": str,  # "us-east-1" (single region)
    "regions": List[str],  # ["us-east-1", "eu-west-1"] (multi-region)
    "multi_region": bool,
    "pillar_name": {"es": str, "en": str},
    "description": {"es": str, "en": str},
    "overall_score": float,  # 0-100
    "total_findings": int,
    "total_best_practices": int,
    "timestamp": str,  # ISO 8601
    "questions": [
        {
            "question_id": str,  # "SEC01", "REL02"
            "title": {"es": str, "en": str},
            "description": {"es": str, "en": str},
            "score": float,  # 0-100
            "bps_evaluated": int,
            "status": str,  # "COMPLIANT", "NON_COMPLIANT", "PENDING_REVIEW"
            "findings": [
                {
                    "bp": str,  # "SEC01-BP01"
                    "description": str,  # BP description
                    "status": str,  # "COMPLIANT", "NON_COMPLIANT", "PENDING_REVIEW"
                    "severity": str,  # "CRITICAL", "HIGH", "MEDIUM", "LOW"
                    "finding": str,  # Descripción del hallazgo
                    "evidence": str,  # Evidencia técnica (ARNs, IDs, configs)
                    "remediation": str,  # Acción recomendada
                    "risk": str  # Descripción del riesgo
                }
            ]
        }
    ],
    "compliance_distribution": {
        "compliant": int,
        "non_compliant": int,
        "pending_review": int
    },
    "severity_distribution": {
        "critical": int,
        "high": int,
        "medium": int,
        "low": int
    }
}
```

**Lógica de Evaluación**:
1. Obtener session_id del header
2. Recuperar credenciales de Secrets Manager
3. Verificar cache en DynamoDB (últimos 5 minutos)
4. Si no hay cache, ejecutar evaluación:
   - Para cada región en credenciales:
     - Crear boto3.Session con credenciales del cliente
     - Para cada pregunta del pilar:
       - Para cada BP de la pregunta:
         - Consultar API de AWS correspondiente
         - Analizar respuesta y determinar estado
         - Generar hallazgo con evidencia
   - Agregar resultados multi-región si aplica
5. Calcular scores (BP → Pregunta → Pilar)
6. Guardar en DynamoDB
7. Retornar resultados

**Mapeo BP → AWS API**:
```python
BP_TO_AWS_SERVICE = {
    # Security
    "SEC01-BP01": ["organizations:ListAccounts"],
    "SEC02-BP01": ["iam:GetAccountPasswordPolicy"],
    "SEC04-BP01": ["cloudtrail:DescribeTrails", "cloudtrail:GetTrailStatus"],
    "SEC05-BP01": ["ec2:DescribeVpcs", "ec2:DescribeSecurityGroups"],
    "SEC08-BP01": ["kms:ListKeys", "kms:DescribeKey"],
    
    # Reliability
    "REL01-BP01": ["servicequotas:ListServiceQuotas"],
    "REL06-BP01": ["cloudwatch:DescribeAlarms"],
    "REL09-BP01": ["backup:ListBackupPlans"],
    
    # Performance
    "PERF01-BP01": ["ec2:DescribeInstances"],
    "PERF02-BP01": ["lambda:ListFunctions"],
    "PERF03-BP01": ["s3:ListBuckets", "dynamodb:ListTables", "rds:DescribeDBInstances"],
    
    # Cost
    "COST01-BP01": ["ce:GetCostAndUsage"],
    "COST02-BP01": ["budgets:DescribeBudgets"],
    
    # Operational Excellence
    "OPS01-BP01": ["cloudformation:ListStacks"],
    "OPS02-BP01": ["ssm:DescribeInstanceInformation"],
    
    # Sustainability
    "SUS01-BP01": ["compute-optimizer:GetRecommendationSummaries"]
}
```

### 3. Frontend Components

#### 3.1 Credential Form (index.html + app.js)

**Responsabilidad**: Capturar y validar credenciales AWS.

**Campos**:
- Access Key ID (requerido)
- Secret Access Key (requerido)
- Session Token (opcional)
- Account ID (requerido)
- Regions (requerido, comma-separated)

**Validación**:
- Todos los campos requeridos no vacíos
- Al menos una región especificada
- Formato de región válido (regex: `^[a-z]{2}-[a-z]+-\d$`)

**Flujo**:
1. Usuario ingresa credenciales
2. Click en "Validar Credenciales"
3. POST a `/credentials/validate`
4. Si éxito: Guardar session_id en sessionStorage → Redirigir a dashboard
5. Si error: Mostrar mensaje de error

#### 3.2 Dashboard (dashboard.html + dashboard.js)

**Responsabilidad**: Mostrar vista ejecutiva de los 6 pilares.

**Datos Mostrados**:
- Card por cada pilar con:
  - Nombre del pilar (español)
  - Score general (0-100) con color (verde ≥80, amarillo ≥60, rojo <60)
  - Total de Best Practices evaluadas
  - Total de hallazgos
  - Distribución de severidad (badges para CRITICAL, HIGH, MEDIUM)

**Flujo**:
1. Verificar session_id en sessionStorage
2. Mostrar loading con progreso
3. Evaluar los 6 pilares secuencialmente:
   - POST a `/evaluate/security`
   - POST a `/evaluate/reliability`
   - POST a `/evaluate/performance`
   - POST a `/evaluate/cost`
   - POST a `/evaluate/operational_excellence`
   - POST a `/evaluate/sustainability`
4. Renderizar cards de pilares
5. Click en card → Guardar datos del pilar en sessionStorage → Navegar a analyst.html

#### 3.3 Analyst View (analyst.html + analyst.js)

**Responsabilidad**: Mostrar vista técnica detallada de un pilar.

**Layout**:
- Sidebar izquierdo: Lista de preguntas con score
- Panel principal: Detalles de pregunta seleccionada
  - Resumen: Score, BPs evaluadas, estado
  - Tabla de hallazgos con columnas:
    - BP ID + Description
    - Status (badge con color)
    - Severity (badge con color)
    - Finding
    - Risk
    - Remediation
    - Evidence (datos técnicos de AWS)

**Interacción**:
- Click en pregunta → Actualizar panel principal
- Resaltado visual para severidad CRITICAL (fondo rojo claro) y HIGH (fondo naranja claro)
- Selector de idioma (futuro) → Actualizar traducciones dinámicamente

### 4. Sistema Multiidioma (i18n.js)

**Responsabilidad**: Proporcionar traducciones para español e inglés.

**Estructura**:
```javascript
const translations = {
    es: {
        // Pilares
        "security": "Seguridad",
        "reliability": "Confiabilidad",
        "performance": "Eficiencia del Rendimiento",
        "cost": "Optimización de Costos",
        "operational": "Excelencia Operacional",
        "sustainability": "Sostenibilidad",
        
        // Estados
        "COMPLIANT": "CUMPLE",
        "NON_COMPLIANT": "NO CUMPLE",
        "PENDING_REVIEW": "PENDIENTE",
        
        // Severidades
        "CRITICAL": "CRÍTICO",
        "HIGH": "ALTO",
        "MEDIUM": "MEDIO",
        "LOW": "BAJO",
        
        // UI
        "dashboard": "Panel de Control",
        "analyst": "Vista de Analista",
        "findings": "Hallazgos",
        "evidence": "Evidencia",
        "remediation": "Remediación",
        "risk": "Riesgo"
    },
    en: {
        // Pilares
        "security": "Security",
        "reliability": "Reliability",
        "performance": "Performance Efficiency",
        "cost": "Cost Optimization",
        "operational": "Operational Excellence",
        "sustainability": "Sustainability",
        
        // Estados
        "COMPLIANT": "COMPLIANT",
        "NON_COMPLIANT": "NON_COMPLIANT",
        "PENDING_REVIEW": "PENDING_REVIEW",
        
        // Severidades
        "CRITICAL": "CRITICAL",
        "HIGH": "HIGH",
        "MEDIUM": "MEDIUM",
        "LOW": "LOW",
        
        // UI
        "dashboard": "Dashboard",
        "analyst": "Analyst View",
        "findings": "Findings",
        "evidence": "Evidence",
        "remediation": "Remediation",
        "risk": "Risk"
    }
};

function translate(key, lang = 'es') {
    return translations[lang][key] || key;
}

function translateBP(bp, lang = 'es') {
    // Traduce campos de un BP: finding, risk, remediation, evidence
    return {
        ...bp,
        finding: translate(bp.finding, lang),
        risk: translate(bp.risk, lang),
        remediation: translate(bp.remediation, lang),
        evidence: translate(bp.evidence, lang)
    };
}
```

**Persistencia**:
- Idioma seleccionado se guarda en `localStorage.getItem('autowar_language')`
- Al cargar página, se detecta idioma de localStorage o navegador
- Cambio de idioma actualiza todas las traducciones sin recargar página

## Modelos de Datos

### 1. Credenciales AWS (Secrets Manager)

**Nombre del Secret**: `autowar/sessions/{session_id}`

**Estructura**:
```json
{
    "access_key_id": "AKIAIOSFODNN7EXAMPLE",
    "secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
    "session_token": "FwoGZXIvYXdzEBYaD...",
    "account_id": "123456789012",
    "regions": ["us-east-1", "eu-west-1"],
    "created_at": "2024-01-15T10:30:00Z"
}
```

**TTL**: 1 hora (configurado en Secrets Manager)

**Cifrado**: KMS con clave gestionada por AutoWAR

### 2. Evaluación (DynamoDB)

**Tabla**: `autowar-evaluations`

**Partition Key**: `session_id` (String)
**Sort Key**: `evaluation_id` (String) - Formato: `{pillar_id}#{timestamp}`

**Atributos**:
```json
{
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "evaluation_id": "security#1705315800",
    "pillar_id": "security",
    "timestamp": "2024-01-15T10:30:00Z",
    "data": {
        // Estructura completa de la respuesta del evaluador
        "pillar_id": "security",
        "pillar_name": {"es": "Seguridad", "en": "Security"},
        "overall_score": 75.5,
        "questions": [...]
    }
}
```

**TTL**: No configurado (mantener histórico de evaluaciones)

**Índices**:
- GSI: `pillar_id-timestamp-index` para consultas por pilar

### 3. Hallazgo (Finding)

**Estructura** (parte de la respuesta de evaluación):
```python
@dataclass
class Finding:
    bp: str  # "SEC01-BP01"
    description: str  # "Separate workloads using accounts"
    status: Literal["COMPLIANT", "NON_COMPLIANT", "PENDING_REVIEW"]
    severity: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    finding: str  # "Multiple AWS accounts detected for workload separation"
    evidence: str  # "Found 3 accounts in organization: 123456789012, 234567890123, 345678901234"
    remediation: str  # "Current state compliant" o acción específica
    risk: str  # "No risk" o descripción del riesgo
```

**Validación**:
- Todos los campos son obligatorios (no pueden ser None o vacíos)
- `status` debe ser uno de los 3 valores permitidos
- `severity` debe ser uno de los 4 valores permitidos
- `evidence` debe contener datos técnicos reales cuando estén disponibles

### 4. Pregunta (Question)

**Estructura**:
```python
@dataclass
class Question:
    question_id: str  # "SEC01", "REL02"
    title: Dict[str, str]  # {"es": "...", "en": "..."}
    description: Dict[str, str]  # {"es": "...", "en": "..."}
    score: float  # 0-100
    bps_evaluated: int
    status: Literal["COMPLIANT", "NON_COMPLIANT", "PENDING_REVIEW"]
    findings: List[Finding]
```

**Cálculo de Score**:
```python
def calculate_question_score(findings: List[Finding]) -> float:
    score_map = {
        "COMPLIANT": 100.0,
        "NON_COMPLIANT": 0.0,
        "PENDING_REVIEW": 50.0
    }
    total_score = sum(score_map[f.status] for f in findings)
    return round(total_score / len(findings), 2)
```

**Determinación de Estado**:
```python
def determine_question_status(findings: List[Finding]) -> str:
    statuses = [f.status for f in findings]
    if all(s == "COMPLIANT" for s in statuses):
        return "COMPLIANT"
    elif any(s == "NON_COMPLIANT" for s in statuses):
        return "NON_COMPLIANT"
    else:
        return "PENDING_REVIEW"
```

### 5. Pilar (Pillar)

**Estructura**:
```python
@dataclass
class Pillar:
    pillar_id: str  # "security", "reliability", etc.
    region: str  # "us-east-1" (single region)
    regions: Optional[List[str]]  # ["us-east-1", "eu-west-1"] (multi-region)
    multi_region: bool
    pillar_name: Dict[str, str]  # {"es": "Seguridad", "en": "Security"}
    description: Dict[str, str]
    overall_score: float  # 0-100
    total_findings: int
    total_best_practices: int
    timestamp: str  # ISO 8601
    questions: List[Question]
    compliance_distribution: Dict[str, int]  # {"compliant": 10, "non_compliant": 5, "pending_review": 3}
    severity_distribution: Dict[str, int]  # {"critical": 2, "high": 5, "medium": 8, "low": 3}
```

**Cálculo de Score del Pilar**:
```python
def calculate_pillar_score(questions: List[Question]) -> float:
    total_weighted_score = sum(q.score * q.bps_evaluated for q in questions)
    total_bps = sum(q.bps_evaluated for q in questions)
    return round(total_weighted_score / total_bps, 2) if total_bps > 0 else 0.0
```

## Manejo de Errores

### 1. Errores de Credenciales

**Escenario**: Credenciales AWS inválidas o expiradas

**Detección**: `sts:GetCallerIdentity` falla con `InvalidClientTokenId` o `ExpiredToken`

**Respuesta**:
```json
{
    "statusCode": 401,
    "body": {
        "error": "Invalid AWS credentials",
        "message": "The security token included in the request is invalid",
        "action": "Please verify your Access Key ID and Secret Access Key"
    }
}
```

**Manejo en Frontend**:
- Mostrar mensaje de error en formulario de credenciales
- No redirigir a dashboard
- Permitir reintentar con nuevas credenciales

### 2. Errores de Permisos

**Escenario**: Credenciales válidas pero sin permisos para consultar API específica

**Detección**: Llamada a API de AWS falla con `AccessDenied` o `UnauthorizedOperation`

**Respuesta**: Marcar BP como `PENDING_REVIEW` con evidencia del error

**Ejemplo**:
```python
{
    "bp": "SEC02-BP01",
    "status": "PENDING_REVIEW",
    "severity": "MEDIUM",
    "finding": "Unable to evaluate due to insufficient permissions",
    "evidence": "Access Denied: AccessDenied - User: arn:aws:iam::123456789012:user/evaluator is not authorized to perform: iam:GetAccountPasswordPolicy",
    "remediation": "Grant iam:GetAccountPasswordPolicy permission to evaluation role",
    "risk": "Cannot determine compliance status"
}
```

**Agregación**: Al final de la evaluación, generar resumen de permisos faltantes

### 3. Errores de Red/Timeout

**Escenario**: Timeout o error de red al consultar API de AWS

**Detección**: `botocore.exceptions.EndpointConnectionError` o timeout

**Respuesta**: Reintentar hasta 3 veces con backoff exponencial (1s, 2s, 4s)

**Si falla después de 3 intentos**: Marcar BP como `PENDING_REVIEW`

```python
{
    "bp": "SEC04-BP01",
    "status": "PENDING_REVIEW",
    "severity": "MEDIUM",
    "finding": "Unable to evaluate due to network error",
    "evidence": "Connection timeout after 3 retries",
    "remediation": "Retry evaluation or check network connectivity",
    "risk": "Cannot determine compliance status"
}
```

### 4. Errores de Evaluación Parcial

**Escenario**: Algunas BPs fallan pero otras se evalúan correctamente

**Comportamiento**: Continuar evaluación de otras BPs

**Resultado**: Evaluación parcial con algunas BPs en `PENDING_REVIEW`

**Ejemplo**: Si 5 de 8 BPs se evalúan correctamente, retornar evaluación con 5 BPs evaluadas y 3 en `PENDING_REVIEW`

### 5. Errores de Sesión

**Escenario**: Session ID inválido o expirado

**Detección**: Secret no existe en Secrets Manager o TTL expirado

**Respuesta**:
```json
{
    "statusCode": 401,
    "body": {
        "error": "Session expired or invalid",
        "message": "Please re-authenticate with AWS credentials",
        "action": "Redirect to login page"
    }
}
```

**Manejo en Frontend**:
- Limpiar sessionStorage
- Redirigir a index.html
- Mostrar mensaje "Sesión expirada, por favor ingrese sus credenciales nuevamente"

## Estrategia de Testing

### Testing Dual: Unit Tests + Property-Based Tests

El sistema requiere dos tipos de testing complementarios:

**Unit Tests**: Validan ejemplos específicos, casos borde y condiciones de error
- Ejemplos concretos de evaluaciones de BPs
- Casos borde (listas vacías, credenciales inválidas, timeouts)
- Integración entre componentes (Frontend ↔ Backend, Backend ↔ AWS)

**Property-Based Tests**: Validan propiedades universales que deben cumplirse para todos los inputs
- Propiedades de correctitud del sistema (ver sección siguiente)
- Configuración: Mínimo 100 iteraciones por test
- Etiquetado: Cada test debe referenciar su propiedad del diseño

### Herramientas de Testing

**Backend (Python)**:
- Unit tests: `pytest`
- Property-based tests: `hypothesis`
- Mocking de AWS: `moto`

**Frontend (JavaScript)**:
- Unit tests: `vitest`
- Property-based tests: `fast-check`
- Mocking de API: `msw` (Mock Service Worker)

### Configuración de Property-Based Tests

Cada test de propiedad debe:
1. Ejecutar mínimo 100 iteraciones
2. Incluir comentario con formato: `# Feature: security-pillar-reorganization, Property {N}: {descripción}`
3. Referenciar la propiedad específica del documento de diseño

Ejemplo:
```python
# Feature: security-pillar-reorganization, Property 1: Score calculation consistency
@given(st.lists(st.sampled_from(["COMPLIANT", "NON_COMPLIANT", "PENDING_REVIEW"]), min_size=1))
@settings(max_examples=100)
def test_question_score_calculation(statuses):
    findings = [{"status": s} for s in statuses]
    score = calculate_question_score(findings)
    assert 0 <= score <= 100
```


## Propiedades de Correctitud

Una propiedad es una característica o comportamiento que debe cumplirse en todas las ejecuciones válidas del sistema - esencialmente, una declaración formal sobre lo que el sistema debe hacer. Las propiedades sirven como puente entre las especificaciones legibles por humanos y las garantías de correctitud verificables por máquinas.

### Property 1: Question Score Calculation Consistency

*For any* question with a non-empty list of findings, the calculated score should be between 0 and 100 (inclusive), and should equal the average of individual finding scores where COMPLIANT=100, NON_COMPLIANT=0, and PENDING_REVIEW=50.

**Validates: Requirements 2.8, 4.2, 4.3**

### Property 2: Pillar Score Calculation Consistency

*For any* pillar with a non-empty list of questions, the calculated pillar score should be between 0 and 100 (inclusive), and should equal the weighted average of question scores where each question is weighted by its number of BPs.

**Validates: Requirements 4.1, 4.6**

### Property 3: Pillar Data Structure Completeness

*For any* pillar evaluation result, it must contain all required fields: pillar_id (string), pillar_name (dict with 'es' and 'en' keys), description (dict with 'es' and 'en' keys), overall_score (float 0-100), total_findings (int ≥0), total_best_practices (int ≥0), timestamp (ISO 8601 string), questions (non-empty list), compliance_distribution (dict), and severity_distribution (dict).

**Validates: Requirements 1.2, 7.1**

### Property 4: Question Data Structure Completeness

*For any* question in any pillar evaluation, it must contain all required fields: question_id (string matching pattern PILAR##), title (dict with 'es' and 'en' keys), description (dict with 'es' and 'en' keys), score (float 0-100), bps_evaluated (int ≥0), status (valid enum), and findings (list).

**Validates: Requirements 2.7, 7.2, 9.6**

### Property 5: Finding Data Structure Completeness

*For any* finding in any question, it must contain all required non-empty fields: bp (string), description (string), status (valid enum), severity (valid enum), finding (non-empty string), evidence (non-empty string), remediation (non-empty string), and risk (non-empty string).

**Validates: Requirements 3.4, 9.1, 9.5**

### Property 6: Status Enumeration Validation

*For any* finding or question status value, it must be exactly one of: "COMPLIANT", "NON_COMPLIANT", or "PENDING_REVIEW" (case-sensitive).

**Validates: Requirements 3.3, 9.3**

### Property 7: Severity Enumeration Validation

*For any* finding severity value, it must be exactly one of: "CRITICAL", "HIGH", "MEDIUM", or "LOW" (case-sensitive).

**Validates: Requirements 3.5, 9.4**

### Property 8: BP ID Format Validation

*For any* Best Practice identifier, it must match the format PILAR##-BP## where PILAR is 2-6 uppercase letters, and ## are two-digit numbers (e.g., SEC01-BP01, REL02-BP03, PERF01-BP01).

**Validates: Requirements 3.1**

### Property 9: Compliant BP Special Values

*For any* finding with status "COMPLIANT", the risk field must equal "No risk" and the remediation field must equal "Current state compliant".

**Validates: Requirements 3.6**

### Property 10: Translation Function Correctness

*For any* translatable content (pillar name, question title, status, severity) and language code ('es' or 'en'), the translation function must return a non-empty string in the requested language, or fall back to English if translation is missing.

**Validates: Requirements 5.1, 5.2, 5.5, 10.3, 10.7**

### Property 11: Bilingual Content Availability

*For any* pillar or question, both Spanish ('es') and English ('en') versions of name/title and description must be present and non-empty.

**Validates: Requirements 5.3, 5.4, 10.4**

### Property 12: Translation Consistency Across Pillars

*For any* status or severity term appearing in multiple pillars, the translation to Spanish must be identical across all occurrences (e.g., "COMPLIANT" always translates to "CUMPLE", "CRITICAL" always translates to "CRÍTICO").

**Validates: Requirements 5.8, 10.6**

### Property 13: Multi-Region Aggregation Correctness

*For any* set of pillar evaluation results from multiple regions, the aggregated result must: (1) include all findings from all regions with region tags, (2) calculate overall_score as the weighted average across all regions, (3) set multi_region flag to true, and (4) include the list of evaluated regions.

**Validates: Requirements 6.7**

### Property 14: Compliance Distribution Accuracy

*For any* pillar evaluation result, the compliance_distribution counts (compliant, non_compliant, pending_review) must sum to exactly total_findings, and each count must accurately reflect the number of findings with that status.

**Validates: Requirements 4.4, 4.5**

### Property 15: Severity Distribution Accuracy

*For any* pillar evaluation result, the severity_distribution counts (critical, high, medium, low) must sum to exactly total_findings, and each count must accurately reflect the number of findings with that severity level.

**Validates: Requirements 4.4, 4.5**

### Property 16: Data Structure Consistency Across Pillars

*For any* two pillar evaluation results (regardless of which pillars), they must have identical top-level field names and types, ensuring structural consistency across all 6 pillars.

**Validates: Requirements 1.6, 9.7**

### Property 17: Question Status Determination

*For any* question with findings, if all findings have status "COMPLIANT" then question status must be "COMPLIANT"; if any finding has status "NON_COMPLIANT" then question status must be "NON_COMPLIANT"; otherwise question status must be "PENDING_REVIEW".

**Validates: Requirements 2.8**

### Property 18: Credential Input Validation

*For any* credential object, it must contain non-empty strings for access_key_id, secret_access_key, and account_id, and a non-empty list of valid region strings (matching pattern ^[a-z]{2}-[a-z]+-\d$).

**Validates: Requirements 6.1**

### Property 19: JSON Field Naming Convention

*For any* serialized finding, question, or pillar object, all field names must be in snake_case format (lowercase with underscores, no camelCase or PascalCase).

**Validates: Requirements 9.2**

### Property 20: Score Range Invariant

*For any* calculated score (question score, pillar score, or aggregated score), the value must be a float between 0.0 and 100.0 (inclusive), rounded to 2 decimal places.

**Validates: Requirements 4.1, 4.2, 4.3, 4.4**

## Estrategia de Testing (Continuación)

### Implementación de Property-Based Tests

Cada propiedad de correctitud debe implementarse como un property-based test con la siguiente estructura:

**Python (Backend) - Ejemplo con Hypothesis**:
```python
from hypothesis import given, strategies as st, settings
import pytest

# Feature: security-pillar-reorganization, Property 1: Question Score Calculation Consistency
@given(st.lists(
    st.sampled_from(["COMPLIANT", "NON_COMPLIANT", "PENDING_REVIEW"]),
    min_size=1,
    max_size=20
))
@settings(max_examples=100)
def test_question_score_calculation_consistency(statuses):
    """
    Property 1: For any question with findings, score should be 0-100
    and equal the average of finding scores (COMPLIANT=100, NON_COMPLIANT=0, PENDING_REVIEW=50)
    """
    findings = [{"status": s} for s in statuses]
    score = calculate_question_score(findings)
    
    # Score must be in valid range
    assert 0.0 <= score <= 100.0
    
    # Score must match formula
    score_map = {"COMPLIANT": 100.0, "NON_COMPLIANT": 0.0, "PENDING_REVIEW": 50.0}
    expected_score = round(sum(score_map[s] for s in statuses) / len(statuses), 2)
    assert score == expected_score
```

**JavaScript (Frontend) - Ejemplo con fast-check**:
```javascript
import fc from 'fast-check';
import { describe, it, expect } from 'vitest';

// Feature: security-pillar-reorganization, Property 10: Translation Function Correctness
describe('Translation Function Correctness', () => {
  it('should return non-empty string for any translatable content and language', () => {
    fc.assert(
      fc.property(
        fc.constantFrom('security', 'reliability', 'performance', 'cost', 'operational', 'sustainability'),
        fc.constantFrom('es', 'en'),
        (pillarId, lang) => {
          const translated = translate(pillarId, lang);
          expect(typeof translated).toBe('string');
          expect(translated.length).toBeGreaterThan(0);
        }
      ),
      { numRuns: 100 }
    );
  });
});
```

### Unit Tests Complementarios

Los unit tests deben enfocarse en:

**Ejemplos Específicos**:
- Security pillar tiene exactamente 11 preguntas (SEC01-SEC11)
- Security pillar tiene exactamente 63 Best Practices totales
- Evaluación independiente de un solo pilar funciona sin evaluar otros
- Dashboard muestra los 6 pilares simultáneamente

**Casos Borde**:
- Credenciales inválidas retornan HTTP 401
- Error de permisos marca BP como PENDING_REVIEW
- Timeout después de 3 reintentos marca BP como PENDING_REVIEW
- Evaluación parcial continúa cuando algunas BPs fallan

**Integración**:
- Frontend → Backend: POST a /evaluate/security retorna estructura válida
- Backend → AWS: Llamada a IAM API con credenciales válidas retorna datos
- Backend → DynamoDB: Evaluación se guarda correctamente con TTL
- Backend → Secrets Manager: Credenciales se almacenan y recuperan correctamente

### Cobertura de Testing

**Objetivo de Cobertura**:
- Property-based tests: 100% de las 20 propiedades implementadas
- Unit tests: 80%+ de cobertura de líneas de código
- Integration tests: Todos los flujos críticos (autenticación, evaluación, visualización)

**Priorización**:
1. **Alta prioridad**: Propiedades 1-10 (cálculos de score, estructura de datos, validaciones)
2. **Media prioridad**: Propiedades 11-16 (traducciones, agregaciones, distribuciones)
3. **Baja prioridad**: Propiedades 17-20 (convenciones de naming, invariantes adicionales)

