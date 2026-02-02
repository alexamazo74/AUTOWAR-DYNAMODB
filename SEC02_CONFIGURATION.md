# SEC02 - Gestión de Identidad y Acceso - Autenticación

## Descripción General

SEC02 cubre 6 Best Practices para la gestión segura de identidad y acceso, con énfasis en autenticación fuerte, credenciales temporales, secretos seguros, proveedores de identidad centralizados, auditoría y rotación de credenciales, y gestión de grupos de usuarios.

---

## SEC02-BP01: Utilizar mecanismos de inicio de sesión fuertes

### Descripción
Strong login mechanisms including MFA, password policies, and adaptive authentication across all identity services.

### Servicios Principales
| Servicio | Descripción |
|----------|-------------|
| **AWS IAM** | Password policies, MFA devices, login profiles |
| **AWS SSO** | Identity Center, authentication policies, MFA requirements |
| **Amazon Cognito** | User pool password policies, MFA, advanced security |
| **AWS Directory Service** | Managed AD, password policies, Kerberos auth |
| **AWS CloudTrail** | Login event logging, failed authentication tracking |
| **Amazon CloudWatch** | Failed login alarms, anomaly detection |

### Recursos a Revisar

#### IAM
- `iam:account-password-policy` - Longitud mínima, complejidad, rotación
- `iam:users` - MFA status por usuario
- `iam:virtual-mfa-devices` - Dispositivos MFA registrados
- `iam:mfa-devices` - Dispositivos hardware
- `iam:login-profile` - Configuración de login
- `iam:account-settings` - Password requirements

#### SSO (Identity Center)
- `sso:instances` - Instancias de SSO
- `sso:authentication-policies` - Políticas de autenticación
- `sso:mfa-devices` - MFA por grupo/usuario
- `sso:session-duration-settings` - Duración de sesión
- `sso:adaptive-authentication` - Autenticación adaptativa
- `sso:risk-based-authentication` - Autenticación basada en riesgos

#### Cognito
- `cognito:user-pools` - User pools configurados
- `cognito:password-policies` - Políticas de contraseña
- `cognito:mfa-configuration` - SMS, TOTP, Hardware tokens
- `cognito:advanced-security-features` - Características de seguridad
- `cognito:risk-based-authentication` - Detección de riesgo
- `cognito:account-takeover-protection` - Protección de takeover

#### Directory Service
- `ds:directories` - Managed Microsoft AD
- `ds:password-policies` - Fine-grained policies
- `ds:account-lockout-policies` - Lockout policies
- `ds:kerberos-settings` - Autenticación Kerberos

#### CloudTrail
- `cloudtrail:trails` - CloudTrail trails activos
- `cloudtrail:console-login-events` - Eventos de login a consola
- `cloudtrail:failed-authentication-events` - Intentos fallidos
- `cloudtrail:mfa-usage-tracking` - Uso de MFA
- `cloudtrail:root-login-events` - Logins de root

#### CloudWatch
- `cloudwatch:alarms-failed-login` - Alarmas de login fallido
- `cloudwatch:alarms-mfa-bypass` - Intento de bypass MFA
- `cloudwatch:alarms-unusual-login` - Patrones inusuales
- `cloudwatch:alarms-geographic-anomaly` - Anomalías geográficas
- `cloudwatch:alarms-brute-force` - Ataques de fuerza bruta

### Criterios de Cumplimiento
- ✓ Password policy: mínimo 12 caracteres, mayúsculas, minúsculas, números, símbolos
- ✓ MFA habilitado para todos los usuarios IAM
- ✓ MFA dispositivos registrados y activos
- ✓ Root account con MFA
- ✓ CloudTrail logging de eventos de autenticación
- ✓ Alarmas para intentos de login fallidos
- ✓ Session timeout configurado adecuadamente

---

## SEC02-BP02: Utilizar credenciales temporales

### Descripción
Use temporary credentials through STS, IAM roles, and avoid long-term access keys across compute, database, and CI/CD services.

