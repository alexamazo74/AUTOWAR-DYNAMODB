#!/usr/bin/env python3
"""Test script to call the backend API with mock credentials"""

import requests
import json

# Test with mock credentials (will trigger mock evaluator)
payload = {
    "access_key_id": "test",
    "secret_access_key": "test",
    "session_token": "",
    "account_id": "123456789012",
    "regions": ["us-east-1"]
}

print("Calling backend API with mock credentials...")
print(f"URL: http://127.0.0.1:8002/security/evaluate-real")

try:
    response = requests.post(
        "http://127.0.0.1:8002/security/evaluate-real",
        json=payload,
        timeout=10
    )
    
    print(f"\nStatus Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        
        if not data.get('success'):
            print(f"\n✗ API returned success=False: {data.get('error')}")
        else:
            evaluation = data.get('evaluation', {})
            summary = data.get('summary', {})
            
            print("\n✓ SUCCESS - Backend returned evaluation data")
            print(f"\nEvaluation ID: {evaluation.get('id')}")
            print(f"Account ID: {evaluation.get('account_id')}")
            print(f"Demo Mode: {evaluation.get('demo_mode', False)}")
            
            questions = evaluation.get('questions_evaluated', [])
            print(f"\nTotal Questions: {len(questions)}")
            print(f"Total BPs: {evaluation.get('total_best_practices', 0)}")
            print(f"Overall Score: {evaluation.get('overall_score', 0)}")
            print(f"\nSummary:")
            print(f"  Total Findings: {summary.get('total_findings', 0)}")
            print(f"  Critical: {summary.get('critical', 0)}")
            print(f"  High: {summary.get('high', 0)}")
            print(f"  Medium: {summary.get('medium', 0)}")
            
            # Validate each question has all BPs
            print("\n" + "=" * 80)
            print("QUESTION DETAILS:")
            print("=" * 80)
            
            total_findings = 0
            for q in questions:
                q_id = q.get('question_id')
                title = q.get('title', '')
                bps_eval = q.get('bps_evaluated', 0)
                findings = q.get('findings', [])
                
                total_findings += len(findings)
                status = "✓" if len(findings) == bps_eval else "✗"
                print(f"\n{status} {q_id}: {title}")
                print(f"   Expected: {bps_eval} BPs, Found: {len(findings)} findings")
                
                # Show first 2 findings
                for i, finding in enumerate(findings[:2]):
                    bp = finding.get('bp')
                    status_val = finding.get('status')
                    severity = finding.get('severity')
                    print(f"   - {bp}: {status_val} [{severity}]")
                    if 'risk' in finding:
                        print(f"     Risk: {finding['risk'][:50]}...")
                    if 'remediation' in finding:
                        print(f"     Remediation: {finding['remediation'][:50]}...")
            
            print("\n" + "=" * 80)
            print(f"TOTAL FINDINGS ACROSS ALL QUESTIONS: {total_findings}/63")
            print("=" * 80)
            
            # Save full response to file for inspection
            with open('backend_response.json', 'w') as f:
                json.dump(data, f, indent=2)
            print("\n✓ Full response saved to: backend_response.json")
        
    else:
        print(f"\n✗ ERROR: {response.text}")
        
except requests.exceptions.ConnectionError:
    print("\n✗ ERROR: Cannot connect to backend at http://127.0.0.1:8002")
    print("Make sure the backend is running: cd src/app && uvicorn main:app --reload --port 8002")
except Exception as e:
    print(f"\n✗ ERROR: {str(e)}")
