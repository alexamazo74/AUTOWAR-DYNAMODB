import os
import boto3
from boto3.dynamodb.conditions import Key
from typing import List, Dict, Any
from botocore.exceptions import ClientError, NoCredentialsError
import logging

logger = logging.getLogger(__name__)
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')

_dynamo_resource = None

def _get_resource():
    global _dynamo_resource
    if _dynamo_resource is None:
        _dynamo_resource = boto3.resource('dynamodb', region_name=AWS_REGION)
    return _dynamo_resource

def get_table(table_name: str):
    """Return a DynamoDB Table resource for the given table name."""
    resource = _get_resource()
    return resource.Table(table_name)

def get_item(table_name: str, item_id: str):
    table = get_table(table_name)
    resp = table.get_item(Key={'id': item_id})
    return resp.get('Item')


class AWSConnector:
    """Connector for AWS services - real boto3 implementation"""

    def __init__(self, access_key_id: str, secret_access_key: str, regions: List[str]):
        """
        Initialize AWS Connector with credentials
        
        Args:
            access_key_id: AWS Access Key ID
            secret_access_key: AWS Secret Access Key
            regions: List of AWS regions to evaluate
        """
        self.access_key_id = access_key_id
        self.secret_access_key = secret_access_key
        self.regions = regions if regions else ['us-east-1']
        self.iam_client = None
        self.cloudtrail_clients = {}
        self.config_clients = {}
        self.guardduty_clients = {}
        self.kms_clients = {}
        self.s3_client = None

    def validate_credentials(self):
        """Validate AWS credentials using STS"""
        try:
            sts_client = boto3.client(
                'sts',
                aws_access_key_id=self.access_key_id,
                aws_secret_access_key=self.secret_access_key,
                region_name='us-east-1'
            )
            identity = sts_client.get_caller_identity()
            logger.info(f"AWS Credentials validated for account: {identity['Account']}")
            return identity
        except (NoCredentialsError, ClientError) as e:
            raise Exception(f"AWS Credentials validation failed: {str(e)}")

    def _get_iam_client(self):
        """Get or create IAM client"""
        if not self.iam_client:
            self.iam_client = boto3.client(
                'iam',
                aws_access_key_id=self.access_key_id,
                aws_secret_access_key=self.secret_access_key,
                region_name='us-east-1'
            )
        return self.iam_client

    def _get_cloudtrail_client(self, region: str):
        """Get or create CloudTrail client for specific region"""
        if region not in self.cloudtrail_clients:
            self.cloudtrail_clients[region] = boto3.client(
                'cloudtrail',
                aws_access_key_id=self.access_key_id,
                aws_secret_access_key=self.secret_access_key,
                region_name=region
            )
        return self.cloudtrail_clients[region]

    def _get_config_client(self, region: str):
        """Get or create Config client for specific region"""
        if region not in self.config_clients:
            self.config_clients[region] = boto3.client(
                'config',
                aws_access_key_id=self.access_key_id,
                aws_secret_access_key=self.secret_access_key,
                region_name=region
            )
        return self.config_clients[region]

    def _get_guardduty_client(self, region: str):
        """Get or create GuardDuty client for specific region"""
        if region not in self.guardduty_clients:
            self.guardduty_clients[region] = boto3.client(
                'guardduty',
                aws_access_key_id=self.access_key_id,
                aws_secret_access_key=self.secret_access_key,
                region_name=region
            )
        return self.guardduty_clients[region]

    def _get_kms_client(self, region: str):
        """Get or create KMS client for specific region"""
        if region not in self.kms_clients:
            self.kms_clients[region] = boto3.client(
                'kms',
                aws_access_key_id=self.access_key_id,
                aws_secret_access_key=self.secret_access_key,
                region_name=region
            )
        return self.kms_clients[region]

    def _get_s3_client(self):
        """Get or create S3 client"""
        if not self.s3_client:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=self.access_key_id,
                aws_secret_access_key=self.secret_access_key,
                region_name='us-east-1'
            )
        return self.s3_client

    # ==================== IAM METHODS ====================

    def get_iam_users(self) -> List[Dict[str, Any]]:
        """Get all IAM users from AWS account"""
        try:
            client = self._get_iam_client()
            response = client.list_users()
            users = []
            for user in response.get('Users', []):
                user_data = {
                    'arn': user['Arn'],
                    'user_name': user['UserName'],
                    'create_date': str(user['CreateDate']),
                    'access_keys': [],
                    'mfa_enabled': False,
                    'policies': []
                }
                
                # Check access keys
                keys_resp = client.list_access_keys(UserName=user['UserName'])
                user_data['access_keys'] = [
                    {
                        'access_key_id': key['AccessKeyId'],
                        'status': key['Status'],
                        'create_date': str(key['CreateDate'])
                    }
                    for key in keys_resp.get('AccessKeyMetadata', [])
                ]
                
                # Check MFA devices
                mfa_resp = client.list_mfa_devices(UserName=user['UserName'])
                user_data['mfa_enabled'] = len(mfa_resp.get('MFADevices', [])) > 0
                
                # Get attached policies
                policies_resp = client.list_attached_user_policies(UserName=user['UserName'])
                user_data['policies'] = [
                    {'name': p['PolicyName'], 'arn': p['PolicyArn']}
                    for p in policies_resp.get('AttachedPolicies', [])
                ]
                
                users.append(user_data)
            
            return users
        except ClientError as e:
            logger.error(f"Error getting IAM users: {str(e)}")
            return []

    def get_iam_roles(self) -> List[Dict[str, Any]]:
        """Get all IAM roles from AWS account"""
        try:
            client = self._get_iam_client()
            response = client.list_roles()
            roles = []
            for role in response.get('Roles', []):
                role_data = {
                    'arn': role['Arn'],
                    'role_name': role['RoleName'],
                    'create_date': str(role['CreateDate']),
                    'assume_role_policy': role.get('AssumeRolePolicyDocument', {}),
                    'policies': []
                }
                
                # Get attached policies
                policies_resp = client.list_attached_role_policies(RoleName=role['RoleName'])
                role_data['policies'] = [
                    {'name': p['PolicyName'], 'arn': p['PolicyArn']}
                    for p in policies_resp.get('AttachedPolicies', [])
                ]
                
                roles.append(role_data)
            
            return roles
        except ClientError as e:
            logger.error(f"Error getting IAM roles: {str(e)}")
            return []

    def get_iam_policies(self) -> List[Dict[str, Any]]:
        """Get all customer-managed IAM policies"""
        try:
            client = self._get_iam_client()
            response = client.list_policies(Scope='Local')
            policies = []
            for policy in response.get('Policies', []):
                policies.append({
                    'arn': policy['Arn'],
                    'policy_name': policy['PolicyName'],
                    'create_date': str(policy['CreateDate']),
                    'attachment_count': policy['AttachmentCount']
                })
            return policies
        except ClientError as e:
            logger.error(f"Error getting IAM policies: {str(e)}")
            return []

    def get_password_policy(self) -> Dict[str, Any]:
        """Get IAM password policy"""
        try:
            client = self._get_iam_client()
            response = client.get_account_password_policy()
            policy = response.get('PasswordPolicy', {})
            return {
                'min_password_length': policy.get('MinimumPasswordLength'),
                'require_symbols': policy.get('RequireSymbols'),
                'require_numbers': policy.get('RequireNumbers'),
                'require_uppercase': policy.get('RequireUppercaseCharacters'),
                'require_lowercase': policy.get('RequireLowercaseCharacters'),
                'allow_users_to_change': policy.get('AllowUsersToChangePassword'),
                'expire_passwords': policy.get('ExpirePasswords'),
                'password_reuse_prevention': policy.get('PasswordReusePrevention')
            }
        except ClientError as e:
            logger.warning(f"No password policy configured: {str(e)}")
            return {}

    # ==================== CLOUDTRAIL METHODS ====================

    def get_cloudtrail_trails(self, region: str) -> List[Dict[str, Any]]:
        """Get CloudTrail trails for specific region"""
        try:
            client = self._get_cloudtrail_client(region)
            response = client.describe_trails()
            trails = []
            for trail in response.get('trailList', []):
                trail_data = {
                    'name': trail.get('Name'),
                    'arn': trail.get('TrailARN'),
                    's3_bucket': trail.get('S3BucketName'),
                    'include_global_service_events': trail.get('IncludeGlobalServiceEvents'),
                    'is_multi_region_trail': trail.get('IsMultiRegionTrail'),
                    'has_custom_event_selectors': trail.get('HasCustomEventSelectors'),
                    'has_organization_trail': trail.get('IsOrganizationTrail'),
                    'region': region
                }
                
                # Get trail status
                trail_name = trail.get('TrailARN', trail.get('Name'))
                try:
                    status_resp = client.get_trail_status(Name=trail_name)
                    trail_data['is_logging'] = status_resp.get('IsLogging')
                    trail_data['latest_delivery_time'] = str(status_resp.get('LatestDeliveryTime', ''))
                except:
                    trail_data['is_logging'] = False
                
                trails.append(trail_data)
            
            return trails
        except ClientError as e:
            logger.error(f"Error getting CloudTrail trails in {region}: {str(e)}")
            return []

    # ==================== AWS CONFIG METHODS ====================

    def get_config_status(self, region: str) -> Dict[str, Any]:
        """Get AWS Config status for specific region"""
        try:
            client = self._get_config_client(region)
            recorders = client.describe_config_recorders()
            config_data = {
                'region': region,
                'enabled': False,
                'recording': False,
                'recorders': []
            }
            
            for recorder in recorders.get('ConfigurationRecorders', []):
                recorder_data = {
                    'name': recorder.get('name'),
                    'role_arn': recorder.get('roleARN'),
                    'recording_group': recorder.get('recordingGroup')
                }
                
                # Check if recording
                status = client.describe_config_recorder_status(
                    ConfigurationRecorderNames=[recorder['name']]
                )
                for s in status.get('ConfigurationRecordersStatus', []):
                    if s['name'] == recorder['name']:
                        recorder_data['recording'] = s.get('recording', False)
                        recorder_data['last_status_change_time'] = str(s.get('lastStatusChangeTime', ''))
                
                config_data['recorders'].append(recorder_data)
                if recorder_data.get('recording'):
                    config_data['enabled'] = True
                    config_data['recording'] = True
            
            return config_data
        except ClientError as e:
            logger.error(f"Error getting AWS Config status in {region}: {str(e)}")
            return {'region': region, 'enabled': False, 'recording': False, 'recorders': []}

    # ==================== GUARDDUTY METHODS ====================

    def get_guardduty_detectors(self, region: str) -> List[Dict[str, Any]]:
        """Get GuardDuty detectors for specific region"""
        try:
            client = self._get_guardduty_client(region)
            response = client.list_detectors()
            detectors = []
            
            for detector_id in response.get('DetectorIds', []):
                detector_resp = client.get_detector(DetectorId=detector_id)
                detector_data = {
                    'detector_id': detector_id,
                    'region': region,
                    'status': detector_resp.get('Status'),
                    'created_at': str(detector_resp.get('CreatedAt', '')),
                    'updated_at': str(detector_resp.get('UpdatedAt', '')),
                    'finding_publishing_frequency': detector_resp.get('FindingPublishingFrequency'),
                    'findings': 0
                }
                
                # Get findings count
                findings = client.list_findings(DetectorId=detector_id)
                detector_data['findings'] = len(findings.get('FindingIds', []))
                
                detectors.append(detector_data)
            
            return detectors
        except ClientError as e:
            logger.error(f"Error getting GuardDuty detectors in {region}: {str(e)}")
            return []

    # ==================== KMS METHODS ====================

    def get_kms_keys(self, region: str) -> List[Dict[str, Any]]:
        """Get KMS keys for specific region"""
        try:
            client = self._get_kms_client(region)
            response = client.list_keys()
            keys = []
            
            for key in response.get('Keys', []):
                key_id = key['KeyId']
                key_meta = client.describe_key(KeyId=key_id)
                key_data = {
                    'key_id': key_id,
                    'arn': key_meta['KeyMetadata'].get('Arn'),
                    'description': key_meta['KeyMetadata'].get('Description'),
                    'creation_date': str(key_meta['KeyMetadata'].get('CreationDate', '')),
                    'enabled': key_meta['KeyMetadata'].get('Enabled'),
                    'key_state': key_meta['KeyMetadata'].get('KeyState'),
                    'key_usage': key_meta['KeyMetadata'].get('KeyUsage'),
                    'region': region
                }
                keys.append(key_data)
            
            return keys
        except ClientError as e:
            logger.error(f"Error getting KMS keys in {region}: {str(e)}")
            return []

    # ==================== S3 METHODS ====================

    def get_s3_buckets(self) -> List[Dict[str, Any]]:
        """Get all S3 buckets and their encryption status"""
        try:
            client = self._get_s3_client()
            response = client.list_buckets()
            buckets = []
            
            for bucket in response.get('Buckets', []):
                bucket_name = bucket['Name']
                bucket_data = {
                    'name': bucket_name,
                    'creation_date': str(bucket['CreationDate']),
                    'encryption_enabled': False,
                    'versioning_enabled': False,
                    'public_access_blocked': False,
                    'server_side_encryption': {}
                }
                
                # Check server-side encryption
                try:
                    encryption = client.get_bucket_encryption(Bucket=bucket_name)
                    if 'ServerSideEncryptionConfiguration' in encryption:
                        bucket_data['encryption_enabled'] = True
                        bucket_data['server_side_encryption'] = {
                            'rules': encryption['ServerSideEncryptionConfiguration'].get('Rules', [])
                        }
                except:
                    pass
                
                # Check versioning
                try:
                    versioning = client.get_bucket_versioning(Bucket=bucket_name)
                    bucket_data['versioning_enabled'] = versioning.get('Status') == 'Enabled'
                except:
                    pass
                
                # Check public access block
                try:
                    public_block = client.get_public_access_block(Bucket=bucket_name)
                    config = public_block.get('PublicAccessBlockConfiguration', {})
                    bucket_data['public_access_blocked'] = all([
                        config.get('BlockPublicAcls'),
                        config.get('BlockPublicPolicy'),
                        config.get('IgnorePublicAcls'),
                        config.get('RestrictPublicBuckets')
                    ])
                except:
                    pass
                
                buckets.append(bucket_data)
            
            return buckets
        except ClientError as e:
            logger.error(f"Error getting S3 buckets: {str(e)}")
            return []

    async def get_resources_by_service(self, service: str) -> List[Dict[str, Any]]:
        """
        Get resources from AWS account for specific service
        Only returns data for the first region
        """
        try:
            region = self.regions[0] if self.regions else 'us-east-1'
            
            if service == 'iam':
                return self.get_iam_users()
            elif service == 'cloudtrail':
                return self.get_cloudtrail_trails(region)
            elif service == 'config':
                return [self.get_config_status(region)]
            elif service == 'guardduty':
                return self.get_guardduty_detectors(region)
            elif service == 'kms':
                return self.get_kms_keys(region)
            elif service == 's3':
                return self.get_s3_buckets()
            else:
                logger.warning(f"Unknown service: {service}")
                return []
        except Exception as e:
            logger.error(f"Error getting resources for service {service}: {str(e)}")
            return []

