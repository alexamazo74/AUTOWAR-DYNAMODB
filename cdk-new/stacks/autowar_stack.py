"""
AutoWAR Main Stack - Serverless Architecture
"""

from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    aws_s3 as s3,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_lambda as lambda_,
    aws_apigateway as apigw,
    aws_dynamodb as dynamodb,
    aws_secretsmanager as secretsmanager,
    aws_iam as iam,
    aws_kms as kms,
    aws_stepfunctions as sfn,
    aws_stepfunctions_tasks as tasks,
)
from constructs import Construct
import json


class AutoWARStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # KMS Key for encryption
        kms_key = kms.Key(
            self, "AutoWARKey",
            description="AutoWAR encryption key",
            enable_key_rotation=True,
            removal_policy=RemovalPolicy.DESTROY
        )
        
        kms_key.add_alias("alias/autowar-secrets")

        # Frontend: S3 + CloudFront
        frontend_bucket = s3.Bucket(
            self, "FrontendBucket",
            public_read_access=False,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True
        )

        # Origin Access Identity for CloudFront
        oai = cloudfront.OriginAccessIdentity(
            self, "OAI",
            comment="OAI for AutoWAR frontend"
        )
        
        # Grant CloudFront read access to S3
        frontend_bucket.grant_read(oai)

        distribution = cloudfront.Distribution(
            self, "CDN",
            default_root_object="index.html",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3Origin(
                    frontend_bucket,
                    origin_access_identity=oai
                ),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                cache_policy=cloudfront.CachePolicy.CACHING_OPTIMIZED
            ),
            error_responses=[
                cloudfront.ErrorResponse(
                    http_status=403,
                    response_http_status=200,
                    response_page_path="/index.html",
                    ttl=Duration.minutes(0)
                ),
                cloudfront.ErrorResponse(
                    http_status=404,
                    response_http_status=200,
                    response_page_path="/index.html",
                    ttl=Duration.minutes(0)
                )
            ]
        )

        # DynamoDB Table for evaluations (session-based, temporary)
        evaluations_table = dynamodb.Table(
            self, "EvaluationsTable",
            partition_key=dynamodb.Attribute(
                name="session_id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="evaluation_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            point_in_time_recovery=True,
            encryption=dynamodb.TableEncryption.AWS_MANAGED,
            time_to_live_attribute="ttl",
            removal_policy=RemovalPolicy.DESTROY
        )

        # DynamoDB Table for historical evaluations (persistent)
        historical_evaluations_table = dynamodb.Table(
            self, "HistoricalEvaluationsTable",
            table_name="AutoWAR-Evaluations",
            partition_key=dynamodb.Attribute(
                name="accountId",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            point_in_time_recovery=True,
            encryption=dynamodb.TableEncryption.AWS_MANAGED,
            removal_policy=RemovalPolicy.DESTROY
        )

        # S3 Bucket for reports storage
        reports_bucket = s3.Bucket(
            self, "ReportsBucket",
            public_read_access=False,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            versioned=True,
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="DeleteOldReports",
                    enabled=True,
                    expiration=Duration.days(30)
                )
            ],
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            cors=[
                s3.CorsRule(
                    allowed_methods=[s3.HttpMethods.GET, s3.HttpMethods.HEAD],
                    allowed_origins=["*"],
                    allowed_headers=["*"],
                    max_age=3600
                )
            ]
        )

        # Lambda Layer (common code)
        common_layer = lambda_.LayerVersion(
            self, "CommonLayer",
            code=lambda_.Code.from_asset("../lambda/layers/common"),
            compatible_runtimes=[lambda_.Runtime.PYTHON_3_11],
            description="AutoWAR common utilities"
        )

        # Lambda Layer (reports - openpyxl, python-docx, matplotlib)
        reports_layer = lambda_.LayerVersion(
            self, "ReportsLayer",
            code=lambda_.Code.from_asset("../lambda/layers/reports"),
            compatible_runtimes=[lambda_.Runtime.PYTHON_3_11],
            description="Report generation libraries"
        )

        # Lambda: Credential Validator
        credential_validator_fn = lambda_.Function(
            self, "CredentialValidatorFunction",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="handler.lambda_handler",
            code=lambda_.Code.from_asset("../lambda/credential_validator"),
            timeout=Duration.seconds(30),
            memory_size=256,
            layers=[common_layer],
            environment={
                "KMS_KEY_ID": kms_key.key_id,
                "HISTORICAL_TABLE": historical_evaluations_table.table_name
            }
        )

        # Grant permissions
        kms_key.grant_encrypt_decrypt(credential_validator_fn)
        historical_evaluations_table.grant_read_data(credential_validator_fn)
        credential_validator_fn.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "secretsmanager:CreateSecret",
                    "secretsmanager:GetSecretValue",
                    "secretsmanager:DeleteSecret",
                    "secretsmanager:TagResource"
                ],
                resources=["arn:aws:secretsmanager:*:*:secret:autowar/sessions/*"]
            )
        )

        # API Gateway
        api = apigw.RestApi(
            self, "AutoWAR-API",
            rest_api_name="AutoWAR API",
            description="AutoWAR Serverless API",
            deploy_options=apigw.StageOptions(
                throttling_rate_limit=100,
                throttling_burst_limit=200,
                logging_level=apigw.MethodLoggingLevel.INFO,
                tracing_enabled=True
            ),
            default_cors_preflight_options=apigw.CorsOptions(
                allow_origins=apigw.Cors.ALL_ORIGINS,
                allow_methods=apigw.Cors.ALL_METHODS,
                allow_headers=["*"]
            )
        )

        # Lambda: Unified Evaluator (handles all pillars)
        unified_evaluator_fn = lambda_.Function(
            self, "UnifiedEvaluatorFunction",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="unified_handler.lambda_handler",
            code=lambda_.Code.from_asset("../lambda/evaluators"),
            timeout=Duration.minutes(10),  # Increased from 5 to 10 minutes for multi-region support
            memory_size=1024,
            layers=[common_layer],
            environment={
                "DYNAMODB_TABLE": evaluations_table.table_name,
                "HISTORICAL_TABLE": historical_evaluations_table.table_name
            }
        )

        # Lambda: Store Evaluation
        store_evaluation_fn = lambda_.Function(
            self, "StoreEvaluationFunction",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="handler.lambda_handler",
            code=lambda_.Code.from_asset("../lambda/store_evaluation"),
            timeout=Duration.seconds(30),
            memory_size=256,
            layers=[common_layer],
            environment={
                "HISTORICAL_TABLE": historical_evaluations_table.table_name
            }
        )

        # Lambda: Evaluation Orchestrator (starts Step Functions)
        evaluation_orchestrator_fn = lambda_.Function(
            self, "EvaluationOrchestratorFunction",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="handler.lambda_handler",
            code=lambda_.Code.from_asset("../lambda/evaluation_orchestrator"),
            timeout=Duration.seconds(30),
            memory_size=256,
            layers=[common_layer],
            environment={
                "EVALUATIONS_TABLE": evaluations_table.table_name,
                "STATE_MACHINE_ARN": ""  # Will be set after Step Functions creation
            }
        )

        # Lambda: Evaluation Status (queries evaluation status)
        evaluation_status_fn = lambda_.Function(
            self, "EvaluationStatusFunction",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="handler.lambda_handler",
            code=lambda_.Code.from_asset("../lambda/evaluation_status"),
            timeout=Duration.seconds(10),
            memory_size=128,
            layers=[common_layer],
            environment={
                "EVALUATIONS_TABLE": evaluations_table.table_name
            }
        )

        # Lambda: Report Manager
        report_manager_fn = lambda_.Function(
            self, "ReportManagerFunction",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="handler.lambda_handler",
            code=lambda_.Code.from_asset("../lambda/report_manager"),
            timeout=Duration.seconds(30),
            memory_size=512,
            layers=[common_layer],
            environment={
                "HISTORICAL_TABLE": historical_evaluations_table.table_name,
                "REPORTS_BUCKET": reports_bucket.bucket_name,
                "TECHNICAL_REPORT_FUNCTION": "",  # Will be set after creation
                "EXECUTIVE_REPORT_FUNCTION": ""   # Will be set after creation
            }
        )

        # Lambda: Technical Report Generator
        technical_report_fn = lambda_.Function(
            self, "TechnicalReportFunction",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="handler.lambda_handler",
            code=lambda_.Code.from_asset("../lambda/report_generator_technical"),
            timeout=Duration.minutes(5),
            memory_size=1024,
            layers=[common_layer, reports_layer],
            environment={
                "REPORTS_BUCKET": reports_bucket.bucket_name
            }
        )

        # Lambda: Executive Report Generator
        executive_report_fn = lambda_.Function(
            self, "ExecutiveReportFunction",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="handler.lambda_handler",
            code=lambda_.Code.from_asset("../lambda/report_generator_executive"),
            timeout=Duration.minutes(5),
            memory_size=1024,
            layers=[common_layer, reports_layer],
            environment={
                "REPORTS_BUCKET": reports_bucket.bucket_name
            }
        )

        # Lambda: Save Evaluation Results (called by Step Functions)
        save_evaluation_results_fn = lambda_.Function(
            self, "SaveEvaluationResultsFunction",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="handler.lambda_handler",
            code=lambda_.Code.from_asset("../lambda/save_evaluation_results"),
            timeout=Duration.seconds(30),
            memory_size=256,
            layers=[common_layer],
            environment={
                "EVALUATIONS_TABLE": evaluations_table.table_name
            }
        )

        # Step Functions: Evaluation State Machine
        # Define tasks for each pillar
        pillars = ['security', 'performance', 'cost', 'reliability', 'operational_excellence', 'sustainability']
        
        pillar_tasks = []
        for pillar in pillars:
            task = tasks.LambdaInvoke(
                self, f"Evaluate{pillar.title().replace('_', '')}",
                lambda_function=unified_evaluator_fn,
                payload=sfn.TaskInput.from_object({
                    "pathParameters": {"pillar": pillar},
                    "headers": {
                        "X-Session-ID": sfn.JsonPath.string_at("$.session_id")
                    },
                    "body": sfn.JsonPath.json_to_string(
                        sfn.JsonPath.object_at("$")
                    )
                }),
                output_path="$.Payload",
                retry_on_service_exceptions=False  # Disable auto-retry to avoid long waits
            )
            # Add explicit retry with limited attempts
            task.add_retry(
                errors=["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException"],
                interval=Duration.seconds(2),
                max_attempts=1,
                backoff_rate=2
            )
            # Add catch to handle failures gracefully
            task.add_catch(
                handler=sfn.Pass(self, f"Catch{pillar.title().replace('_', '')}",
                    result=sfn.Result.from_object({
                        "statusCode": 500,
                        "body": json.dumps({"error": f"Evaluation failed for {pillar}", "pillar_id": pillar})
                    })
                ),
                result_path="$.Payload"
            )
            pillar_tasks.append(task)
        
        # Create parallel state for all pillars
        parallel_evaluation = sfn.Parallel(
            self, "EvaluateAllPillars",
            result_path="$.pillar_results"
        )
        
        for task in pillar_tasks:
            parallel_evaluation.branch(task)
        
        # Save results task
        save_results_task = tasks.LambdaInvoke(
            self, "SaveEvaluationResults",
            lambda_function=save_evaluation_results_fn,
            payload=sfn.TaskInput.from_object({
                "session_id": sfn.JsonPath.string_at("$.session_id"),
                "evaluation_id": sfn.JsonPath.string_at("$.evaluation_id"),
                "timestamp": sfn.JsonPath.string_at("$.timestamp"),
                "pillar_results": sfn.JsonPath.object_at("$.pillar_results")
            }),
            result_path=sfn.JsonPath.DISCARD
        )
        
        # Define state machine
        definition = parallel_evaluation.next(save_results_task)
        
        evaluation_state_machine = sfn.StateMachine(
            self, "EvaluationStateMachine",
            definition=definition,
            timeout=Duration.hours(1),
            tracing_enabled=True
        )
        
        # Update orchestrator environment with state machine ARN
        evaluation_orchestrator_fn.add_environment("STATE_MACHINE_ARN", evaluation_state_machine.state_machine_arn)
        
        # Grant permissions to orchestrator to start executions
        evaluation_state_machine.grant_start_execution(evaluation_orchestrator_fn)
        
        # Grant permissions to Unified Evaluator
        kms_key.grant_encrypt_decrypt(unified_evaluator_fn)
        evaluations_table.grant_read_write_data(unified_evaluator_fn)
        historical_evaluations_table.grant_read_write_data(unified_evaluator_fn)
        unified_evaluator_fn.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "secretsmanager:GetSecretValue"
                ],
                resources=["arn:aws:secretsmanager:*:*:secret:autowar/sessions/*"]
            )
        )
        
        # Grant permissions to Store Evaluation
        historical_evaluations_table.grant_write_data(store_evaluation_fn)
        
        # Grant permissions to Save Evaluation Results
        evaluations_table.grant_read_write_data(save_evaluation_results_fn)
        
        # Grant permissions to Evaluation Orchestrator
        evaluations_table.grant_read_write_data(evaluation_orchestrator_fn)
        
        # Grant permissions to Evaluation Status
        evaluations_table.grant_read_write_data(evaluation_status_fn)
        
        # Allow Evaluation Status to check Step Functions execution status
        evaluation_state_machine.grant_read(evaluation_status_fn)
        
        # Grant permissions to Report Manager
        historical_evaluations_table.grant_read_data(report_manager_fn)
        reports_bucket.grant_read_write(report_manager_fn)
        
        # Grant permissions to Technical Report Generator
        reports_bucket.grant_read_write(technical_report_fn)
        
        # Grant permissions to Executive Report Generator
        reports_bucket.grant_read_write(executive_report_fn)
        
        # Allow Report Manager to invoke report generators
        technical_report_fn.grant_invoke(report_manager_fn)
        executive_report_fn.grant_invoke(report_manager_fn)
        
        # Update Report Manager environment with function names
        report_manager_fn.add_environment("TECHNICAL_REPORT_FUNCTION", technical_report_fn.function_name)
        report_manager_fn.add_environment("EXECUTIVE_REPORT_FUNCTION", executive_report_fn.function_name)
        
        # Grant read-only permissions for AWS service evaluations
        # These permissions allow the evaluator to assess customer infrastructure
        unified_evaluator_fn.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    # IAM - for identity and access management checks
                    "iam:GetAccountPasswordPolicy",
                    "iam:GetAccountSummary",
                    "iam:ListUsers",
                    "iam:ListRoles",
                    "iam:ListPolicies",
                    "iam:ListAccessKeys",
                    "iam:GetUser",
                    "iam:GetRole",
                    "iam:ListMFADevices",
                    "iam:ListUserPolicies",
                    "iam:ListAttachedUserPolicies",
                    "iam:ListRolePolicies",
                    "iam:ListAttachedRolePolicies",
                    
                    # Organizations - for account structure checks
                    "organizations:ListAccounts",
                    "organizations:DescribeOrganization",
                    
                    # CloudTrail - for logging and detection checks
                    "cloudtrail:DescribeTrails",
                    "cloudtrail:GetTrailStatus",
                    "cloudtrail:GetEventSelectors",
                    "cloudtrail:LookupEvents",
                    
                    # GuardDuty - for threat detection checks
                    "guardduty:ListDetectors",
                    "guardduty:GetDetector",
                    
                    # EC2 - for network and compute checks
                    "ec2:DescribeVpcs",
                    "ec2:DescribeSecurityGroups",
                    "ec2:DescribeInstances",
                    "ec2:DescribeVolumes",
                    "ec2:DescribeSnapshots",
                    "ec2:DescribeNetworkAcls",
                    "ec2:DescribeFlowLogs",
                    "ec2:DescribeSubnets",
                    "ec2:DescribeRouteTables",
                    
                    # VPC - for network protection checks
                    "ec2:DescribeVpcEndpoints",
                    "ec2:DescribeNatGateways",
                    
                    # KMS - for encryption checks
                    "kms:ListKeys",
                    "kms:DescribeKey",
                    "kms:GetKeyRotationStatus",
                    "kms:ListAliases",
                    
                    # S3 - for data protection checks
                    "s3:ListAllMyBuckets",
                    "s3:GetBucketEncryption",
                    "s3:GetBucketVersioning",
                    "s3:GetBucketPublicAccessBlock",
                    "s3:GetBucketLogging",
                    
                    # RDS - for database checks
                    "rds:DescribeDBInstances",
                    "rds:DescribeDBClusters",
                    "rds:DescribeDBSnapshots",
                    
                    # Lambda - for compute checks
                    "lambda:ListFunctions",
                    "lambda:GetFunction",
                    
                    # CloudWatch - for monitoring checks
                    "cloudwatch:DescribeAlarms",
                    "cloudwatch:GetMetricStatistics",
                    "cloudwatch:GetMetricData",
                    "cloudwatch:ListDashboards",
                    "logs:DescribeLogGroups",
                    
                    # Config - for compliance checks
                    "config:DescribeConfigurationRecorders",
                    "config:DescribeConfigurationRecorderStatus",
                    "config:DescribeDeliveryChannels",
                    
                    # ACM - for certificate checks
                    "acm:ListCertificates",
                    "acm:DescribeCertificate",
                    
                    # Secrets Manager - for secrets management checks
                    "secretsmanager:ListSecrets",
                    "secretsmanager:DescribeSecret",
                    
                    # Systems Manager - for operational excellence checks
                    "ssm:DescribeInstanceInformation",
                    "ssm:ListDocuments",
                    
                    # CloudFormation - for infrastructure as code checks
                    "cloudformation:ListStacks",
                    "cloudformation:DescribeStacks",
                    
                    # Backup - for reliability checks
                    "backup:ListBackupPlans",
                    "backup:ListBackupVaults",
                    
                    # Cost Explorer - for cost optimization checks
                    "ce:GetCostAndUsage",
                    "ce:GetCostForecast",
                    
                    # Budgets - for cost management checks
                    "budgets:DescribeBudgets",
                    
                    # Service Quotas - for reliability checks
                    "servicequotas:ListServiceQuotas",
                    "servicequotas:GetServiceQuota",
                    
                    # Compute Optimizer - for sustainability checks
                    "compute-optimizer:GetRecommendationSummaries",
                    "compute-optimizer:GetEC2InstanceRecommendations",
                    
                    # DynamoDB - for data storage checks
                    "dynamodb:ListTables",
                    "dynamodb:DescribeTable",
                    
                    # ELB - for load balancer checks
                    "elasticloadbalancing:DescribeLoadBalancers",
                    "elasticloadbalancing:DescribeTargetGroups",
                    "elasticloadbalancing:DescribeListeners",
                    
                    # Auto Scaling - for reliability/performance checks
                    "autoscaling:DescribeAutoScalingGroups",
                    "autoscaling:DescribePolicies",
                    "application-autoscaling:DescribeScalableTargets",
                    
                    # ElastiCache - for performance (caching) checks
                    "elasticache:DescribeCacheClusters",
                    "elasticache:DescribeReplicationGroups",
                    
                    # CloudFront - for performance (edge/CDN) checks
                    "cloudfront:ListDistributions",
                    "cloudfront:GetDistribution",
                    
                    # EC2 (VPN) - for performance (hybrid connectivity) checks
                    "ec2:DescribeVpnConnections",
                    
                    # Route53 - for DNS checks
                    "route53:ListHostedZones",
                    "route53:ListResourceRecordSets",
                    
                    # STS - for identity validation
                    "sts:GetCallerIdentity"
                ],
                resources=["*"]
            )
        )

        # API Resources
        credentials_resource = api.root.add_resource("credentials")
        validate_resource = credentials_resource.add_resource("validate")
        
        validate_resource.add_method(
            "POST",
            apigw.LambdaIntegration(credential_validator_fn)
        )

        # Evaluate resource
        evaluate_resource = api.root.add_resource("evaluate")
        pillar_resource = evaluate_resource.add_resource("{pillar}")
        
        pillar_resource.add_method(
            "POST",
            apigw.LambdaIntegration(unified_evaluator_fn),
            request_parameters={
                'method.request.path.pillar': True,
                'method.request.header.X-Session-ID': True
            }
        )

        # Store evaluation resource
        store_resource = api.root.add_resource("store-evaluation")
        store_resource.add_method(
            "POST",
            apigw.LambdaIntegration(store_evaluation_fn)
        )

        # Async evaluation resources
        evaluate_async_resource = evaluate_resource.add_resource("start")
        evaluate_async_resource.add_method(
            "POST",
            apigw.LambdaIntegration(evaluation_orchestrator_fn),
            request_parameters={
                'method.request.header.X-Session-ID': True
            }
        )
        
        # Evaluation status resource
        status_resource = evaluate_resource.add_resource("status")
        evaluation_id_resource = status_resource.add_resource("{evaluation_id}")
        evaluation_id_resource.add_method(
            "GET",
            apigw.LambdaIntegration(evaluation_status_fn),
            request_parameters={
                'method.request.path.evaluation_id': True,
                'method.request.header.X-Session-ID': True
            }
        )

        # Reports resources
        reports_resource = api.root.add_resource("reports")
        
        # GET /reports/list
        list_resource = reports_resource.add_resource("list")
        list_resource.add_method(
            "GET",
            apigw.LambdaIntegration(report_manager_fn)
        )
        
        # POST /reports/generate
        generate_resource = reports_resource.add_resource("generate")
        generate_resource.add_method(
            "POST",
            apigw.LambdaIntegration(report_manager_fn)
        )

        # Outputs
        self.add_output("FrontendBucketName", frontend_bucket.bucket_name)
        self.add_output("CloudFrontURL", f"https://{distribution.distribution_domain_name}")
        self.add_output("APIEndpoint", api.url)
        self.add_output("EvaluationsTableName", evaluations_table.table_name)
        self.add_output("HistoricalEvaluationsTableName", historical_evaluations_table.table_name)
        self.add_output("ReportsBucketName", reports_bucket.bucket_name)

    def add_output(self, id: str, value: str):
        from aws_cdk import CfnOutput
        CfnOutput(self, id, value=value)
