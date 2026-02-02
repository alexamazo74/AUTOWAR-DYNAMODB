"""Configuration mapping SEC01 Best Practices to specific AWS services and resources."""

SEC01_BP_SERVICES = {
    "SEC01-BP01": {
        "name": "Operate workload securely",
        "services": [
            "organizations",  # AWS Organizations for centralized governance
            "control-tower",  # AWS Control Tower
            "ram",  # AWS Resource Access Manager
            "sso",  # AWS IAM Identity Center (SSO)
            "iam",  # IAM roles and policies
        ],
        "resources": [
            "organizations:organizations",
            "organizations:accounts",
            "organizations:organizational-units",
            "controltower:landing-zone",
            "sso:instances",
            "sso:permission-sets",
            "ram:resource-shares",
        ],
    },
    "SEC01-BP02": {
        "name": "Separate workload using accounts",
        "services": [
            "organizations",  # AWS Organizations for multi-account structure
            "control-tower",  # AWS Control Tower
        ],
        "resources": [
            "organizations:accounts",
            "organizations:organizational-units",
            "controltower:landing-zone",
        ],
    },
    "SEC01-BP03": {
        "name": "Secure AWS account",
        "services": [
            "iam",  # Root account protection, MFA
            "guardduty",  # AWS GuardDuty
            "securityhub",  # AWS Security Hub
            "config",  # AWS Config
            "cloudtrail",  # AWS CloudTrail
        ],
        "resources": [
            "iam:account-password-policy",
            "iam:account-summary",
            "iam:virtual-mfa-devices",
            "guardduty:detectors",
            "securityhub:hubs",
            "config:configuration-recorders",
            "cloudtrail:trails",
        ],
    },
    "SEC01-BP04": {
        "name": "Identify and validate control objectives",
        "services": [
            "config",  # AWS Config for control validation
            "securityhub",  # AWS Security Hub
            "audit-manager",  # AWS Audit Manager
        ],
        "resources": [
            "config:config-rules",
            "config:conformance-packs",
            "securityhub:standards-subscriptions",
            "auditmanager:assessments",
            "auditmanager:frameworks",
        ],
    },
    "SEC01-BP05": {
        "name": "Stay up to date with security threats and recommendations",
        "services": [
            "securityhub",  # AWS Security Hub for threat intelligence
            "guardduty",  # AWS GuardDuty
            "inspector",  # Amazon Inspector
            "detective",  # Amazon Detective
            "trusted-advisor",  # AWS Trusted Advisor
        ],
        "resources": [
            "securityhub:findings",
            "guardduty:findings",
            "inspector2:findings",
            "detective:graphs",
            "support:trusted-advisor-checks",
        ],
    },
    "SEC01-BP06": {
        "name": "Automate testing and validation",
        "services": [
            "config",  # AWS Config for automated compliance checks
            "securityhub",  # AWS Security Hub
            "lambda",  # AWS Lambda for automation
            "systems-manager",  # AWS Systems Manager Automation
        ],
        "resources": [
            "config:config-rules",
            "config:remediation-configurations",
            "securityhub:automation-rules",
            "lambda:functions",
            "ssm:automation-executions",
        ],
    },
    "SEC01-BP07": {
        "name": "Identify and prioritize risks using threat model",
        "services": [
            "securityhub",  # AWS Security Hub for risk aggregation
            "guardduty",  # AWS GuardDuty
            "inspector",  # Amazon Inspector for vulnerability assessment
            "access-analyzer",  # IAM Access Analyzer
        ],
        "resources": [
            "securityhub:findings",
            "guardduty:findings",
            "inspector2:findings",
            "access-analyzer:analyzers",
            "access-analyzer:findings",
        ],
    },
    "SEC01-BP08": {
        "name": "Keep up to date with security recommendations",
        "services": [
            "securityhub",  # AWS Security Hub
            "trusted-advisor",  # AWS Trusted Advisor
            "config",  # AWS Config
            "inspector",  # Amazon Inspector
        ],
        "resources": [
            "securityhub:insights",
            "support:trusted-advisor-checks",
            "config:config-rules",
            "inspector2:coverage",
        ],
    },
}


def get_bp_services(bp_id: str) -> list[str]:
    """Get list of AWS services to check for a specific Best Practice.

    Args:
        bp_id: The Best Practice ID (e.g., 'SEC01-BP01')

    Returns:
        List of AWS service identifiers
    """
    return SEC01_BP_SERVICES.get(bp_id, {}).get("services", [])


def get_bp_resources(bp_id: str) -> list[str]:
    """Get list of AWS resource types to check for a specific Best Practice.

    Args:
        bp_id: The Best Practice ID (e.g., 'SEC01-BP01')

    Returns:
        List of AWS resource type identifiers
    """
    return SEC01_BP_SERVICES.get(bp_id, {}).get("resources", [])


def get_bp_name(bp_id: str) -> str:
    """Get the name/description of a Best Practice.

    Args:
        bp_id: The Best Practice ID (e.g., 'SEC01-BP01')

    Returns:
        Best Practice name/description
    """
    return SEC01_BP_SERVICES.get(bp_id, {}).get("name", "Unknown Best Practice")
