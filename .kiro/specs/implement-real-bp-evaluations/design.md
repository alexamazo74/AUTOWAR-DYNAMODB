# Design Document: Real AWS Best Practice Evaluations

## Overview

This design implements real AWS API-based evaluations for Best Practices across all six Well-Architected Framework pillars. The implementation replaces "Manual review required" placeholders with actual AWS service checks that gather evidence, determine compliance, and provide actionable remediation.

The design follows the existing pattern established by the Security pillar (which already has 63 real evaluations) and extends it to:
- Cost Optimization: 50 BPs → Target 15-20 real evaluations (30-40%)
- Performance Efficiency: 32 BPs → Target 10-12 real evaluations (30-40%)
- Reliability: 37 BPs → Target 12-15 real evaluations (30-40%)
- Operational Excellence: 31 BPs → Target 10-12 real evaluations (30-40%)
- Sustainability: 29 BPs → Target 9-12 real evaluations (30-40%)

## Architecture

### Current Architecture
Each pillar has a Lambda evaluator at `lambda/evaluators/{pillar}/handler.py` that:
1. Receives evaluation request with session credentials
2. Checks DynamoDB cache (5-minute TTL)
3. Creates boto3 session with user credentials
4. Evaluates all questions and BPs for the pillar
5. Calculates scores and distributions
6. Stores results in DynamoDB
7. Returns JSON response

### Design Pattern
The Security pillar uses a modular pattern:
- `handler.py`: Main Lambda handler and orchestration
- `all_bp_evaluations.py`: Individual BP evaluation functions
- `bp_descriptions.py`: BP description strings

Other pillars currently have all logic in `handler.py` with `_create_pending()` for manual review BPs.

### Proposed Changes
Extend each pillar's handler to include real evaluation logic:
1. Keep existing `handler.py` structure
2. Add real evaluation methods for high-impact BPs
3. Keep `_create_pending()` for BPs requiring manual review
4. Maintain backward compatibility with existing response format

## Components and Interfaces

### Component 1: Cost Optimization Evaluator

**Location**: `lambda/evaluators/cost/handler.py`

**Methods to Implement**:

```python
def _evaluate_cost01_bp03_budgets(self) -> Dict[str, Any]:
    """Check if AWS Budgets are configured"""
    # Query: budgets.describe_budgets()
    # COMPLIANT: len(budgets) > 0
    # Evidence: "{count} budget(s) configured"
    # Severity: HIGH if non-compliant
    
def _evaluate_cost02_bp03_organizations(self) -> Dict[str, Any]:
    """Check if AWS Organizations is configured"""
    # Query: organizations.describe_organization()
    # COMPLIANT: organization exists
    # Evidence: "Organization ID: {org_id}"
    # Severity: MEDIUM if non-compliant
    
def _evaluate_cost03_bp01_cost_explorer(self) -> Dict[str, Any]:
    """Check if Cost Explorer is accessible"""
    # Query: ce.get_cost_and_usage()
    # COMPLIANT: API call succeeds
    # Evidence: "Cost data available"
    # Severity: HIGH if non-compliant
    
def _evaluate_cost04_bp03_stopped_instances(self) -> Dict[str, Any]:
    """Check for stopped EC2 instances"""
    # Query: ec2.describe_instances(Filters=[{'Name': 'instance-state-name', 'Values': ['stopped']}])
    # NON_COMPLIANT: len(stopped_instances) > 0
    # Evidence: "{count} stopped instance(s): {instance_ids}"
    # Severity: MEDIUM
    
def _evaluate_cost06_bp04_load_balancers(self) -> Dict[str, Any]:
    """Check if load balancers are used (shared resources)"""
    # Query: elbv2.describe_load_balancers()
    # COMPLIANT: len(load_balancers) > 0
    # Evidence: "{count} load balancer(s)"
    # Severity: LOW
    
def _evaluate_cost07_bp04_reserved_instances(self) -> Dict[str, Any]:
    """Check for Reserved Instances or Savings Plans"""
    # Query: ec2.describe_reserved_instances(Filters=[{'Name': 'state', 'Values': ['active']}])
    # COMPLIANT: len(reserved_instances) > 0
    # Evidence: "{count} active RI(s)"
    # Severity: MEDIUM if non-compliant
    
def _evaluate_cost09_bp03_auto_scaling(self) -> Dict[str, Any]:
    """Check if Auto Scaling is configured"""
    # Query: autoscaling.describe_auto_scaling_groups()
    # COMPLIANT: len(asgs) > 0
    # Evidence: "{count} ASG(s) configured"
    # Severity: MEDIUM if non-compliant
    
def _evaluate_cost11_bp01_lambda_automation(self) -> Dict[str, Any]:
    """Check if Lambda is used for automation"""
    # Query: lambda_client.list_functions()
    # COMPLIANT: len(functions) > 0
    # Evidence: "{count} Lambda function(s)"
    # Severity: MEDIUM if non-compliant
```

