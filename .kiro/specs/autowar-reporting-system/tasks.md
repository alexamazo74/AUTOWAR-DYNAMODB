# Implementation Plan: AutoWAR Reporting System

## Overview

Este plan implementa el sistema de reportes para AutoWAR en fases incrementales: primero la infraestructura de almacenamiento (DynamoDB y S3), luego la modificación del validador de credenciales para soportar evaluaciones históricas, después los generadores de reportes (ejecutivo y técnico), y finalmente la interfaz frontend. Cada fase incluye pruebas de propiedades para validar la corrección del sistema.

## Tasks

- [x] 1. Set up DynamoDB table for historical evaluations
  - Create DynamoDB table "AutoWAR-Evaluations" with composite key (accountId, timestamp)
  - Configure table settings: PAY_PER_REQUEST billing, point-in-time recovery, encryption
  - Create helper functions for DynamoDB operations (put_evaluation, get_evaluation, query_evaluations)
  - _Requirements: 1.4, 1.5, 8.1, 8.2, 8.3, 8.4_

- [ ]* 1.1 Write property test for evaluation storage round trip
  - **Property 1: Evaluation Storage Round Trip**
  - **Validates: Requirements 1.4, 1.5, 8.3**

- [x] 2. Set up S3 bucket for report storage
  - Create S3 bucket "autowar-reports-{account-id}" with encryption and versioning
  - Configure bucket policy to block public access
  - Implement S3 lifecycle policy to delete reports older than 30 days
  - Create helper functions for S3 operations (upload_report, generate_signed_url)
  - _Requirements: 9.1, 9.2, 9.5, 9.6_

- [ ]* 2.1 Write property test for S3 access control
  - **Property 15: S3 Access Control**
  - **Validates: Requirements 9.6**

- [x] 3. Modify Credential Validator Lambda to support historical evaluations
  - [x] 3.1 Add action parameter to credential validator input schema
    - Extend input validation to accept "action" field: "new_evaluation" | "load_recent"
    - _Requirements: 1.1_
  
  - [x] 3.2 Implement "load recent evaluation" logic
    - Query DynamoDB for most recent evaluation by accountId
    - Return evaluation data if found, error if not found
    - _Requirements: 1.3_
  
  - [x] 3.3 Implement "new evaluation" storage logic
    - After WAR evaluation completes, store results in DynamoDB with timestamp
    - Include all evaluation data: pillarScores, bestPractices, metadata
    - _Requirements: 1.2, 1.4, 1.5_
  
  - [ ]* 3.4 Write property test for most recent evaluation retrieval
    - **Property 2: Most Recent Evaluation Retrieval**
    - **Validates: Requirements 1.3**

- [x] 4. Checkpoint - Ensure storage layer tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Implement Report Manager Lambda
  - [x] 5.1 Create Lambda function structure and API endpoints
    - Set up Lambda handler with routing for GET /reports/list and POST /reports/generate
    - Implement request parsing and validation
    - _Requirements: 6.3, 6.4_
  
  - [x] 5.2 Implement GET /reports/list endpoint
    - Query DynamoDB for all evaluations by accountId
    - Support optional date range filtering (startDate, endDate)
    - Return evaluations ordered by timestamp descending
    - _Requirements: 2.1, 2.2, 2.3, 2.4_
  
  - [ ]* 5.3 Write property tests for evaluation queries
    - **Property 3: Evaluation Query Ordering**
    - **Property 4: Date Range Filtering**
    - **Property 5: Complete Evaluation Data Retrieval**
    - **Validates: Requirements 2.2, 2.3, 2.4**
  
  - [x] 5.4 Implement POST /reports/generate endpoint
    - Validate request: evaluation exists, at least one pilar selected, valid report type
    - Retrieve evaluation data from DynamoDB
    - Invoke appropriate report generator Lambda (executive or technical)
    - Generate S3 signed URL for generated report
    - Return signed URL with expiration time
    - _Requirements: 6.5, 6.6, 6.7, 6.8, 6.9, 6.10_
  
  - [ ]* 5.5 Write property test for report request validation
    - **Property 12: Report Request Validation**
    - **Validates: Requirements 6.5, 6.6**
  
  - [ ]* 5.6 Write property test for error message propagation
    - **Property 14: Error Message Propagation**
    - **Validates: Requirements 6.10, 8.7, 9.7**

