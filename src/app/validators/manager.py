from typing import List, Dict, Any
from .s3_validators import S3PublicAccessValidator
from .iam_validators import IAMPasswordPolicyValidator, RootMFAValidator
from .cloudtrail_validators import CloudTrailLoggingValidator
from .config_validators import ConfigRecorderValidator
from .vpc_validators import VPCFlowLogsValidator
from .waf_validators import WAFWebACLPresenceValidator


VALIDATOR_MAP = {
    "s3": [S3PublicAccessValidator()],
    "iam": [IAMPasswordPolicyValidator(), RootMFAValidator()],
    "cloudtrail": [CloudTrailLoggingValidator()],
    "config": [ConfigRecorderValidator()],
    "vpc": [VPCFlowLogsValidator()],
    "waf": [WAFWebACLPresenceValidator()],
}


def run_validators_for_evaluation(
    targets: List[Dict[str, Any]], region: str = None, account_id: str = None
) -> List[Dict[str, Any]]:
    results = []
    if not targets:
        return results
    for t in targets:
        ttype = t.get("type")
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
                res = {"name": v.name, "status": "ERROR", "details": str(e)}
            results.append(res)
    return results
