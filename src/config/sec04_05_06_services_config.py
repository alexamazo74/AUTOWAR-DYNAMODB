"""
SEC04, SEC05, SEC06 Services Configuration
Detailed service and resource specifications for Detection, Network Protection, and Compute Protection
"""

# SEC04: Detection - Services and resources to review
SEC04_SERVICES = {
    "SEC04-BP01": {
        "name": "Configure service and application logging",
        "services": [
            "AWS CloudTrail",
            "Amazon CloudWatch Logs",
            "AWS Config",
            "Amazon VPC Flow Logs",
            "AWS X-Ray",
            "Application Load Balancer",
            "Amazon RDS",
            "AWS Lambda"
        ],
        "resources": [
            "Management events enabled",
            "Data events configured",
            "Multi-region trails",
            "Log file integrity validation",
            "Log groups with retention policies",
            "Configuration recording",
            "VPC Flow Logs (VPC, Subnet, ENI level)",
            "Service tracing and sampling"
        ]
    },
    "SEC04-BP02": {
        "name": "Capture logs, findings, and metrics in standardized locations",
        "services": [
            "AWS Security Hub",
            "Amazon CloudWatch",
            "Amazon S3",
            "Amazon Kinesis",
            "AWS Organizations",
            "Amazon OpenSearch Service",
            "AWS Glue"
        ],
        "resources": [
            "Security standards enabled",
            "Centralized metrics collection",
            "Centralized log storage buckets",
            "Organization trails",
            "Finding format standardization",
            "Cross-account log aggregation",
            "Lifecycle policies for logs"
        ]
    },
    "SEC04-BP03": {
        "name": "Correlate and enrich security alerts",
        "services": [
            "Amazon GuardDuty",
            "Amazon Detective",
            "AWS Security Hub",
            "Amazon EventBridge",
            "AWS Lambda",
            "Amazon DynamoDB",
            "Amazon SNS"
        ],
        "resources": [
            "Threat detection enabled",
            "Behavior graphs",
            "Finding correlation rules",
            "Custom insights for patterns",
            "Event pattern matching",
            "Threat intelligence storage",
            "Alert notification topics"
        ]
    },
    "SEC04-BP04": {
        "name": "Initiate remediation for non-compliant resources",
        "services": [
            "AWS Config",
            "AWS Systems Manager",
            "AWS Security Hub",
            "AWS Lambda",
            "Amazon EventBridge",
            "AWS Step Functions"
        ],
        "resources": [
            "Auto-remediation rules",
            "Automation documents",
            "Custom actions",
            "Remediation workflows",
            "Error handling states",
            "Execution history"
        ]
    }
}

# SEC05: Network Protection - Services and resources to review
SEC05_SERVICES = {
    "SEC05-BP01": {
        "name": "Create network layers",
        "services": [
            "Amazon VPC",
            "AWS Transit Gateway",
            "Amazon VPC Peering",
            "AWS PrivateLink",
            "AWS Direct Connect",
            "AWS Site-to-Site VPN",
            "AWS Client VPN",
            "Amazon ECS",
            "Amazon EKS",
            "Elastic Load Balancing (ALB/NLB)",
            "Amazon CloudFront"
        ],
        "resources": [
            "Multi-tier architecture",
            "Public/private subnet segregation",
            "Availability Zone distribution",
            "Hub-and-spoke topology",
            "VPC endpoint services",
            "BGP routing configurations",
            "Internet gateway and egress-only IGW",
            "Public vs private route table associations",
            "ALB/NLB scheme (internet-facing/internal)",
            "CloudFront origin protection (OAC/OAI)",
            "Service discovery namespaces",
            "ECS/EKS VPC and service networking"
        ]
    },
    "SEC05-BP02": {
        "name": "Control traffic flow within network layers",
        "services": [
            "Security Groups",
            "Network ACLs",
            "AWS Network Firewall",
            "Route Tables",
            "NAT Gateways",
            "AWS WAF",
            "Elastic Load Balancing (ALB/NLB)"
            "Amazon ECS",
            "Amazon EKS"
        ],
        "resources": [
            "Inbound/outbound rules",
            "Port and protocol restrictions",
            "Stateless rule configurations",
            "Firewall policies",
            "Rule group implementations",
            "Web ACL configurations",
            "Security group references and default SG rules",
            "Network ACL rule order and subnet associations",
            "ALB security group attachments",
            "Egress filtering and NAT routing",
            "VPN authorization rules and route propagation",
            "ECS/EKS task/pod security group controls",
            "Kubernetes network policies"
        ]
    },
    "SEC05-BP03": {
        "name": "Implement inspection-based protection",
        "services": [
            "AWS Network Firewall",
            "AWS WAF",
            "Amazon GuardDuty",
            "AWS Shield Advanced",
            "Amazon Inspector",
            "Third-party NGFW/IDS",
            "Elastic Load Balancing (ALB/NLB)",
            "Amazon CloudFront",
            "Amazon API Gateway"
        ],
        "resources": [
            "Deep packet inspection rules",
            "Intrusion detection/prevention",
            "SQL injection protection",
            "Cross-site scripting prevention",
            "VPC Flow Log analysis",
            "DDoS protection",
            "WAF managed rule groups",
            "Rate-based rules and bot control",
            "WAF logging and sampled requests",
            "WAF association with ALB/CloudFront/API Gateway"
        ]
    },
    "SEC05-BP04": {
        "name": "Automate network protection",
        "services": [
            "AWS Config",
            "AWS Systems Manager",
            "AWS Lambda",
            "Amazon EventBridge",
            "AWS CloudFormation",
            "AWS CDK",
            "AWS Firewall Manager",
            "AWS WAF",
            "Amazon CloudFront",
            "Amazon API Gateway"
        ],
        "resources": [
            "Network security compliance rules",
            "Automated remediation",
            "Network automation documents",
            "Infrastructure as Code templates",
            "Event routing",
            "Drift detection",
            "Automated WAF policy enforcement",
            "Managed rule group updates",
            "Centralized WAF/Shield policies"
        ]
    }
}

