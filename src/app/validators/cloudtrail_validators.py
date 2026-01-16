import boto3
from botocore.exceptions import ClientError
from typing import Optional, Dict, Any
from .base import ValidatorBase


class CloudTrailLoggingValidator(ValidatorBase):
    name = "cloudtrail-logging"

    def run(
        self,
        name: Optional[str] = None,
        region: Optional[str] = None,
        account_id: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        ct = boto3.client("cloudtrail", region_name=region)
        result: Dict[str, Any] = {"name": self.name}
        try:
            trails = ct.describe_trails()["trailList"]
            if not trails:
                result["status"] = "FAIL"
                result["details"] = {"trails": 0}
                return result
            # check at least one trail is logging
            for t in trails:
                name = t.get("Name")
                try:
                    status = ct.get_trail_status(Name=name)
                    if status.get("IsLogging"):
                        result["status"] = "PASS"
                        result["details"] = {"logging": True, "trail": name}
                        return result
                except ClientError:
                    continue
            result["status"] = "FAIL"
            result["details"] = {"logging": False}
        except ClientError as e:
            result["status"] = "ERROR"
            result["details"] = {"error": str(e)}
        return result
