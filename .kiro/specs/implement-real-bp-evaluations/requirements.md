# Requirements Document

## Introduction

This feature implements real AWS API-based evaluations for Best Practices (BPs) across all six AWS Well-Architected Framework pillars. Currently, most BPs return "Manual review required" with PENDING_REVIEW status. This implementation will replace manual review placeholders with actual AWS API calls that gather evidence, determine compliance status, provide specific findings, and offer actionable remediation steps.

The system evaluates AWS accounts against Well-Architected Framework best practices across:
- Security (11 questions, 63 BPs) - Already has real evaluations
- Cost Optimization (11 questions, 50 BPs)
- Performance Efficiency (5 questions, 32 BPs)
- Reliability (13 questions, 37 BPs)
- Operational Excellence (11 questions, 31 BPs)
- Sustainability (6 questions, 29 BPs)

## Glossary

- **BP (Best Practice)**: A specific recommendation from the AWS Well-Architected Framework, identified by a code like COST01-BP03
- **Pillar**: One of the six Well-Architected Framework pillars (Security, Cost, Performance, Reliability, Operational Excellence, Sustainability)
- **Evaluator**: A Lambda function that evaluates all BPs for a specific pillar
- **Finding**: The result of evaluating a BP, including status, severity, evidence, and remediation
- **Status**: Compliance state - COMPLIANT, NON_COMPLIANT, or PENDING_REVIEW
- **Severity**: Risk level - CRITICAL, HIGH, MEDIUM, or LOW
- **Evidence**: Specific AWS resource data supporting the finding (ARNs, counts, configurations)
- **Session**: User authentication session managed by CredentialsManager
- **Multi-Region Evaluation**: Evaluation across multiple AWS regions specified by the user
- **DynamoDB Cache**: 5-minute cache of evaluation results to avoid redundant API calls
- **Manual Review BP**: A BP that requires human judgment (architecture decisions, organizational processes)

## Requirements

### Requirement 1: Implement Real Evaluations for Cost Optimization Pillar

**User Story:** As a cloud architect, I want automated evaluation of Cost Optimization best practices, so that I can identify cost savings opportunities without manual review.

#### Acceptance Criteria

1. WHEN evaluating COST01-BP03 (budgets), THE System SHALL query AWS Budgets API and return COMPLIANT if budgets exist, NON_COMPLIANT otherwise
2. WHEN evaluating COST02-BP03 (account structure), THE System SHALL query AWS Organizations API and return COMPLIANT if organization exists, NON_COMPLIANT otherwise
3. WHEN evaluating COST03-BP01 (cost monitoring), THE System SHALL query Cost Explorer API and return COMPLIANT if accessible, NON_COMPLIANT otherwise
4. WHEN evaluating COST04-BP03 (decommission resources), THE System SHALL query EC2 API for stopped instances and return NON_COMPLIANT if any exist, COMPLIANT otherwise
5. WHEN evaluating COST06-BP04 (shared resources), THE System SHALL query ELB API and return COMPLIANT if load balancers exist
6. WHEN evaluating COST07-BP04 (pricing models), THE System SHALL query EC2 API for Reserved Instances and return COMPLIANT if any active RIs exist, NON_COMPLIANT otherwise
7. WHEN evaluating COST09-BP03 (dynamic resources), THE System SHALL query Auto Scaling API and return COMPLIANT if ASGs exist, NON_COMPLIANT otherwise
8. WHEN evaluating COST11-BP01 (automation), THE System SHALL query Lambda API and return COMPLIANT if functions exist, NON_COMPLIANT otherwise
9. FOR ALL Cost Optimization evaluations, THE System SHALL include specific evidence (resource counts, ARNs, configurations)
10. FOR ALL Cost Optimization evaluations, THE System SHALL assign appropriate severity (CRITICAL, HIGH, MEDIUM, LOW)
11. FOR ALL Cost Optimization evaluations, THE System SHALL provide actionable remediation steps
12. WHEN a BP requires organizational/process review, THE System SHALL return PENDING_REVIEW status with explanation

### Requirement 2: Implement Real Evaluations for Performance Efficiency Pillar

**User Story:** As a performance engineer, I want automated evaluation of Performance Efficiency best practices, so that I can identify performance optimization opportunities.

#### Acceptance Criteria

