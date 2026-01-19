# AWS Well-Architected Security Pillar - 11 Questions & 63 Best Practices

## Overview
Complete specification of the Security pillar evaluation with 11 foundational questions and 63 best practices.

---

## SEC01: ¿Cómo trabaja su organización en el pilar de seguridad?
**Focus:** Organization, Governance, and Permission Management
**BPs:** 9 total

### SEC01-BP01: Separar entidades de trabajo
- Use AWS Organizations for multi-account structure
- Implement SCPs at organization level
- Automate account creation via Control Tower

### SEC01-BP02: Establecer políticas de seguridad
- Document security policies and procedures
- Define security standards and baselines
- Create runbooks for common scenarios

### SEC01-BP03: Centralizar la auditoría de seguridad
- CloudTrail Organization Trail (multi-account)
- CloudTrail logging to S3 with encryption
- CloudTrail log file validation enabled

### SEC01-BP04: Cumplir requisitos de cumplimiento normativo
- AWS Artifact for compliance reports
- Config Rules for compliance checking
- Maintain audit logs for compliance

### SEC01-BP05: Automatizar protecciones de seguridad
- AWS Config Conformance Packs
- EventBridge for automated remediation
- Systems Manager Automation documents

### SEC01-BP06: Gestionar cambios de seguridad
- Change Management Board process
- Change approval workflow
- Impact assessment for security changes

### SEC01-BP07: Administrar políticas de calificación de seguridad
- Security training requirements
- Competency assessments
- Continuous learning programs

### SEC01-BP08: Incidentes de seguridad de investigación
- Incident response procedures
- Investigation playbooks
- Post-incident reviews

### SEC01-BP09: Asignar responsabilidades de seguridad
- Clear RACI matrix
- Security team organization
- Escalation procedures

---

## SEC02: ¿Cómo gestiona el acceso de cuentas de AWS?
**Focus:** Multi-Account Access Management
**BPs:** 7 total

### SEC02-BP01: Prevenir acceso a la cuenta raíz
- Root account protection policy
- Credential Report monitoring
- No active root access keys

### SEC02-BP02: Asegurar acceso de la cuenta mediante múltiples cuentas
- AWS Organizations for account management
- Service Control Policies (SCPs)
- AWS SSO/IAM Identity Center

### SEC02-BP03: Usar políticas basadas en servicio
- SCP for service restrictions
- Permission boundaries
- Least privilege by default

### SEC02-BP04: Usar roles de asumir de rol
- Cross-account role assumption audit
- STS AssumeRole logging
- External ID for cross-account access

### SEC02-BP05: Restringuir la delegación de acceso entre cuentas
- Explicit trust policy requirements
- Audit cross-account role usage
- Regular access review

### SEC02-BP06: Prevenir el acceso público involuntario a cuentas de AWS
- S3 Block Public Access enabled
- IAM policy conditions
- Public access detection

### SEC02-BP07: Auditar el acceso a cuentas de AWS
- CloudTrail for all AssumeRole events
- CloudWatch Logs Insights queries
- Regular access reviews

---

## SEC03: ¿Cómo gestiona identidades de personas?
**Focus:** Human User Identity Management
**BPs:** 8 total

### SEC03-BP01: Usar SSO para identidades humanas
- AWS SSO / IAM Identity Center
- Federation with corporate directory
- SAML 2.0 integration

### SEC03-BP02: Usar un almacén de identidades externo
- Cognito User Pools for customer identities
- Okta, Auth0, or similar for enterprise
- MFA enforced at directory level

### SEC03-BP03: Implementar MFA para todos los usuarios
- Hardware tokens or software MFA
- Enforce on console access
- Enforce on programmatic access

### SEC03-BP04: Usar credenciales temporales
- STS AssumeRole for all access
- No long-term access keys for humans
- Session duration limits

### SEC03-BP05: Gestionar credenciales en tránsito
- VPC Endpoints for private access
- HTTPS-only policy enforcement
- Certificate validation