# SEC06: Compute Protection - Services and resources to review
SEC06_SERVICES = {
    "SEC06-BP01": {
        "name": "Perform vulnerability management",
        "services": [
            "Amazon Inspector",
            "AWS Systems Manager Patch Manager",
            "AWS Systems Manager Inventory",
            "Amazon ECR",
            "Amazon ECS",
            "Amazon EKS",
            "AWS Security Hub",
            "Third-party vulnerability scanners"
        ],
        "resources": [
            "EC2 instance assessments",
            "Container image scanning",
            "Lambda function scanning",
            "Patch baselines",
            "Patch compliance tracking",
            "Software inventory tracking",
            "ECS task definition image scan status",
            "EKS node patching and add-on updates"
        ]
    },
    "SEC06-BP02": {
        "name": "Provision compute from hardened images",
        "services": [
            "Amazon EC2",
            "AWS Systems Manager Image Builder",
            "Amazon ECS",
            "Amazon EKS",
            "AWS Lambda",
            "AWS Batch"
        ],
        "resources": [
            "AMI hardening standards",
            "Golden image management",
            "Image builder pipelines",
            "Container image hardening",
            "Pod security standards",
            "Runtime environment security",
            "EBS encryption at launch",
            "Block device mappings and volume types",
            "Base image provenance and signing"
        ]
    },
    "SEC06-BP03": {
        "name": "Reduce manual management and interactive access",
        "services": [
            "AWS Systems Manager Session Manager",
            "AWS Systems Manager Run Command",
            "AWS Systems Manager Automation",
            "AWS CodeDeploy",
            "Amazon ECS/EKS",
            "AWS Lambda"
        ],
        "resources": [
            "Shell access replacement",
            "Remote command execution",
            "Automated deployments",
            "Container orchestration",
            "Auto-scaling",
            "Event-driven execution",
            "SSM-only access policies",
            "SSH/RDP restriction and bastion controls",
            "ECS Exec and kubectl access controls"
        ]
    },
    "SEC06-BP04": {
        "name": "Validate software integrity",
        "services": [
            "AWS Signer",
            "AWS Lambda",
            "Amazon ECR",
            "AWS Systems Manager",
            "AWS CloudFormation",
            "Third-party tools"
        ],
        "resources": [
            "Code signing profiles",
            "Trusted signers",
            "Image signing",
            "Document integrity validation",
            "Checksum validation",
            "Digital signatures"
        ]
    },
    "SEC06-BP05": {
        "name": "Automate compute protection",
        "services": [
            "AWS Config",
            "Amazon CloudWatch",
            "AWS Auto Scaling",
            "AWS Systems Manager",
            "Amazon EventBridge",
            "AWS Security Hub"
        ],
        "resources": [
            "Compute compliance rules",
            "Scaling policies",
            "Alarm configurations",
            "Patch automation",
            "Compliance automation",
            "Workflow automation"
        ]
    }
}

# Metrics and KPIs to monitor
SECURITY_METRICS = {
    "detection_metrics": [
        "Mean time to detection (MTTD)",
        "False positive rate",
        "Alert volume trends",
        "Coverage percentage"
    ],
    "network_security": [
        "Traffic flow compliance",
        "Blocked connection attempts",
        "DDoS mitigation effectiveness",
        "Network segmentation compliance"
    ],
    "compute_security": [
        "Vulnerability remediation time",
        "Patch compliance rate",
        "Image hardening compliance",
        "Automated response success rate"
    ],
    "operational_efficiency": [
        "Manual intervention reduction",
        "Automation success rate",
        "Mean time to remediation (MTTR)",
        "Cost per security event"
    ]
}


def get_sec04_bp_services(bp_id: str) -> list:
    """Get services for a specific SEC04 BP"""
    bp_config = SEC04_SERVICES.get(bp_id, {})
    return bp_config.get("services", [])


def get_sec04_bp_resources(bp_id: str) -> list:
    """Get resources to review for a specific SEC04 BP"""
    bp_config = SEC04_SERVICES.get(bp_id, {})
    return bp_config.get("resources", [])


def get_sec05_bp_services(bp_id: str) -> list:
    """Get services for a specific SEC05 BP"""
    bp_config = SEC05_SERVICES.get(bp_id, {})
    return bp_config.get("services", [])


def get_sec05_bp_resources(bp_id: str) -> list:
    """Get resources to review for a specific SEC05 BP"""
    bp_config = SEC05_SERVICES.get(bp_id, {})
    return bp_config.get("resources", [])


def get_sec06_bp_services(bp_id: str) -> list:
    """Get services for a specific SEC06 BP"""
    bp_config = SEC06_SERVICES.get(bp_id, {})
    return bp_config.get("services", [])


def get_sec06_bp_resources(bp_id: str) -> list:
    """Get resources to review for a specific SEC06 BP"""
    bp_config = SEC06_SERVICES.get(bp_id, {})
    return bp_config.get("resources", [])


def get_security_metrics() -> dict:
    """Get all security metrics and KPIs to monitor"""
    return SECURITY_METRICS
