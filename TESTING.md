# AutoWAR Testing Guide

## Quick Start with Mock Data

If you don't have AWS credentials yet, you can test the UI with mock evaluation data:

1. **Start Backend**:
   ```bash
   cd c:\AAM\autowar-dynamodb
   python -m uvicorn src.app.main:app --reload --port 8002
   ```

2. **Start Frontend**:
   ```bash
   cd c:\AAM\autowar-dynamodb\web
   npm run dev
   ```

3. **Access Mock Evaluation**:
   - Open browser to `http://localhost:8080`
   - Instead of entering AWS credentials, directly call the mock endpoint:
     ```
     http://127.0.0.1:8002/security/evaluate-mock
     ```
   - This returns realistic mock security evaluation data

## Using Real AWS Credentials

To evaluate your actual AWS account:

1. **Obtain AWS Credentials**:
   - Get your AWS Access Key ID and Secret Access Key from AWS IAM console
   - Optionally include a Session Token if using temporary credentials

2. **Enter Credentials in Frontend**:
   - Account ID: Your 12-digit AWS Account ID (e.g., 123456789012)
   - Regions: Comma-separated list (e.g., `us-east-1,eu-west-1`)
   - Access Key ID: AKIA...
   - Secret Access Key: wJal...
   - Session Token: (optional) FwoGZXI...

3. **Click Connect**:
   - Frontend will validate credentials
   - Backend will evaluate all 11 Security pillar questions
   - Results will appear in Dashboard and Analyst View

## Troubleshooting

### Backend Tests
Run the test suite:
```bash
python test_backend.py
```

Expected output:
```
[TEST] Testing health endpoint...
✓ Health: 200 - {'status': 'ok'}

[TEST] Testing validate credentials with fake credentials...
Status: 200
Response: {...}

[TEST] Testing mock evaluate endpoint...
✓ Mock Evaluation Success: ...
```

### API Endpoints

- `GET /health` - Health check
- `GET /security/evaluate-mock` - Mock evaluation (no auth required, for testing)
- `POST /security/validate-credentials` - Validate AWS credentials
- `POST /security/evaluate-real` - Real AWS evaluation (requires valid credentials)

### Frontend Data Flow

1. CredentialsForm.jsx validates input
2. Calls `/security/validate-credentials` to verify AWS creds
3. On success, calls `/security/evaluate-real` to get evaluation
4. Data flows: App.jsx → Dashboard.jsx / AnalystView.jsx

## Data Structure

All evaluations return:
```json
{
  "success": true,
  "evaluation": {
    "account_id": "123456789012",
    "overall_score": 65.45,
    "total_questions": 11,
    "total_best_practices": 63,
    "questions_evaluated": [
      {
        "question_id": "SEC01",
        "question": "Question text",
        "score": 55,
        "bps_evaluated": 8,
        "findings": [
          {
            "bp": "SEC01-BP01",
            "status": "NON_COMPLIANT",
            "finding": "Finding text",
            "severity": "HIGH",
            "risk": "Risk description",
            "remediation": "How to fix it",
            "evidence": "What was found"
          }
        ]
      }
      ...
    ]
  },
  "summary": {
    "total_findings": 3,
    "critical": 1,
    "high": 1,
    "medium": 1,
    "score": 65.45,
    "bps_evaluated": 63
  }
}
```

## AWS IAM Permissions Required

For real AWS evaluation, the IAM user/role needs permissions for:

- `sts:GetCallerIdentity` (validation)
- `iam:ListUsers`, `iam:ListRoles`, `iam:ListPolicies` (authentication assessment)
- `ec2:DescribeInstances`, `ec2:DescribeSecurityGroups` (compute security)
- `rds:DescribeDBInstances` (database security)
- `s3:ListAllMyBuckets` (data security)
- `kms:ListKeys` (encryption key management)
- `cloudtrail:DescribeTrails` (logging)
- `config:DescribeConfigurationRecorders` (compliance monitoring)
- `guardduty:ListDetectors` (threat detection)
- And more for comprehensive evaluation...

A simpler approach is to use an IAM role with managed policy `SecurityAudit` attached, which grants read-only access to most AWS services.

