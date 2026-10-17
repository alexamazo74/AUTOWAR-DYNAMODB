# Requirements Document

## Introduction

El sistema de reportes para AutoWAR permite gestionar evaluaciones históricas de Well-Architected Reviews y generar dos tipos de reportes: ejecutivo (orientado a negocio en formato DOCX/PDF) y técnico (detalle de Best Practices en formato XLSX). El sistema almacena todas las evaluaciones en DynamoDB, permite consultar evaluaciones históricas, y genera reportes personalizados basados en pilares seleccionados.

## Glossary

- **AutoWAR**: Sistema automatizado de evaluación Well-Architected Review para cuentas AWS
- **Evaluation**: Evaluación completa de Well-Architected Review que incluye análisis de todos los pilares
- **Pilar**: Uno de los seis pilares del Well-Architected Framework (Security, Reliability, Performance, Cost, Operational Excellence, Sustainability)
- **Best_Practice**: Práctica recomendada dentro de un pilar del Well-Architected Framework
- **Executive_Report**: Reporte orientado a negocio en formato DOCX o PDF con análisis estratégico
- **Technical_Report**: Reporte técnico en formato XLSX con detalle de todas las Best Practices
- **DynamoDB**: Base de datos NoSQL de AWS utilizada para almacenar evaluaciones históricas
- **S3**: Servicio de almacenamiento de objetos de AWS utilizado para almacenar reportes generados
- **Lambda**: Servicio de computación serverless de AWS utilizado para generar reportes
- **Credential_Validator**: Componente que valida credenciales AWS y permite elegir entre nueva evaluación o cargar datos históricos
- **Frontend**: Interfaz web del sistema AutoWAR
- **Signed_URL**: URL temporal con firma de seguridad para descargar archivos desde S3

## Requirements

### Requirement 1: Historical Evaluation Management

**User Story:** Como usuario del sistema AutoWAR, quiero poder elegir entre realizar una nueva evaluación o cargar datos de una evaluación previa, para poder ahorrar tiempo cuando solo necesito generar reportes de evaluaciones ya realizadas.

#### Acceptance Criteria

1. WHEN the Credential_Validator validates AWS credentials, THE System SHALL present two options: perform new WAR evaluation or load most recent stored evaluation
2. WHEN a user selects "perform new evaluation", THE System SHALL execute a complete WAR evaluation and store results in DynamoDB with timestamp
3. WHEN a user selects "load recent evaluation", THE System SHALL retrieve the most recent evaluation data from DynamoDB for that AWS account
4. THE System SHALL store all evaluation results in DynamoDB with AWS account ID, timestamp, and complete evaluation data
5. WHEN storing an evaluation, THE System SHALL include metadata: account ID, evaluation timestamp, pillar scores, and all Best Practice results

### Requirement 2: Historical Evaluation Query

**User Story:** Como usuario del sistema, quiero poder consultar evaluaciones históricas por cuenta AWS y fecha, para poder acceder a evaluaciones anteriores y generar reportes retrospectivos.

#### Acceptance Criteria

1. THE System SHALL provide an API endpoint to query evaluations by AWS account ID
2. WHEN querying evaluations, THE System SHALL return a list of all evaluations with their timestamps ordered by date descending
3. THE System SHALL allow filtering evaluations by date range
4. WHEN retrieving an evaluation, THE System SHALL return complete evaluation data including all pillar results and Best Practice details
5. THE DynamoDB table SHALL use AWS account ID as partition key and timestamp as sort key for efficient queries

### Requirement 3: Reports Menu Interface

**User Story:** Como usuario del sistema, quiero una interfaz de reportes donde pueda seleccionar una evaluación específica, elegir pilares y tipo de reporte, para poder generar reportes personalizados según mis necesidades.

#### Acceptance Criteria

1. THE Frontend SHALL provide a new "Reportes" view accessible from the main navigation
2. WHEN the Reports view loads, THE System SHALL display a list of all WAR evaluations with their dates
3. THE System SHALL allow selecting exactly one evaluation by date using a dropdown or radio button selector
4. THE System SHALL display checkboxes for each of the six pilares allowing multiple selection
5. THE System SHALL provide radio buttons to choose between "Ejecutivo" and "Técnico" report types
6. THE System SHALL provide a "Generar Reporte" button that is enabled only when an evaluation and at least one pilar are selected
7. WHEN no evaluation is selected, THE System SHALL disable the report generation button and display a message indicating selection is required

### Requirement 4: Executive Report Generation

**User Story:** Como ejecutivo o stakeholder de negocio, quiero un reporte ejecutivo en formato DOCX o PDF con análisis estratégico y orientado a negocio, para poder entender el impacto de negocio de las recomendaciones sin detalles técnicos.

#### Acceptance Criteria

1. WHEN a user requests an Executive_Report, THE System SHALL generate a document in DOCX or PDF format
2. THE Executive_Report SHALL include a "Resumen Ejecutivo" section with strategic overview of the selected pilares
3. FOR EACH selected pilar, THE Executive_Report SHALL include a dedicated section with business-oriented analysis
4. THE Executive_Report SHALL include trend analysis and global benchmarks comparing the evaluation against industry standards
5. THE Executive_Report SHALL identify and describe business risks associated with findings in business language
6. THE Executive_Report SHALL include relevant market experiences and case studies related to identified issues
7. THE Executive_Report SHALL explain the strategic importance of recommended remediations
8. THE Executive_Report SHALL include a conclusions and executive recommendations section
9. THE Executive_Report SHALL include graphical visualizations: scores, distributions, and comparative charts
10. THE Executive_Report SHALL use business-oriented language avoiding technical jargon
11. THE System SHALL generate the Executive_Report using a Lambda function with python-docx or ReportLab library
12. WHEN the Executive_Report is generated, THE System SHALL store it in S3 and return a Signed_URL for download

