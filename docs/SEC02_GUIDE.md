# SEC02 Configuration Guide

## Overview

SEC02 is the second security pillar question in AutoWAR: **Gestión de Identidad y Acceso - Autenticación** (Identity and Access Management - Authentication).

This pillar covers **6 Best Practices** with detailed mapping to **12 AWS services** and their specific resources that need to be evaluated.

## Structure

### Configuration Files

- **`sec02_services_config.py`** - Main configuration file with all services and resources
- **`SEC02_CONFIGURATION.md`** - Detailed documentation with tables and compliance checklist
- **`sec02_examples.py`** - Example usage and utility functions

### Configuration Format

Each Best Practice (BP) is configured with:

```python
"SEC02-BP0X": {
    "name": "BP Title",
    "description": "Brief description",
    "services": ["service1", "service2", ...],
    "resources": {
        "service1": ["resource1", "resource2", ...],
        "service2": ["resource1", "resource2", ...],
    },
    "checks": ["check1", "check2", ...],
}
```

## Best Practices

### SEC02-BP01: Utilizar mecanismos de inicio de sesión fuertes
**Strong login mechanisms including MFA, password policies, and adaptive authentication**

- **Services**: IAM, SSO, Cognito, Directory Service, CloudTrail, CloudWatch
- **Key Resources**:
  - IAM password policies with strength requirements
  - MFA devices and virtual MFA
  - SSO authentication policies
  - Cognito advanced security features
  - CloudTrail login event logging
  - CloudWatch alarms for failed login attempts

### SEC02-BP02: Utilizar credenciales temporales
**Use temporary credentials through STS, IAM roles, avoiding long-term access keys**

- **Services**: STS, IAM, EC2, Lambda, ECS, EKS, CodeBuild, CodePipeline, Config
- **Key Resources**:
  - STS AssumeRole configurations
  - IAM service roles and trust policies
  - EC2 instance profiles with IMDSv2
  - Lambda execution roles
  - ECS/EKS task roles and service accounts
  - Config compliance rules for credential rotation

### SEC02-BP03: Almacenar y utilizar secretos de forma segura
**Secure storage and retrieval of secrets using Secrets Manager and Parameter Store**

- **Services**: Secrets Manager, Systems Manager, KMS, RDS, ElastiCache, Lambda, ECS, EKS
- **Key Resources**:
  - Secrets Manager with automatic rotation
  - Parameter Store SecureString parameters
  - KMS customer managed keys
  - RDS Secrets Manager integration
  - ElastiCache auth tokens
  - VPC endpoints for private access

### SEC02-BP04: Confíe en un proveedor de identidad centralizado
**Centralized identity provider for federated access and single sign-on**

- **Services**: SSO, IAM, Cognito, Directory Service, Client VPN, WorkSpaces
- **Key Resources**:
  - AWS SSO/Identity Center with external IdPs
  - SAML and OIDC provider configuration
  - Cognito federation settings
  - AD Connector or Managed AD
  - Trust relationships configured

### SEC02-BP05: Auditar y rotar credenciales periódicamente
**Regular audit and rotation of all credentials**

- **Services**: IAM, Config, CloudTrail, CloudWatch, Secrets Manager, Systems Manager, Lambda
- **Key Resources**:
  - IAM credential reports
  - Access key age tracking
  - Config compliance rules
  - CloudTrail credential usage logging
  - Secrets Manager rotation schedules
  - Lambda rotation functions

### SEC02-BP06: Emplear grupos de usuarios y atributos
**Use user groups and attribute-based access control**

- **Services**: IAM, SSO, Cognito, Directory Service, RAM, Organizations
- **Key Resources**:
  - IAM groups with attached policies
  - SSO permission sets and groups
  - Cognito user pool groups
  - AD security groups and OUs
  - Resource Access Manager sharing
  - Service Control Policies (SCPs)

## AWS Services Covered

| Service | BP Count | Primary Use |
|---------|----------|-------------|
| AWS IAM | 4 | Roles, groups, MFA, password policy |
| AWS STS | 1 | Temporary credentials |
| AWS SSO | 3 | Federated access, permission sets |
| Amazon Cognito | 4 | User pools, federated identity |
| AWS Directory Service | 3 | AD integration, Kerberos |
| AWS CloudTrail | 3 | Audit logging, event tracking |
| Amazon CloudWatch | 2 | Alarms, monitoring |
| AWS Secrets Manager | 2 | Secret storage, rotation |
| AWS Systems Manager | 2 | Parameter Store, automation |
| AWS KMS | 1 | Encryption key management |
| AWS Config | 2 | Compliance checks |
| AWS Organizations | 1 | Account structure, SCPs |

