#!/usr/bin/env python
"""
Test script to verify the UI integration with the backend
Tests all 11 Security questions and 63 BPs evaluation
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://127.0.0.1:8002"

def test_health():
    """Test health endpoint"""
    print("\n" + "="*60)
    print("TEST 1: Health Check")
    print("="*60)
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_validate_credentials():
    """Test credential validation"""
    print("\n" + "="*60)
    print("TEST 2: Validate Credentials (Mock)")
    print("="*60)
    try:
        payload = {
            "access_key_id": "AKIAIOSFODNN7EXAMPLE",
            "secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            "session_token": None,
            "account_id": "123456789012",
            "regions": ["us-east-1"]
        }
        response = requests.post(
            f"{BASE_URL}/security/validate-credentials",
            json=payload,
            timeout=10
        )
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_evaluate_all():
    """Test full security evaluation with all 11 questions and 63 BPs"""
    print("\n" + "="*60)
    print("TEST 3: Full Security Evaluation (11 Questions × 63 BPs)")
    print("="*60)
    try:
        payload = {
            "access_key_id": "AKIAIOSFODNN7EXAMPLE",
            "secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            "session_token": None,
            "account_id": "123456789012",
            "regions": ["us-east-1"]
        }
        response = requests.post(
            f"{BASE_URL}/security/evaluate-real",
            json=payload,
            timeout=30
        )
        print(f"Status: {response.status_code}")
        data = response.json()
        
        # Check response structure
        evaluation = data.get("evaluation", {})
        questions = evaluation.get("questions_evaluated") or data.get("questions", [])
        
        if questions and len(questions) > 0:
            print(f"\n[OK] Total Questions: {len(questions)}/11")
            
            total_bps = 0
            total_findings = 0
            
            for q in questions:
                bps = q.get("bps_evaluated", 0)
                findings = len(q.get("findings", []))
                total_bps += bps
                total_findings += findings
                
                print(f"  {q.get('question_id')}: Score={q.get('score', 0)}%, BPs={bps}, Findings={findings}")
            
            print(f"\n[OK] Total BPs Evaluated: {total_bps}/63")
            overall = evaluation.get('overall_score', data.get('overall_score', 0))
            print(f"[OK] Overall Score: {overall}/100")
            print(f"[OK] Total Findings: {total_findings}")
            
            # Show finding summary
            critical = sum(1 for q in questions
                          for finding in q.get("findings", []) 
                          if finding.get("severity") == "CRITICAL")
            high = sum(1 for q in questions
                      for finding in q.get("findings", []) 
                      if finding.get("severity") == "HIGH")
            
            print(f"\nFinding Severity Summary:")
            print(f"  CRITICAL: {critical}")
            print(f"  HIGH: {high}")
            print(f"  (+ other severities)")
            
            # Show sample findings
            print(f"\nSample Findings:")
            for q in questions[:2]:
                if q.get("findings"):
                    print(f"\n  {q.get('question_id')}:")
                    for f in q.get("findings")[:2]:
                        print(f"    - {f.get('bp')}: {f.get('status')} ({f.get('severity')})")
            
            return response.status_code == 200 and total_bps == 63
        else:
            print("Error: Missing 'questions' in response")
            print(json.dumps(data, indent=2)[:500])
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    print("\n" + "="*60)
    print("AutoWAR UI Integration Tests")
    print("11 Security Questions x 63 BPs")
    print("="*60)
    
    results = []
    
    # Run tests
    results.append(("Health Check", test_health()))
    results.append(("Credential Validation", test_validate_credentials()))
    results.append(("Full Evaluation (11Q + 63BP)", test_evaluate_all()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    for test_name, result in results:
        status = "[OK]" if result else "[FAIL]"
        print("{}: {}".format(status, test_name))
    
    total = len(results)
    passed = sum(1 for _, r in results if r)
    print("\nTotal: {}/{} tests passed".format(passed, total))
    
    if passed == total:
        print("\n[OK] All tests passed!")
        print("\nThe UI can now display:")
        print("  - 11 Security questions (SEC01-SEC11)")
        print("  - 63 best practices evaluated")
        print("  - Real-time AWS findings")
        print("  - Per-question scoring (0-100%)")
        print("  - Finding severity classification")
    else:
        print("\n[FAIL] Some tests failed. Check the output above.")

if __name__ == "__main__":
    main()
