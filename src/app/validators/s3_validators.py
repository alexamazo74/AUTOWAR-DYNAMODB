import boto3
from botocore.exceptions import ClientError
from typing import Optional, Dict, Any, List
from .base import ValidatorBase


class S3BucketPublicAccessValidator(ValidatorBase):
    name = "s3-public-access"

    def run(
        self,
        name: Optional[str] = None,
        region: Optional[str] = None,
        account_id: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        s3 = boto3.client("s3", region_name=region)
        result: Dict[str, Any] = {"name": self.name}
        try:
            if name:
                # check single bucket
                pab = s3.get_public_access_block(Bucket=name)
                config = pab.get("PublicAccessBlockConfiguration", {})
                blocked = all(
                    config.get(k, False)
                    for k in (
                        "BlockPublicAcls",
                        "IgnorePublicAcls",
                        "BlockPublicPolicy",
                        "RestrictPublicBuckets",
                    )
                )
                acl = s3.get_bucket_acl(Bucket=name)
                public_acl = any(
                    g.get("Grantee", {}).get("URI")
                    == "http://acs.amazonaws.com/groups/global/AllUsers"
                    for g in acl.get("Grants", [])
                )
                if blocked and not public_acl:
                    result["status"] = "PASS"
                    result["details"] = {"public_block": True}
                else:
                    result["status"] = "FAIL"
                    result["details"] = {
                        "public_block": blocked,
                        "public_acl": public_acl,
                    }
            else:
                resp = s3.list_buckets()
                buckets = resp.get("Buckets", [])
                public: List[str] = []
                for b in buckets:
                    bname = b.get("Name")
                    acl = s3.get_bucket_acl(Bucket=bname)
                    # rudimentary: if any grant is 'AllUsers' it's public
                    for g in acl.get("Grants", []):
                        grantee = g.get("Grantee", {})
                        if (
                            grantee.get("URI")
                            == "http://acs.amazonaws.com/groups/global/AllUsers"
                        ):
                            public.append(bname)
                if public:
                    result["status"] = "FAIL"
                    result["details"] = {"public_buckets": public}
                else:
                    result["status"] = "PASS"
                    result["details"] = {"public_buckets": 0}
        except ClientError as e:
            result["status"] = "ERROR"
            result["details"] = {"error": str(e)}
        return result


# Backwards-compatible alias for tests and external callers
S3PublicAccessValidator = S3BucketPublicAccessValidator