### SEC03-BP06: Auditar identidades humanas
- CloudTrail user activity logging
- IAM Access Advisor
- CloudWatch alarms for suspicious activity

### SEC03-BP07: Implementar permisos granulares
- Least privilege policies per role
- Group-based permissions
- Regular privilege reviews

### SEC03-BP08: Revocar acceso oportuno
- Automated offboarding process
- Session termination on role removal
- Active access review schedule

---

## SEC04: ¿Cómo gestiona identidades de máquinas?
**Focus:** Service and Application Identity Management
**BPs:** 6 total

### SEC04-BP01: Usar roles de IAM para máquinas
- EC2 instances with instance profiles
- ECS task roles
- Lambda execution roles

### SEC04-BP02: Usar perfiles de instancia de IAM
- Every EC2 with appropriate role
- ECS task role for containers
- No embedded credentials

### SEC04-BP03: Gestionar credenciales de máquina
- No hardcoded credentials in code
- Secrets Manager for database passwords
- Parameter Store for configuration

### SEC04-BP04: Usar AssumeRole para acceso entre cuentas
- Service-to-service AssumeRole
- Cross-account service communication
- Audit trail for service access

### SEC04-BP05: Usar Secrets Manager
- Database credentials in Secrets Manager
- Automatic rotation enabled
- Encryption with KMS

### SEC04-BP06: Auditar acceso de máquinas
- CloudTrail for service principal actions
- EventBridge notifications
- Regular access pattern review

---

## SEC05: ¿Cómo gestiona los permisos?
**Focus:** Least Privilege and Permission Management
**BPs:** 7 total

### SEC05-BP01: Usar principio de menor privilegio
- Policy analysis and validation
- Avoid wildcard permissions
- Resource-specific policies

### SEC05-BP02: Usar atributos para autorización
- ABAC (Attribute-Based Access Control)
- Tag-based permissions
- Dynamic policy conditions

### SEC05-BP03: Usar Access Analyzer
- Access Analyzer enabled
- Regular finding review
- External access audit

### SEC05-BP04: Usar políticas de control de servicio
- Organization SCPs
- Preventive controls on services
- Allowlist/blocklist approach

### SEC05-BP05: Usar límites de permiso
- Permission Boundary policy
- Prevent privilege escalation
- Regular boundary review

### SEC05-BP06: Auditar los cambios en los permisos
- CloudTrail for policy changes
- Config for permission drift
- SNS alerts on policy modification

### SEC05-BP07: Revocar permisos no utilizados
- Access Advisor reports
- Remove unused policies
- Regular permission cleanup

---

## SEC06: ¿Cómo detecta y investiga eventos de seguridad?
**Focus:** Event Detection and Incident Investigation
**BPs:** 7 total

### SEC06-BP01: Implementar la auditoría de eventos
- CloudTrail enabled on all regions
- Organization trail configuration
- Log file integrity validation

### SEC06-BP02: Registrar el estado de los recursos
- AWS Config enabled
- Configuration recorder running
- Config Aggregator for multi-account

### SEC06-BP03: Implementar detección de amenazas
- GuardDuty enabled
- GuardDuty findings integration
- Threat finding investigation process

### SEC06-BP04: Implementar agregación de hallazgos
- AWS Security Hub enabled
- Centralized finding dashboard
- Custom insight creation

### SEC06-BP05: Implementar el enrutamiento de eventos
- EventBridge rules for findings
- SNS topics for alerts
- SIEM integration

### SEC06-BP06: Implementar monitoreo y alertas
- CloudWatch Logs Insights
- Custom metrics and alarms
- Real-time alerting

### SEC06-BP07: Automatizar investigación y remediación
- Lambda-based response
- Systems Manager automation
- Runbook automation

---

## SEC07: ¿Cómo protege su infraestructura de red?
**Focus:** Network Protection and Isolation
**BPs:** 8 total

### SEC07-BP01: Implementar logging de flujo de red
- VPC Flow Logs enabled
- S3 storage and analysis
- CloudWatch Logs integration

### SEC07-BP02: Controlar acceso de red
- Security Groups with least privilege
- Explicit allow rules
- Regular SG audit

