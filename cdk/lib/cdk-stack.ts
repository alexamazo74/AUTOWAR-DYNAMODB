import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as path from 'path';
import * as events from 'aws-cdk-lib/aws-events';
import * as targets from 'aws-cdk-lib/aws-events-targets';
import * as sqs from 'aws-cdk-lib/aws-sqs';
import * as lambdaEventSources from 'aws-cdk-lib/aws-lambda-event-sources';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as sns from 'aws-cdk-lib/aws-sns';
import * as apigateway from 'aws-cdk-lib/aws-apigateway';
import * as cognito from 'aws-cdk-lib/aws-cognito';
import { CfnOutput } from 'aws-cdk-lib';

export class AutoWarStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // DynamoDB tables required by the AutoWAR platform
    const tables: { [key: string]: dynamodb.Table } = {};

    const tableNames = [
      'autowar-clients',
      'autowar-evaluations',
      'autowar-waf-questions',
      'autowar-best-practices',
      'autowar-aws-resources',
      'autowar-remediation-tracking',
      'autowar-automation-config',
      'autowar-risks',
      'autowar-analysis-history',
      'autowar-comparative-analysis',
      'autowar-periodic-results',
      'autowar-evidence-technical',
      'autowar-ai-prompts-results',
      'autowar-industry-benchmarks',
      'autowar-notifications-log',
      'autowar-user-management',
      'autowar-aws-credentials',
    ];

    for (const name of tableNames) {
      tables[name] = new dynamodb.Table(this, `${name.replace(/-/g, '')}Table`, {
        tableName: name,
        partitionKey: { name: 'id', type: dynamodb.AttributeType.STRING },
        billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
        removalPolicy: cdk.RemovalPolicy.DESTROY,
      });
    }

    // Add useful GSIs for evaluations table to query by clientId and by account
    if (tables['autowar-evaluations']) {
      tables['autowar-evaluations'].addGlobalSecondaryIndex({
        indexName: 'clientIndex',
        partitionKey: { name: 'client_id', type: dynamodb.AttributeType.STRING },
        sortKey: { name: 'created_at', type: dynamodb.AttributeType.NUMBER },
        projectionType: dynamodb.ProjectionType.ALL,
      });
      tables['autowar-evaluations'].addGlobalSecondaryIndex({
        indexName: 'accountIndex',
        partitionKey: { name: 'account_id', type: dynamodb.AttributeType.STRING },
        sortKey: { name: 'created_at', type: dynamodb.AttributeType.NUMBER },
        projectionType: dynamodb.ProjectionType.ALL,
      });
    }

    // Add GSI for scores table to query by evaluation_id
    if (tables['autowar-scores']) {
      tables['autowar-scores'].addGlobalSecondaryIndex({
        indexName: 'evaluationIndex',
        partitionKey: { name: 'evaluation_id', type: dynamodb.AttributeType.STRING },
        sortKey: { name: 'created_at', type: dynamodb.AttributeType.STRING },
        projectionType: dynamodb.ProjectionType.ALL,
      });
    }

    // Tablas opcionales recomendadas con esquema PK/SK y GSIs específicos
    const reportsTable = new dynamodb.Table(this, 'AutowarReportsTable', {
      tableName: 'autowar-reports',
      partitionKey: { name: 'pk', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'sk', type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      timeToLiveAttribute: 'ttl',
    });
    reportsTable.addGlobalSecondaryIndex({
      indexName: 'evaluationIndex',
      partitionKey: { name: 'evaluationId', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'generated_at', type: dynamodb.AttributeType.NUMBER },
      projectionType: dynamodb.ProjectionType.ALL,
    });
    tables['autowar-reports'] = reportsTable;

    const auditTable = new dynamodb.Table(this, 'AutowarAuditLogTable', {
      tableName: 'autowar-audit-log',
      partitionKey: { name: 'pk', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'sk', type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });
    auditTable.addGlobalSecondaryIndex({
      indexName: 'actionIndex',
      partitionKey: { name: 'action', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'created_at', type: dynamodb.AttributeType.NUMBER },
      projectionType: dynamodb.ProjectionType.ALL,
    });
    tables['autowar-audit-log'] = auditTable;

    // If the scores table was created manually (outside CDK), import it so
    // we can call `grantReadWriteData` on it later. This makes grants idempotent
    // whether the table is managed by CDK or exists already.
    if (!tables['autowar-scores']) {
      try {
        // import by table name
        // cast to any to avoid strict typing issues since fromTableName returns ITable
        // and our `tables` map holds concrete Table objects in the creation path.
        // eslint-disable-next-line @typescript-eslint/ban-ts-comment
        // @ts-ignore
        tables['autowar-scores'] = dynamodb.Table.fromTableName(this, 'ImportedAutowarScoresTable', 'autowar-scores') as any;
      } catch (e) {
        // ignore import errors — grants will be no-ops if import fails
        console.warn('Could not import existing autowar-scores table:', e);
      }
    }

    // Precompute ARNs for the scores table so we can attach inline policies
    const scoresTableArn = `arn:aws:dynamodb:${this.region}:${this.account}:table/autowar-scores`;
    const scoresIndexArn = `${scoresTableArn}/index/*`;

    // Cognito User Pool for production authentication
    const userPool = new cognito.UserPool(this, 'AutoWarUserPool', {
      userPoolName: 'autowar-user-pool',
      selfSignUpEnabled: false,
      signInAliases: { email: true },
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    const userPoolClient = new cognito.UserPoolClient(this, 'AutoWarUserPoolClient', {
      userPool,
      generateSecret: false,
    });

    new CfnOutput(this, 'AutoWarUserPoolId', { value: userPool.userPoolId });
    new CfnOutput(this, 'AutoWarUserPoolClientId', { value: userPoolClient.userPoolClientId });

    // Funci�n Lambda
    const autoWarLambda = new lambda.Function(this, 'AutoWarLambda', {
      runtime: lambda.Runtime.NODEJS_18_X,
      handler: 'index.handler',
      code: lambda.Code.fromInline('exports.handler = async (event) => { return { statusCode: 200, body: JSON.stringify({ message: "AutoWAR funcionando!" }) }; }'),
      environment: {
        TABLE_NAME: tables['autowar-evaluations'].tableName,
      },
    });

    // Permisos para que Lambda acceda a DynamoDB
    // Grant the lambda access to evaluations and to credentials/user management tables
    tables['autowar-evaluations'].grantReadWriteData(autoWarLambda);
    tables['autowar-aws-credentials'].grantReadWriteData(autoWarLambda);
    tables['autowar-user-management'].grantReadWriteData(autoWarLambda);
    // Grant Lambda access to reports and audit log as well
    if (tables['autowar-reports']) {
      tables['autowar-reports'].grantReadWriteData(autoWarLambda);
    }
    if (tables['autowar-audit-log']) {
      tables['autowar-audit-log'].grantReadWriteData(autoWarLambda);
    }

    // Credentials maintenance Lambda: scans credentials, deletes expired secrets, flags rotation-due
    const credentialsMaintLambda = new lambda.Function(this, 'CredentialsMaintenanceLambda', {
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: 'lambdas.credentials_maintenance.handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '..', '..', 'src')),
      environment: {
        AUTOWAR_CREDENTIALS_TABLE: tables['autowar-aws-credentials'].tableName,
      },
      timeout: cdk.Duration.seconds(60),
    });

    // Grant access to credentials table and limited Secrets Manager permissions
    tables['autowar-aws-credentials'].grantReadWriteData(credentialsMaintLambda);
    // Restrict Secrets Manager access to secrets that follow the autowar-* prefix
    const secretsArn = `arn:aws:secretsmanager:${this.region}:${this.account}:secret:autowar-*`;
    credentialsMaintLambda.addToRolePolicy(new iam.PolicyStatement({
      actions: [
        'secretsmanager:DeleteSecret',
        'secretsmanager:DescribeSecret',
        'secretsmanager:GetSecretValue',
        'secretsmanager:PutSecretValue'
      ],
      resources: [secretsArn],
    }));
    // Allow creating and pruning IAM access keys for rotation (best-effort).
    // Tighten: restrict to IAM users that follow the `autowar-` naming convention
    // so rotation only affects managed service accounts. For customer-specific
    // users or roles consider granting scoped roles per-customer instead.
    const iamUsersArn = `arn:aws:iam::${this.account}:user/autowar-*`;
    credentialsMaintLambda.addToRolePolicy(new iam.PolicyStatement({
      actions: [
        'iam:CreateAccessKey',
        'iam:ListAccessKeys',
        'iam:DeleteAccessKey',
        'iam:UpdateAccessKey',
        'iam:GetUser'
      ],
      resources: [iamUsersArn],
    }));

    // Allow assuming roles that follow the autowar-* naming pattern across accounts
    // This permits the maintenance lambda to refresh AssumeRole-based credentials
    credentialsMaintLambda.addToRolePolicy(new iam.PolicyStatement({
      actions: ['sts:AssumeRole'],
      resources: [`arn:aws:iam::*:role/autowar-*`],
    }));

    // SNS topic to publish alerts when rotation fails or requires manual attention
    const alertsTopic = new sns.Topic(this, 'CredentialsAlertsTopic', {
      topicName: 'autowar-credentials-alerts',
      displayName: 'AutoWAR Credentials Alerts',
    });
    alertsTopic.grantPublish(credentialsMaintLambda);
    // Pass topic ARN to lambda
    credentialsMaintLambda.addEnvironment('CREDENTIALS_ALERT_TOPIC_ARN', alertsTopic.topicArn);

    // Schedule: run daily to cleanup expired credentials and flag rotations
    const scheduleRule = new events.Rule(this, 'CredentialsMaintenanceSchedule', {
      schedule: events.Schedule.rate(cdk.Duration.hours(24)),
      description: 'Daily maintenance for credentials (cleanup and rotation marking)'
    });
    scheduleRule.addTarget(new targets.LambdaFunction(credentialsMaintLambda));

    // Evaluation worker: queue + lambda to run validators asynchronously
    const evalQueue = new sqs.Queue(this, 'EvalQueue', {
      queueName: 'autowar-eval-queue',
      retentionPeriod: cdk.Duration.days(14),
      visibilityTimeout: cdk.Duration.seconds(300),
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    const evalWorker = new lambda.Function(this, 'EvalWorkerLambda', {
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: 'lambdas.evaluation_worker.handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '..', '..', 'src')),
      environment: {
        AUTOWAR_EVALUATIONS_TABLE: tables['autowar-evaluations'].tableName,
        AUTOWAR_EVIDENCE_TABLE: tables['autowar-evidence-technical'] ? tables['autowar-evidence-technical'].tableName : '',
      },
      timeout: cdk.Duration.seconds(300),
    });

    // Grant the worker access to evaluations and evidence tables
    tables['autowar-evaluations'].grantReadWriteData(evalWorker);
    if (tables['autowar-evidence-technical']) {
      tables['autowar-evidence-technical'].grantReadWriteData(evalWorker);
    }
    // Grant eval worker access to scores table
    if (tables['autowar-scores']) {
      tables['autowar-scores'].grantReadWriteData(evalWorker);
    }

    // Also ensure EvalWorker role has explicit access to scores table
    evalWorker.addToRolePolicy(new iam.PolicyStatement({
      actions: [
        'dynamodb:BatchGetItem', 'dynamodb:Query', 'dynamodb:GetItem', 'dynamodb:Scan',
        'dynamodb:ConditionCheckItem', 'dynamodb:BatchWriteItem', 'dynamodb:PutItem',
        'dynamodb:UpdateItem', 'dynamodb:DeleteItem', 'dynamodb:DescribeTable'
      ],
      resources: [scoresTableArn, scoresIndexArn],
    }));

    // Attach SQS event source
    evalWorker.addEventSource(new lambdaEventSources.SqsEventSource(evalQueue, {
      batchSize: 5,
      maxBatchingWindow: cdk.Duration.seconds(30),
    }));

    // Allow API or backend to send messages to the queue (broad permission for now)
    evalQueue.grantSendMessages(autoWarLambda);

    new CfnOutput(this, 'AutoWarEvalQueueUrl', { value: evalQueue.queueUrl });
    new CfnOutput(this, 'AutoWarEvalQueueArn', { value: evalQueue.queueArn });

    // Reports infrastructure: S3 bucket + SQS + report generator Lambda
    const reportsBucket = new s3.Bucket(this, 'AutoWarReportsBucket', {
      bucketName: `autowar-reports-${this.account}-${this.region}`,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
      publicReadAccess: false,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
    });

    const reportQueue = new sqs.Queue(this, 'ReportQueue', {
      queueName: 'autowar-report-queue',
      retentionPeriod: cdk.Duration.days(7),
      visibilityTimeout: cdk.Duration.seconds(300),
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    const reportGenerator = new lambda.Function(this, 'ReportGeneratorLambda', {
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: 'lambdas.report_generator.handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '..', '..', 'src')),
      environment: {
        REPORTS_BUCKET: reportsBucket.bucketName,
        AUTOWAR_REPORTS_TABLE: tables['autowar-reports'] ? tables['autowar-reports'].tableName : '',
      },
      timeout: cdk.Duration.seconds(300),
    });

    // Grant report generator permissions
    reportsBucket.grantPut(reportGenerator);
    if (tables['autowar-reports']) tables['autowar-reports'].grantReadWriteData(reportGenerator);
    reportQueue.grantConsumeMessages(reportGenerator);
    if (tables['autowar-scores']) {
      tables['autowar-scores'].grantReadWriteData(reportGenerator);
    }

    // Also grant ReportGenerator explicit permissions to scores table
    reportGenerator.addToRolePolicy(new iam.PolicyStatement({
      actions: [
        'dynamodb:BatchGetItem', 'dynamodb:Query', 'dynamodb:GetItem', 'dynamodb:Scan',
        'dynamodb:ConditionCheckItem', 'dynamodb:BatchWriteItem', 'dynamodb:PutItem',
        'dynamodb:UpdateItem', 'dynamodb:DeleteItem', 'dynamodb:DescribeTable'
      ],
      resources: [scoresTableArn, scoresIndexArn],
    }));

    // Attach event source from SQS
    reportGenerator.addEventSource(new lambdaEventSources.SqsEventSource(reportQueue, { batchSize: 1 }));

    // Allow eval worker to send messages to report queue
    reportQueue.grantSendMessages(evalWorker);

    // Grant EvalWorker permission to write/read report metadata in DynamoDB
    if (tables['autowar-reports']) {
      tables['autowar-reports'].grantReadWriteData(evalWorker);
    }

    // Grant AutoWarLambda access to scores table for API operations
    if (tables['autowar-scores']) {
      tables['autowar-scores'].grantReadWriteData(autoWarLambda);
    }

    // Ensure role has explicit permissions for the scores table (covers case
    // where the table exists outside CDK or import didn't attach grants).
    autoWarLambda.addToRolePolicy(new iam.PolicyStatement({
      actions: [
        'dynamodb:BatchGetItem', 'dynamodb:Query', 'dynamodb:GetItem', 'dynamodb:Scan',
        'dynamodb:ConditionCheckItem', 'dynamodb:BatchWriteItem', 'dynamodb:PutItem',
        'dynamodb:UpdateItem', 'dynamodb:DeleteItem', 'dynamodb:DescribeTable'
      ],
      resources: [scoresTableArn, scoresIndexArn],
    }));

    // Create explicit inline IAM Policy resources named 'AutowarScoresAccess'
    // and attach them to the Lambda service roles so the permissions are
    // managed by CDK (persisted in CloudFormation) rather than added manually.
    const scoresPolicyStatement = new iam.PolicyStatement({
      actions: [
        'dynamodb:BatchGetItem', 'dynamodb:Query', 'dynamodb:GetItem', 'dynamodb:Scan',
        'dynamodb:ConditionCheckItem', 'dynamodb:BatchWriteItem', 'dynamodb:PutItem',
        'dynamodb:UpdateItem', 'dynamodb:DeleteItem', 'dynamodb:DescribeTable'
      ],
      resources: [scoresTableArn, scoresIndexArn],
    });

    const autoWarScoresPolicy = new iam.Policy(this, 'AutoWarScoresPolicyForAutoWar', {
      policyName: 'AutowarScoresAccess-AutoWar',
      statements: [scoresPolicyStatement],
    });
    if (autoWarLambda.role) {
      autoWarLambda.role.attachInlinePolicy(autoWarScoresPolicy);
    }

    const evalWorkerScoresPolicy = new iam.Policy(this, 'AutoWarScoresPolicyForEvalWorker', {
      policyName: 'AutowarScoresAccess-EvalWorker',
      statements: [scoresPolicyStatement],
    });
    if (evalWorker.role) {
      evalWorker.role.attachInlinePolicy(evalWorkerScoresPolicy);
    }

    const reportGenScoresPolicy = new iam.Policy(this, 'AutoWarScoresPolicyForReportGenerator', {
      policyName: 'AutowarScoresAccess-ReportGenerator',
      statements: [scoresPolicyStatement],
    });
    if (reportGenerator.role) {
      reportGenerator.role.attachInlinePolicy(reportGenScoresPolicy);
    }

    // Provide EvalWorker the ReportQueue URL so it can enqueue report jobs
    evalWorker.addEnvironment('AUTOWAR_REPORT_QUEUE_URL', reportQueue.queueUrl);

    new CfnOutput(this, 'AutoWarReportsBucketName', { value: reportsBucket.bucketName });
    new CfnOutput(this, 'AutoWarReportQueueUrl', { value: reportQueue.queueUrl });

    // API Gateway
    const api = new apigateway.RestApi(this, 'AutoWarApi', {
      restApiName: 'AutoWAR Service',
      description: 'API para el sistema AutoWAR',
    });

    // Integraci�n Lambda con API Gateway
    const integration = new apigateway.LambdaIntegration(autoWarLambda);
    api.root.addMethod('GET', integration);

    // NOTE: temporary public test endpoint removed. For integration testing
    // use authenticated endpoints or recreate a temporary unauthenticated
    // route explicitly when needed.
  }
}