### Servicios Principales
| Servicio | Descripción |
|----------|-------------|
| **AWS STS** | AssumeRole, session duration, external ID |
| **AWS IAM** | Service roles, cross-account, trust policies |
| **Amazon EC2** | Instance profiles, IMDSv2, credential rotation |
| **AWS Lambda** | Execution roles, environment variables |
| **Amazon ECS/EKS** | Task roles, service accounts |
| **AWS CodeBuild/Pipeline** | Service roles, deployment roles |
| **AWS Config** | Credential rotation checks |

### Recursos a Revisar

#### STS
- `sts:assume-role` - Operaciones de AssumeRole
- `sts:session-duration` - Duración de sesión
- `sts:external-id-usage` - External ID para third-party
- `sts:token-vending-machine` - Token vending machine
- `sts:cross-account-assumptions` - Cross-account role assumptions

#### IAM
- `iam:roles` - Roles creados
- `iam:service-roles` - Service roles para EC2, Lambda, ECS
- `iam:cross-account-roles` - Roles cross-account
- `iam:trust-policies` - Trust policies restrictivas
- `iam:maximum-session-duration` - Max session duration (máximo 43200 seg = 12 horas)
- `iam:condition-keys` - Condition keys en policies

#### EC2
- `ec2:instances` - Instancias con instance profiles
- `ec2:instance-profiles` - Instance profiles asociados
- `ec2:iam-instance-profiles` - IAM roles en instancias
- `ec2:metadata-service-v2` - IMDSv2 habilitado (recomendado)
- `ec2:credential-rotation` - Rotación automática de credenciales

#### Lambda
- `lambda:execution-roles` - Execution roles configurados
- `lambda:environment-variables` - Sin credentials en env vars
- `lambda:temporary-credentials` - Uso de credenciales temporales
- `lambda:vpc-configuration` - VPC para acceso seguro

#### ECS
- `ecs:task-definitions` - Task definitions
- `ecs:task-roles` - Task IAM roles
- `ecs:task-execution-roles` - Execution roles

#### EKS
- `eks:clusters` - Clusters EKS
- `eks:service-accounts` - Service accounts
- `eks:pod-identity` - Pod Identity configuration
- `eks:iam-roles-for-service-accounts` - IRSA

#### CodeBuild/Pipeline
- `codebuild:projects` - Build projects
- `codebuild:service-roles` - Service roles
- `codepipeline:pipelines` - Pipelines
- `codepipeline:service-roles` - Service roles
- `codepipeline:cross-account-roles` - Cross-account roles

#### Config
- `config:iam-user-unused-credentials` - Credenciales no usadas
- `config:iam-access-key-rotation` - Access key rotation check
- `config:root-access-key-check` - Root access keys
- `config:iam-role-last-used` - Last used tracking

### Criterios de Cumplimiento
- ✓ No hay access keys de long-term para aplicaciones
- ✓ STS AssumeRole utilizado para acceso temporal
- ✓ Session duration máximo 12 horas
- ✓ Service roles attached a instancias EC2
- ✓ IMDSv2 habilitado en EC2
- ✓ No hay credentials hardcoded en código o variables de entorno
- ✓ Task roles configurados en ECS/EKS
- ✓ Cross-account roles con external ID

---

## SEC02-BP03: Almacenar y utilizar secretos de forma segura

### Descripción
Secure storage and retrieval of secrets, API keys, and sensitive credentials using Secrets Manager, Parameter Store, and KMS encryption.

### Servicios Principales
| Servicio | Descripción |
|----------|-------------|
| **AWS Secrets Manager** | Secret storage, auto-rotation, replication |
| **AWS Systems Manager** | Parameter Store, SecureString, policies |
| **AWS KMS** | Customer managed keys, rotation, access control |
| **Amazon RDS** | Secrets Manager integration, IAM auth |
| **Amazon ElastiCache** | Auth tokens, encryption |
| **AWS Lambda** | Secret retrieval, VPC access |
| **Amazon ECS/EKS** | Secret mounting, init containers |

