# Design Document: AutoWAR Reporting System

## Overview

El sistema de reportes para AutoWAR extiende la funcionalidad existente para permitir la gestión de evaluaciones históricas y la generación de dos tipos de reportes: ejecutivo (orientado a negocio) y técnico (detalle de Best Practices). El sistema se integra con la arquitectura serverless existente de AutoWAR, agregando nuevos componentes Lambda para generación de reportes, almacenamiento en DynamoDB para evaluaciones históricas, y una nueva interfaz frontend para gestión de reportes.

### Key Design Decisions

1. **Separation of Report Generation**: Dos Lambda functions separadas (ejecutivo y técnico) para permitir optimización independiente y escalabilidad
2. **DynamoDB for Historical Data**: Uso de DynamoDB con composite key (accountId + timestamp) para queries eficientes de evaluaciones históricas
3. **S3 with Signed URLs**: Almacenamiento de reportes en S3 con URLs firmadas temporales para seguridad y control de acceso
4. **Python Libraries**: python-docx para reportes DOCX y openpyxl para reportes XLSX por su madurez y facilidad de uso
5. **Asynchronous Generation**: Generación de reportes como operación asíncrona con indicador de progreso en frontend

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend Layer                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  index.html  │  │dashboard.html│  │ reports.html │ (NEW)   │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         API Gateway                             │
│  GET  /reports/list                                             │
│  POST /reports/generate                                         │
│  (existing endpoints...)                                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                ┌─────────────┴─────────────┐
                ▼                           ▼
┌───────────────────────────┐   ┌───────────────────────────┐
│  Lambda: Report Manager   │   │ Lambda: Credential        │
│  - List evaluations       │   │ Validator (MODIFIED)      │
│  - Trigger generation     │   │ - Validate credentials    │
│  - Return signed URLs     │   │ - Choose new/historical   │
└───────────────────────────┘   └───────────────────────────┘
                │                           │
        ┌───────┴───────┐                  │
        ▼               ▼                  ▼
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│ Lambda:         │   │ Lambda:         │   │   DynamoDB:     │
│ Executive       │   │ Technical       │   │   Evaluations   │
│ Report Gen      │   │ Report Gen      │   │   (NEW)         │
└─────────────────┘   └─────────────────┘   └─────────────────┘
        │                     │                       │
        └─────────┬───────────┘                       │
                  ▼                                   │
          ┌───────────────┐                          │
          │   S3 Bucket   │◄─────────────────────────┘
          │   Reports     │
          │   (NEW)       │
          └───────────────┘
```

### Data Flow

**Historical Evaluation Storage Flow:**
1. User validates credentials → Credential Validator Lambda
2. User chooses "new evaluation" → Complete WAR evaluation executes
3. Evaluation results → Stored in DynamoDB with timestamp
4. User proceeds to dashboard with evaluation data

**Report Generation Flow:**
1. User accesses reports.html → Frontend loads evaluation list from DynamoDB
2. User selects evaluation, pilares, report type → POST /reports/generate
3. Report Manager Lambda validates request → Invokes appropriate report generator Lambda
4. Report Generator Lambda retrieves evaluation data from DynamoDB
5. Report Generator creates document (DOCX/XLSX) → Uploads to S3
6. Report Manager returns Signed URL → Frontend triggers automatic download

## Components and Interfaces

### 1. Modified Credential Validator Lambda

**Purpose**: Extend existing credential validator to offer choice between new evaluation or loading historical data.

**Interface:**
```python
def lambda_handler(event, context):
    """
    Input:
        {
            "credentials": {
                "accessKeyId": str,
                "secretAccessKey": str,
                "sessionToken": str (optional)
            },
            "action": "new_evaluation" | "load_recent"
        }
    
    Output:
        {
            "statusCode": 200,
            "body": {
                "accountId": str,
                "evaluationData": dict (if load_recent),
                "timestamp": str (ISO 8601)
            }
        }
    """