1. WHEN evaluating PERF01-BP01 (instance diversity), THE System SHALL query EC2 API for running instances and return COMPLIANT if 5+ different instance types exist, NON_COMPLIANT if fewer
2. WHEN evaluating PERF02-BP01 (compute options), THE System SHALL query EC2 and Lambda APIs and return COMPLIANT if both services are in use, COMPLIANT with MEDIUM severity if only one
3. WHEN evaluating PERF03-BP01 (data stores), THE System SHALL query S3, DynamoDB, and RDS APIs and return COMPLIANT if 2+ different store types exist
4. WHEN evaluating PERF04-BP01 (networking), THE System SHALL query EC2 VPC API and return COMPLIANT if VPCs exist
5. WHEN evaluating PERF04-BP04 (load balancing), THE System SHALL query ELB API and return COMPLIANT if load balancers exist
6. WHEN evaluating PERF03-BP05 (caching), THE System SHALL query ElastiCache API and return COMPLIANT if cache clusters exist, NON_COMPLIANT otherwise
7. WHEN evaluating PERF04-BP05 (network protocols), THE System SHALL query VPC endpoints and return COMPLIANT if PrivateLink endpoints exist
8. FOR ALL Performance evaluations, THE System SHALL include specific evidence (instance types, service counts, configurations)
9. FOR ALL Performance evaluations, THE System SHALL assign appropriate severity based on performance impact
10. FOR ALL Performance evaluations, THE System SHALL provide actionable remediation steps
11. WHEN a BP requires architectural analysis, THE System SHALL return PENDING_REVIEW status with explanation

### Requirement 3: Implement Real Evaluations for Reliability Pillar

**User Story:** As a reliability engineer, I want automated evaluation of Reliability best practices, so that I can identify and fix reliability risks.

#### Acceptance Criteria

1. WHEN evaluating REL02-BP01 (network connectivity), THE System SHALL query VPC and Route53 APIs and return COMPLIANT if redundant connectivity exists
2. WHEN evaluating REL06-BP01 (monitoring), THE System SHALL query CloudWatch API and return COMPLIANT if alarms exist, NON_COMPLIANT otherwise
3. WHEN evaluating REL07-BP01 (auto scaling), THE System SHALL query Auto Scaling API and return COMPLIANT if ASGs with scaling policies exist
4. WHEN evaluating REL09-BP01 (backups), THE System SHALL query AWS Backup API and return COMPLIANT if backup plans exist, NON_COMPLIANT otherwise
5. WHEN evaluating REL09-BP03 (automated backups), THE System SHALL query RDS and DynamoDB APIs for automated backup configurations
6. WHEN evaluating REL10-BP01 (multi-location), THE System SHALL query EC2 API across regions and return COMPLIANT if resources exist in 2+ regions
7. WHEN evaluating REL11-BP02 (failover), THE System SHALL query Route53 health checks and return COMPLIANT if health checks exist
8. WHEN evaluating REL11-BP03 (auto healing), THE System SHALL query Auto Scaling and ECS APIs for health check configurations
9. FOR ALL Reliability evaluations, THE System SHALL include specific evidence (backup counts, alarm counts, region distribution)
10. FOR ALL Reliability evaluations, THE System SHALL assign CRITICAL or HIGH severity for availability risks
11. FOR ALL Reliability evaluations, THE System SHALL provide actionable remediation steps
12. WHEN a BP requires architectural design decisions, THE System SHALL return PENDING_REVIEW status with explanation

### Requirement 4: Implement Real Evaluations for Operational Excellence Pillar

**User Story:** As a DevOps engineer, I want automated evaluation of Operational Excellence best practices, so that I can improve operational processes.

#### Acceptance Criteria

1. WHEN evaluating OPS04-BP02 (application telemetry), THE System SHALL query CloudWatch Logs API and return COMPLIANT if log groups exist, NON_COMPLIANT otherwise
2. WHEN evaluating OPS05-BP01 (version control), THE System SHALL query CodeCommit API and return COMPLIANT if repositories exist
3. WHEN evaluating OPS05-BP04 (deployment systems), THE System SHALL query CodePipeline and CodeDeploy APIs and return COMPLIANT if pipelines exist
4. WHEN evaluating OPS06-BP04 (automated rollback), THE System SHALL query CodeDeploy API for deployment configurations with automatic rollback enabled
5. WHEN evaluating OPS08-BP01 (analyze metrics), THE System SHALL query CloudWatch API for custom metrics and return COMPLIANT if custom metrics exist
6. WHEN evaluating OPS08-BP02 (analyze logs), THE System SHALL query CloudWatch Logs Insights and return COMPLIANT if queries are saved
7. FOR ALL Operational Excellence evaluations, THE System SHALL include specific evidence (pipeline counts, log group counts, metric counts)
8. FOR ALL Operational Excellence evaluations, THE System SHALL assign appropriate severity based on operational impact
9. FOR ALL Operational Excellence evaluations, THE System SHALL provide actionable remediation steps
10. WHEN a BP requires organizational culture or process review, THE System SHALL return PENDING_REVIEW status with explanation

