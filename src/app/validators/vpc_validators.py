import boto3
from botocore.exceptions import ClientError
from typing import Optional, Dict, Any
from .base import ValidatorBase


class VPCFlowLogsValidator(ValidatorBase):
    name = "vpc-flow-logs"

    def run(
        self,
        name: Optional[str] = None,
        region: Optional[str] = None,
        account_id: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        ec2 = boto3.client("ec2", region_name=region)
        result: Dict[str, Any] = {"name": self.name}
        try:
            resp = ec2.describe_flow_logs()
            if resp.get("FlowLogs"):
                result["status"] = "PASS"
                result["details"] = {"count": len(resp.get("FlowLogs"))}
            else:
                result["status"] = "FAIL"
                result["details"] = {"flow_logs": 0}
        except ClientError as e:
            result["status"] = "ERROR"
            result["details"] = {"error": str(e)}
            return result
        # ensure a return for all control paths
        return result
