#!/usr/bin/env python3
"""
Test IAM connection and data collection
"""
import sys
import logging
from src.app.aws_connector import AWSConnector

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Sample credentials - user should replace these
access_key_id = input("Enter AWS Access Key ID: ").strip()
secret_access_key = input("Enter AWS Secret Access Key: ").strip()
session_token = input("Enter AWS Session Token (leave blank if none): ").strip() or None
regions = ['us-east-1']  # Default region

if not access_key_id or not secret_access_key:
    print("ERROR: Access Key ID and Secret Access Key are required!")
    sys.exit(1)

try:
    print("\n[TEST] Creating AWS Connector...")
    connector = AWSConnector(
        access_key_id=access_key_id,
        secret_access_key=secret_access_key,
        session_token=session_token,
        regions=regions
    )
    
    print("[TEST] Testing IAM users collection...")
    users = connector.get_iam_users()
    print(f"\n✓ Successfully retrieved {len(users)} IAM users")
    
    if users:
        print("\nUsers found:")
        for user in users:
            mfa_status = "✓ MFA" if user.get('mfa_enabled') else "✗ No MFA"
            access_keys = len(user.get('access_keys', []))
            print(f"  - {user['user_name']}: {mfa_status}, {access_keys} access keys")
    else:
        print("\n⚠ No IAM users found - verify credentials have IAM permissions")
    
except Exception as e:
    print(f"\n✗ Error: {str(e)}")
    logger.exception("Full traceback:")
    sys.exit(1)