**Additional Evaluations**:
- COST04-BP04: Check for automated decommissioning (Lambda functions with "cleanup" or "decommission" in name)
- COST07-BP02: Check region selection (compare costs across regions using Cost Explorer)
- COST09-BP02: Check for throttling (API Gateway throttling settings)

### Component 2: Performance Efficiency Evaluator

**Location**: `lambda/evaluators/performance/handler.py`

**Methods to Implement**:

```python
def _evaluate_perf01_bp01_instance_diversity(self) -> Dict[str, Any]:
    """Check for diverse instance types"""
    # Query: ec2.describe_instances()
    # COMPLIANT: len(unique_instance_types) >= 5
    # Evidence: "{count} different instance types: {types}"
    # Severity: MEDIUM if non-compliant
    
def _evaluate_perf02_bp01_compute_options(self) -> Dict[str, Any]:
    """Check for multiple compute options"""
    # Query: ec2.describe_instances(), lambda_client.list_functions()
    # COMPLIANT: has_ec2 and has_lambda
    # Evidence: "Using EC2 and Lambda"
    # Severity: MEDIUM if only one
    
def _evaluate_perf03_bp01_data_stores(self) -> Dict[str, Any]:
    """Check for purpose-built data stores"""
    # Query: s3.list_buckets(), dynamodb.list_tables(), rds.describe_db_instances()
    # COMPLIANT: len(data_store_types) >= 2
    # Evidence: "Using: {store_types}"
    # Severity: MEDIUM if only one
    
def _evaluate_perf03_bp05_caching(self) -> Dict[str, Any]:
    """Check if caching is implemented"""
    # Query: elasticache.describe_cache_clusters()
    # COMPLIANT: len(cache_clusters) > 0
    # Evidence: "{count} cache cluster(s)"
    # Severity: MEDIUM if non-compliant
    
def _evaluate_perf04_bp01_vpc_networking(self) -> Dict[str, Any]:
    """Check VPC configuration"""
    # Query: ec2.describe_vpcs()
    # COMPLIANT: len(vpcs) > 0
    # Evidence: "{count} VPC(s) configured"
    # Severity: LOW
    
def _evaluate_perf04_bp04_load_balancing(self) -> Dict[str, Any]:
    """Check for load balancing"""
    # Query: elbv2.describe_load_balancers()
    # COMPLIANT: len(load_balancers) > 0
    # Evidence: "{count} load balancer(s)"
    # Severity: MEDIUM if non-compliant
    
def _evaluate_perf04_bp05_vpc_endpoints(self) -> Dict[str, Any]:
    """Check for VPC endpoints (PrivateLink)"""
    # Query: ec2.describe_vpc_endpoints()
    # COMPLIANT: len(vpc_endpoints) > 0
    # Evidence: "{count} VPC endpoint(s)"
    # Severity: LOW
```

**Additional Evaluations**:
- PERF02-BP05: Check for dynamic scaling (Auto Scaling policies)
- PERF03-BP04: Check for read replicas (RDS read replicas)
- PERF04-BP06: Check for CloudFront distributions

### Component 3: Reliability Evaluator

**Location**: `lambda/evaluators/reliability/handler.py`

**Methods to Implement**:

