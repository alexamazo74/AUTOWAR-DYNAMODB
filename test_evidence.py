"""Test script to verify evidence field in PENDING_REVIEW findings"""
import requests
import json
import os

# Get AWS credentials from environment
aws_key = os.getenv('AWS_ACCESS_KEY_ID', 'test-key')
aws_secret = os.getenv('AWS_SECRET_ACCESS_KEY', 'test-secret')

payload = {
    "access_key_id": aws_key,
    "secret_access_key": aws_secret,
    "account_id": "102080400524",
    "regions": ["us-east-1"]
}

try:
    print("🔄 Llamando al API de evaluación...")
    response = requests.post(
        "http://localhost:8002/security/evaluate-real",
        json=payload,
        timeout=120
    )
    
    if response.status_code == 200:
        result = response.json()
        sec01_findings = result.get('results', {}).get('SEC01', {}).get('findings', [])
        
        print("\n" + "="*80)
        print("📋 BPs de SEC01 con estado PENDING_REVIEW")
        print("="*80)
        
        pending_count = 0
        for finding in sec01_findings:
            if finding['status'] == 'PENDING_REVIEW':
                pending_count += 1
                print(f"\n🔸 {finding['bp']}")
                print(f"   Status: {finding['status']}")
                print(f"   Finding: {finding['finding']}")
                print(f"   Evidence: {finding['evidence'][:200]}..." if len(finding['evidence']) > 200 else f"   Evidence: {finding['evidence']}")
                print(f"   Severity: {finding['severity']}")
        
        if pending_count == 0:
            print("\n✅ No hay BPs en PENDING_REVIEW")
            print("\n📊 Resumen de todos los BPs:")
            for finding in sec01_findings:
                print(f"   {finding['bp']}: {finding['status']}")
        else:
            print(f"\n📊 Total BPs en PENDING_REVIEW: {pending_count}")
            
    else:
        print(f"❌ Error: Status {response.status_code}")
        print(response.text[:500])
        
except Exception as e:
    print(f"❌ Error: {e}")