## Compliance Criteria

### SEC02-BP01 Compliance
- ✓ Password policy: 12+ characters, mixed case, numbers, symbols
- ✓ MFA enabled for all users
- ✓ Root account with MFA
- ✓ CloudTrail logging of authentication events
- ✓ Alarms for failed login attempts

### SEC02-BP02 Compliance
- ✓ No long-term access keys for applications
- ✓ STS AssumeRole for temporary credentials
- ✓ Service roles on EC2/Lambda/ECS
- ✓ IMDSv2 enabled on EC2
- ✓ Session duration maximum 12 hours

### SEC02-BP03 Compliance
- ✓ Database passwords in Secrets Manager
- ✓ Automatic rotation every 30-90 days
- ✓ KMS encryption enabled
- ✓ VPC endpoints for private access
- ✓ No secrets hardcoded in code

### SEC02-BP04 Compliance
- ✓ Identity Center/SSO configured
- ✓ SAML/OIDC integrated
- ✓ Attribute mapping configured
- ✓ Permission sets defined
- ✓ MFA required in IdP

### SEC02-BP05 Compliance
- ✓ Access keys rotated every 90 days
- ✓ Unused credentials identified and removed
- ✓ CloudTrail logging enabled
- ✓ Alarms for credential expiry
- ✓ Compliance reports generated monthly

### SEC02-BP06 Compliance
- ✓ Users organized in groups
- ✓ Policies attached to groups
- ✓ Principle of least privilege applied
- ✓ Permission sets per role
- ✓ ABAC implemented

## Usage Examples

### Getting BP Details
```python
from src.config.sec02_services_config import get_bp_services

bp = get_bp_services("SEC02-BP01")
print(f"Services: {bp['services']}")
print(f"Checks: {bp['checks']}")
```

### Getting All Services
```python
from src.config.sec02_services_config import get_all_services

services = get_all_services()
print(f"Services: {services}")
```

### Getting BP Checks
```python
from src.config.sec02_services_config import get_bp_checks

checks = get_bp_checks("SEC02-BP02")
for check in checks:
    print(f"- {check}")
```

### Running Example Scripts
```bash
# Overview
python src/config/sec02_examples.py overview

# All BPs
python src/config/sec02_examples.py all

# Service coverage
python src/config/sec02_examples.py services

# Compliance checklist
python src/config/sec02_examples.py checklist

# Specific BP
python src/config/sec02_examples.py bp:SEC02-BP01

# Export as JSON
python src/config/sec02_examples.py export
```

## Integration with Security Evaluator

The SEC02 configuration is integrated into `security_evaluator.py`:

```python
from ..config.sec02_services_config import (
    get_bp_services as get_bp_services_sec02,
    get_all_services as get_all_services_sec02,
    get_bp_checks as get_bp_checks_sec02,
)

# In evaluate_sec02() method
def evaluate_sec02(self) -> Dict[str, Any]:
    """SEC02: ¿Cómo se gestiona la autenticación de personas y máquinas? (6 BPs)"""
    # Uses the detailed service configuration for enhanced checks
```

## Testing the Configuration

Run the example script to verify the configuration is correct:

```bash
cd /path/to/project
python -m src.config.sec02_examples

# Or with specific command
python -m src.config.sec02_examples checklist
```

## Next Steps

1. **Create Validators** - Implement specific validators for each BP
2. **Enhance Checks** - Add AWS API calls for each resource type
3. **Add Monitoring** - Create CloudWatch alarms for compliance
4. **Generate Reports** - Create detailed compliance reports
5. **Automate Remediation** - Create automation for common issues

## References

- [AWS Well-Architected Framework - Security Pillar](https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/)
- [AWS IAM Best Practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)
- [AWS Identity Center Documentation](https://docs.aws.amazon.com/singlesignon/)
- [AWS Secrets Manager Documentation](https://docs.aws.amazon.com/secretsmanager/)