```python
def _evaluate_rel02_bp01_network_connectivity(self) -> Dict[str, Any]:
    """Check for redundant network connectivity"""
    # Query: ec2.describe_vpcs(), ec2.describe_nat_gateways()
    # COMPLIANT: len(nat_gateways) >= 2 (multi-AZ)
    # Evidence: "{count} NAT gateway(s) across AZs"
    # Severity: HIGH if non-compliant
    
def _evaluate_rel06_bp01_monitoring(self) -> Dict[str, Any]:
    """Check if monitoring is configured"""
    # Query: cloudwatch.describe_alarms()
    # COMPLIANT: len(alarms) > 0
    # Evidence: "{count} CloudWatch alarm(s)"
    # Severity: CRITICAL if non-compliant
    
def _evaluate_rel07_bp01_auto_scaling(self) -> Dict[str, Any]:
    """Check for auto scaling"""
    # Query: autoscaling.describe_auto_scaling_groups()
    # COMPLIANT: len(asgs_with_policies) > 0
    # Evidence: "{count} ASG(s) with scaling policies"
    # Severity: HIGH if non-compliant
    
def _evaluate_rel09_bp01_backups(self) -> Dict[str, Any]:
    """Check if backups are configured"""
    # Query: backup.list_backup_plans()
    # COMPLIANT: len(backup_plans) > 0
    # Evidence: "{count} backup plan(s)"
    # Severity: CRITICAL if non-compliant
    
def _evaluate_rel09_bp03_automated_backups(self) -> Dict[str, Any]:
    """Check for automated backups"""
    # Query: rds.describe_db_instances(), dynamodb.describe_continuous_backups()
    # COMPLIANT: all databases have automated backups enabled
    # Evidence: "{count}/{total} databases with automated backups"
    # Severity: CRITICAL if non-compliant
    
def _evaluate_rel10_bp01_multi_location(self) -> Dict[str, Any]:
    """Check for multi-region deployment"""
    # Query: ec2.describe_instances() across regions
    # COMPLIANT: resources in >= 2 regions
    # Evidence: "Resources in {count} region(s): {regions}"
    # Severity: HIGH if non-compliant
    
def _evaluate_rel11_bp02_health_checks(self) -> Dict[str, Any]:
    """Check for health checks and failover"""
    # Query: route53.list_health_checks()
    # COMPLIANT: len(health_checks) > 0
    # Evidence: "{count} Route53 health check(s)"
    # Severity: HIGH if non-compliant
    
def _evaluate_rel11_bp03_auto_healing(self) -> Dict[str, Any]:
    """Check for auto healing"""
    # Query: autoscaling.describe_auto_scaling_groups(), ecs.describe_services()
    # COMPLIANT: ASGs or ECS services with health checks
    # Evidence: "{count} resource(s) with auto healing"
    # Severity: HIGH if non-compliant
```

**Additional Evaluations**:
- REL02-BP03: Check subnet allocation (VPC CIDR blocks)
- REL06-BP03: Check for SNS topics (notifications)
- REL09-BP02: Check backup encryption

### Component 4: Operational Excellence Evaluator

**Location**: `lambda/evaluators/operational_excellence/handler.py`

**Methods to Implement**:

```python
def _evaluate_ops04_bp02_application_telemetry(self) -> Dict[str, Any]:
    """Check for application logging"""
    # Query: logs.describe_log_groups()
    # COMPLIANT: len(log_groups) > 0
    # Evidence: "{count} CloudWatch log group(s)"
    # Severity: HIGH if non-compliant
    
def _evaluate_ops05_bp01_version_control(self) -> Dict[str, Any]:
    """Check for version control"""
    # Query: codecommit.list_repositories()
    # COMPLIANT: len(repositories) > 0
    # Evidence: "{count} CodeCommit repository(ies)"
    # Severity: MEDIUM if non-compliant
    
def _evaluate_ops05_bp04_deployment_systems(self) -> Dict[str, Any]:
    """Check for CI/CD pipelines"""
    # Query: codepipeline.list_pipelines()
    # COMPLIANT: len(pipelines) > 0
    # Evidence: "{count} CodePipeline(s)"
    # Severity: MEDIUM if non-compliant
    
def _evaluate_ops06_bp04_automated_rollback(self) -> Dict[str, Any]:
    """Check for automated rollback"""
    # Query: codedeploy.list_deployment_configs()
    # COMPLIANT: deployment configs with automatic rollback
    # Evidence: "{count} deployment config(s) with rollback"
    # Severity: MEDIUM if non-compliant
    
def _evaluate_ops08_bp01_custom_metrics(self) -> Dict[str, Any]:
    """Check for custom metrics"""
    # Query: cloudwatch.list_metrics(Namespace='Custom')
    # COMPLIANT: len(custom_metrics) > 0
    # Evidence: "{count} custom metric(s)"
    # Severity: LOW
    
def _evaluate_ops08_bp02_log_insights(self) -> Dict[str, Any]:
    """Check for log analysis"""
    # Query: logs.describe_queries()
    # COMPLIANT: saved queries exist
    # Evidence: "{count} saved log query(ies)"
    # Severity: LOW
```

