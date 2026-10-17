"""
Credentials Manager - Session-based credential storage
"""

import boto3
import json
import re
import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional
from botocore.exceptions import ClientError


class CredentialsManager:
    # Regex pattern for valid AWS region format: us-east-1, eu-west-2, ap-south-1, etc.
    REGION_PATTERN = re.compile(r'^[a-z]{2}-[a-z]+-\d$')
    
    def __init__(self):
        self.secrets_client = boto3.client('secretsmanager')
        self.sts_client = boto3.client('sts')
        self.session_ttl = 3600  # 1 hour
        
    def validate_and_create_session(self, credentials: Dict) -> Dict:
        """
        Validates AWS credentials and creates temporary session
        Supports multiple regions
        Returns session_id for subsequent requests
        """
        # Handle both single region (legacy) and multiple regions
        regions = credentials.get('regions', [credentials.get('region')])
        if not regions or not regions[0]:
            raise ValueError("At least one region must be specified")
        
        # Validate region format for all regions
        for region in regions:
            if not self.REGION_PATTERN.match(region):
                raise ValueError(f"Invalid region format: {region}. Expected format: xx-xxxx-# (e.g., us-east-1, eu-west-2)")
        
        # Validate credentials with STS (using first region)
        credentials_with_region = {**credentials, 'region': regions[0]}
        if not self.validate_credentials(credentials_with_region):
            raise ValueError("Invalid AWS credentials")
        
        # Generate unique session ID
        session_id = str(uuid.uuid4())
        
        # Store credentials temporarily in Secrets Manager
        secret_name = f"autowar/sessions/{session_id}"
        
        session_data = {
            'credentials': {
                'access_key_id': credentials['access_key_id'],
                'secret_access_key': credentials['secret_access_key'],
                'session_token': credentials.get('session_token'),
                'account_id': credentials['account_id'],
                'regions': regions  # Store all regions
            },
            'created_at': datetime.utcnow().isoformat(),
            'expires_at': (datetime.utcnow() + timedelta(seconds=self.session_ttl)).isoformat(),
            'account_id': credentials['account_id']
        }
        
        try:
            self.secrets_client.create_secret(
                Name=secret_name,
                SecretString=json.dumps(session_data),
                KmsKeyId='alias/autowar-secrets',
                Tags=[
                    {'Key': 'type', 'Value': 'temporary-session'},
                    {'Key': 'ttl', 'Value': str(self.session_ttl)}
                ]
            )
            
            return {
                'session_id': session_id,
                'expires_at': session_data['expires_at'],
                'account_id': credentials['account_id'],
                'regions': regions
            }
        except ClientError as e:
            raise Exception(f"Failed to create session: {str(e)}")
    
    def get_session_credentials(self, session_id: str) -> Optional[Dict]:
        """Retrieves credentials from temporary session"""
        secret_name = f"autowar/sessions/{session_id}"
        
        try:
            response = self.secrets_client.get_secret_value(SecretId=secret_name)
            session_data = json.loads(response['SecretString'])
            
            # Check if session expired
            expires_at = datetime.fromisoformat(session_data['expires_at'])
            if datetime.utcnow() > expires_at:
                self.cleanup_session(session_id)
                return None
            
            return session_data['credentials']
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                return None
            raise
    
    def validate_credentials(self, credentials: Dict) -> bool:
        """Validates credentials using STS GetCallerIdentity"""
        try:
            # Get region from credentials (single region for validation)
            region = credentials.get('region', 'us-east-1')
            
            session = boto3.Session(
                aws_access_key_id=credentials['access_key_id'],
                aws_secret_access_key=credentials['secret_access_key'],
                aws_session_token=credentials.get('session_token'),
                region_name=region
            )
            sts = session.client('sts')
            identity = sts.get_caller_identity()
            
            # Verify account ID matches
            if identity['Account'] != credentials['account_id']:
                return False
            
            return True
        except ClientError:
            return False
    
    def get_user_info(self, credentials: Dict) -> Dict:
        """Gets user information from STS GetCallerIdentity"""
        try:
            region = credentials.get('region', credentials.get('regions', ['us-east-1'])[0])
            
            session = boto3.Session(
                aws_access_key_id=credentials['access_key_id'],
                aws_secret_access_key=credentials['secret_access_key'],
                aws_session_token=credentials.get('session_token'),
                region_name=region
            )
            sts = session.client('sts')
            identity = sts.get_caller_identity()
            
            # Parse ARN to get user/role name
            arn = identity['Arn']
            arn_parts = arn.split('/')
            user_name = arn_parts[-1] if len(arn_parts) > 1 else 'Unknown'
            
            # Determine if it's a user or role
            if ':user/' in arn:
                user_type = 'IAM User'
            elif ':assumed-role/' in arn:
                user_type = 'IAM Role'
            elif ':root' in arn:
                user_type = 'Root User'
                user_name = 'root'
            else:
                user_type = 'Unknown'
            
            return {
                'account_id': identity['Account'],
                'user_id': identity['UserId'],
                'arn': arn,
                'user_name': user_name,
                'user_type': user_type
            }
        except ClientError as e:
            return {
                'account_id': credentials.get('account_id', 'Unknown'),
                'user_id': 'Unknown',
                'arn': 'Unknown',
                'user_name': 'Unknown',
                'user_type': 'Unknown'
            }
    
    def cleanup_session(self, session_id: str):
        """Deletes session credentials from Secrets Manager"""
        secret_name = f"autowar/sessions/{session_id}"
        try:
            self.secrets_client.delete_secret(
                SecretId=secret_name,
                ForceDeleteWithoutRecovery=True
            )
        except ClientError as e:
            if e.response['Error']['Code'] != 'ResourceNotFoundException':
                raise