### Recursos a Revisar

#### Secrets Manager
- `secretsmanager:secrets` - Secretos almacenados
- `secretsmanager:database-credentials` - Credenciales de BD
- `secretsmanager:api-keys` - API keys y tokens
- `secretsmanager:automatic-rotation` - Rotación automática
- `secretsmanager:cross-region-replication` - Replicación multi-región
- `secretsmanager:resource-policies` - Resource-based policies
- `secretsmanager:vpc-endpoints` - VPC endpoints para acceso privado

#### Systems Manager Parameter Store
- `ssm:parameters` - Parámetros almacenados
- `ssm:secure-string-parameters` - SecureString type (KMS encrypted)
- `ssm:kms-encryption` - Encriptación KMS habilitada
- `ssm:parameter-policies` - Políticas de parámetros
- `ssm:access-logging` - Logging de acceso
- `ssm:parameter-hierarchies` - Organización jerárquica

#### KMS
- `kms:keys` - Customer managed keys
- `kms:customer-managed-keys` - CMKs para secrets
- `kms:key-policies` - Key policies restrictivas
- `kms:key-rotation` - Automatic key rotation (anual)
- `kms:cross-account-usage` - Uso cross-account
- `kms:cloudtrail-logging` - CloudTrail logging

#### RDS
- `rds:db-instances` - Instancias RDS
- `rds:secrets-manager-integration` - Integración con Secrets Manager
- `rds:master-credentials` - Master user en Secrets Manager
- `rds:password-rotation` - Automatic password rotation
- `rds:iam-database-authentication` - IAM database authentication
- `rds:ssl-tls-enforcement` - SSL/TLS required

#### ElastiCache
- `elasticache:clusters` - Clusters ElastiCache
- `elasticache:auth-tokens` - Auth tokens configurados
- `elasticache:in-transit-encryption` - In-transit encryption
- `elasticache:at-rest-encryption` - At-rest encryption
- `elasticache:redis-auth` - Redis AUTH command

#### Lambda
- `lambda:environment-variables` - Sin secrets en env vars
- `lambda:secrets-manager-integration` - Integración con Secrets Manager
- `lambda:hardcoded-secrets-check` - Sin secrets hardcoded
- `lambda:vpc-configuration` - VPC para secure access

#### ECS/EKS
- `ecs:task-definitions` - Task definitions
- `ecs:secret-mounting` - Secrets como volumes
- `ecs:environment-variables` - Desde Secrets Manager
- `eks:secret-volumes` - Secret volumes
- `eks:init-containers` - Init containers para retrieval

### Criterios de Cumplimiento
- ✓ Database passwords en Secrets Manager
- ✓ API keys almacenados en Secrets Manager o Parameter Store
- ✓ Automatic rotation habilitado (mínimo anual)
- ✓ KMS encryption para todos los secrets
- ✓ VPC endpoints para acceso privado a secretos
- ✓ Resource-based policies restrictivas
- ✓ No hay secrets en código, logs, o variables de entorno
- ✓ Cross-region replication para disaster recovery

---

## SEC02-BP04: Confíe en un proveedor de identidad centralizado

### Descripción
Centralized identity provider for federated access, reducing the need for local user management and enabling single sign-on.

### Servicios Principales
| Servicio | Descripción |
|----------|-------------|
| **AWS SSO** | Identity Center, SAML/OIDC, permission sets |
| **AWS IAM** | Identity providers, SAML, OIDC, federation |
| **Amazon Cognito** | User pools, identity pools, federation |
| **AWS Directory Service** | AD Connector, Managed AD, trust relationships |
| **AWS Client VPN** | SAML authentication, AD integration |
| **Amazon WorkSpaces** | Directory integration, SAML, MFA |

### Recursos a Revisar