```

**Behavior:**
- Validates AWS credentials using boto3 STS
- If action = "new_evaluation": proceeds with normal WAR evaluation flow
- If action = "load_recent": queries DynamoDB for most recent evaluation
- Stores new evaluation results in DynamoDB after completion

### 2. DynamoDB Evaluations Table

**Table Name**: `AutoWAR-Evaluations`

**Schema:**
```python
{
    "accountId": str,          # Partition Key
    "timestamp": str,          # Sort Key (ISO 8601 format)
    "pillarScores": {
        "security": int,
        "reliability": int,
        "performance": int,
        "cost": int,
        "operationalExcellence": int,
        "sustainability": int
    },
    "bestPractices": [
        {
            "pilar": str,
            "bpId": str,
            "description": str,
            "status": str,
            "severity": str,
            "finding": str,
            "evidence": str,
            "remediation": str,
            "risk": str
        }
    ],
    "metadata": {
        "region": str,
        "evaluationDuration": int,
        "totalBestPractices": int
    }
}
```

**Indexes:**
- Primary: accountId (HASH) + timestamp (RANGE)
- GSI (optional): timestamp (HASH) for cross-account queries

**Configuration:**
- Billing mode: PAY_PER_REQUEST
- Point-in-time recovery: ENABLED
- Encryption: AWS managed key

### 3. Report Manager Lambda

**Purpose**: Orchestrate report generation requests and manage evaluation queries.

**Endpoints:**

**GET /reports/list**
```python
def list_evaluations(event, context):
    """
    Query parameters:
        accountId: str (required)
        startDate: str (optional, ISO 8601)
        endDate: str (optional, ISO 8601)
    
    Response:
        {
            "statusCode": 200,
            "body": {
                "evaluations": [
                    {
                        "accountId": str,
                        "timestamp": str,
                        "pillarScores": dict,
                        "totalBestPractices": int
                    }
                ]
            }
        }
    """
```

**POST /reports/generate**
```python
def generate_report(event, context):
    """
    Input:
        {
            "accountId": str,
            "evaluationTimestamp": str,
            "pilares": ["security", "reliability", ...],
            "reportType": "executive" | "technical"
        }
    
    Response:
        {
            "statusCode": 200,
            "body": {
                "reportUrl": str (Signed URL),
                "expiresIn": int (seconds),
                "reportKey": str
            }
        }
    """
```

**Implementation:**
- Validates request parameters
- Retrieves evaluation data from DynamoDB
- Invokes appropriate report generator Lambda (async)
- Waits for report generation completion
- Generates S3 signed URL (1 hour expiration)
- Returns URL to frontend

### 4. Executive Report Generator Lambda

**Purpose**: Generate business-oriented reports in DOCX format.

**Interface:**
```python
def lambda_handler(event, context):
    """
    Input:
        {
            "evaluationData": dict,
            "selectedPilares": list[str],
            "accountId": str,
            "timestamp": str
        }
    
    Output:
        {
            "s3Key": str,
            "success": bool,
            "error": str (optional)
        }
    """
```

**Document Structure:**
1. **Portada**: Título, fecha, cuenta AWS
2. **Resumen Ejecutivo**: Overview estratégico con scores generales
3. **Análisis por Pilar**: Una sección por cada pilar seleccionado
   - Score del pilar
   - Análisis de negocio
   - Riesgos identificados
   - Impacto estratégico
4. **Tendencias y Benchmarks**: Comparación con estándares globales
5. **Recomendaciones Ejecutivas**: Priorización de acciones
6. **Conclusiones**: Resumen y próximos pasos

**Libraries:**
- `python-docx`: Document creation and formatting
- `matplotlib`: Chart generation (embedded as images)
- `boto3`: S3 upload

**Chart Types:**
- Radar chart: Scores por pilar
- Bar chart: Distribución de estados (OK, RISK, HIGH_RISK)
- Pie chart: Severidad de hallazgos

### 5. Technical Report Generator Lambda

**Purpose**: Generate detailed technical reports in XLSX format.

**Interface:**
```python
def lambda_handler(event, context):
    """
    Input:
        {
            "evaluationData": dict,
            "selectedPilares": list[str],
            "accountId": str,
            "timestamp": str
        }
    
    Output:
        {
            "s3Key": str,
            "success": bool,
            "error": str (optional)
        }
    """