- [x] 6. Implement Executive Report Generator Lambda
  - [x] 6.1 Create Lambda function with python-docx dependency
    - Set up Lambda layer with python-docx and matplotlib libraries
    - Create Lambda handler to receive evaluation data and selected pilares
    - _Requirements: 4.11_
  
  - [x] 6.2 Implement document structure generation
    - Create DOCX document with title page
    - Add "Resumen Ejecutivo" section with overall scores
    - Add one section per selected pilar with business analysis
    - Add trend analysis and benchmarks section
    - Add market experiences section
    - Add strategic importance section
    - Add conclusions and recommendations section
    - _Requirements: 4.2, 4.3, 4.4, 4.6, 4.7, 4.8_
  
  - [x] 6.3 Implement chart generation and embedding
    - Generate radar chart for pilar scores using matplotlib
    - Generate bar chart for status distribution
    - Generate pie chart for severity distribution
    - Embed charts as images in DOCX document
    - _Requirements: 4.9_
  
  - [x] 6.4 Implement S3 upload and signed URL generation
    - Upload generated DOCX to S3 with structured key pattern
    - Generate signed URL with 1 hour expiration
    - Return S3 key and signed URL
    - _Requirements: 4.12, 6.7, 6.8, 9.3, 9.4_
  
  - [ ]* 6.5 Write property tests for executive report generation
    - **Property 7: Executive Report Document Completeness**
    - **Property 8: Executive Report Format and Storage**
    - **Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.6, 4.7, 4.8, 4.9, 4.12, 6.7, 6.8, 6.9, 9.3, 9.4**

- [ ] 7. Checkpoint - Ensure executive report generation tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Implement Technical Report Generator Lambda
  - [x] 8.1 Create Lambda function with openpyxl dependency
    - Set up Lambda layer with openpyxl library
    - Create Lambda handler to receive evaluation data and selected pilares
    - _Requirements: 5.6_
  
  - [x] 8.2 Implement workbook structure generation
    - Create XLSX workbook
    - Add summary worksheet with overall scores and distributions
    - Add one worksheet per selected pilar
    - _Requirements: 5.4, 5.5_
  
  - [x] 8.3 Implement best practices data population
    - Filter best practices by selected pilares
    - Populate each pilar worksheet with BP data (ID, Description, Status, Severity, Finding, Evidence, Remediation, Risk)
    - Ensure all and only selected pilar BPs are included
    - _Requirements: 5.2, 5.3_
  
  - [x] 8.4 Implement cell formatting
    - Apply header formatting (bold, background color, frozen pane)
    - Apply status color coding (green=OK, yellow=RISK, red=HIGH_RISK)
    - Apply borders and auto-width columns
    - Enable filters on header row
    - _Requirements: 5.8_
  
  - [x] 8.5 Implement S3 upload and signed URL generation
    - Upload generated XLSX to S3 with structured key pattern
    - Generate signed URL with 1 hour expiration
    - Return S3 key and signed URL
    - _Requirements: 5.7, 6.7, 6.8, 9.3, 9.4_
  
  - [ ]* 8.6 Write property tests for technical report generation
    - **Property 9: Technical Report Data Completeness**
    - **Property 10: Technical Report Workbook Structure**
    - **Property 11: Technical Report Format and Storage**
    - **Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5, 5.7, 5.8, 6.7, 6.8, 6.9, 9.3, 9.4**