### Requirement 5: Implement Real Evaluations for Sustainability Pillar

**User Story:** As a sustainability officer, I want automated evaluation of Sustainability best practices, so that I can reduce environmental impact.

#### Acceptance Criteria

1. WHEN evaluating SUS02-BP01 (dynamic scaling), THE System SHALL query Auto Scaling API and return COMPLIANT if ASGs exist, NON_COMPLIANT otherwise
2. WHEN evaluating SUS02-BP03 (unused assets), THE System SHALL query EC2, RDS, and EBS APIs for stopped/unused resources and return NON_COMPLIANT if any exist
3. WHEN evaluating SUS03-BP02 (remove unused components), THE System SHALL query Lambda API for functions with zero invocations in last 30 days
4. WHEN evaluating SUS04-BP03 (lifecycle policies), THE System SHALL query S3 API for bucket lifecycle configurations and return COMPLIANT if policies exist
5. WHEN evaluating SUS04-BP05 (remove redundant data), THE System SHALL query S3 API for versioning and intelligent tiering configurations
6. WHEN evaluating SUS05-BP01 (minimum hardware), THE System SHALL query EC2 API for instance utilization via CloudWatch and flag over-provisioned instances
7. WHEN evaluating SUS05-BP03 (managed services), THE System SHALL query multiple service APIs and return COMPLIANT if managed services (RDS, DynamoDB, Lambda) are in use
8. FOR ALL Sustainability evaluations, THE System SHALL include specific evidence (resource counts, utilization metrics, configuration details)
9. FOR ALL Sustainability evaluations, THE System SHALL assign appropriate severity based on environmental impact
10. FOR ALL Sustainability evaluations, THE System SHALL provide actionable remediation steps
11. WHEN a BP requires organizational process review, THE System SHALL return PENDING_REVIEW status with explanation

### Requirement 6: Handle AWS API Permissions Gracefully

**User Story:** As a system administrator, I want the system to handle missing permissions gracefully, so that partial evaluations can still provide value.

#### Acceptance Criteria

1. WHEN an AWS API call fails due to AccessDenied error, THE System SHALL return PENDING_REVIEW status for that BP
2. WHEN an AWS API call fails due to AccessDenied error, THE System SHALL include the permission error in the evidence field
3. WHEN an AWS API call fails due to AccessDenied error, THE System SHALL provide remediation steps to grant required permissions
4. WHEN an AWS API call fails due to service unavailability, THE System SHALL return PENDING_REVIEW status with error details
5. WHEN multiple API calls fail for a question, THE System SHALL continue evaluating remaining BPs
6. FOR ALL permission errors, THE System SHALL log the error for debugging purposes
7. FOR ALL permission errors, THE System SHALL NOT fail the entire pillar evaluation

### Requirement 7: Support Multi-Region Evaluation

**User Story:** As a cloud architect, I want to evaluate best practices across multiple regions, so that I can ensure consistent compliance globally.

#### Acceptance Criteria

1. WHEN credentials include multiple regions, THE System SHALL evaluate each region independently
2. WHEN evaluating multiple regions, THE System SHALL aggregate findings across all regions
3. WHEN a BP is NON_COMPLIANT in any region, THE System SHALL mark the overall status as NON_COMPLIANT
4. WHEN a BP is COMPLIANT in all regions, THE System SHALL mark the overall status as COMPLIANT
5. FOR ALL multi-region findings, THE System SHALL include region information in the evidence
6. FOR ALL multi-region evaluations, THE System SHALL include a list of evaluated regions in the response
7. WHEN aggregating scores, THE System SHALL weight findings equally across regions

### Requirement 8: Cache Evaluation Results

**User Story:** As a system user, I want evaluation results cached for 5 minutes, so that I don't trigger redundant AWS API calls.

#### Acceptance Criteria