**Additional Evaluations**:
- OPS04-BP04: Check for X-Ray tracing
- OPS05-BP02: Check for automated testing (CodeBuild projects)
- OPS06-BP02: Check for deployment testing (CodeDeploy test configurations)

### Component 5: Sustainability Evaluator

**Location**: `lambda/evaluators/sustainability/handler.py`

**Methods to Implement**:

```python
def _evaluate_sus02_bp01_dynamic_scaling(self) -> Dict[str, Any]:
    """Check for dynamic scaling"""
    # Query: autoscaling.describe_auto_scaling_groups()
    # COMPLIANT: len(asgs) > 0
    # Evidence: "{count} ASG(s) for dynamic scaling"
    # Severity: MEDIUM if non-compliant
    
def _evaluate_sus02_bp03_unused_resources(self) -> Dict[str, Any]:
    """Check for unused resources"""
    # Query: ec2.describe_instances(stopped), rds.describe_db_instances(stopped), ec2.describe_volumes(available)
    # NON_COMPLIANT: any unused resources found
    # Evidence: "{count} unused resource(s): {details}"
    # Severity: MEDIUM
    
def _evaluate_sus03_bp02_unused_functions(self) -> Dict[str, Any]:
    """Check for unused Lambda functions"""
    # Query: lambda_client.list_functions(), cloudwatch.get_metric_statistics(Invocations, last 30 days)
    # NON_COMPLIANT: functions with zero invocations
    # Evidence: "{count} function(s) with no invocations in 30 days"
    # Severity: LOW
    
def _evaluate_sus04_bp03_lifecycle_policies(self) -> Dict[str, Any]:
    """Check for S3 lifecycle policies"""
    # Query: s3.get_bucket_lifecycle_configuration()
    # COMPLIANT: buckets with lifecycle policies
    # Evidence: "{count}/{total} bucket(s) with lifecycle policies"
    # Severity: MEDIUM if non-compliant
    
def _evaluate_sus04_bp05_intelligent_tiering(self) -> Dict[str, Any]:
    """Check for S3 Intelligent-Tiering"""
    # Query: s3.get_bucket_intelligent_tiering_configuration()
    # COMPLIANT: buckets with intelligent tiering
    # Evidence: "{count} bucket(s) with intelligent tiering"
    # Severity: LOW
    
def _evaluate_sus05_bp01_right_sizing(self) -> Dict[str, Any]:
    """Check for over-provisioned instances"""
    # Query: ec2.describe_instances(), cloudwatch.get_metric_statistics(CPUUtilization, last 7 days)
    # NON_COMPLIANT: instances with <20% avg CPU
    # Evidence: "{count} under-utilized instance(s)"
    # Severity: MEDIUM
    
def _evaluate_sus05_bp03_managed_services(self) -> Dict[str, Any]:
    """Check for managed services usage"""
    # Query: rds.describe_db_instances(), dynamodb.list_tables(), lambda_client.list_functions()
    # COMPLIANT: using managed services
    # Evidence: "Using: {services}"
    # Severity: LOW
```

**Additional Evaluations**:
- SUS02-BP04: Check for regional optimization (resources in optimal regions)
- SUS04-BP07: Check for data transfer optimization (VPC endpoints, CloudFront)
- SUS05-BP04: Check for Graviton instances

### Component 6: Error Handling Module

**Common Error Handler**:

```python
def _handle_api_error(self, bp_id: str, error: Exception) -> Dict[str, Any]:
    """Handle AWS API errors gracefully"""
    error_code = error.response.get('Error', {}).get('Code', 'Unknown')
    
    if error_code == 'AccessDenied':
        return {
            'bp': bp_id,
            'description': BP_DESCRIPTIONS.get(bp_id, ''),
            'status': 'PENDING_REVIEW',
            'severity': 'MEDIUM',
            'finding': 'Insufficient permissions to evaluate',
            'evidence': f'AccessDenied: {str(error)}',
            'remediation': f'Grant required IAM permissions for {bp_id} evaluation',
            'risk': 'Unable to determine compliance'
        }
    else:
        return {
            'bp': bp_id,
            'description': BP_DESCRIPTIONS.get(bp_id, ''),
            'status': 'PENDING_REVIEW',
            'severity': 'MEDIUM',
            'finding': 'Unable to evaluate due to API error',
            'evidence': f'{error_code}: {str(error)}',
            'remediation': 'Check AWS service availability and permissions',
            'risk': 'Unable to determine compliance'
        }
```