- [ ] 9. Checkpoint - Ensure technical report generation tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 10. Implement Frontend Reports Page
  - [x] 10.1 Create reports.html page structure
    - Create new HTML file with navigation integration
    - Add page title and description
    - Create container divs for UI components
    - _Requirements: 7.1_
  
  - [x] 10.2 Implement evaluation selector dropdown
    - Add dropdown element for evaluation selection
    - Fetch evaluations from GET /reports/list on page load
    - Populate dropdown with evaluation dates
    - _Requirements: 3.2, 7.2_
  
  - [x] 10.3 Implement pilar checkboxes
    - Add checkboxes for all six pilares: Security, Reliability, Performance, Cost, Operational Excellence, Sustainability
    - Implement multi-select logic
    - _Requirements: 3.4, 7.3_
  
  - [x] 10.4 Implement report type radio buttons
    - Add radio buttons for "Ejecutivo" and "Técnico"
    - Implement single-select logic
    - _Requirements: 3.5, 7.4_
  
  - [x] 10.5 Implement "Generar Reporte" button with validation
    - Add button element
    - Implement enablement logic: enabled only when evaluation selected AND at least one pilar selected AND report type selected
    - Add event listener for button click
    - _Requirements: 3.6, 7.5, 7.10_
  
  - [x] 10.6 Implement report generation flow
    - On button click, send POST request to /reports/generate with selected parameters
    - Display loading indicator during generation
    - On success, trigger automatic download using signed URL
    - On error, display error message to user
    - _Requirements: 7.6, 7.7, 7.8, 7.9_
  
  - [ ]* 10.7 Write property tests for frontend behavior
    - **Property 6: Report Generation Button State**
    - **Property 13: Frontend Report Generation Flow**
    - **Validates: Requirements 3.6, 7.6, 7.7, 7.8, 7.10**

- [ ] 11. Implement error handling across all components
  - [ ] 11.1 Add DynamoDB error handling
    - Implement exponential backoff retry for connection failures
    - Return user-friendly error messages for item not found and validation errors
    - Log errors to CloudWatch
    - _Requirements: 8.6, 8.7_
  
  - [ ] 11.2 Add S3 error handling
    - Implement retry logic for upload failures
    - Handle signed URL generation failures
    - Return appropriate error messages for access denied
    - _Requirements: 9.7_
  
  - [ ] 11.3 Add report generation error handling
    - Validate evaluation data structure before generation
    - Catch and log library exceptions (python-docx, openpyxl)
    - Handle Lambda timeout scenarios
    - Return descriptive error messages
    - _Requirements: 6.10_
  
  - [ ] 11.4 Add frontend error handling
    - Handle network errors with retry option
    - Display inline validation messages
    - Provide manual download link if automatic download fails
    - _Requirements: 7.9_

- [ ]* 11.5 Write unit tests for error handling paths
  - Test DynamoDB error scenarios
  - Test S3 error scenarios
  - Test report generation error scenarios
  - Test frontend error display

- [x] 12. Integration and CDK infrastructure updates
  - [x] 12.1 Update CDK stack to include new resources
    - Add DynamoDB table definition
    - Add S3 bucket definition with lifecycle policy
    - Add Report Manager Lambda definition
    - Add Executive Report Generator Lambda definition with layer
    - Add Technical Report Generator Lambda definition with layer
    - Add API Gateway routes for /reports/list and /reports/generate
    - Configure IAM roles and permissions
    - _Requirements: All infrastructure requirements_
  
  - [x] 12.2 Wire all components together
    - Connect Credential Validator to DynamoDB for evaluation storage
    - Connect Report Manager to DynamoDB for evaluation queries
    - Connect Report Manager to report generator Lambdas
    - Connect report generators to S3 for report storage
    - Connect frontend to API Gateway endpoints
    - _Requirements: All integration requirements_
  
  - [ ]* 12.3 Write integration tests
    - Test end-to-end flow: new evaluation → store → generate executive report → download
    - Test end-to-end flow: load recent → generate technical report → download
    - Test multi-pilar report generation
    - Test error flows with invalid inputs

- [ ] 13. Final checkpoint - Ensure all tests pass
  - Run all unit tests
  - Run all property tests (minimum 100 iterations each)
  - Run all integration tests
  - Verify test coverage meets goals (>80% unit test coverage)
  - Ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Property tests validate universal correctness properties across all inputs
- Unit tests validate specific examples, edge cases, and error conditions
- Integration tests validate end-to-end flows across all components
- Python backend uses: boto3 (AWS SDK), python-docx (DOCX generation), openpyxl (XLSX generation), matplotlib (charts), pytest (testing), hypothesis (property testing)
- JavaScript frontend uses: Fetch API (HTTP requests), Jest (testing), fast-check (property testing)
- All Lambda functions should have appropriate timeout (5 minutes for report generators) and memory (1024 MB minimum) configurations
