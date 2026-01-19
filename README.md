# AutoWAR - AWS Well-Architected Review automation (scaffold)

This repository contains an initial scaffold for the AutoWAR platform described in the project scope.

Quickstart (local backend):

1. Create a Python virtualenv and install deps:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Copy `.env.example` to `.env` and add AWS credentials.

3. Run the FastAPI app:

```powershell
uvicorn src.app.main:app --reload --port 8000
```

4. Endpoints:
- `GET /health`
- `GET /clients`
- `POST /clients`
- `GET /evaluations`

Credentials endpoint
--------------------

Before running an analysis you must provide credentials for the target AWS account. Preferred flow is `AssumeRole` (the customer provides a Role ARN); fallback is providing access keys which will be stored in Secrets Manager if requested.

1) AssumeRole (preferred)

Request JSON (POST /credentials):
```
{
	"client_id": "client-123",
	"role_arn": "arn:aws:iam::111122223333:role/AutoWARReadOnly",
	"external_id": "optional-external-id",
	"region": "us-east-1"
}
```

Example curl:
```
curl -X POST http://localhost:8000/credentials \
	-H "Content-Type: application/json" \
	-d '{"client_id":"client-123","role_arn":"arn:aws:iam::111122223333:role/AutoWARReadOnly","region":"us-east-1"}'
```

Response: JSON metadata registered in `autowar-aws-credentials` (role record). The backend calls `sts:AssumeRole` and validates with `sts:GetCallerIdentity`.

2) Access keys (fallback)

Request JSON (POST /credentials):
```
{
	"client_id": "client-456",
	"access_key_id": "AKIA...",
	"secret_access_key": "...",
	"session_token": "optional",
	"region": "us-east-1",
	"save_secret": true
}
```

Example curl:
```
curl -X POST http://localhost:8000/credentials \
	-H "Content-Type: application/json" \
	-d '{"client_id":"client-456","access_key_id":"AKIA...","secret_access_key":"...","region":"us-east-1","save_secret":true}'
```

If `save_secret` is true the keys are stored in AWS Secrets Manager and the DynamoDB record stores the `secret_arn` reference only. The backend validates keys by calling `sts:GetCallerIdentity` before storing.

Security notes
- Prefer `AssumeRole` with a customer-managed role and `external_id` to avoid transferring long-lived keys.
- Never store raw secret values in DynamoDB or application logs. Use AWS Secrets Manager + KMS.
- The service validates credentials on receipt; ensure network access to AWS endpoints from the running service.

API Key protection for sensitive endpoints
----------------------------------------

To protect sensitive endpoints (like `POST /credentials`) set the environment variable `AUTOWAR_API_KEY` before starting the service. The endpoint requires an `x-api-key` header matching that value.

Example (set env var and run):
```powershell
$env:AUTOWAR_API_KEY = 'my-secret-key'
uvicorn src.app.main:app --reload --port 8000
```

Example curl using the API key:
```bash
curl -X POST http://localhost:8000/credentials \
	-H "Content-Type: application/json" \
	-H "x-api-key: my-secret-key" \
	-d '{"client_id":"client-123","role_arn":"arn:aws:iam::111122223333:role/AutoWARReadOnly","region":"us-east-1"}'
```

If `AUTOWAR_API_KEY` is not configured the server will return a 500 for protected endpoints to force proper configuration.

Cognito configuration (production)
--------------------------------

The CDK stack now creates an Amazon Cognito User Pool and a User Pool Client. After deploying the CDK stack you will see two CloudFormation outputs: `AutoWarUserPoolId` and `AutoWarUserPoolClientId`.

Set the following environment variables in the backend to enable JWT validation:

```powershell
$env:COGNITO_REGION = 'us-east-1'
$env:COGNITO_USER_POOL_ID = '<AutoWarUserPoolId from CDK>'
$env:COGNITO_APP_CLIENT_ID = '<AutoWarUserPoolClientId from CDK>'
```