## Data Models

### Finding Structure
```python
{
    'bp': str,              # BP ID (e.g., "COST01-BP03")
    'description': str,     # BP description from BP_DESCRIPTIONS
    'status': str,          # "COMPLIANT" | "NON_COMPLIANT" | "PENDING_REVIEW"
    'severity': str,        # "CRITICAL" | "HIGH" | "MEDIUM" | "LOW"
    'finding': str,         # Human-readable finding summary
    'evidence': str,        # Specific AWS resource data
    'remediation': str,     # Actionable steps to fix
    'risk': str            # Risk description
}
```

### Question Structure
```python
{
    'question_id': str,     # Question ID (e.g., "COST01")
    'title': {              # Bilingual title
        'es': str,
        'en': str
    },
    'description': {        # Bilingual description
        'es': str,
        'en': str
    },
    'score': float,         # 0-100 score
    'bps_evaluated': int,   # Number of BPs
    'status': str,          # Overall status
    'findings': List[Finding]
}
```

### Pillar Response Structure
```python
{
    'pillar_id': str,
    'region': str,
    'pillar_name': {'es': str, 'en': str},
    'description': {'es': str, 'en': str},
    'overall_score': float,
    'total_findings': int,
    'total_best_practices': int,
    'timestamp': str,
    'questions': List[Question],
    'compliance_distribution': {
        'compliant': int,
        'non_compliant': int,
        'pending_review': int
    },
    'severity_distribution': {
        'critical': int,
        'high': int,
        'medium': int,
        'low': int
    },
    # Optional for multi-region
    'regions': List[str],
    'multi_region': bool
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*


### Property Reflection

After analyzing all acceptance criteria, I identified several patterns of redundancy:

1. **API Query Properties (1.1-1.8, 2.1-2.7, 3.1-3.8, 4.1-4.6, 5.1-5.7)**: Each individual BP evaluation follows the same pattern: query AWS API, evaluate condition, return status. Rather than having 30+ separate properties for each BP, these can be consolidated into a single property about the evaluation pattern.

2. **Validation Properties (1.9-1.11, 2.8-2.10, etc.)**: The requirements that "all evaluations SHALL include evidence", "all evaluations SHALL assign severity", and "all evaluations SHALL provide remediation" can be combined into a single comprehensive property about finding structure.

3. **Error Handling Properties (6.1-6.7)**: All error handling criteria test the same behavior with different error types. These can be consolidated into properties about error handling patterns.

4. **Multi-Region Properties (7.1-7.7)**: All multi-region criteria test aspects of the same aggregation logic. These can be consolidated.

5. **Caching Properties (8.1-8.7)**: All caching criteria test the cache lookup and storage logic. These can be consolidated.

After consolidation, the unique properties are:
- BP evaluation correctness (covers 1.1-1.8, 2.1-2.7, 3.1-3.8, 4.1-4.6, 5.1-5.7)
- Finding structure completeness (covers 1.9-1.11, 2.8-2.10, etc.)
- Error handling behavior (covers 6.1-6.7)
- Multi-region aggregation (covers 7.1-7.7)
- Cache behavior (covers 8.1-8.7)
- Response structure compatibility (covers 11.1-11.7)
- Severity assignment logic (covers 10.1-10.7)
- Remediation content (covers 9.1-9.7)

### Correctness Properties

**Property 1: BP Evaluation Correctness**
*For any* BP evaluation function and AWS API response, when the evaluation function processes the API response, the returned status SHALL be COMPLIANT if the condition is met, NON_COMPLIANT if the condition is not met, or PENDING_REVIEW if evaluation cannot be performed.
**Validates: Requirements 1.1-1.8, 2.1-2.7, 3.1-3.8, 4.1-4.6, 5.1-5.7**

**Property 2: Finding Structure Completeness**
*For any* BP evaluation result, the finding SHALL contain all required fields (bp, description, status, severity, finding, evidence, remediation, risk) with non-empty values.
**Validates: Requirements 1.9-1.11, 2.8-2.10, 3.9-3.11, 4.7-4.9, 5.8-5.10**

**Property 3: Severity Value Validity**
*For any* finding, the severity field SHALL be one of the valid values: CRITICAL, HIGH, MEDIUM, or LOW.
**Validates: Requirements 1.10, 2.9, 3.10, 4.8, 5.9, 10.1-10.7**

**Property 4: Status Value Validity**
*For any* finding, the status field SHALL be one of the valid values: COMPLIANT, NON_COMPLIANT, or PENDING_REVIEW.
**Validates: Requirements 1.1-1.8, 2.1-2.7, 3.1-3.8, 4.1-4.6, 5.1-5.7**

**Property 5: Error Handling Graceful Degradation**
*For any* BP evaluation that encounters an AWS API error, the evaluation SHALL return PENDING_REVIEW status with error details in the evidence field, and SHALL NOT raise an exception that fails the entire pillar evaluation.
**Validates: Requirements 6.1-6.7**

**Property 6: AccessDenied Error Handling**
*For any* BP evaluation that encounters an AccessDenied error, the returned finding SHALL have status PENDING_REVIEW, evidence containing "AccessDenied", and remediation mentioning required IAM permissions.
**Validates: Requirements 6.1-6.3**

**Property 7: Multi-Region Aggregation Correctness**
*For any* set of findings from multiple regions, if any region has NON_COMPLIANT status, the aggregated status SHALL be NON_COMPLIANT; if all regions have COMPLIANT status, the aggregated status SHALL be COMPLIANT; otherwise PENDING_REVIEW.
**Validates: Requirements 7.2-7.4**

**Property 8: Multi-Region Evidence Inclusion**
*For any* multi-region evaluation, each finding SHALL include region information in the evidence or as a separate field.
**Validates: Requirements 7.5**

**Property 9: Cache Freshness Check**
*For any* evaluation request, if cached results exist with timestamp less than 5 minutes old, the system SHALL return cached results; if cached results are older than 5 minutes or don't exist, the system SHALL perform a new evaluation.
**Validates: Requirements 8.1-8.3**

**Property 10: Cache Storage Completeness**
*For any* completed evaluation, the system SHALL store the results in DynamoDB with session_id, evaluation_id (pillar#timestamp), pillar_id, timestamp, and data fields.
**Validates: Requirements 8.4-8.7**

**Property 11: Response Structure Compatibility**
*For any* pillar evaluation response, the JSON structure SHALL contain all required fields: pillar_id, region, pillar_name, description, overall_score, total_findings, total_best_practices, timestamp, questions, compliance_distribution, and severity_distribution.
**Validates: Requirements 11.1-11.7**

**Property 12: Question Structure Validity**
*For any* question in a pillar evaluation, the question SHALL contain question_id, title (bilingual), description (bilingual), score, bps_evaluated, status, and findings fields.
**Validates: Requirements 11.3**

**Property 13: Score Calculation Correctness**
*For any* set of findings in a question, the question score SHALL equal the weighted average of finding scores (COMPLIANT=100, NON_COMPLIANT=0, PENDING_REVIEW=50), and the pillar score SHALL equal the weighted average of question scores by BP count.
**Validates: Requirements 11.6**

**Property 14: Compliance Distribution Accuracy**
*For any* pillar evaluation, the compliance_distribution counts SHALL equal the sum of findings with each status (compliant, non_compliant, pending_review).
**Validates: Requirements 11.7**

**Property 15: Severity Distribution Accuracy**
*For any* pillar evaluation, the severity_distribution counts SHALL equal the sum of findings with each severity (critical, high, medium, low).
**Validates: Requirements 11.7**

**Property 16: Remediation Content for Non-Compliant Findings**
*For any* finding with NON_COMPLIANT status, the remediation field SHALL contain actionable steps including AWS service names and required actions.
**Validates: Requirements 9.1-9.4**

**Property 17: Remediation Content for Compliant Findings**
*For any* finding with COMPLIANT status, the remediation field SHALL state "Current state compliant" or similar affirmative message.
**Validates: Requirements 9.6**

**Property 18: Remediation Content for Pending Review Findings**
*For any* finding with PENDING_REVIEW status, the remediation field SHALL explain why manual review is required or what permissions are needed.
**Validates: Requirements 9.7**

**Property 19: Evidence Specificity**
*For any* finding with COMPLIANT or NON_COMPLIANT status, the evidence field SHALL contain specific AWS resource data such as counts, ARNs, or configuration details.
**Validates: Requirements 1.9, 2.8, 3.9, 4.7, 5.8**

**Property 20: Manual Review BP Identification**
*For any* BP that requires organizational or architectural decisions (as defined in the BP descriptions), the evaluation SHALL return PENDING_REVIEW status with an explanation.
**Validates: Requirements 1.12, 2.11, 3.12, 4.10, 5.11**

## Error Handling

### Error Categories

1. **Permission Errors (AccessDenied)**
   - Return PENDING_REVIEW status
   - Include error details in evidence
   - Provide IAM permission requirements in remediation
   - Log error for debugging
   - Continue with remaining evaluations

2. **Service Unavailability Errors**
   - Return PENDING_REVIEW status
   - Include error code and message in evidence
   - Suggest checking service availability in remediation
   - Log error for debugging
   - Continue with remaining evaluations

3. **Invalid Credentials**
   - Return 401 Unauthorized at handler level
   - Do not attempt evaluation
   - Provide clear error message

4. **DynamoDB Errors**
   - Log error but continue evaluation
   - Skip caching if DynamoDB unavailable
   - Return fresh evaluation results

5. **Unexpected Errors**
   - Return PENDING_REVIEW for affected BP
   - Include error details in evidence
   - Log full stack trace
   - Continue with remaining evaluations

### Error Handling Pattern

```python
try:
    # AWS API call
    result = client.some_api_call()
    # Evaluation logic
    return create_finding(...)
