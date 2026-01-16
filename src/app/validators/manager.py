from typing import List, Dict, Any
from .s3_validators import S3BucketPublicAccessValidator
from .base import ValidatorBase
from .iam_validators import IAMPasswordPolicyValidator, RootMFAValidator
from .cloudtrail_validators import CloudTrailLoggingValidator
from .config_validators import ConfigRecorderValidator
from .vpc_validators import VPCFlowLogsValidator
from .waf_validators import WAFWebACLPresenceValidator


VALIDATOR_MAP: Dict[str, List[ValidatorBase]] = {
    "s3": [S3BucketPublicAccessValidator()],
    "iam": [IAMPasswordPolicyValidator(), RootMFAValidator()],
    "cloudtrail": [CloudTrailLoggingValidator()],
    "config": [ConfigRecorderValidator()],
    "vpc": [VPCFlowLogsValidator()],
    "waf": [WAFWebACLPresenceValidator()],
}



def run_validators_for_evaluation(
    targets: List[Dict[str, Any]], region: str = None, account_id: str = None
) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    if not targets:
        return results
    for t in targets:
        ttype = str(t.get("type") or "")
        name = t.get("name")
        validators = VALIDATOR_MAP.get(ttype, [])
        for v in validators:
            try:
                res = v.run(
                    name=name,
                    region=region,
                    account_id=account_id,
                    extra=t.get("extra"),
                )
            except Exception as e:
                res = {"name": v.name, "status": "ERROR", "details": {"error": str(e)}}
            results.append(res)
    return results
