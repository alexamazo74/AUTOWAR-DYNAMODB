"""
Test script to verify real credentials evaluation
Run this to see what's happening with your AWS credentials
"""
import requests
import json
import sys

# Replace these with your actual AWS credentials
AWS_ACCESS_KEY_ID = input("Enter your AWS Access Key ID: ")
AWS_SECRET_ACCESS_KEY = input("Enter your AWS Secret Access Key: ")
AWS_SESSION_TOKEN = input("Enter your AWS Session Token (press Enter if none): ").strip() or None
AWS_ACCOUNT_ID = input("Enter your AWS Account ID: ")
REGIONS = input("Enter regions (comma-separated, e.g., us-east-1,us-west-2): ").split(",")

print("\n" + "="*60)
print("Testing Real Credentials Evaluation")
print("="*60 + "\n")

# Test 1: Validate credentials
print("Step 1: Validating credentials...")
validate_payload = {
    "access_key_id": AWS_ACCESS_KEY_ID,
    "secret_access_key": AWS_SECRET_ACCESS_KEY,
    "session_token": AWS_SESSION_TOKEN,
    "account_id": AWS_ACCOUNT_ID,
    "regions": REGIONS
}

try:
    response = requests.post(
        "http://127.0.0.1:8002/security/validate-credentials",
        json=validate_payload,
        timeout=10
    )
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Success: {result.get('success')}")
    if not result.get('success'):
        print(f"Error: {result.get('error')}")
        sys.exit(1)
    print("✓ Credentials validated successfully\n")
except Exception as e:
    print(f"✗ Error validating credentials: {e}\n")
    sys.exit(1)

# Test 2: Run evaluation
print("Step 2: Running security evaluation...")
print("This may take 2-5 minutes depending on your AWS resources...")

try:
    response = requests.post(
        "http://127.0.0.1:8002/security/evaluate-real",
        json=validate_payload,
        timeout=320  # 5+ minutes
    )
    print(f"Status: {response.status_code}")
    result = response.json()
    
    if result.get('success'):
        evaluation = result.get('evaluation', {})
        print(f"\n✓ Evaluation completed successfully!")
        print(f"  Overall Score: {evaluation.get('overall_score')}%")
        print(f"  Questions Evaluated: {evaluation.get('total_questions')}")
        print(f"  Best Practices: {evaluation.get('total_best_practices')}")
        
        questions = evaluation.get('questions_evaluated', [])
        print(f"\n  Questions found: {len(questions)}")
        
        if questions:
            print("\n  Question Details:")
            for q in questions:
                print(f"    - {q.get('question_id')}: {q.get('score')}% ({q.get('best_practices_evaluated')} BPs)")
        else:
            print("\n  ⚠ WARNING: No questions_evaluated data returned!")
            print(f"  Raw evaluation keys: {list(evaluation.keys())}")
    else:
        print(f"\n✗ Evaluation failed")
        print(f"  Error: {result.get('error')}")
        
except requests.exceptions.Timeout:
    print("\n✗ Evaluation timed out (>5 minutes)")
except Exception as e:
    print(f"\n✗ Error during evaluation: {e}")

print("\n" + "="*60)
print("Test Complete")
print("="*60)