### SEC07-BP03: Usar ACL de red
- Network ACLs for stateless filtering
- Deny rules for known threats
- Multi-layer defense

### SEC07-BP04: Implementar protección de aplicación web
- AWS WAF enabled
- Web ACL rules
- Rate limiting configured

### SEC07-BP05: Implementar protección DDoS
- AWS Shield Standard (automatic)
- Shield Advanced option for critical apps
- DDoS incident plan

### SEC07-BP06: Usar VPC Endpoints
- S3 Gateway Endpoint
- Interface Endpoints for AWS services
- Private service access

### SEC07-BP07: Usar subredes privadas
- Public subnets for ALB/NLB only
- Private subnets for compute
- NAT Gateway for outbound access

### SEC07-BP08: Usar gestión de sistemas para acceso basado en sesiones
- Systems Manager Session Manager
- No SSH/RDP keys needed
- Full audit trail of sessions

---

## SEC08: ¿Cómo cifra y protege sus datos en tránsito?
**Focus:** Encryption for Data in Transit
**BPs:** 5 total

### SEC08-BP01: Cifrar datos en tránsito
- TLS 1.2 minimum
- HTTPS everywhere
- Certificate validation

### SEC08-BP02: Usar certificate management
- AWS Certificate Manager (ACM)
- Automatic renewal enabled
- Certificate pinning for critical apps

### SEC08-BP03: Configurar aplicación de cifrado
- VPN for site-to-site connectivity
- AWS Direct Connect encryption
- Transit encryption for databases

### SEC08-BP04: Usar VPN o PrivateLink
- Site-to-Site VPN for on-premises
- AWS PrivateLink for service access
- Encrypted tunnel monitoring

### SEC08-BP05: Validar cifrado de datos en tránsito
- SSL Labs testing for web apps
- TLS handshake verification
- Cipher suite validation

---

## SEC09: ¿Cómo cifra y protege sus datos en reposo?
**Focus:** Encryption for Data at Rest
**BPs:** 6 total

### SEC09-BP01: Usar AWS KMS
- Customer-managed CMK
- Key rotation enabled
- Key usage audit

### SEC09-BP02: Cifrar datos en reposo en S3
- S3 default encryption
- Bucket-level enforcement
- Disable unencrypted uploads

### SEC09-BP03: Cifrar base de datos
- RDS encryption enabled
- Encrypted snapshots
- EBS encryption for database servers

### SEC09-BP04: Cifrar DynamoDB
- DynamoDB encryption with CMK
- Table-level encryption
- Backup encryption

### SEC09-BP05: Cifrar volúmenes EBS
- EBS encryption enabled
- Default encryption policy
- Snapshot encryption

### SEC09-BP06: Cifrar copias de seguridad
- AWS Backup integration
- Encrypted snapshots
- Multi-region backup copies

---

## SEC10: ¿Cómo se anticipa, responde y se recupera ante incidentes?
**Focus:** Incident Response and Disaster Recovery
**BPs:** 6 total

### SEC10-BP01: Implementar plan de respuesta ante incidentes
- Documented incident response plan
- Regular tabletop exercises
- Clear escalation procedures

### SEC10-BP02: Implementar copias de seguridad
- AWS Backup enabled
- Daily backup schedule
- Cross-region backups

### SEC10-BP03: Implementar una estrategia de recuperación ante desastres
- RTO and RPO defined
- DR test schedule
- Failover procedures documented

### SEC10-BP04: Validar restauración de datos
- Regular restore testing
- Recovery Time Objective (RTO) verification
- Data integrity validation

### SEC10-BP05: Implementar protección de datos
- Immutable backups
- MFA delete on S3
- Backup lifecycle policies

### SEC10-BP06: Automatizar respuesta a incidentes
- Lambda-based remediation
- Systems Manager documents
- Notification and escalation

---

## SEC11: ¿Cómo cumple con los requisitos regulatorios?
**Focus:** Compliance and Audit
**BPs:** 3 total