except ClientError as e:
    error_code = e.response.get('Error', {}).get('Code', 'Unknown')
    if error_code == 'AccessDenied':
        return {
            'bp': bp_id,
            'status': 'PENDING_REVIEW',
            'severity': 'MEDIUM',
            'finding': 'Insufficient permissions',
            'evidence': f'AccessDenied: {str(e)}',
            'remediation': f'Grant {service}:{action} permission',
            'risk': 'Unable to determine'
        }
    else:
        return {
            'bp': bp_id,
            'status': 'PENDING_REVIEW',
            'severity': 'MEDIUM',
            'finding': 'API error during evaluation',
            'evidence': f'{error_code}: {str(e)}',
            'remediation': 'Check service availability and permissions',
            'risk': 'Unable to determine'
        }
except Exception as e:
    logger.exception(f"Unexpected error evaluating {bp_id}")
    return {
        'bp': bp_id,
        'status': 'PENDING_REVIEW',
        'severity': 'MEDIUM',
        'finding': 'Unexpected error',
        'evidence': str(e),
        'remediation': 'Contact support',
        'risk': 'Unable to determine'
    }
```

## Testing Strategy

### Dual Testing Approach

This feature requires both unit tests and property-based tests:

**Unit Tests**: Verify specific examples and edge cases
- Test specific BP evaluation with known AWS API responses
- Test error handling with specific error codes
- Test cache hit/miss scenarios
- Test multi-region aggregation with specific region sets
- Test score calculation with known finding sets

**Property-Based Tests**: Verify universal properties across all inputs
- Generate random AWS API responses and verify evaluation logic
- Generate random error types and verify graceful handling
- Generate random finding sets and verify score calculations
- Generate random region sets and verify aggregation
- Generate random timestamps and verify cache behavior

### Property Test Configuration

- Use `hypothesis` library for Python property-based testing
- Configure each property test to run minimum 100 iterations
- Tag each test with feature name and property number
- Example tag: `# Feature: implement-real-bp-evaluations, Property 1: BP Evaluation Correctness`