```

**Workbook Structure:**
1. **Summary Sheet**: Resumen general
   - Tabla de scores por pilar
   - Distribución de estados
   - Estadísticas generales
2. **One Sheet per Pilar**: Detalle de Best Practices
   - Columns: BP ID | Description | Status | Severity | Finding | Evidence | Remediation | Risk
   - Conditional formatting por status
   - Filtros habilitados

**Libraries:**
- `openpyxl`: Excel file creation and formatting
- `boto3`: S3 upload

**Formatting:**
- Header row: Bold, background color, frozen pane
- Status column: Color coding (green=OK, yellow=RISK, red=HIGH_RISK)
- Auto-width columns
- Cell borders

### 6. S3 Reports Bucket

**Bucket Name**: `autowar-reports-{account-id}`

**Structure:**
```
reports/
  ├── {account-id}/
  │   ├── {evaluation-timestamp}/
  │   │   ├── executive-{generation-timestamp}.docx
  │   │   └── technical-{generation-timestamp}.xlsx
```

**Configuration:**
- Encryption: AES-256 (SSE-S3)
- Versioning: ENABLED
- Public access: BLOCKED
- Lifecycle policy: Delete objects older than 30 days
- CORS: Enabled for frontend domain

**Access Control:**
- Bucket policy: Deny all public access
- Lambda execution roles: PutObject, GetObject permissions
- Signed URLs: 1 hour expiration

### 7. Frontend Reports Page

**File**: `frontend-new/reports.html`

**UI Components:**

```html
<div id="reports-container">
  <!-- Evaluation Selector -->
  <div class="evaluation-selector">
    <label>Seleccionar Evaluación:</label>
    <select id="evaluation-select">
      <option value="">-- Seleccione una evaluación --</option>
      <!-- Populated dynamically -->
    </select>
  </div>

  <!-- Pilar Checkboxes -->
  <div class="pilar-selector">
    <label>Pilares a incluir:</label>
    <div class="checkbox-group">
      <input type="checkbox" id="security" value="security">
      <label for="security">Security</label>
      <!-- Repeat for all 6 pilares -->
    </div>
  </div>

  <!-- Report Type Selector -->
  <div class="report-type-selector">
    <label>Tipo de Reporte:</label>
    <input type="radio" id="executive" name="reportType" value="executive">
    <label for="executive">Ejecutivo (DOCX)</label>
    <input type="radio" id="technical" name="reportType" value="technical">
    <label for="technical">Técnico (XLSX)</label>
  </div>

  <!-- Generate Button -->
  <button id="generate-report-btn" disabled>Generar Reporte</button>
  
  <!-- Loading Indicator -->
  <div id="loading-indicator" style="display:none;">
    Generando reporte...
  </div>
</div>
```

**JavaScript Logic** (`reports.js`):
```javascript
// Load evaluations on page load
async function loadEvaluations() {
  const accountId = getAccountIdFromSession();
  const response = await fetch(`/reports/list?accountId=${accountId}`);
  const data = await response.json();
  populateEvaluationSelect(data.evaluations);
}

// Validate form and enable/disable button
function validateForm() {
  const evaluationSelected = document.getElementById('evaluation-select').value;
  const pilaresSelected = getSelectedPilares().length > 0;
  const reportTypeSelected = document.querySelector('input[name="reportType"]:checked');
  
  document.getElementById('generate-report-btn').disabled = 
    !(evaluationSelected && pilaresSelected && reportTypeSelected);
}

