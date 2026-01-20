# AutoWAR - Complete Setup & Deployment Guide

## Status Summary

✅ **Backend** (FastAPI on port 8002):
- Health endpoint working
- AWS credentials validation implemented
- Mock evaluation endpoint ready (`/security/evaluate-mock`)
- Real evaluation endpoint ready (`/security/evaluate-real`)
- All 11 Security pillar questions implemented with real AWS checks
- Logging with debug output for monitoring

✅ **Frontend** (React/Vite on port 8080):
- Credentials form with AWS credentials input
- "Load Demo Data" button for testing without AWS credentials
- Dashboard view showing Security pillar score and findings
- Analyst View showing all 11 questions with detailed findings
- Client View with recommendations
- Report Generator

## Quick Start (Testing with Mock Data)

### 1. Start Backend
```bash
cd c:\AAM\autowar-dynamodb
python -m uvicorn src.app.main:app --reload --port 8002
```

### 2. Start Frontend
```bash
cd c:\AAM\autowar-dynamodb\web
npm run dev
```

### 3. Open Browser
```
http://localhost:8080
```

### 4. Click "Load Demo Data" Button
The app will fetch mock evaluation results and display:
- Overall Security Score: 65.45%
- All 11 Questions with scores
- Findings grouped by severity (Critical, High, Medium)
- Detailed recommendations per best practice

## Real AWS Evaluation

To evaluate your actual AWS account:

### 1. Get AWS Credentials
- Open [AWS IAM Console](https://console.aws.amazon.com/iam)
- Click "Users" → Your User → "Security Credentials"
- Create an Access Key (or use existing)
- Copy Access Key ID and Secret Access Key
- Optionally get Session Token if using temporary credentials

### 2. Enter Credentials in Frontend
- **Account ID**: Your 12-digit AWS Account ID (found in top-right corner)
- **Regions**: Comma-separated list (e.g., `us-east-1,eu-west-1`)
- **Access Key ID**: AKIA...
- **Secret Access Key**: wJal...
- **Session Token**: (Optional) FwoGZXI...

### 3. Click Connect
- Backend validates credentials with AWS STS
- Evaluates all 11 Security pillar questions
- Returns score, findings, and recommendations
- Displays results in Dashboard and Analyst View

## API Endpoints

### Health Check
```bash
curl http://127.0.0.1:8002/health
# Response: {"status": "ok"}
```

### Mock Evaluation (No Auth)
```bash
curl http://127.0.0.1:8002/security/evaluate-mock
# Response: Complete mock evaluation with 11 questions, findings, score, etc.
```

### Real Evaluation (Requires Valid AWS Credentials)
```bash
curl -X POST http://127.0.0.1:8002/security/evaluate-real \
  -H "Content-Type: application/json" \
  -d '{
    "access_key_id": "AKIA...",
    "secret_access_key": "wJal...",
    "session_token": null,
    "account_id": "123456789012",
    "regions": ["us-east-1"]
  }'
```

## Evaluation Results Structure

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
        "question": "Fundamentos de seguridad - Operación segura",
        "score": 55,
        "bps_evaluated": 8,
        "findings": [
          {
            "bp": "SEC01-BP01",
            "status": "NON_COMPLIANT",
            "finding": "AWS Organizations not configured",
            "severity": "HIGH",
            "risk": "Single account limits blast radius",
            "remediation": "Enable AWS Organizations",
            "evidence": "No organization structure detected"
          }
        ]
      },
      // ... 10 more questions
    ]
  },
  "summary": {
    "total_findings": 35,
    "critical": 2,
    "high": 8,
    "medium": 25,
    "score": 65.45,
    "bps_evaluated": 63
  }
}
```

## Implemented Security Checks

### SEC01 - Security Fundamentals (8 BPs)
- ✅ AWS Organizations configuration
- ✅ Password policy strength
- ✅ AWS Config status
- ✅ GuardDuty threat detection
- ✅ Systems Manager usage
- ✅ CloudTrail logging
- ✅ Threat modeling
- ✅ AWS security services review

### SEC02 - Authentication (6 BPs)
- ✅ MFA enforcement
- ✅ Long-term credentials vs STS
- ✅ Secrets Manager usage
- ✅ Centralized identity provider
- ✅ Credential rotation
- ✅ User groups vs direct policies

### SEC03-SEC11 (Additional 54 BPs)
- SEC03: Human identity management
- SEC04: Machine identity management
- SEC05: Permission management
- SEC06: Detection & investigation
- SEC07: Data classification
- SEC08: Data protection at rest
- SEC09: Data protection in transit
- SEC10: Incident response
- SEC11: Regulatory compliance

## Architecture

```
Frontend (Vite/React)          Backend (FastAPI)           AWS
                              
CredentialsForm ────────────> POST /validate-credentials ──> AWS STS
  ↓                                                         
Dashboard ←──────────────── GET /security/evaluate-mock   (Mock Data)
  ↓                        POST /security/evaluate-real ──> AWS APIs
AnalystView
  ↓
ClientView
  ↓
ReportGenerator
```

## Troubleshooting

### Backend won't start
```bash
# Make sure port 8002 is available
netstat -ano | findstr :8002

# Check Python virtual environment
.\.venv\Scripts\python.exe -m pip list | grep fastapi
```

### Frontend won't connect to backend
```bash
# Test backend directly
curl http://127.0.0.1:8002/health

# Check CORS is enabled (should be *)
# Check backend logs for errors
```

### AWS credentials rejected
```bash
# Verify credentials are correct
# Check they have required IAM permissions
# If using temporary credentials, verify session token is current
# Try with SecurityAudit managed policy attached to IAM user
```

### Mock data not loading
```bash
# Run backend test
python test_backend.py

# Check /security/evaluate-mock endpoint returns data
curl http://127.0.0.1:8002/security/evaluate-mock | python -m json.tool
```

## Next Steps

1. **Test with Demo Data**: Click "Load Demo Data" button to verify UI
2. **Set Up AWS Credentials**: Follow Real AWS Evaluation section
3. **Customize Evaluations**: Modify checks in `src/app/security_evaluator.py`
4. **Deploy to Production**: Configure for your AWS environment
5. **Integrate with SIEM**: Send findings to your monitoring system

## File Structure

```
autowar-dynamodb/
├── src/app/
│   ├── main.py                    # FastAPI app, endpoints
│   ├── security_evaluator.py      # 11 Security pillar evaluators
│   ├── aws_connector.py           # AWS API calls
│   └── ...
├── web/
│   ├── src/
│   │   ├── App.jsx               # Main React component
│   │   ├── components/
│   │   │   ├── CredentialsForm.jsx
│   │   │   ├── Dashboard.jsx
│   │   │   ├── AnalystView.jsx
│   │   │   ├── ClientView.jsx
│   │   │   └── ...
│   │   └── ...
│   ├── vite.config.js
│   └── package.json
├── test_backend.py                # Backend test suite
├── TESTING.md                      # Testing guide
└── README.md
```

## Security Notes

⚠️ **Important**: 
- Credentials are stored in browser session memory only
- Not persisted to disk or databases
- Use temporary AWS credentials (STS tokens) when possible
- Never hardcode credentials in the application
- Use IAM roles in production deployments