Once configured, the backend will be able to validate Cognito JWTs using the JWKS endpoint. The helper `src/app/cognito_auth.py` performs JWKS fetch and token verification. Protect endpoints by creating a dependency that calls `verify_jwt_token` on the `Authorization: Bearer <token>` header.

Recommended production setup:
- Deploy CDK to create Cognito and DynamoDB tables.
- Create users in the Cognito User Pool or configure a federation provider.
- Use the issued `id_token`/`access_token` in requests to protected endpoints.

Using JWT tokens with the API
----------------------------

Once you obtain an `access_token` or `id_token` from Cognito, include it on requests to endpoints protected by Cognito (for example `POST /evaluations` or `POST /clients`) using the `Authorization` header:

```bash
curl -X POST http://localhost:8000/evaluations \
	-H "Authorization: Bearer <ACCESS_TOKEN>" \
	-H "Content-Type: application/json" \
	-d '{"client_id":"client-123","account_id":"111122223333","region":"us-east-1","summary":"scan"}'
```

The backend will validate the token signature and claims (audience + issuer) against the Cognito User Pool configuration.

Security Pillar Implementation
-----------------------------

The Security pillar has been fully implemented with comprehensive best practice validation. The implementation includes:

### Available Security Questions:
- **SEC01**: ¿Cómo opera usted su carga de trabajo de forma segura? (9 Best Practices)
- **SEC02**: ¿Cómo gestiona las identidades de personas y máquinas? (2 Best Practices)
- **SEC03**: ¿Cómo protege los datos confidenciales? (2 Best Practices)
- **SEC04**: ¿Cómo detecta y investiga los eventos de seguridad? (1 Best Practice)
- **SEC05**: ¿Cómo protege sus recursos de red? (1 Best Practice)

### Key Features:
- **Complete BP Coverage**: All 15 security best practices implemented with detailed validators
- **Mock AWS Resources**: Uses boto3 stubs for testing without requiring real AWS resources
- **Descriptive Responses**: All responses include question and BP descriptions in Spanish
- **CORS Enabled**: Frontend-backend communication configured for local development
- **Web Interface**: Complete HTML/JS frontend for testing all endpoints

### API Endpoints:
- `POST /security/evaluate` - Evaluate a single security question
- `GET /security/evaluations/{evaluation_id}` - List all evaluations for an ID
- `GET /security/evaluations/{evaluation_id}/{question_id}` - Get specific question evaluation
- `GET /security/reports/{evaluation_id}` - Generate comprehensive security report

### Quick Start for Security Testing:

1. **Start servers in background:**
```powershell
.\start-servers.ps1
```

2. **Open frontend:**
   - Navigate to http://127.0.0.1:8080
   - Select a question from the dropdown
   - Click "POST /security/evaluate" to test

3. **Direct API testing:**
```bash
# Evaluate SEC01 question
curl -X POST http://localhost:8002/security/evaluate \
  -H "Content-Type: application/json" \
  -d '{"evaluation_id":"test-security-eval-1","question_id":"SEC01"}'
```

### Response Format:
Each evaluation returns detailed results including:
- Question text and description
- Individual BP compliance status with evidence
- Scoring and recommendations
- Overall security posture assessment

The Security pillar is now ready for integration with the full AutoWAR platform and can be extended to include real AWS resource scanning when credentials are provided.

CDK:

The `cdk/` folder has an AWS CDK stack that now creates the DynamoDB tables listed in the project scope. Use the CDK app to deploy the infrastructure.

Development notes:
- This is an initial scaffold for a junior developer; implement features incrementally.
- Next steps: implement authentication, evaluation engine, AI integration, tests, CI.

Run locally (format/type/tests):
```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
ruff check src tests
black src tests
mypy src tests --config-file mypy.ini
pytest -q
```

If CI fails due to formatting, run the `black` command above and include the changes in your PR. CI also enforces tighter `mypy` checks now; run `mypy` locally to inspect and fix type issues.
