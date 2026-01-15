import boto3
from botocore.exceptions import ClientError
from .base import ValidatorBase


class ConfigRecorderValidator(ValidatorBase):
    name = 'config-recorder'

    def run(self, name: str = None, region: str = None, account_id: str = None, extra=None):
        cfg = boto3.client('config', region_name=region)
        result = {'name': self.name}
        try:
            recs = cfg.describe_configuration_recorders().get('ConfigurationRecorders', [])
            if not recs:
                result['status'] = 'FAIL'
                result['details'] = {'recorders': 0}
                return result
            statuses = cfg.describe_configuration_recorder_status().get('ConfigurationRecordersStatus', [])
            recording = any(s.get('recording') for s in statuses)
            result['status'] = 'PASS' if recording else 'FAIL'
            result['details'] = {'recording': recording}
        except ClientError as e:
            result['status'] = 'ERROR'
            result['details'] = {'error': str(e)}
        return result
