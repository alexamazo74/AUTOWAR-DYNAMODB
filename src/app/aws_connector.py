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

    def __init__(self, access_key_id: str, secret_access_key: str, session_token: str | None = None, regions: List[str] = None):
        """
        Initialize AWS Connector with credentials
        
        Args:
            access_key_id: AWS Access Key ID
            secret_access_key: AWS Secret Access Key
            session_token: Optional AWS session token (for STS temporary creds)
            regions: List of AWS regions to evaluate
        """
        self.access_key_id = access_key_id
        self.secret_access_key = secret_access_key
        self.session_token = session_token
        self.regions = regions if regions else ['us-east-1']
        self.iam_client = None
        self.cloudtrail_clients = {}
        self.config_clients = {}
        self.guardduty_clients = {}
        self.kms_clients = {}
        self.s3_client = None
        self.ec2_clients = {}
        self.rds_clients = {}
        self.lambda_clients = {}
        self.secretsmanager_clients = {}
        self.cloudwatch_clients = {}
        self.sns_clients = {}
        self.logs_clients = {}
        self.organizations_client = None

    def validate_credentials(self):
        """Validate AWS credentials using STS"""
        try:
            sts_client = boto3.client(
                'sts',
                aws_access_key_id=self.access_key_id,
                aws_secret_access_key=self.secret_access_key,
                aws_session_token=self.session_token,
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
                aws_session_token=self.session_token,
                region_name='us-east-1',
                config=boto3.session.Config(
                    connect_timeout=30,
                    read_timeout=120,
                    retries={'max_attempts': 3, 'mode': 'adaptive'}
                )
            )
        return self.iam_client

    def _get_cloudtrail_client(self, region: str):
        """Get or create CloudTrail client for specific region"""
        if region not in self.cloudtrail_clients:
            self.cloudtrail_clients[region] = boto3.client(
                'cloudtrail',
                aws_access_key_id=self.access_key_id,
                aws_secret_access_key=self.secret_access_key,
                aws_session_token=self.session_token,
                region_name=region,
                config=boto3.session.Config(connect_timeout=30, read_timeout=120, retries={'max_attempts': 3, 'mode': 'adaptive'})
            )
        return self.cloudtrail_clients[region]

    def _get_config_client(self, region: str):
        """Get or create Config client for specific region"""
        if region not in self.config_clients:
            self.config_clients[region] = boto3.client(
                'config',
                aws_access_key_id=self.access_key_id,
                aws_secret_access_key=self.secret_access_key,
                aws_session_token=self.session_token,
                region_name=region,
                config=boto3.session.Config(connect_timeout=30, read_timeout=120, retries={'max_attempts': 3, 'mode': 'adaptive'})
            )
        return self.config_clients[region]

    def _get_guardduty_client(self, region: str):
        """Get or create GuardDuty client for specific region"""
        if region not in self.guardduty_clients:
            self.guardduty_clients[region] = boto3.client(
                'guardduty',
                aws_access_key_id=self.access_key_id,
                aws_secret_access_key=self.secret_access_key,
                aws_session_token=self.session_token,
                region_name=region,
                config=boto3.session.Config(connect_timeout=30, read_timeout=120, retries={'max_attempts': 3, 'mode': 'adaptive'})
            )
        return self.guardduty_clients[region]

    def _get_kms_client(self, region: str):
        """Get or create KMS client for specific region"""
        if region not in self.kms_clients:
            self.kms_clients[region] = boto3.client(
                'kms',
                aws_access_key_id=self.access_key_id,
                aws_secret_access_key=self.secret_access_key,
                aws_session_token=self.session_token,
                region_name=region,
                config=boto3.session.Config(connect_timeout=30, read_timeout=120, retries={'max_attempts': 3, 'mode': 'adaptive'})
            )
        return self.kms_clients[region]

    def _get_s3_client(self):
        """Get or create S3 client"""
        if not self.s3_client:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=self.access_key_id,
                aws_secret_access_key=self.secret_access_key,
                aws_session_token=self.session_token,
                region_name='us-east-1',
                config=boto3.session.Config(connect_timeout=30, read_timeout=120, retries={'max_attempts': 3, 'mode': 'adaptive'})
            )
        return self.s3_client

    def _get_ec2_client(self, region: str):
        """Get or create EC2 client for specific region"""
        if region not in self.ec2_clients:
            self.ec2_clients[region] = boto3.client(
                'ec2',
                aws_access_key_id=self.access_key_id,
                aws_secret_access_key=self.secret_access_key,
                aws_session_token=self.session_token,
                region_name=region,
                config=boto3.session.Config(connect_timeout=30, read_timeout=120, retries={'max_attempts': 3, 'mode': 'adaptive'})
            )
        return self.ec2_clients[region]

    def _get_rds_client(self, region: str):
        """Get or create RDS client for specific region"""
        if region not in self.rds_clients:
            self.rds_clients[region] = boto3.client(
                'rds',
                aws_access_key_id=self.access_key_id,
                aws_secret_access_key=self.secret_access_key,
                aws_session_token=self.session_token,
                region_name=region,
                config=boto3.session.Config(connect_timeout=30, read_timeout=120, retries={'max_attempts': 3, 'mode': 'adaptive'})
            )
        return self.rds_clients[region]

    def _get_lambda_client(self, region: str):
        """Get or create Lambda client for specific region"""
        if region not in self.lambda_clients:
            self.lambda_clients[region] = boto3.client(
                'lambda',
                aws_access_key_id=self.access_key_id,
                aws_secret_access_key=self.secret_access_key,
                aws_session_token=self.session_token,
                region_name=region,
                config=boto3.session.Config(connect_timeout=30, read_timeout=120, retries={'max_attempts': 3, 'mode': 'adaptive'})
            )
        return self.lambda_clients[region]

    def _get_secretsmanager_client(self, region: str):
        """Get or create Secrets Manager client for specific region"""
        if region not in self.secretsmanager_clients:
            self.secretsmanager_clients[region] = boto3.client(
                'secretsmanager',
                aws_access_key_id=self.access_key_id,
                aws_secret_access_key=self.secret_access_key,
                aws_session_token=self.session_token,
                region_name=region,
                config=boto3.session.Config(connect_timeout=30, read_timeout=120, retries={'max_attempts': 3, 'mode': 'adaptive'})
            )
        return self.secretsmanager_clients[region]

    def _get_cloudwatch_client(self, region: str):
        """Get or create CloudWatch client for specific region"""
        if region not in self.cloudwatch_clients:
            self.cloudwatch_clients[region] = boto3.client(
                'cloudwatch',
                aws_access_key_id=self.access_key_id,
                aws_secret_access_key=self.secret_access_key,
                aws_session_token=self.session_token,
                region_name=region,
                config=boto3.session.Config(connect_timeout=30, read_timeout=120, retries={'max_attempts': 3, 'mode': 'adaptive'})
            )
        return self.cloudwatch_clients[region]

    def _get_sns_client(self, region: str):
        """Get or create SNS client for specific region"""
        if region not in self.sns_clients:
            self.sns_clients[region] = boto3.client(
                'sns',
                aws_access_key_id=self.access_key_id,
                aws_secret_access_key=self.secret_access_key,
                aws_session_token=self.session_token,
                region_name=region,
                config=boto3.session.Config(connect_timeout=30, read_timeout=120, retries={'max_attempts': 3, 'mode': 'adaptive'})
            )
        return self.sns_clients[region]

    def _get_logs_client(self, region: str):
        """Get or create CloudWatch Logs client for specific region"""
        if region not in self.logs_clients:
            self.logs_clients[region] = boto3.client(
                'logs',
                aws_access_key_id=self.access_key_id,
                aws_secret_access_key=self.secret_access_key,
                aws_session_token=self.session_token,
                region_name=region,
                config=boto3.session.Config(connect_timeout=30, read_timeout=120, retries={'max_attempts': 3, 'mode': 'adaptive'})
            )
        return self.logs_clients[region]

    def _get_organizations_client(self):
        """Get or create Organizations client"""
        if not self.organizations_client:
            self.organizations_client = boto3.client(
                'organizations',
                aws_access_key_id=self.access_key_id,
                aws_secret_access_key=self.secret_access_key,
                aws_session_token=self.session_token,
                region_name='us-east-1',
                config=boto3.session.Config(connect_timeout=30, read_timeout=120, retries={'max_attempts': 3, 'mode': 'adaptive'})
            )
        return self.organizations_client

    # ==================== IAM METHODS ====================

    def get_iam_users(self) -> List[Dict[str, Any]]:
        """Get all IAM users from AWS account"""
        try:
            logger.info("[AWS-CONN] Starting get_iam_users()")
            client = self._get_iam_client()
            logger.info("[AWS-CONN] IAM client created, calling list_users()...")
            response = client.list_users()
            logger.info(f"[AWS-CONN] list_users() returned {len(response.get('Users', []))} users")
            users = []
            for user in response.get('Users', []):
                logger.info(f"[AWS-CONN] Processing user: {user['UserName']}")
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
                logger.info(f"[AWS-CONN] User {user['UserName']}: MFA enabled = {user_data['mfa_enabled']}, Access keys = {len(user_data['access_keys'])}")
                
                # Get attached policies
                policies_resp = client.list_attached_user_policies(UserName=user['UserName'])
                user_data['policies'] = [
                    {'name': p['PolicyName'], 'arn': p['PolicyArn']}
                    for p in policies_resp.get('AttachedPolicies', [])
                ]
                
                users.append(user_data)
            
            logger.info(f"[AWS-CONN] get_iam_users() completed successfully. Total users: {len(users)}")
            return users
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            error_msg = e.response.get('Error', {}).get('Message', str(e))
            logger.error(f"[AWS-CONN] ClientError getting IAM users: {error_code} - {error_msg}")
            raise
        except Exception as e:
            logger.error(f"[AWS-CONN] Unexpected error getting IAM users: {str(e)}", exc_info=True)
            raise

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

    # ==================== EC2 METHODS ====================

    def get_ec2_instances(self, region: str) -> List[Dict[str, Any]]:
        """Get EC2 instances in specific region"""
        try:
            client = self._get_ec2_client(region)
            response = client.describe_instances()
            instances = []
            
            for reservation in response.get('Reservations', []):
                for instance in reservation.get('Instances', []):
                    instance_data = {
                        'instance_id': instance.get('InstanceId'),
                        'instance_type': instance.get('InstanceType'),
                        'state': instance.get('State', {}).get('Name'),
                        'launch_time': str(instance.get('LaunchTime', '')),
                        'vpc_id': instance.get('VpcId'),
                        'subnet_id': instance.get('SubnetId'),
                        'public_ip': instance.get('PublicIpAddress'),
                        'private_ip': instance.get('PrivateIpAddress'),
                        'iam_instance_profile': instance.get('IamInstanceProfile'),
                        'security_groups': [sg['GroupId'] for sg in instance.get('SecurityGroups', [])],
                        'monitoring': instance.get('Monitoring', {}).get('State'),
                        'region': region,
                        'encrypted_volumes': []
                    }
                    
                    # Check EBS encryption
                    for bdm in instance.get('BlockDeviceMappings', []):
                        if 'Ebs' in bdm:
                            volume_id = bdm['Ebs'].get('VolumeId')
                            try:
                                vol_resp = client.describe_volumes(VolumeIds=[volume_id])
                                if vol_resp.get('Volumes'):
                                    volume = vol_resp['Volumes'][0]
                                    instance_data['encrypted_volumes'].append({
                                        'volume_id': volume_id,
                                        'encrypted': volume.get('Encrypted', False)
                                    })
                            except:
                                pass
                    
                    instances.append(instance_data)
            
            return instances
        except ClientError as e:
            logger.error(f"Error getting EC2 instances in {region}: {str(e)}")
            return []

    def get_vpcs(self, region: str) -> List[Dict[str, Any]]:
        """Get VPCs in specific region"""
        try:
            client = self._get_ec2_client(region)
            response = client.describe_vpcs()
            vpcs = []
            
            for vpc in response.get('Vpcs', []):
                vpc_data = {
                    'vpc_id': vpc.get('VpcId'),
                    'cidr_block': vpc.get('CidrBlock'),
                    'is_default': vpc.get('IsDefault'),
                    'state': vpc.get('State'),
                    'region': region
                }
                vpcs.append(vpc_data)
            
            return vpcs
        except ClientError as e:
            logger.error(f"Error getting VPCs in {region}: {str(e)}")
            return []

    def get_security_groups(self, region: str) -> List[Dict[str, Any]]:
        """Get Security Groups in specific region"""
        try:
            client = self._get_ec2_client(region)
            response = client.describe_security_groups()
            groups = []
            
            for sg in response.get('SecurityGroups', []):
                # Check for overly permissive rules
                open_to_world = False
                for rule in sg.get('IpPermissions', []):
                    for ip_range in rule.get('IpRanges', []):
                        if ip_range.get('CidrIp') == '0.0.0.0/0':
                            open_to_world = True
                            break
                
                sg_data = {
                    'group_id': sg.get('GroupId'),
                    'group_name': sg.get('GroupName'),
                    'description': sg.get('Description'),
                    'vpc_id': sg.get('VpcId'),
                    'ingress_rules_count': len(sg.get('IpPermissions', [])),
                    'egress_rules_count': len(sg.get('IpPermissionsEgress', [])),
                    'open_to_world': open_to_world,
                    'region': region
                }
                groups.append(sg_data)
            
            return groups
        except ClientError as e:
            logger.error(f"Error getting Security Groups in {region}: {str(e)}")
            return []

    def get_ebs_volumes(self, region: str) -> List[Dict[str, Any]]:
        """Get EBS volumes in specific region"""
        try:
            client = self._get_ec2_client(region)
            response = client.describe_volumes()
            volumes = []
            
            for vol in response.get('Volumes', []):
                volume_data = {
                    'volume_id': vol.get('VolumeId'),
                    'size': vol.get('Size'),
                    'volume_type': vol.get('VolumeType'),
                    'encrypted': vol.get('Encrypted', False),
                    'kms_key_id': vol.get('KmsKeyId'),
                    'state': vol.get('State'),
                    'region': region
                }
                volumes.append(volume_data)
            
            return volumes
        except ClientError as e:
            logger.error(f"Error getting EBS volumes in {region}: {str(e)}")
            return []

    # ==================== RDS METHODS ====================

    def get_rds_instances(self, region: str) -> List[Dict[str, Any]]:
        """Get RDS instances in specific region"""
        try:
            client = self._get_rds_client(region)
            response = client.describe_db_instances()
            instances = []
            
            for db in response.get('DBInstances', []):
                instance_data = {
                    'db_instance_identifier': db.get('DBInstanceIdentifier'),
                    'engine': db.get('Engine'),
                    'engine_version': db.get('EngineVersion'),
                    'db_instance_class': db.get('DBInstanceClass'),
                    'publicly_accessible': db.get('PubliclyAccessible', False),
                    'encrypted': db.get('StorageEncrypted', False),
                    'kms_key_id': db.get('KmsKeyId'),
                    'backup_retention_period': db.get('BackupRetentionPeriod', 0),
                    'multi_az': db.get('MultiAZ', False),
                    'vpc_security_groups': [sg['VpcSecurityGroupId'] for sg in db.get('VpcSecurityGroups', [])],
                    'region': region
                }
                instances.append(instance_data)
            
            return instances
        except ClientError as e:
            logger.error(f"Error getting RDS instances in {region}: {str(e)}")
            return []

    # ==================== LAMBDA METHODS ====================

    def get_lambda_functions(self, region: str) -> List[Dict[str, Any]]:
        """Get Lambda functions in specific region"""
        try:
            client = self._get_lambda_client(region)
            response = client.list_functions()
            functions = []
            
            for func in response.get('Functions', []):
                function_data = {
                    'function_name': func.get('FunctionName'),
                    'function_arn': func.get('FunctionArn'),
                    'runtime': func.get('Runtime'),
                    'role': func.get('Role'),
                    'handler': func.get('Handler'),
                    'vpc_config': func.get('VpcConfig'),
                    'environment_variables': bool(func.get('Environment', {}).get('Variables')),
                    'kms_key_arn': func.get('KMSKeyArn'),
                    'region': region
                }
                functions.append(function_data)
            
            return functions
        except ClientError as e:
            logger.error(f"Error getting Lambda functions in {region}: {str(e)}")
            return []

    # ==================== SECRETS MANAGER METHODS ====================

    def get_secrets(self, region: str) -> List[Dict[str, Any]]:
        """Get secrets from Secrets Manager in specific region"""
        try:
            client = self._get_secretsmanager_client(region)
            response = client.list_secrets()
            secrets = []
            
            for secret in response.get('SecretList', []):
                secret_data = {
                    'name': secret.get('Name'),
                    'arn': secret.get('ARN'),
                    'description': secret.get('Description'),
                    'kms_key_id': secret.get('KmsKeyId'),
                    'rotation_enabled': secret.get('RotationEnabled', False),
                    'last_rotated_date': str(secret.get('LastRotatedDate', '')),
                    'region': region
                }
                secrets.append(secret_data)
            
            return secrets
        except ClientError as e:
            logger.error(f"Error getting secrets in {region}: {str(e)}")
            return []

    # ==================== CLOUDWATCH METHODS ====================

    def get_cloudwatch_alarms(self, region: str) -> List[Dict[str, Any]]:
        """Get CloudWatch alarms in specific region"""
        try:
            client = self._get_cloudwatch_client(region)
            response = client.describe_alarms()
            alarms = []
            
            for alarm in response.get('MetricAlarms', []):
                alarm_data = {
                    'alarm_name': alarm.get('AlarmName'),
                    'alarm_arn': alarm.get('AlarmArn'),
                    'state_value': alarm.get('StateValue'),
                    'actions_enabled': alarm.get('ActionsEnabled'),
                    'alarm_actions': alarm.get('AlarmActions', []),
                    'metric_name': alarm.get('MetricName'),
                    'namespace': alarm.get('Namespace'),
                    'region': region
                }
                alarms.append(alarm_data)
            
            return alarms
        except ClientError as e:
            logger.error(f"Error getting CloudWatch alarms in {region}: {str(e)}")
            return []

    def get_log_groups(self, region: str) -> List[Dict[str, Any]]:
        """Get CloudWatch Log Groups in specific region"""
        try:
            client = self._get_logs_client(region)
            response = client.describe_log_groups()
            log_groups = []
            
            for lg in response.get('logGroups', []):
                log_data = {
                    'log_group_name': lg.get('logGroupName'),
                    'arn': lg.get('arn'),
                    'creation_time': lg.get('creationTime'),
                    'retention_in_days': lg.get('retentionInDays'),
                    'kms_key_id': lg.get('kmsKeyId'),
                    'stored_bytes': lg.get('storedBytes'),
                    'region': region
                }
                log_groups.append(log_data)
            
            return log_groups
        except ClientError as e:
            logger.error(f"Error getting log groups in {region}: {str(e)}")
            return []

    # ==================== SNS METHODS ====================

    def get_sns_topics(self, region: str) -> List[Dict[str, Any]]:
        """Get SNS topics in specific region"""
        try:
            client = self._get_sns_client(region)
            response = client.list_topics()
            topics = []
            
            for topic in response.get('Topics', []):
                topic_arn = topic.get('TopicArn')
                attrs = client.get_topic_attributes(TopicArn=topic_arn)
                topic_data = {
                    'topic_arn': topic_arn,
                    'display_name': attrs.get('Attributes', {}).get('DisplayName'),
                    'subscriptions_confirmed': attrs.get('Attributes', {}).get('SubscriptionsConfirmed'),
                    'kms_master_key_id': attrs.get('Attributes', {}).get('KmsMasterKeyId'),
                    'region': region
                }
                topics.append(topic_data)
            
            return topics
        except ClientError as e:
            logger.error(f"Error getting SNS topics in {region}: {str(e)}")
            return []

    # ==================== ORGANIZATIONS METHODS ====================

    def get_organization_info(self) -> Dict[str, Any]:
        """Get AWS Organization information"""
        try:
            client = self._get_organizations_client()
            org_resp = client.describe_organization()
            org = org_resp.get('Organization', {})
            
            # Get accounts
            accounts_resp = client.list_accounts()
            accounts = accounts_resp.get('Accounts', [])
            
            return {
                'id': org.get('Id'),
                'arn': org.get('Arn'),
                'master_account_id': org.get('MasterAccountId'),
                'feature_set': org.get('FeatureSet'),
                'accounts_count': len(accounts),
                'accounts': [{'id': a.get('Id'), 'name': a.get('Name'), 'email': a.get('Email')} for a in accounts]
            }
        except ClientError as e:
            logger.warning(f"Organization not configured or no access: {str(e)}")
            return {'enabled': False, 'reason': str(e)}


