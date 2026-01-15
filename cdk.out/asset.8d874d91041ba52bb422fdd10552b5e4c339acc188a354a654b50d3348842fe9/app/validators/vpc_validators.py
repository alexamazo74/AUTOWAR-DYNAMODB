import boto3
from botocore.exceptions import ClientError
from .base import ValidatorBase


class VPCFlowLogsValidator(ValidatorBase):
    name = 'vpc-flow-logs'

    def run(self, name: str, region: str = None, account_id: str = None, extra=None):
        """Expect `name` to be a VPC id (e.g., vpc-xxxx)."""
        ec2 = boto3.client('ec2', region_name=region)
        result = {'name': self.name, 'resource': name}
        try:
            resp = ec2.describe_flow_logs(Filters=[{'Name': 'resource-id', 'Values': [name]}])
            logs = resp.get('FlowLogs', [])
            if logs:
                result['status'] = 'PASS'
                result['details'] = {'flow_logs': len(logs)}
            else:
                result['status'] = 'FAIL'
                result['details'] = {'flow_logs': 0}
        except ClientError as e:
            result['status'] = 'ERROR'
            result['details'] = {'error': str(e)}
        return result
