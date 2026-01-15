import boto3
from botocore.exceptions import ClientError
from .base import ValidatorBase


class IAMPasswordPolicyValidator(ValidatorBase):
    name = 'iam-password-policy'

    def run(self, name: str = None, region: str = None, account_id: str = None, extra=None):
        iam = boto3.client('iam')
        result = {'name': self.name}
        try:
            policy = iam.get_account_password_policy()
            pwd = policy.get('PasswordPolicy', {})
            good = (
                pwd.get('MinimumPasswordLength', 0) >= 14 and
                pwd.get('RequireSymbols', False) and
                pwd.get('RequireNumbers', False) and
                pwd.get('RequireUppercaseCharacters', False) and
                pwd.get('RequireLowercaseCharacters', False)
            )
            result['status'] = 'PASS' if good else 'FAIL'
            result['details'] = {'policy': pwd}
        except ClientError as e:
            # no policy or access denied
            result['status'] = 'FAIL'
            result['details'] = {'error': str(e)}
        return result


class RootMFAValidator(ValidatorBase):
    name = 'iam-root-mfa'

    def run(self, name: str = None, region: str = None, account_id: str = None, extra=None):
        iam = boto3.client('iam')
        result = {'name': self.name}
        try:
            summary = iam.get_account_summary()
            # AccountMFAEnabled key indicates if account has any MFA devices
            enabled = bool(summary.get('SummaryMap', {}).get('AccountMFAEnabled'))
            result['status'] = 'PASS' if enabled else 'FAIL'
            result['details'] = {'AccountMFAEnabled': enabled}
        except ClientError as e:
            result['status'] = 'ERROR'
            result['details'] = {'error': str(e)}
        return result
