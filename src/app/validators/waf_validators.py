import boto3
from botocore.exceptions import ClientError
from typing import Optional, Dict, Any
from .base import ValidatorBase


class WAFWebACLPresenceValidator(ValidatorBase):
    name = "waf-web-acl"

    def run(
        self,
        name: Optional[str] = None,
        region: Optional[str] = None,
        account_id: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        # name may be resource or webacl name; we check if there is any web ACL configured
        waf = boto3.client("wafv2", region_name=region)
        result: Dict[str, Any] = {"name": self.name}
        try:
            # try regional
            resp = waf.list_web_acls(Scope="REGIONAL")
            if resp.get("WebACLs"):
                result["status"] = "PASS"
                result["details"] = {"count": len(resp.get("WebACLs"))}
                return result
            # try CLOUDFRONT (global)
            resp2 = waf.list_web_acls(Scope="CLOUDFRONT")
            if resp2.get("WebACLs"):
                result["status"] = "PASS"
                result["details"] = {"count": len(resp2.get("WebACLs"))}
                return result
            result["status"] = "FAIL"
            result["details"] = {"web_acls": 0}
        except ClientError as e:
            result["status"] = "ERROR"
            result["details"] = {"error": str(e)}
        return result