1. WHEN an evaluation is requested, THE System SHALL check DynamoDB for cached results from the last 5 minutes
2. WHEN cached results exist and are less than 5 minutes old, THE System SHALL return cached results immediately
3. WHEN cached results are older than 5 minutes, THE System SHALL perform a new evaluation
4. WHEN a new evaluation completes, THE System SHALL store results in DynamoDB with timestamp
5. FOR ALL cached results, THE System SHALL include the evaluation timestamp in the response
6. FOR ALL cached results, THE System SHALL use session_id and pillar_id as cache keys
7. WHEN storing results, THE System SHALL NOT set TTL (keep historical data)

### Requirement 9: Provide Actionable Remediation Steps

**User Story:** As a cloud engineer, I want specific remediation steps for each finding, so that I can fix issues quickly.

#### Acceptance Criteria

1. FOR ALL NON_COMPLIANT findings, THE System SHALL provide specific remediation steps
2. FOR ALL remediation steps, THE System SHALL include AWS service names and actions required
3. WHEN remediation requires AWS Console actions, THE System SHALL provide step-by-step instructions
4. WHEN remediation requires CLI commands, THE System SHALL provide example commands
5. WHEN remediation requires IAM permissions, THE System SHALL list required permissions
6. FOR ALL COMPLIANT findings, THE System SHALL state "Current state compliant"
7. FOR ALL PENDING_REVIEW findings, THE System SHALL explain why manual review is required

### Requirement 10: Assign Appropriate Severity Levels

**User Story:** As a security officer, I want findings prioritized by severity, so that I can address critical issues first.

#### Acceptance Criteria

1. WHEN a finding impacts security or availability, THE System SHALL assign CRITICAL severity
2. WHEN a finding impacts cost significantly (>$1000/month potential savings), THE System SHALL assign HIGH severity
3. WHEN a finding impacts performance or reliability moderately, THE System SHALL assign MEDIUM severity
4. WHEN a finding is a best practice recommendation with low impact, THE System SHALL assign LOW severity
5. FOR ALL severity assignments, THE System SHALL be consistent across similar findings
6. FOR ALL PENDING_REVIEW findings, THE System SHALL default to MEDIUM severity
7. WHEN a BP has no resources to evaluate, THE System SHALL assign LOW severity and COMPLIANT status

### Requirement 11: Maintain Backward Compatibility

**User Story:** As a system maintainer, I want new evaluations to maintain the existing response format, so that the frontend continues to work without changes.

#### Acceptance Criteria

1. FOR ALL pillar evaluations, THE System SHALL return the same JSON structure as existing evaluations
2. FOR ALL findings, THE System SHALL include bp, description, status, severity, finding, evidence, remediation, and risk fields
3. FOR ALL questions, THE System SHALL include question_id, title, description, score, bps_evaluated, status, and findings fields
4. FOR ALL pillar responses, THE System SHALL include pillar_id, region, pillar_name, description, overall_score, total_findings, total_best_practices, timestamp, questions, compliance_distribution, and severity_distribution fields
5. WHEN multi-region evaluation is performed, THE System SHALL include regions and multi_region fields
6. FOR ALL scores, THE System SHALL calculate using the same formula (weighted average by BP count)
7. FOR ALL distributions, THE System SHALL count findings by status and severity

### Requirement 12: Prioritize High-Impact Best Practices

**User Story:** As a product manager, I want high-impact BPs implemented first, so that users get maximum value quickly.

#### Acceptance Criteria

1. WHEN implementing Cost Optimization, THE System SHALL prioritize BPs that identify actual cost savings (stopped instances, unused resources, missing RIs)
2. WHEN implementing Performance, THE System SHALL prioritize BPs that identify performance bottlenecks (missing caching, no load balancing, single instance types)
3. WHEN implementing Reliability, THE System SHALL prioritize BPs that identify availability risks (no backups, no multi-AZ, no monitoring)
4. WHEN implementing Operational Excellence, THE System SHALL prioritize BPs that identify automation gaps (no CI/CD, no monitoring, no logging)
5. WHEN implementing Sustainability, THE System SHALL prioritize BPs that identify waste (unused resources, over-provisioning, no lifecycle policies)
6. FOR ALL pillars, THE System SHALL implement at least 30% of BPs with real evaluations (not PENDING_REVIEW)
7. WHEN a BP genuinely requires manual review (architecture decisions, organizational culture), THE System SHALL keep PENDING_REVIEW status

