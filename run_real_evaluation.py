#!/usr/bin/env python3
"""
Run real AWS evaluation with detailed output
"""

import requests
import json
import os
import time

BACKEND_URL = "http://localhost:8002"

def main():
    # Set credentials from environment
    region = os.environ.get("AWS_REGION", "us-east-1")
    account_id = os.environ.get("AWS_ACCOUNT_ID", "407958903426")
    creds = {
        "access_key_id": os.environ.get("AWS_ACCESS_KEY_ID"),
        "secret_access_key": os.environ.get("AWS_SECRET_ACCESS_KEY"),
        "session_token": os.environ.get("AWS_SESSION_TOKEN"),
        "regions": [region],
        "account_id": account_id,
    }
    
    if not creds["access_key_id"]:
        print("ERROR: AWS_ACCESS_KEY_ID not set")
        return
    
    print("=" * 80)
    print("AWS Security Evaluation - Real Account")
    print("=" * 80)
    print(f"Account: {creds['account_id']}")
    print(f"Region: {creds['regions'][0]}")
    print(f"Credentials: {creds['access_key_id'][:10]}...")
    print()
    
    # Test backend
    print("[1] Testing backend connection...")
    try:
        resp = requests.get(f"{BACKEND_URL}/health", timeout=5)
        print(f"✓ Backend: {resp.json()}")
    except Exception as e:
        print(f"✗ Backend error: {e}")
        return
    
    # Run evaluation
    print("\n[2] Running evaluation (this takes 2-3 minutes)...")
    start = time.time()
    try:
        resp = requests.post(
            f"{BACKEND_URL}/security/evaluate-real",
            json=creds,
            timeout=600
        )
        elapsed = time.time() - start
        
        print(f"✓ Response received ({elapsed:.0f}s)")
        print(f"  Status: {resp.status_code}")
        
        if resp.status_code == 200:
            data = resp.json()
            print(f"\n[3] Results:")
            print(f"  Overall Score: {data.get('overall_score', 'N/A')}")
            print(f"  Questions: {len(data.get('questions', []))}")
            
            # Show SEC04, SEC05, SEC06 scores
            for q in data.get('questions', []):
                if q.get('id') in ['SEC04', 'SEC05', 'SEC06']:
                    print(f"    {q['id']}: {q.get('score', 'N/A')}% - {q.get('name', '')}")
            
            # Show critical findings
            critical = []
            for q in data.get('questions', []):
                for bp in q.get('best_practices', []):
                    for finding in bp.get('findings', []):
                        if finding.get('severity') == 'CRITICAL':
                            critical.append({
                                'section': q.get('id'),
                                'bp': bp.get('id'),
                                'issue': finding.get('issue')
                            })
            
            if critical:
                print(f"\n  Critical Issues: {len(critical)}")
                for item in critical[:5]:
                    print(f"    - {item['section']}/{item['bp']}: {item['issue'][:50]}...")
            
            # Save full results
            with open('evaluation_results.json', 'w') as f:
                json.dump(data, f, indent=2)
            print(f"\n✓ Full results saved to evaluation_results.json")
            
        else:
            print(f"  Error: {resp.text[:200]}")
            
    except requests.Timeout:
        print("✗ Timeout (>10 minutes)")
    except Exception as e:
        print(f"✗ Error: {e}")

if __name__ == "__main__":
    main()