#### AWS SSO (Identity Center)
- `sso:instances` - Instancias de Identity Center
- `sso:identity-providers` - External IdPs (Okta, Azure AD, etc.)
- `sso:saml-configuration` - SAML 2.0 setup
- `sso:oidc-providers` - OIDC provider configuration
- `sso:attribute-mapping` - Attribute mapping from IdP
- `sso:permission-sets` - Permission sets definidos
- `sso:account-assignments` - Account assignments por usuario/grupo

#### IAM Identity Providers
- `iam:saml-providers` - SAML providers configurados
- `iam:oidc-providers` - OIDC providers setup
- `iam:web-identity-federation` - Web identity federation
- `iam:trust-relationships` - Trust relationships
- `iam:thumbprint-validation` - Thumbprint validation

#### Amazon Cognito
- `cognito:identity-pools` - Identity pools para AWS resource access
- `cognito:user-pools` - User pools para app authentication
- `cognito:external-providers` - Google, Facebook, SAML
- `cognito:saml-providers` - SAML provider integration
- `cognito:attribute-mapping` - Attribute mapping
- `cognito:role-resolution` - Role resolution rules

#### AWS Directory Service
- `ds:directories` - Directories (AD Connector, Managed AD)
- `ds:ad-connector` - AD Connector to on-premises
- `ds:managed-ad` - Managed Microsoft AD
- `ds:trust-relationships` - Trust relationships
- `ds:ldap-integration` - LDAP integration
- `ds:kerberos-settings` - Kerberos authentication

#### AWS Client VPN
- `clientvpn:endpoints` - Client VPN endpoints
- `clientvpn:saml-authentication` - SAML-based authentication
- `clientvpn:ad-integration` - Active Directory integration
- `clientvpn:certificate-authentication` - Mutual TLS
- `clientvpn:mfa-settings` - MFA requirements

#### Amazon WorkSpaces
- `workspaces:workspaces` - WorkSpaces instances
- `workspaces:directory-integration` - Directory integration
- `workspaces:saml-authentication` - SAML authentication
- `workspaces:mfa-settings` - MFA enabled
- `workspaces:ip-access-control` - IP access control groups

### Criterios de Cumplimiento
- ✓ Identity Center configurado con external IdP
- ✓ SAML 2.0 o OIDC integrado
- ✓ Attribute mapping de IdP a AWS
- ✓ Permission sets definidos para cada rol
- ✓ Account assignments configurados
- ✓ MFA requerido en IdP o AWS
- ✓ Federated users no requieren local IAM users
- ✓ SSO habilitado para aplicaciones integradas

---

## SEC02-BP05: Auditar y rotar credenciales periódicamente

### Descripción
Regular audit and rotation of all credentials to minimize the window of exposure if credentials are compromised.

### Servicios Principales
| Servicio | Descripción |
|----------|-------------|
| **AWS IAM** | Access key age, password tracking, rotation |
| **AWS Config** | Compliance rules, rotation checks |
| **AWS CloudTrail** | Credential usage tracking, audit logs |
| **Amazon CloudWatch** | Alerts, dashboards, monitoring |
| **AWS Secrets Manager** | Automatic rotation, version management |
| **AWS Systems Manager** | Automation, maintenance windows |
| **AWS Lambda** | Rotation functions, event-driven updates |

### Recursos a Revisar

#### IAM
- `iam:users` - Usuario IAM
- `iam:access-keys` - Access keys (máximo 2, rotadas cada 90 días)
- `iam:credential-report` - Credential report
- `iam:access-key-age` - Edad de access keys
- `iam:password-last-used` - Last used date
- `iam:rotation-policies` - Rotation policies
- `iam:unused-credentials` - Credenciales no usadas

#### Config
- `config:iam-password-policy` - Password policy checks
- `config:access-key-rotation-rule` - Access key rotation rules
- `config:unused-iam-user-check` - Unused users detection
- `config:root-access-key-check` - Root access keys (deben ser 0)
- `config:iam-user-mfa-enabled` - MFA enabled check