### Requirement 5: Technical Report Generation

**User Story:** Como ingeniero o arquitecto técnico, quiero un reporte técnico en formato XLSX con el detalle completo de todas las Best Practices, para poder analizar y planificar las remediaciones técnicas necesarias.

#### Acceptance Criteria

1. WHEN a user requests a Technical_Report, THE System SHALL generate a document in XLSX format
2. THE Technical_Report SHALL include all Best_Practices from the selected pilares
3. FOR EACH Best_Practice, THE Technical_Report SHALL include columns: BP ID, Description, Status, Severity, Finding, Evidence, Remediation, Risk
4. THE Technical_Report SHALL create one worksheet per selected pilar
5. THE Technical_Report SHALL include a summary worksheet with overall scores and status distributions for all selected pilares
6. THE System SHALL generate the Technical_Report using a Lambda function with openpyxl or xlsxwriter library
7. WHEN the Technical_Report is generated, THE System SHALL store it in S3 and return a Signed_URL for download
8. THE Technical_Report SHALL format cells appropriately with headers, borders, and color coding for status values

### Requirement 6: Report Generation Backend

**User Story:** Como sistema backend, necesito procesar solicitudes de generación de reportes de manera eficiente y escalable, para poder servir múltiples usuarios concurrentemente.

#### Acceptance Criteria

1. THE System SHALL provide a Lambda function dedicated to Executive_Report generation
2. THE System SHALL provide a Lambda function dedicated to Technical_Report generation
3. THE System SHALL provide an API endpoint GET /reports/list to retrieve available evaluations
4. THE System SHALL provide an API endpoint POST /reports/generate to request report generation
5. WHEN receiving a report generation request, THE System SHALL validate that the evaluation ID exists in DynamoDB
6. WHEN receiving a report generation request, THE System SHALL validate that at least one pilar is selected
7. WHEN a report is generated, THE System SHALL store it in S3 with a structured key: reports/{account-id}/{evaluation-timestamp}/{report-type}-{timestamp}.{extension}
8. WHEN a report is stored in S3, THE System SHALL generate a Signed_URL valid for 1 hour
9. THE System SHALL return the Signed_URL to the Frontend for automatic download
10. IF report generation fails, THE System SHALL return an error message with details

### Requirement 7: Frontend Reports Page

**User Story:** Como usuario del frontend, quiero una página de reportes intuitiva que me guíe en la selección de parámetros y descargue automáticamente el reporte generado, para tener una experiencia fluida y sin fricciones.

#### Acceptance Criteria

1. THE Frontend SHALL provide a new page reports.html with the reports interface
2. THE reports.html page SHALL include a date selector dropdown populated with available evaluation dates
3. THE reports.html page SHALL include checkboxes for each pilar: Security, Reliability, Performance, Cost, Operational Excellence, Sustainability
4. THE reports.html page SHALL include radio buttons for report type: "Ejecutivo" and "Técnico"
5. THE reports.html page SHALL include a "Generar Reporte" button
6. WHEN the "Generar Reporte" button is clicked, THE Frontend SHALL send a POST request to /reports/generate with selected parameters
7. WHEN the report generation is successful, THE Frontend SHALL automatically trigger download of the generated file using the Signed_URL
8. WHEN the report generation is in progress, THE Frontend SHALL display a loading indicator
9. IF report generation fails, THE Frontend SHALL display an error message to the user
10. THE Frontend SHALL validate that at least one pilar is selected before enabling the "Generar Reporte" button

### Requirement 8: Data Persistence and Retrieval

**User Story:** Como sistema, necesito almacenar y recuperar evaluaciones de manera eficiente y confiable, para garantizar la disponibilidad de datos históricos y la integridad de los reportes.

#### Acceptance Criteria

1. THE System SHALL use a DynamoDB table named "AutoWAR-Evaluations" to store evaluation data
2. THE DynamoDB table SHALL use composite key: partition key = AWS account ID, sort key = evaluation timestamp (ISO 8601 format)
3. WHEN storing an evaluation, THE System SHALL include all attributes: accountId, timestamp, pillarScores, bestPractices, metadata
4. THE System SHALL enable point-in-time recovery for the DynamoDB table
5. WHEN querying evaluations, THE System SHALL use efficient query operations (not scan) leveraging the partition and sort keys
6. THE System SHALL implement error handling for DynamoDB operations with appropriate retry logic
7. IF a DynamoDB operation fails after retries, THE System SHALL return a descriptive error message

### Requirement 9: Report Storage and Access Control

**User Story:** Como administrador del sistema, necesito que los reportes generados se almacenen de manera segura y sean accesibles solo temporalmente, para proteger información sensible de las evaluaciones.

#### Acceptance Criteria

1. THE System SHALL store all generated reports in an S3 bucket with encryption at rest enabled
2. THE S3 bucket SHALL have versioning enabled for audit purposes
3. THE System SHALL organize reports using a hierarchical key structure: reports/{account-id}/{evaluation-timestamp}/{report-type}-{generation-timestamp}.{extension}
4. WHEN generating a Signed_URL, THE System SHALL set expiration time to 1 hour
5. THE System SHALL implement S3 lifecycle policies to automatically delete reports older than 30 days
6. THE S3 bucket SHALL block public access and require signed URLs for all downloads
7. IF S3 operations fail, THE System SHALL return appropriate error messages to the user