// Generate report
async function generateReport() {
  showLoadingIndicator();
  
  const payload = {
    accountId: getAccountIdFromSession(),
    evaluationTimestamp: document.getElementById('evaluation-select').value,
    pilares: getSelectedPilares(),
    reportType: document.querySelector('input[name="reportType"]:checked').value
  };
  
  const response = await fetch('/reports/generate', {
    method: 'POST',
    body: JSON.stringify(payload)
  });
  
  const data = await response.json();
  
  if (data.reportUrl) {
    downloadReport(data.reportUrl);
  } else {
    showError(data.error);
  }
  
  hideLoadingIndicator();
}

// Trigger download
function downloadReport(url) {
  const link = document.createElement('a');
  link.href = url;
  link.download = '';
  link.click();
}
```

## Data Models

### Evaluation Model

```python
from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict

@dataclass
class BestPractice:
    pilar: str
    bp_id: str
    description: str
    status: str  # "OK", "RISK", "HIGH_RISK", "NOT_APPLICABLE"
    severity: str  # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    finding: str
    evidence: str
    remediation: str
    risk: str

@dataclass
class PillarScores:
    security: int
    reliability: int
    performance: int
    cost: int
    operational_excellence: int
    sustainability: int

@dataclass
class Evaluation:
    account_id: str
    timestamp: datetime
    pillar_scores: PillarScores
    best_practices: List[BestPractice]
    metadata: Dict[str, any]
    
    def to_dynamodb_item(self) -> dict:
        """Convert to DynamoDB item format"""
        return {
            "accountId": self.account_id,
            "timestamp": self.timestamp.isoformat(),
            "pillarScores": {
                "security": self.pillar_scores.security,
                "reliability": self.pillar_scores.reliability,
                "performance": self.pillar_scores.performance,
                "cost": self.pillar_scores.cost,
                "operationalExcellence": self.pillar_scores.operational_excellence,
                "sustainability": self.pillar_scores.sustainability
            },
            "bestPractices": [
                {
                    "pilar": bp.pilar,
                    "bpId": bp.bp_id,
                    "description": bp.description,
                    "status": bp.status,
                    "severity": bp.severity,
                    "finding": bp.finding,
                    "evidence": bp.evidence,
                    "remediation": bp.remediation,
                    "risk": bp.risk
                }
                for bp in self.best_practices
            ],
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dynamodb_item(cls, item: dict) -> 'Evaluation':
        """Create from DynamoDB item"""
        return cls(
            account_id=item["accountId"],
            timestamp=datetime.fromisoformat(item["timestamp"]),
            pillar_scores=PillarScores(**item["pillarScores"]),
            best_practices=[
                BestPractice(**bp) for bp in item["bestPractices"]
            ],
            metadata=item["metadata"]
        )
```

### Report Request Model

```python
@dataclass
class ReportRequest:
    account_id: str
    evaluation_timestamp: str
    pilares: List[str]
    report_type: str  # "executive" | "technical"
    
    def validate(self) -> tuple[bool, str]:
        """Validate request parameters"""
        if not self.account_id:
            return False, "accountId is required"
        
        if not self.evaluation_timestamp:
            return False, "evaluationTimestamp is required"
        
        if not self.pilares or len(self.pilares) == 0:
            return False, "At least one pilar must be selected"
        
        valid_pilares = {"security", "reliability", "performance", 
                        "cost", "operationalExcellence", "sustainability"}
        if not all(p in valid_pilares for p in self.pilares):
            return False, f"Invalid pilar. Valid options: {valid_pilares}"
        
        if self.report_type not in ["executive", "technical"]:
            return False, "reportType must be 'executive' or 'technical'"
        
        return True, ""
```

### Report Metadata Model

```python
@dataclass
class ReportMetadata:
    report_key: str
    account_id: str
    evaluation_timestamp: str
    generation_timestamp: datetime
    report_type: str
    pilares: List[str]
    file_size_bytes: int
    signed_url: str
    expires_at: datetime
```


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Evaluation Storage Round Trip

*For any* valid evaluation data, storing it in DynamoDB and then retrieving it should return an equivalent evaluation with all attributes intact (accountId, timestamp, pillarScores, bestPractices, metadata).

**Validates: Requirements 1.4, 1.5, 8.3**

### Property 2: Most Recent Evaluation Retrieval

*For any* AWS account with multiple stored evaluations, selecting "load recent evaluation" should return the evaluation with the most recent timestamp.

**Validates: Requirements 1.3**

### Property 3: Evaluation Query Ordering

*For any* AWS account with stored evaluations, querying evaluations should return a list ordered by timestamp in descending order (most recent first).

**Validates: Requirements 2.2**

### Property 4: Date Range Filtering

*For any* date range query, all returned evaluations should have timestamps that fall within the specified start and end dates (inclusive).

**Validates: Requirements 2.3**

### Property 5: Complete Evaluation Data Retrieval

*For any* stored evaluation, retrieving it should return complete data including all pillar scores and all best practices with no data loss.

**Validates: Requirements 2.4**

### Property 6: Report Generation Button State

*For any* combination of UI selections (evaluation, pilares, report type), the "Generar Reporte" button should be enabled if and only if an evaluation is selected AND at least one pilar is selected AND a report type is selected.

**Validates: Requirements 3.6, 7.10**

### Property 7: Executive Report Document Completeness

*For any* set of selected pilares, the generated executive report should contain: a "Resumen Ejecutivo" section, one dedicated section per selected pilar, trend analysis section, benchmarks section, market experiences section, strategic importance section, conclusions section, and embedded graphical visualizations.

**Validates: Requirements 4.2, 4.3, 4.4, 4.6, 4.7, 4.8, 4.9**

### Property 8: Executive Report Format and Storage

*For any* valid executive report request, the system should generate a valid DOCX file, store it in S3 with the key pattern `reports/{account-id}/{evaluation-timestamp}/executive-{timestamp}.docx`, and return a signed URL valid for 1 hour.

**Validates: Requirements 4.1, 4.12, 6.7, 6.8, 6.9, 9.3, 9.4**

### Property 9: Technical Report Data Completeness

*For any* set of selected pilares, the generated technical report should include all and only the best practices from those pilares, with each best practice having all required columns (BP ID, Description, Status, Severity, Finding, Evidence, Remediation, Risk).

**Validates: Requirements 5.2, 5.3**

### Property 10: Technical Report Workbook Structure

*For any* set of N selected pilares, the generated XLSX workbook should contain exactly N+1 worksheets: one summary sheet and one sheet per selected pilar, with the summary sheet containing overall scores and status distributions.

**Validates: Requirements 5.4, 5.5**

### Property 11: Technical Report Format and Storage

*For any* valid technical report request, the system should generate a valid XLSX file with proper cell formatting (headers, borders, color coding), store it in S3 with the key pattern `reports/{account-id}/{evaluation-timestamp}/technical-{timestamp}.xlsx`, and return a signed URL valid for 1 hour.

**Validates: Requirements 5.1, 5.7, 5.8, 6.7, 6.8, 6.9, 9.3, 9.4**

### Property 12: Report Request Validation

*For any* report generation request, the system should validate that: (1) the evaluation ID exists in DynamoDB, and (2) at least one pilar is selected. If either validation fails, the system should return an error without generating a report.

**Validates: Requirements 6.5, 6.6**

### Property 13: Frontend Report Generation Flow

*For any* valid report generation request from the frontend, clicking "Generar Reporte" should: (1) send a POST request to /reports/generate with correct parameters (accountId, evaluationTimestamp, pilares, reportType), (2) display a loading indicator during generation, and (3) trigger automatic download using the returned signed URL upon success.

**Validates: Requirements 7.6, 7.7, 7.8**

### Property 14: Error Message Propagation

*For any* failed operation (DynamoDB failure, S3 failure, report generation failure), the system should return a descriptive error message to the user indicating what went wrong.

**Validates: Requirements 6.10, 7.9, 8.7, 9.7**

### Property 15: S3 Access Control

*For any* report stored in S3, attempting to access it without a valid signed URL should fail with an access denied error.

**Validates: Requirements 9.6**

## Error Handling

### DynamoDB Errors

**Connection Failures:**
- Implement exponential backoff retry (3 attempts)
- Log error details to CloudWatch
- Return user-friendly error: "Unable to access evaluation data. Please try again."

**Item Not Found:**
- Return 404 status code
- Error message: "Evaluation not found for the specified account and timestamp."

**Validation Errors:**
- Return 400 status code
- Error message: "Invalid request: {specific validation error}"

### S3 Errors

**Upload Failures:**
- Retry upload once
- If still fails, return error: "Unable to store report. Please try again."
- Clean up any partial uploads

**Signed URL Generation Failures:**
- Log error details
- Return error: "Unable to generate download link. Please contact support."

**Access Denied:**
- Return 403 status code
- Error message: "Access denied. Please ensure you have proper permissions."

### Report Generation Errors

**Invalid Evaluation Data:**
- Validate data structure before generation
- Return 400 status code
- Error message: "Evaluation data is incomplete or corrupted."

**Library Errors (python-docx, openpyxl):**
- Catch exceptions during document creation
- Log full stack trace
- Return error: "Report generation failed. Please try again or contact support."

**Timeout Errors:**
- Lambda timeout set to 5 minutes
- If approaching timeout, save partial progress and return error
- Error message: "Report generation timed out. Please try with fewer pilares."

### Frontend Errors

**Network Errors:**
- Display error message: "Network error. Please check your connection and try again."
- Provide retry button

**Invalid Selections:**
- Disable submit button until valid selections made
- Display inline validation messages

**Download Failures:**
- If automatic download fails, provide manual download link
- Error message: "Automatic download failed. Click here to download manually."

## Testing Strategy

### Unit Testing

**Backend Components:**
- Test DynamoDB operations (put, query, get) with mocked boto3 client
- Test report generation functions with sample evaluation data
- Test S3 operations (upload, signed URL generation) with mocked boto3 client
- Test request validation logic with various invalid inputs
- Test error handling paths with simulated failures

**Frontend Components:**
- Test UI state management (button enablement logic)
- Test form validation
- Test API request payload construction
- Test download trigger mechanism
- Test error message display

**Edge Cases:**
- Empty evaluation data
- Evaluation with no best practices
- Single pilar selection vs. all pilares
- Very large evaluation data (stress test)
- Expired signed URLs
- Concurrent report generation requests

### Property-Based Testing

All property-based tests should run a minimum of 100 iterations to ensure comprehensive coverage through randomization.

**Property Test 1: Evaluation Storage Round Trip**
- Generate random evaluation data (varying pilares, best practices, scores)
- Store in DynamoDB
- Retrieve and compare
- Tag: **Feature: autowar-reporting-system, Property 1: Evaluation Storage Round Trip**

**Property Test 2: Most Recent Evaluation Retrieval**
- Generate random set of evaluations with different timestamps
- Store all in DynamoDB
- Query for most recent
- Verify returned evaluation has latest timestamp
- Tag: **Feature: autowar-reporting-system, Property 2: Most Recent Evaluation Retrieval**

**Property Test 3: Evaluation Query Ordering**
- Generate random set of evaluations
- Store in DynamoDB
- Query all
- Verify descending timestamp order
- Tag: **Feature: autowar-reporting-system, Property 3: Evaluation Query Ordering**

**Property Test 4: Date Range Filtering**
- Generate random evaluations across wide date range
- Generate random date range query
- Verify all results fall within range
- Tag: **Feature: autowar-reporting-system, Property 4: Date Range Filtering**

**Property Test 5: Complete Evaluation Data Retrieval**
- Generate random evaluation with all fields populated
- Store and retrieve
- Verify all fields present and correct
- Tag: **Feature: autowar-reporting-system, Property 5: Complete Evaluation Data Retrieval**

**Property Test 6: Report Generation Button State**
- Generate random UI state combinations
- Verify button enabled state matches logic
- Tag: **Feature: autowar-reporting-system, Property 6: Report Generation Button State**

**Property Test 7: Executive Report Document Completeness**
- Generate random pilar selections
- Generate executive report
- Parse document and verify all required sections present
- Tag: **Feature: autowar-reporting-system, Property 7: Executive Report Document Completeness**

**Property Test 8: Executive Report Format and Storage**
- Generate random executive report requests
- Verify DOCX validity
- Verify S3 key pattern
- Verify signed URL validity and expiration
- Tag: **Feature: autowar-reporting-system, Property 8: Executive Report Format and Storage**

**Property Test 9: Technical Report Data Completeness**
- Generate random pilar selections
- Generate technical report
- Parse XLSX and verify correct best practices included
- Verify all columns present
- Tag: **Feature: autowar-reporting-system, Property 9: Technical Report Data Completeness**

**Property Test 10: Technical Report Workbook Structure**
- Generate random pilar selections (1 to 6 pilares)
- Generate technical report
- Verify worksheet count = N + 1
- Verify summary sheet exists
- Tag: **Feature: autowar-reporting-system, Property 10: Technical Report Workbook Structure**

**Property Test 11: Technical Report Format and Storage**
- Generate random technical report requests
- Verify XLSX validity
- Verify cell formatting applied
- Verify S3 key pattern
- Verify signed URL validity
- Tag: **Feature: autowar-reporting-system, Property 11: Technical Report Format and Storage**

**Property Test 12: Report Request Validation**
- Generate random invalid requests (missing evaluation, empty pilares, invalid pilar names)
- Verify all return errors without generating reports
- Tag: **Feature: autowar-reporting-system, Property 12: Report Request Validation**

**Property Test 13: Frontend Report Generation Flow**
- Generate random valid report requests
- Simulate button click
- Verify POST request sent with correct payload
- Verify loading indicator shown
- Verify download triggered on success
- Tag: **Feature: autowar-reporting-system, Property 13: Frontend Report Generation Flow**

**Property Test 14: Error Message Propagation**
- Generate random failure scenarios
- Verify error messages returned and displayed
- Tag: **Feature: autowar-reporting-system, Property 14: Error Message Propagation**

**Property Test 15: S3 Access Control**
- Generate random reports
- Attempt access without signed URL
- Verify access denied
- Tag: **Feature: autowar-reporting-system, Property 15: S3 Access Control**

### Integration Testing

**End-to-End Flows:**
1. Complete flow: Validate credentials → New evaluation → Store in DynamoDB → Generate executive report → Download
2. Historical flow: Validate credentials → Load recent evaluation → Generate technical report → Download
3. Multi-pilar report: Select multiple pilares → Generate report → Verify all pilares included
4. Error flow: Invalid evaluation ID → Verify error message displayed

**AWS Service Integration:**
- Test actual DynamoDB operations (use test table)
- Test actual S3 operations (use test bucket)
- Test Lambda invocations (use test functions)
- Test API Gateway endpoints (use test stage)

### Testing Tools

**Python Backend:**
- `pytest`: Test framework
- `moto`: AWS service mocking
- `hypothesis`: Property-based testing library
- `pytest-cov`: Code coverage

**JavaScript Frontend:**
- `Jest`: Test framework
- `@testing-library/dom`: DOM testing utilities
- `fast-check`: Property-based testing library
- `MSW`: API mocking

### Test Coverage Goals

- Unit test coverage: >80%
- Property test coverage: All 15 properties implemented
- Integration test coverage: All critical paths
- Edge case coverage: All identified edge cases tested