#### CloudTrail
- `cloudtrail:trails` - CloudTrail trails activos
- `cloudtrail:api-calls` - API call logging
- `cloudtrail:authentication-events` - Auth events
- `cloudtrail:credential-usage` - Credential usage
- `cloudtrail:cross-account-access` - Cross-account access

#### CloudWatch
- `cloudwatch:alarms-credential-age` - Alarmas de edad de credenciales
- `cloudwatch:alarms-unused-credentials` - Credenciales no usadas
- `cloudwatch:alarms-failed-auth` - Fallos de autenticación
- `cloudwatch:alarms-anomalous-access` - Acceso anómalo
- `cloudwatch:dashboards-rotation-status` - Dashboards de rotación

#### Secrets Manager
- `secretsmanager:secrets` - Secretos
- `secretsmanager:rotation-configuration` - Rotation config
- `secretsmanager:rotation-schedules` - Rotation schedule (30 días recomendado)
- `secretsmanager:rotation-monitoring` - Success/failure monitoring
- `secretsmanager:version-management` - Version management

#### Systems Manager
- `ssm:parameters` - Parámetros
- `ssm:automation-documents` - Rotation automation
- `ssm:maintenance-windows` - Maintenance windows
- `ssm:patch-manager` - Patch updates
- `ssm:compliance-tracking` - Compliance tracking

#### Lambda
- `lambda:rotation-functions` - Rotation Lambda functions
- `lambda:event-driven-updates` - Event-driven updates
- `lambda:error-handling` - Error handling
- `lambda:dead-letter-queues` - DLQs para fallos
- `lambda:monitoring` - Monitoring y logging

### Criterios de Cumplimiento
- ✓ Access keys rotadas cada 90 días máximo
- ✓ Passwords rotadas cada 90 días máximo
- ✓ Credenciales no usadas eliminadas (> 90 días sin uso)
- ✓ Root account sin access keys
- ✓ Automatic rotation habilitado para secrets
- ✓ CloudTrail logging de credential usage
- ✓ Alarmas para credenciales vencidas
- ✓ Compliance reports generados mensualmente

---

## SEC02-BP06: Emplear grupos de usuarios y atributos

### Descripción
Use user groups and attribute-based access control for scalable and maintainable permission management.

### Servicios Principales
| Servicio | Descripción |
|----------|-------------|
| **AWS IAM** | Groups, group policies, nested groups |
| **AWS SSO** | Permission sets, groups, ABAC |
| **Amazon Cognito** | User pool groups, role mapping |
| **AWS Directory Service** | Security groups, OUs, GPOs |
| **AWS Resource Access Manager** | Resource sharing with groups |
| **AWS Organizations** | SCPs, organizational structure |

### Recursos a Revisar

#### IAM Groups
- `iam:groups` - Grupos IAM
- `iam:group-policies` - Políticas attached a grupos
- `iam:nested-groups` - Nested group memberships
- `iam:group-memberships` - Memberships (por función)
- `iam:service-control-policies` - SCPs por grupo

#### AWS SSO
- `sso:permission-sets` - Permission sets por rol
- `sso:groups` - Grupos del IdP
- `sso:group-assignments` - Asignaciones a cuentas
- `sso:attribute-based-access` - ABAC rules
- `sso:session-tags` - Session tags para ABAC
- `sso:dynamic-groups` - Dynamic group membership

#### Cognito
- `cognito:user-pool-groups` - User pool groups
- `cognito:group-precedence` - Group precedence rules
- `cognito:group-role-mapping` - Role mapping por groups
- `cognito:custom-attributes` - Custom attributes para ABAC
- `cognito:group-based-authorization` - Authorization rules

#### Directory Service
- `ds:security-groups` - Security groups en AD
- `ds:organizational-units` - OUs structure
- `ds:group-policy-objects` - Group Policy Objects (GPOs)
- `ds:distribution-groups` - Distribution groups
- `ds:nested-groups` - Nested group memberships