### Test Coverage Goals

- Unit test coverage: 80%+ for evaluation logic
- Property test coverage: All 20 correctness properties
- Integration tests: End-to-end evaluation for each pillar
- Error injection tests: All error handling paths

### Example Property Test

```python
from hypothesis import given, strategies as st
import pytest

@given(
    budgets_count=st.integers(min_value=0, max_value=100),
    api_error=st.one_of(st.none(), st.sampled_from(['AccessDenied', 'ServiceUnavailable']))
)
def test_cost01_bp03_evaluation_correctness(budgets_count, api_error):
    """
    Feature: implement-real-bp-evaluations
    Property 1: BP Evaluation Correctness
    
    For any AWS Budgets API response, the evaluation should return:
    - COMPLIANT if budgets exist and no error
    - NON_COMPLIANT if no budgets and no error
    - PENDING_REVIEW if API error occurs
    """
    # Mock AWS API response
    if api_error:
        mock_response = create_error_response(api_error)
    else:
        mock_response = create_budgets_response(budgets_count)
    
    # Execute evaluation
    result = evaluate_cost01_bp03(mock_response)
    
    # Verify correctness
    if api_error:
        assert result['status'] == 'PENDING_REVIEW'
        assert api_error in result['evidence']
    elif budgets_count > 0:
        assert result['status'] == 'COMPLIANT'
        assert str(budgets_count) in result['evidence']
    else:
        assert result['status'] == 'NON_COMPLIANT'
        assert 'No budgets' in result['finding']
```

