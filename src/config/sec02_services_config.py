"""Configuration mapping SEC02 Best Practices to specific AWS services and resources.

SEC02: Gestión de identidad y acceso - Autenticación
This module defines the services and resources to check for each SEC02 Best Practice.
"""

SEC02_BP_SERVICES = {
    "SEC02-BP01": {
        "name": "Utilizar mecanismos de inicio de sesión fuertes",
        "description": "Strong login mechanisms including MFA, password policies, and adaptive authentication",
        "services": [
            "iam",  # IAM password policies and MFA devices
            "sso",  # AWS IAM Identity Center
            "cognito",  # Amazon Cognito user pools
            "ds",  # AWS Directory Service
            "cloudtrail",  # Authentication event logging
            "cloudwatch",  # Failed login alarms
        ],
        "resources": {
            "iam": [
                "iam:account-password-policy",
                "iam:users",
                "iam:virtual-mfa-devices",
                "iam:mfa-devices",
                "iam:login-profile",
                "iam:account-settings",
            ],
            "sso": [
                "sso:instances",
                "sso:authentication-policies",
                "sso:mfa-devices",
                "sso:session-duration-settings",
                "sso:adaptive-authentication",
                "sso:risk-based-authentication",
            ],
            "cognito": [
                "cognito:user-pools",
                "cognito:password-policies",
                "cognito:mfa-configuration",
                "cognito:advanced-security-features",
                "cognito:risk-based-authentication",
                "cognito:account-takeover-protection",
            ],
            "ds": [
                "ds:directories",
                "ds:password-policies",
                "ds:fine-grained-password-policies",
                "ds:account-lockout-policies",
                "ds:kerberos-settings",
            ],
            "cloudtrail": [
                "cloudtrail:trails",
                "cloudtrail:console-login-events",
                "cloudtrail:failed-authentication-events",
                "cloudtrail:mfa-usage-tracking",
                "cloudtrail:root-login-events",
            ],
            "cloudwatch": [
                "cloudwatch:alarms-failed-login",
                "cloudwatch:alarms-mfa-bypass",
                "cloudwatch:alarms-unusual-login",
                "cloudwatch:alarms-geographic-anomaly",
                "cloudwatch:alarms-brute-force",
            ],
        },
        "checks": [
            "password_policy_strength",
            "mfa_enabled_for_users",
            "mfa_devices_active",
            "sso_authentication_configured",
            "cognito_mfa_configured",
            "failed_login_monitoring",
            "root_mfa_enabled",
        ],
    },
    "SEC02-BP02": {
        "name": "Utilizar credenciales temporales",
        "description": "Temporary credentials through STS, IAM roles, and avoiding long-term access keys",
        "services": [
            "sts",  # Security Token Service
            "iam",  # IAM roles and policies
            "ec2",  # Instance profiles and metadata
            "lambda",  # Execution roles
            "ecs",  # Task roles
            "eks",  # Service accounts with IAM roles
            "codebuild",  # Service roles
            "codepipeline",  # Deployment roles
            "config",  # Credential checks
        ],
        "resources": {
            "sts": [
                "sts:assume-role",
                "sts:session-duration",
                "sts:external-id-usage",
                "sts:token-vending-machine",
                "sts:cross-account-assumptions",
            ],
            "iam": [
                "iam:roles",
                "iam:service-roles",
                "iam:cross-account-roles",
                "iam:trust-policies",
                "iam:maximum-session-duration",
                "iam:condition-keys",
                "iam:access-keys",
            ],
            "ec2": [
                "ec2:instances",
                "ec2:instance-profiles",
                "ec2:iam-instance-profiles",
                "ec2:metadata-service-v2",
                "ec2:credential-rotation",
            ],
            "lambda": [
                "lambda:execution-roles",
                "lambda:environment-variables",
                "lambda:temporary-credentials",
                "lambda:vpc-configuration",
            ],
            "ecs": [
                "ecs:task-definitions",
                "ecs:task-roles",
                "ecs:task-execution-roles",
            ],
            "eks": [
                "eks:clusters",
                "eks:service-accounts",
                "eks:pod-identity",
                "eks:iam-roles-for-service-accounts",
            ],
            "codebuild": [
                "codebuild:projects",
                "codebuild:service-roles",
                "codebuild:environment-variables",
            ],
            "codepipeline": [
                "codepipeline:pipelines",
                "codepipeline:service-roles",
                "codepipeline:cross-account-roles",
            ],
            "config": [
                "config:iam-user-unused-credentials",
                "config:iam-access-key-rotation",
                "config:root-access-key-check",
                "config:iam-role-last-used",
            ],
        },
        "checks": [
            "sts_assume_role_configured",
            "service_roles_attached",
            "no_hardcoded_credentials",
            "temporary_credentials_used",
            "imdsv2_enabled",
            "cross_account_roles_configured",
            "access_key_rotation",
            "unused_credentials_identified",
        ],
    },
    "SEC02-BP03": {
        "name": "Almacenar y utilizar secretos de forma segura",
        "description": "Secure storage and usage of secrets, API keys, and sensitive credentials",
        "services": [
            "secretsmanager",  # Secrets Manager for secret storage
            "ssm",  # Systems Manager Parameter Store
            "kms",  # Key Management Service
            "rds",  # RDS database credentials
            "elasticache",  # ElastiCache authentication
            "lambda",  # Lambda secret handling
            "ecs",  # ECS secret mounting
            "eks",  # EKS secret management
        ],
        "resources": {
            "secretsmanager": [
                "secretsmanager:secrets",
                "secretsmanager:database-credentials",
                "secretsmanager:api-keys",
                "secretsmanager:automatic-rotation",
                "secretsmanager:cross-region-replication",
                "secretsmanager:resource-policies",
                "secretsmanager:vpc-endpoints",
            ],
            "ssm": [
                "ssm:parameters",
                "ssm:secure-string-parameters",
                "ssm:kms-encryption",
                "ssm:parameter-policies",
                "ssm:access-logging",
                "ssm:parameter-hierarchies",
            ],
            "kms": [
                "kms:keys",
                "kms:customer-managed-keys",
                "kms:key-policies",
                "kms:key-rotation",
                "kms:cross-account-usage",
                "kms:cloudtrail-logging",
            ],
            "rds": [
                "rds:db-instances",
                "rds:secrets-manager-integration",
                "rds:master-credentials",
                "rds:password-rotation",
                "rds:iam-database-authentication",
                "rds:ssl-tls-enforcement",
            ],
            "elasticache": [
                "elasticache:clusters",
                "elasticache:auth-tokens",
                "elasticache:in-transit-encryption",
                "elasticache:at-rest-encryption",
                "elasticache:redis-auth",
            ],
            "lambda": [
                "lambda:environment-variables",
                "lambda:secrets-manager-integration",
                "lambda:hardcoded-secrets-check",
                "lambda:vpc-configuration",
            ],
            "ecs": [
                "ecs:task-definitions",
                "ecs:secret-mounting",
                "ecs:environment-variables",
                "ecs:init-containers",
            ],
            "eks": [
                "eks:pods",
                "eks:secret-volumes",
                "eks:secrets-manager-integration",
                "eks:init-containers",
            ],
        },
        "checks": [
            "secrets_manager_configured",
            "automatic_rotation_enabled",
            "kms_encryption_enabled",
            "no_hardcoded_secrets",
            "secret_access_logging",
            "vpc_endpoints_configured",
            "cross_region_replication",
            "parameter_store_secure_strings",
        ],
    },
    "SEC02-BP04": {
        "name": "Confíe en un proveedor de identidad centralizado",
        "description": "Centralized identity provider for federated access and single sign-on",
        "services": [
            "sso",  # AWS IAM Identity Center
            "iam",  # IAM identity providers
            "cognito",  # Amazon Cognito federation
            "ds",  # Directory Service
            "clientvpn",  # Client VPN authentication
            "workspaces",  # WorkSpaces directory integration
        ],
        "resources": {
            "sso": [
                "sso:instances",
                "sso:identity-providers",
                "sso:saml-configuration",
                "sso:oidc-providers",
                "sso:attribute-mapping",
                "sso:permission-sets",
                "sso:account-assignments",
            ],
            "iam": [
                "iam:saml-providers",
                "iam:oidc-providers",
                "iam:web-identity-federation",
                "iam:trust-relationships",
                "iam:thumbprint-validation",
            ],
            "cognito": [
                "cognito:identity-pools",
                "cognito:user-pools",
                "cognito:external-providers",
                "cognito:saml-providers",
                "cognito:attribute-mapping",
                "cognito:role-resolution",
            ],
            "ds": [
                "ds:directories",
                "ds:ad-connector",
                "ds:managed-ad",
                "ds:trust-relationships",
                "ds:ldap-integration",
                "ds:kerberos-settings",
            ],
            "clientvpn": [
                "clientvpn:endpoints",
                "clientvpn:saml-authentication",
                "clientvpn:ad-integration",
                "clientvpn:certificate-authentication",
                "clientvpn:mfa-settings",
            ],
            "workspaces": [
                "workspaces:workspaces",
                "workspaces:directory-integration",
                "workspaces:saml-authentication",
                "workspaces:mfa-settings",
                "workspaces:ip-access-control",
            ],
        },
        "checks": [
            "sso_identity_provider_configured",
            "saml_provider_configured",
            "oidc_provider_configured",
            "cognito_federation_enabled",
            "directory_integration_configured",
            "attribute_mapping_configured",
            "permission_sets_defined",
            "external_identity_provider_trusted",
        ],
    },
    "SEC02-BP05": {
        "name": "Auditar y rotar credenciales periódicamente",
        "description": "Regular credential audit and rotation to minimize exposure",
        "services": [
            "iam",  # Credential management and rotation
            "config",  # Compliance checking
            "cloudtrail",  # Credential usage tracking
            "cloudwatch",  # Monitoring and alerts
            "secretsmanager",  # Secret rotation
            "ssm",  # Parameter store and automation
            "lambda",  # Rotation functions
        ],
        "resources": {
            "iam": [
                "iam:users",
                "iam:access-keys",
                "iam:credential-report",
                "iam:access-key-age",
                "iam:password-last-used",
                "iam:rotation-policies",
                "iam:unused-credentials",
            ],
            "config": [
                "config:iam-password-policy",
                "config:access-key-rotation-rule",
                "config:unused-iam-user-check",
                "config:root-access-key-check",
                "config:iam-user-mfa-enabled",
            ],
            "cloudtrail": [
                "cloudtrail:trails",
                "cloudtrail:api-calls",
                "cloudtrail:authentication-events",
                "cloudtrail:credential-usage",
                "cloudtrail:cross-account-access",
            ],
            "cloudwatch": [
                "cloudwatch:alarms-credential-age",
                "cloudwatch:alarms-unused-credentials",
                "cloudwatch:alarms-failed-auth",
                "cloudwatch:alarms-anomalous-access",
                "cloudwatch:dashboards-rotation-status",
            ],
            "secretsmanager": [
                "secretsmanager:secrets",
                "secretsmanager:rotation-configuration",
                "secretsmanager:rotation-schedules",
                "secretsmanager:rotation-monitoring",
                "secretsmanager:version-management",
            ],
            "ssm": [
                "ssm:parameters",
                "ssm:automation-documents",
                "ssm:maintenance-windows",
                "ssm:patch-manager",
                "ssm:compliance-tracking",
            ],
            "lambda": [
                "lambda:rotation-functions",
                "lambda:event-driven-updates",
                "lambda:error-handling",
                "lambda:dead-letter-queues",
                "lambda:monitoring",
            ],
        },
        "checks": [
            "access_key_age_tracked",
            "password_last_used_tracked",
            "credential_rotation_policy",
            "automatic_rotation_enabled",
            "unused_credentials_identified",
            "rotation_monitoring_enabled",
            "audit_logging_enabled",
            "compliance_rules_configured",
        ],
    },
    "SEC02-BP06": {
        "name": "Emplear grupos de usuarios y atributos",
        "description": "User groups and attribute-based access control for efficient permission management",
        "services": [
            "iam",  # IAM groups and policies
            "sso",  # Permission sets and groups
            "cognito",  # User pool groups
            "ds",  # Active Directory groups
            "ram",  # Resource sharing
            "organizations",  # Organizational structure
        ],
        "resources": {
            "iam": [
                "iam:groups",
                "iam:group-policies",
                "iam:nested-groups",
                "iam:group-memberships",
                "iam:service-control-policies",
            ],
            "sso": [
                "sso:permission-sets",
                "sso:groups",
                "sso:group-assignments",
                "sso:attribute-based-access",
                "sso:session-tags",
                "sso:dynamic-groups",
            ],
            "cognito": [
                "cognito:user-pool-groups",
                "cognito:group-precedence",
                "cognito:group-role-mapping",
                "cognito:custom-attributes",
                "cognito:group-based-authorization",
            ],
            "ds": [
                "ds:security-groups",
                "ds:organizational-units",
                "ds:group-policy-objects",
                "ds:distribution-groups",
                "ds:nested-groups",
            ],
            "ram": [
                "ram:resource-shares",
                "ram:principal-associations",
                "ram:resource-associations",
                "ram:sharing-policies",
                "ram:cross-account-sharing",
            ],
            "organizations": [
                "organizations:organizational-units",
                "organizations:service-control-policies",
                "organizations:account-grouping",
                "organizations:tag-based-access",
                "organizations:delegated-administration",
            ],
        },
        "checks": [
            "user_groups_organized",
            "group_policies_attached",
            "least_privilege_applied",
            "permission_sets_configured",
            "attribute_based_access_enabled",
            "role_mapping_configured",
            "organizational_structure_defined",
            "service_control_policies_applied",
        ],
    },
}

# Summary statistics
SEC02_TOTAL_BPS = len(SEC02_BP_SERVICES)
SEC02_TOTAL_SERVICES = len(
    set(
        service
        for bp_data in SEC02_BP_SERVICES.values()
        for service in bp_data["services"]
    )
)

SEC02_SERVICE_LIST = sorted(
    set(
        service
        for bp_data in SEC02_BP_SERVICES.values()
        for service in bp_data["services"]
    )
)


def get_bp_services(bp_code: str) -> dict:
    """Get detailed service configuration for a specific best practice."""
    return SEC02_BP_SERVICES.get(bp_code, {})


def get_all_services() -> list:
    """Get list of all AWS services used in SEC02."""
    return SEC02_SERVICE_LIST


def get_bp_checks(bp_code: str) -> list:
    """Get list of checks for a specific best practice."""
    bp = SEC02_BP_SERVICES.get(bp_code, {})
    return bp.get("checks", [])
