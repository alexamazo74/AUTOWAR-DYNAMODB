"""
SEC03 - Gestión de identidad y acceso (Gestión de Permisos)
9 Best Practices con servicios y recursos específicos a revisar
"""

SEC03_CONFIG = {
    "SEC03-BP01": {
        "title": "Definir los requisitos de acceso",
        "description": "Documentar y analizar los requisitos de acceso para cada rol y función",
        "services": [
            {
                "name": "AWS IAM",
                "resources": [
                    "Policy documents y statements",
                    "Resource-based policies",
                    "Condition keys",
                    "Principal specifications",
                    "Action granularity",
                ],
            },
            {
                "name": "AWS Organizations",
                "resources": [
                    "Service Control Policies (SCPs)",
                    "Organizational Unit (OU) structure",
                    "Account categorization",
                    "Cross-account access requirements",
                    "Compliance requirements",
                ],
            },
            {
                "name": "AWS SSO (Identity Center)",
                "resources": [
                    "Permission sets",
                    "Job function-based access definitions",
                    "ABAC rules",
                    "Session duration requirements",
                    "MFA requirements",
                ],
            },
            {
                "name": "AWS Systems Manager",
                "resources": [
                    "Session Manager access requirements",
                    "Run Command permissions",
                    "Patch Manager access controls",
                    "Parameter Store access patterns",
                    "OpsCenter access definitions",
                ],
            },
            {
                "name": "AWS Service Catalog",
                "resources": [
                    "Portfolio access requirements",
                    "Product launch constraints",
                    "TagOption requirements",
                    "Approval workflows",
                    "End user self-service boundaries",
                ],
            },
        ],
    },
    "SEC03-BP02": {
        "title": "Otorgar acceso con privilegios mínimos",
        "description": "Implementar el principio de privilegios mínimos en todas las políticas de acceso",
        "services": [
            {
                "name": "AWS IAM",
                "resources": [
                    "Managed policies vs inline policies",
                    "Policy simulator usage",
                    "Condition-based restrictions",
                    "Resource-level permissions",
                    "Time-based access controls",
                    "IP-based restrictions",
                ],
            },
            {
                "name": "AWS Access Analyzer",
                "resources": [
                    "Policy validation findings",
                    "Unused access identification",
                    "External access analysis",
                    "Policy generation recommendations",
                    "Archive rules",
                ],
            },
            {
                "name": "AWS CloudTrail",
                "resources": [
                    "API usage analysis",
                    "Permission usage tracking",
                    "Unused permission identification",
                    "Access pattern analysis",
                    "Service-to-service calls",
                ],
            },
            {
                "name": "AWS Config",
                "resources": [
                    "IAM policy compliance rules",
                    "Overly permissive policy detection",
                    "Root account usage monitoring",
                    "Administrative privilege tracking",
                    "Cross-account role analysis",
                ],
            },
            {
                "name": "Amazon S3",
                "resources": [
                    "Bucket policies restrictivas",
                    "Access Control Lists (ACLs)",
                    "Block Public Access settings",
                    "Object-level permissions",
                    "Pre-signed URL policies",
                ],
            },
            {
                "name": "Amazon RDS",
                "resources": [
                    "Database user permissions",
                    "IAM database authentication",
                    "Resource-level IAM policies",
                    "VPC security group restrictions",
                    "Subnet group limitations",
                ],
            },
            {
                "name": "AWS Lambda",
                "resources": [
                    "Function execution roles",
                    "Resource-based policies",
                    "VPC configuration restrictions",
                    "Environment variable access",
                    "Layer permissions",
                ],
            },
            {
                "name": "Amazon EKS",
                "resources": [
                    "RBAC roles and bindings",
                    "Service accounts with IAM roles (IRSA)",
                    "Cluster authentication modes",
                    "Namespace access boundaries",
                    "Pod security admission controls",
                ],
            },
            {
                "name": "Amazon API Gateway",
                "resources": [
                    "Resource policies",
                    "IAM authorization",
                    "Cognito/Lambda authorizers",
                    "Stage-level access controls",
                    "Usage plans and API keys",
                ],
            },
        ],
    },
    "SEC03-BP03": {
        "title": "Establecer proceso de acceso de emergencia",
        "description": "Mantener un proceso documentado de acceso de emergencia (break-glass)",
        "services": [
            {
                "name": "AWS IAM",
                "resources": [
                    "Break-glass roles",
                    "Emergency access procedures",
                    "Temporary elevated permissions",
                    "Emergency contact roles",
                    "Cross-account emergency access",
                ],
            },
            {
                "name": "AWS SSO (Identity Center)",
                "resources": [
                    "Emergency permission sets",
                    "Temporary access workflows",
                    "Emergency user provisioning",
                    "Emergency session duration",
                    "Emergency MFA bypass procedures",
                ],
            },
            {
                "name": "AWS Systems Manager",
                "resources": [
                    "Emergency automation documents",
                    "Session Manager emergency access",
                    "Run Command emergency procedures",
                    "Incident Manager integration",
                    "Emergency maintenance windows",
                ],
            },
            {
                "name": "Amazon CloudWatch",
                "resources": [
                    "Emergency access alarms",
                    "Break-glass usage monitoring",
                    "Escalation procedures",
                    "Emergency notification chains",
                    "Automated response triggers",
                ],
            },
            {
                "name": "AWS Security Hub",
                "resources": [
                    "Emergency access findings",
                    "Incident response integration",
                    "Emergency procedure documentation",
                    "Compliance exception tracking",
                    "Emergency access reporting",
                ],
            },
            {
                "name": "AWS Secrets Manager",
                "resources": [
                    "Emergency credential storage",
                    "Break-glass secret access",
                    "Emergency rotation procedures",
                    "Cross-region secret replication",
                    "Emergency access logging",
                ],
            },
        ],
    },
    "SEC03-BP04": {
        "title": "Reducir permisos continuamente",
        "description": "Implementar procesos para revisar y reducir permisos regularmente",
        "services": [
            {
                "name": "AWS Access Analyzer",
                "resources": [
                    "Unused access findings",
                    "Policy optimization recommendations",
                    "External access reviews",
                    "Archive rule effectiveness",
                    "Finding trend analysis",
                ],
            },
            {
                "name": "AWS CloudTrail",
                "resources": [
                    "Service last accessed data",
                    "API usage analytics",
                    "Permission utilization tracking",
                    "Unused service identification",
                    "Access pattern changes",
                ],
            },
            {
                "name": "AWS IAM",
                "resources": [
                    "Access Advisor reports",
                    "Credential reports analysis",
                    "Policy version management",
                    "Permission boundary usage",
                    "Role trust policy reviews",
                ],
            },
            {
                "name": "AWS Config",
                "resources": [
                    "IAM compliance rules",
                    "Permission drift detection",
                    "Policy change tracking",
                    "Compliance timeline analysis",
                    "Remediation action tracking",
                ],
            },
            {
                "name": "AWS Systems Manager",
                "resources": [
                    "Compliance scanning results",
                    "Patch compliance correlation",
                    "Inventory data analysis",
                    "Association compliance",
                    "Resource group management",
                ],
            },
        ],
    },
    "SEC03-BP05": {
        "title": "Defina las barreras de permisos para su organización",
        "description": "Establecer límites de permisos a nivel organizacional",
        "services": [
            {
                "name": "AWS Organizations",
                "resources": [
                    "Service Control Policies (SCPs)",
                    "Organizational Unit boundaries",
                    "Account isolation strategies",
                    "Cross-account restrictions",
                    "Service usage limitations",
                ],
            },
            {
                "name": "AWS IAM",
                "resources": [
                    "Permission boundaries implementation",
                    "Policy inheritance chains",
                    "Administrative boundaries",
                    "Delegation boundaries",
                    "Service-linked role restrictions",
                ],
            },
            {
                "name": "AWS Control Tower",
                "resources": [
                    "Guardrails implementation",
                    "Account Factory constraints",
                    "Landing Zone boundaries",
                    "Compliance boundaries",
                    "Preventive controls",
                ],
            },
            {
                "name": "AWS Config",
                "resources": [
                    "Organizational rules deployment",
                    "Compliance boundaries",
                    "Configuration boundaries",
                    "Remediation boundaries",
                    "Aggregator configurations",
                ],
            },
            {
                "name": "AWS Security Hub",
                "resources": [
                    "Security standard boundaries",
                    "Finding aggregation rules",
                    "Cross-account security posture",
                    "Compliance framework boundaries",
                    "Custom insight boundaries",
                ],
            },
        ],
    },
    "SEC03-BP06": {
        "title": "Gestionar el acceso según el ciclo de vida",
        "description": "Automatizar la provisión y desprovisionamiento de acceso",
        "services": [
            {
                "name": "AWS SSO (Identity Center)",
                "resources": [
                    "User lifecycle management",
                    "Automated provisioning/deprovisioning",
                    "Group membership automation",
                    "Permission set assignments",
                    "Access review workflows",
                ],
            },
            {
                "name": "AWS IAM",
                "resources": [
                    "User lifecycle policies",
                    "Access key rotation schedules",
                    "Inactive user identification",
                    "Role assumption tracking",
                    "Credential expiration management",
                ],
            },
            {
                "name": "AWS Directory Service",
                "resources": [
                    "User account lifecycle",
                    "Group membership management",
                    "Password policy enforcement",
                    "Account lockout policies",
                    "Organizational unit management",
                ],
            },
            {
                "name": "Amazon Cognito",
                "resources": [
                    "User pool lifecycle management",
                    "User migration procedures",
                    "Account verification processes",
                    "User attribute management",
                    "Group membership automation",
                ],
            },
            {
                "name": "AWS Lambda",
                "resources": [
                    "Automated lifecycle functions",
                    "User onboarding automation",
                    "Access review automation",
                    "Deprovisioning workflows",
                    "Notification systems",
                ],
            },
        ],
    },
    "SEC03-BP07": {
        "title": "Analizar el acceso público y entre cuentas",
        "description": "Revisar y controlar el acceso público y cross-account",
        "services": [
            {
                "name": "AWS Access Analyzer",
                "resources": [
                    "External access findings",
                    "Cross-account access analysis",
                    "Public resource identification",
                    "Internet-accessible resources",
                    "Unused external access",
                ],
            },
            {
                "name": "Amazon S3",
                "resources": [
                    "Public bucket analysis",
                    "Cross-account bucket policies",
                    "ACL public permissions",
                    "Block Public Access settings",
                    "Access point configurations",
                ],
            },
            {
                "name": "AWS IAM",
                "resources": [
                    "Cross-account role analysis",
                    "External ID usage",
                    "Trust policy reviews",
                    "Resource-based policy analysis",
                    "Public policy identification",
                ],
            },
            {
                "name": "Amazon EC2",
                "resources": [
                    "Security group analysis",
                    "Public IP assignments",
                    "Internet gateway access",
                    "NAT gateway configurations",
                    "Elastic IP usage",
                ],
            },
            {
                "name": "Amazon RDS",
                "resources": [
                    "Public accessibility settings",
                    "Cross-account snapshots",
                    "Security group configurations",
                    "Subnet group analysis",
                    "VPC endpoint usage",
                ],
            },
            {
                "name": "AWS Lambda",
                "resources": [
                    "Resource-based policies",
                    "Cross-account invocations",
                    "Public function URLs",
                    "API Gateway integrations",
                    "Event source mappings",
                ],
            },
            {
                "name": "Amazon API Gateway",
                "resources": [
                    "Public API endpoints",
                    "Cross-account access",
                    "Resource policies",
                    "CORS configurations",
                    "Authentication methods",
                ],
            },
            {
                "name": "Amazon CloudFront",
                "resources": [
                    "Public distribution analysis",
                    "Origin access controls",
                    "Geo restrictions",
                    "Signed URLs and cookies",
                    "Public vs private distributions",
                ],
            },
            {
                "name": "Elastic Load Balancing (ALB/NLB)",
                "resources": [
                    "Internet-facing vs internal load balancers",
                    "Listener exposure and protocols",
                    "Target group accessibility",
                    "Security group exposure",
                    "Public endpoint analysis",
                ],
            },
        ],
    },
    "SEC03-BP08": {
        "title": "Comparta recursos de forma segura dentro de su organización",
        "description": "Usar AWS RAM para compartir recursos de forma segura",
        "services": [
            {
                "name": "AWS Resource Access Manager (RAM)",
                "resources": [
                    "Resource shares configurados",
                    "Principal associations",
                    "Resource associations",
                    "Sharing policies",
                    "Cross-account resource usage",
                ],
            },
            {
                "name": "AWS Organizations",
                "resources": [
                    "Trusted access para RAM",
                    "Service integration settings",
                    "Cross-account sharing policies",
                    "Organizational sharing rules",
                    "Account trust relationships",
                ],
            },
            {
                "name": "Amazon VPC",
                "resources": [
                    "VPC sharing configurations",
                    "Subnet sharing policies",
                    "Security group sharing",
                    "Route table sharing",
                    "Transit Gateway sharing",
                ],
            },
            {
                "name": "AWS Transit Gateway",
                "resources": [
                    "Cross-account attachments",
                    "Route table sharing",
                    "Resource sharing policies",
                    "Network segmentation",
                    "Access control configurations",
                ],
            },
            {
                "name": "Amazon Route 53",
                "resources": [
                    "Private hosted zone sharing",
                    "Cross-account DNS resolution",
                    "Resolver rule sharing",
                    "Domain sharing policies",
                    "DNS query logging",
                ],
            },
            {
                "name": "AWS KMS",
                "resources": [
                    "Cross-account key usage",
                    "Key policies para sharing",
                    "Grant mechanisms",
                    "Encryption context usage",
                    "Cross-account grants",
                ],
            },
        ],
    },
    "SEC03-BP09": {
        "title": "Compartir recursos de forma segura con un tercero",
        "description": "Implementar controles seguros para terceros",
        "services": [
            {
                "name": "AWS IAM",
                "resources": [
                    "Cross-account roles para third parties",
                    "External ID implementation",
                    "Condition-based restrictions",
                    "Time-limited access",
                    "MFA requirements",
                ],
            },
            {
                "name": "AWS STS",
                "resources": [
                    "AssumeRole operations",
                    "Session token management",
                    "External ID validation",
                    "Session duration limits",
                    "Cross-account token usage",
                ],
            },
            {
                "name": "Amazon S3",
                "resources": [
                    "Pre-signed URLs para third parties",
                    "Bucket policies para external access",
                    "Cross-account replication",
                    "Access point configurations",
                    "VPC endpoint restrictions",
                ],
            },
            {
                "name": "AWS PrivateLink",
                "resources": [
                    "VPC endpoint services",
                    "Service provider configurations",
                    "Consumer acceptance settings",
                    "Network load balancer integration",
                    "DNS resolution configurations",
                ],
            },
            {
                "name": "AWS Direct Connect",
                "resources": [
                    "Virtual interfaces sharing",
                    "Cross-account connections",
                    "BGP routing configurations",
                    "VLAN configurations",
                    "Bandwidth allocations",
                ],
            },
            {
                "name": "Amazon API Gateway",
                "resources": [
                    "Third-party API access",
                    "API key management",
                    "Usage plans para partners",
                    "Throttling configurations",
                    "Authentication methods",
                ],
            },
        ],
    },
}


def get_sec03_bp_services(bp_id: str) -> list:
    """Get services for a specific SEC03 best practice"""
    if bp_id in SEC03_CONFIG:
        return [s["name"] for s in SEC03_CONFIG[bp_id]["services"]]
    return []


def get_sec03_bp_resources(bp_id: str, service_name: str) -> list:
    """Get resources for a specific service in a SEC03 best practice"""
    if bp_id in SEC03_CONFIG:
        for service in SEC03_CONFIG[bp_id]["services"]:
            if service["name"] == service_name:
                return service["resources"]
    return []


def get_all_sec03_bps() -> list:
    """Get all SEC03 best practice IDs"""
    return list(SEC03_CONFIG.keys())


def get_sec03_bp_info(bp_id: str) -> dict:
    """Get title and description for a SEC03 best practice"""
    if bp_id in SEC03_CONFIG:
        return {
            "title": SEC03_CONFIG[bp_id]["title"],
            "description": SEC03_CONFIG[bp_id]["description"],
        }
    return {}
