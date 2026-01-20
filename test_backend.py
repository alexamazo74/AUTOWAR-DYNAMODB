#!/usr/bin/env python
"""Test backend connectivity and mock evaluation"""
import requests
import json
from datetime import datetime

BASE_URL = "http://127.0.0.1:8002"

def test_health():
    print("[TEST] Testing health endpoint...")
    try:
        resp = requests.get(f"{BASE_URL}/health")
        print(f"✓ Health: {resp.status_code} - {resp.json()}")
        return True
    except Exception as e:
        print(f"✗ Health failed: {e}")
        return False

def test_validate_credentials_mock():
    print("\n[TEST] Testing validate credentials with fake credentials...")
    payload = {
        "access_key_id": "AKIAIOSFODNN7EXAMPLE",
        "secret_access_key": "wJalrXUtnFEMI/K7MDENG+bPxRfiCYEXAMPLEKEY",
        "session_token": None,
        "account_id": "123456789012",
        "regions": ["us-east-1"]
    }
    try:
        resp = requests.post(f"{BASE_URL}/security/validate-credentials", json=payload)
        print(f"Status: {resp.status_code}")
        print(f"Response: {json.dumps(resp.json(), indent=2)}")
        return resp.status_code == 200 and resp.json().get('success') == True
    except Exception as e:
        print(f"✗ Request failed: {e}")
        return False

def test_evaluate_mock():
    print("\n[TEST] Testing mock evaluate endpoint...")
    try:
        resp = requests.get(f"{BASE_URL}/security/evaluate-mock")
        print(f"Status: {resp.status_code}")
        data = resp.json()
        if data.get('success'):
            evaluation = data.get('evaluation', {})
            print(f"✓ Mock Evaluation Success:")
            print(f"  - Account: {evaluation.get('account_id')}")
            print(f"  - Score: {evaluation.get('overall_score')}%")
            print(f"  - Questions: {evaluation.get('total_questions')}")
            print(f"  - Questions evaluated: {len(evaluation.get('questions_evaluated', []))}")
            
            # Count findings
            all_findings = []
            for q in evaluation.get('questions_evaluated', []):
                all_findings.extend(q.get('findings', []))
            print(f"  - Total findings: {len(all_findings)}")
            
            # Show first question's findings
            if evaluation.get('questions_evaluated'):
                first_q = evaluation['questions_evaluated'][0]
                print(f"\n  First question ({first_q.get('question_id')}):")
                print(f"    - Score: {first_q.get('score')}%")
                print(f"    - BPs evaluated: {first_q.get('bps_evaluated')}")
                print(f"    - Findings: {len(first_q.get('findings', []))}")
                if first_q.get('findings'):
                    print(f"    - First finding: {first_q['findings'][0].get('bp')} - {first_q['findings'][0].get('status')}")
            return True
        else:
            print(f"✗ Mock evaluation failed: {data.get('error')}")
            return False
    except Exception as e:
        print(f"✗ Request failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print(f"Testing AutoWAR Backend at {BASE_URL}\n")
    print("=" * 60)
    
    results = {
        "health": test_health(),
        "validate_creds": test_validate_credentials_mock(),
        "mock_eval": test_evaluate_mock()
    }
    
    print("\n" + "=" * 60)
    print("[SUMMARY]")
    for test, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {test}: {status}")
    
    print(f"\nOverall: {'✓ ALL TESTS PASSED' if all(results.values()) else '✗ SOME TESTS FAILED'}")