### Example Unit Test

```python
def test_cost01_bp03_with_budgets():
    """Test COST01-BP03 evaluation when budgets exist"""
    # Arrange
    mock_session = create_mock_session()
    mock_budgets_response = {
        'Budgets': [
            {'BudgetName': 'Monthly', 'BudgetLimit': {'Amount': '1000'}},
            {'BudgetName': 'Quarterly', 'BudgetLimit': {'Amount': '3000'}}
        ]
    }
    mock_session.client('budgets').describe_budgets.return_value = mock_budgets_response
    
    evaluator = CostOptimizationEvaluator(mock_session, 'us-east-1')
    
    # Act
    result = evaluator._evaluate_cost01_bp03_budgets()
    
    # Assert
    assert result['status'] == 'COMPLIANT'
    assert result['severity'] == 'LOW'
    assert '2 budget(s)' in result['evidence']
    assert 'Current state compliant' in result['remediation']
```

## Implementation Notes

### Code Organization

Each pillar evaluator will follow this structure:
1. Keep existing `_evaluate_<question>()` methods
2. Add specific evaluation methods for high-impact BPs
3. Update question evaluation to call specific methods instead of `_create_pending()`
4. Keep `_create_pending()` for BPs requiring manual review
5. Add `_handle_api_error()` method for consistent error handling

### Incremental Implementation

Implement in priority order:
1. Cost Optimization (highest business value)
2. Performance Efficiency (performance impact)
3. Reliability (availability impact)
4. Operational Excellence (operational efficiency)
5. Sustainability (environmental impact)

For each pillar:
1. Implement 30-40% of BPs with highest impact
2. Test thoroughly with unit and property tests
3. Deploy and validate
4. Gather feedback
5. Iterate on remaining BPs

### AWS Service Clients Required

- **Cost**: budgets, organizations, ce (Cost Explorer), ec2, elbv2, autoscaling, lambda
- **Performance**: ec2, lambda, s3, dynamodb, rds, elasticache, elbv2
- **Reliability**: ec2, cloudwatch, autoscaling, backup, route53, ecs
- **Operational Excellence**: logs, codecommit, codepipeline, codedeploy, cloudwatch
- **Sustainability**: ec2, rds, s3, lambda, cloudwatch, autoscaling

### IAM Permissions Required

Each evaluation requires read-only permissions for the services it queries. Document required permissions in remediation messages when AccessDenied errors occur.

Example permissions for Cost Optimization:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "budgets:DescribeBudgets",
        "organizations:DescribeOrganization",
        "ce:GetCostAndUsage",
        "ec2:DescribeInstances",
        "ec2:DescribeReservedInstances",
        "elasticloadbalancing:DescribeLoadBalancers",
        "autoscaling:DescribeAutoScalingGroups",
        "lambda:ListFunctions"
      ],
      "Resource": "*"
    }
  ]
}
```

### Performance Considerations

1. **API Call Optimization**
   - Batch API calls where possible
   - Use pagination efficiently
   - Limit results to reasonable numbers (e.g., first 100 resources)
   - Cache results in memory during single evaluation

2. **Timeout Management**
   - Lambda timeout: 5 minutes (current)
   - Individual API call timeout: 30 seconds
   - Total evaluation time target: < 2 minutes per pillar

3. **Multi-Region Optimization**
   - Evaluate regions in parallel where possible
   - Skip regions with no resources
   - Aggregate efficiently

4. **DynamoDB Caching**
   - 5-minute cache reduces redundant API calls
   - Use conditional writes to avoid race conditions
   - Query efficiently with partition key (session_id) and sort key (evaluation_id)

### Backward Compatibility

All changes maintain backward compatibility:
- Response structure unchanged
- Existing PENDING_REVIEW BPs remain unchanged
- New real evaluations replace PENDING_REVIEW with actual status
- Frontend requires no changes
- API contract unchanged

### Deployment Strategy

1. Deploy to development environment
2. Test with real AWS accounts
3. Validate response format compatibility
4. Deploy to staging
5. Perform load testing
6. Deploy to production with monitoring
7. Monitor error rates and performance
8. Iterate based on feedback
