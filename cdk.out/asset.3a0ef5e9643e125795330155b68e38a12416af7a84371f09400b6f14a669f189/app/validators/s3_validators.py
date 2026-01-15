import boto3
from botocore.exceptions import ClientError
from .base import ValidatorBase


class S3PublicAccessValidator(ValidatorBase):
    name = 's3-public-access'

    def run(self, name: str, region: str = None, account_id: str = None, extra=None):
        """
        Check whether an S3 bucket has public access allowed.
        Returns {'name': str, 'status': 'PASS'|'FAIL', 'details': {...}}
        """
        s3 = boto3.client('s3', region_name=region)
        result = {'name': self.name, 'resource': name}
        try:
            # Check public access block
            try:
                pab = s3.get_public_access_block(Bucket=name)
                pab_cfg = pab.get('PublicAccessBlockConfiguration', {})
                blocked = all([pab_cfg.get('BlockPublicAcls'), pab_cfg.get('IgnorePublicAcls'), pab_cfg.get('BlockPublicPolicy'), pab_cfg.get('RestrictPublicBuckets')])
            except ClientError:
                blocked = False

            # Check ACL for AllUsers or AuthenticatedUsers grants (best-effort)
            try:
                acl = s3.get_bucket_acl(Bucket=name)
                grants = acl.get('Grants', [])
                public_acl = any(g.get('Grantee', {}).get('URI') in ('http://acs.amazonaws.com/groups/global/AllUsers', 'http://acs.amazonaws.com/groups/global/AuthenticatedUsers') for g in grants)
            except ClientError:
                public_acl = False

            if blocked and not public_acl:
                result['status'] = 'PASS'
                result['details'] = {'public_block': True}
            else:
                result['status'] = 'FAIL'
                result['details'] = {'public_block': blocked, 'public_acl': public_acl}
        except Exception as e:
            result['status'] = 'ERROR'
            result['details'] = {'error': str(e)}
        return result