#### Resource Access Manager
- `ram:resource-shares` - Resource shares
- `ram:principal-associations` - Principal associations (usuarios/grupos)
- `ram:resource-associations` - Resource associations
- `ram:sharing-policies` - Sharing policies
- `ram:cross-account-sharing` - Cross-account sharing

#### Organizations
- `organizations:organizational-units` - OU structure
- `organizations:service-control-policies` - SCPs
- `organizations:account-grouping` - Account grouping
- `organizations:tag-based-access` - Tag-based access control
- `organizations:delegated-administration` - Delegated admins

### Criterios de Cumplimiento
- ✓ Usuarios organizados en grupos por función
- ✓ Grupos con políticas attach, no usuarios directamente
- ✓ Principle of least privilege aplicado
- ✓ Permission sets definidos en SSO
- ✓ Attribute-based access control implementado
- ✓ Role mapping configurado por grupos
- ✓ Organizational structure clara (OUs)
- ✓ Service Control Policies aplicadas

---

## Resumen de Servicios AWS Utilizados

Total de **12 servicios AWS** cubiertos en SEC02:

| Servicio | BPs | Uso Principal |
|----------|-----|---------------|
| AWS IAM | 1,2,5,6 | Roles, groups, MFA, password policy |
| AWS STS | 2 | Temporary credentials |
| AWS SSO | 1,4,6 | Federated access, permission sets |
| Amazon Cognito | 1,3,4,6 | User pools, federated identity |
| AWS Directory Service | 1,4,6 | AD integration, Kerberos |
| AWS CloudTrail | 1,2,5 | Audit logging, event tracking |
| Amazon CloudWatch | 1,5 | Alarms, monitoring |
| AWS Secrets Manager | 3,5 | Secret storage, auto-rotation |
| AWS Systems Manager | 3,5 | Parameter Store, automation |
| AWS KMS | 3 | Encryption key management |
| AWS Config | 2,5 | Compliance checks, rules |
| AWS Organizations | 6 | SCPs, account structure |

---

## Matriz de Cumplimiento Rápida

```
SEC02-BP01 (Login Fuerte)
├─ [ ] Password policy configurada (12+ chars, complejidad, rotación)
├─ [ ] MFA habilitado para todos los usuarios
├─ [ ] Root account con MFA
├─ [ ] CloudTrail logging de eventos
└─ [ ] Alarmas para intentos fallidos

SEC02-BP02 (Credenciales Temporales)
├─ [ ] STS AssumeRole utilizado
├─ [ ] Service roles en EC2/Lambda/ECS
├─ [ ] IMDSv2 habilitado
├─ [ ] No hay access keys de long-term
└─ [ ] Session duration máximo 12 horas

SEC02-BP03 (Secrets Seguros)
├─ [ ] Database passwords en Secrets Manager
├─ [ ] Automatic rotation cada 30-90 días
├─ [ ] KMS encryption habilitado
├─ [ ] VPC endpoints para acceso privado
└─ [ ] No hay secrets hardcoded

SEC02-BP04 (Proveedor Centralizado)
├─ [ ] SSO/Identity Center configurado
├─ [ ] SAML/OIDC integrado
├─ [ ] Attribute mapping configurado
├─ [ ] Permission sets definidos
└─ [ ] MFA requerido en IdP

SEC02-BP05 (Auditoría y Rotación)
├─ [ ] Access keys rotadas cada 90 días
├─ [ ] Credenciales no usadas eliminadas
├─ [ ] CloudTrail logging habilitado
├─ [ ] Alarmas de credenciales vencidas
└─ [ ] Compliance reports generados

SEC02-BP06 (Grupos y Atributos)
├─ [ ] Usuarios organizados en grupos
├─ [ ] Policies attached a grupos
├─ [ ] ABAC implementado
├─ [ ] Permission sets por rol
└─ [ ] Principle of least privilege aplicado
```

---

## Próximos Pasos

1. Crear validadores para cada SEC02-BP
2. Integrar en security_evaluator.py
3. Agregar checks específicos de AWS
4. Configurar alarms y monitoring
5. Crear reportes de cumplimiento