### SEC11-BP01: Usar AWS Artifact
- Compliance reports access
- Agreement signatures
- Audit documentation

### SEC11-BP02: Usar AWS Config Rules
- Industry standards rules
- Custom compliance rules
- Continuous compliance monitoring

### SEC11-BP03: Implementar auditoría continua
- CloudTrail for all events
- Immutable audit logs
- Compliance dashboard

---

## Summary Statistics
- **Total Questions:** 11 (SEC01 - SEC11)
- **Total Best Practices:** 63
- **Distribution:**
  - SEC01: 9 BPs (Organization & Governance)
  - SEC02: 7 BPs (Account Access Management)
  - SEC03: 8 BPs (Human Identity)
  - SEC04: 6 BPs (Machine Identity)
  - SEC05: 7 BPs (Permission Management)
  - SEC06: 7 BPs (Detection & Investigation)
  - SEC07: 8 BPs (Network Protection)
  - SEC08: 5 BPs (Encryption in Transit)
  - SEC09: 6 BPs (Encryption at Rest)
  - SEC10: 6 BPs (Incident Response)
  - SEC11: 3 BPs (Compliance & Audit)

---

## AWS Services Mapped to Questions

| Service | Questions |
|---------|-----------|
| IAM | SEC01, SEC02, SEC03, SEC04, SEC05 |
| CloudTrail | SEC01, SEC02, SEC03, SEC06, SEC11 |
| Organizations | SEC01, SEC02, SEC05 |
| AWS Config | SEC01, SEC06, SEC11 |
| GuardDuty | SEC06 |
| Security Hub | SEC06 |
| KMS | SEC08, SEC09 |
| VPC/SecurityGroups | SEC07 |
| WAF/Shield | SEC07 |
| Secrets Manager | SEC04 |
| Backup | SEC10 |
| Systems Manager | SEC07, SEC08, SEC10 |
| Cognito | SEC03 |
| Certificate Manager | SEC08 |
| Artifact | SEC11 |

---

## Implementation Status

### ✅ Implemented (Real AWS Checks)
- SEC03-BP03: MFA enforcement for IAM users
- SEC03-BP04: STS temporary credentials usage
- SEC04-BP01: IAM roles for services
- SEC05-BP01: Custom-managed policies inventory
- SEC06-BP01: CloudTrail logging status
- SEC06-BP02: AWS Config recording status
- SEC09-BP01: KMS keys inventory
- SEC09-BP02: S3 bucket encryption

### ⏳ Pending Implementation
- SEC01: Organization and governance checks
- SEC02: Multi-account and SCP validations
- SEC03-BP01, BP02, BP05-BP08: SSO, Cognito, credential transit
- SEC04-BP02-BP06: Instance profiles, hardcoded credentials, AssumeRole audit
- SEC05-BP02-BP07: ABAC, Access Analyzer, permission boundaries
- SEC06-BP03-BP07: GuardDuty, Security Hub, automated remediation
- SEC07: Network protection (VPC, SG, WAF, Shield)
- SEC08: Encryption in transit validation
- SEC09-BP03-BP06: Database and backup encryption
- SEC10-BP01-BP06: Backup and DR validation
- SEC11: Compliance reporting

---

## Evaluation Workflow

1. **User inputs AWS credentials** (Access Key, Secret Key, optional Session Token)
2. **Credentials validated** via STS `get_caller_identity()`
3. **SecurityPillarEvaluator** called to assess all 11 questions
4. **Each question evaluates** relevant AWS resources:
   - Real API calls to get current state
   - Comparison against best practice criteria
   - Score calculation (0-100 per question)
5. **Findings aggregated** with severity levels:
   - CRITICAL: Immediate attention required
   - HIGH: Should be addressed soon
   - MEDIUM: Plan for remediation
   - LOW: Nice to have
6. **Overall Security score** calculated (0-100) based on:
   - Individual question scores
   - Severity weighting
   - Best practice compliance
7. **Results displayed** with:
   - Question scores
   - Finding details
   - Evidence and examples
   - Remediation recommendations
