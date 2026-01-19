"""
Mock Security Pillar Evaluator - Returns realistic demo data for UI testing
Shows all 11 Security questions with 63 best practices organized per AWS Well-Architected Framework
Structure from: Alcance Proyecto AutoWAR (ACTUALIZADO).md - line 206+
"""

from datetime import datetime

class MockSecurityEvaluator:
    """Mock evaluator that returns realistic but synthetic security evaluation results"""
    
    def __init__(self):
        self.timestamp = datetime.now().isoformat()
    
    def evaluate_all(self):
        """Return all 11 questions with 63 best practices and mock findings"""
        return {
            'overall_score': 78.5,
            'total_findings': 24,
            'total_best_practices': 63,
            'timestamp': self.timestamp,
            'questions': [
                # SEC01: Fundamentos de Seguridad (8 BPs)
                self._get_sec01_question(),
                # SEC02: Autenticación (6 BPs)
                self._get_sec02_question(),
                # SEC03: Permisos (9 BPs)
                self._get_sec03_question(),
                # SEC04: Detección (4 BPs)
                self._get_sec04_question(),
                # SEC05: Protección de Red (4 BPs)
                self._get_sec05_question(),
                # SEC06: Protección de Recursos (5 BPs)
                self._get_sec06_question(),
                # SEC07: Clasificación de Datos (4 BPs)
                self._get_sec07_question(),
                # SEC08: Datos en Reposo (4 BPs)
                self._get_sec08_question(),
                # SEC09: Datos en Tránsito (3 BPs)
                self._get_sec09_question(),
                # SEC10: Respuesta a Incidentes (8 BPs)
                self._get_sec10_question(),
                # SEC11: Seguridad de Aplicaciones (8 BPs)
                self._get_sec11_question(),
            ]
        }
    
    
    def _get_sec01_question(self):
        """SEC01: Fundamentos de Seguridad - 8 BPs"""
        return {
            'question_id': 'SEC01',
            'title': 'Fundamentos de Seguridad - ¿Cómo opera su carga de trabajo?',
            'description': 'How do you operate your workload securely?',
            'score': 95,
            'bps_evaluated': 8,
            'status': 'COMPLIANT',
            'findings': [
                {'bp': 'SEC01-BP01', 'status': 'COMPLIANT', 'finding': 'Separar cargas de trabajo mediante cuentas', 'severity': 'LOW', 'evidence': 'AWS Organizations configured with 5 accounts', 'remediation': 'Current state compliant', 'risk': 'No risk'},
                {'bp': 'SEC01-BP02', 'status': 'NON_COMPLIANT', 'finding': 'Proteger la identidad raíz de la cuenta', 'severity': 'MEDIUM', 'evidence': 'MFA not enabled on root account', 'remediation': 'Enable MFA on root account and apply IP restrictions', 'risk': 'Root account compromise'},
                {'bp': 'SEC01-BP03', 'status': 'COMPLIANT', 'finding': 'Identificar y validar objetivos de control', 'severity': 'LOW', 'evidence': 'Security control matrix documented and reviewed', 'remediation': 'Current state compliant', 'risk': 'No risk'},
                {'bp': 'SEC01-BP04', 'status': 'COMPLIANT', 'finding': 'Manténgase actualizado con las amenazas', 'severity': 'LOW', 'evidence': 'Threat landscape reviewed quarterly; security patches current', 'remediation': 'Current state compliant', 'risk': 'No risk'},
                {'bp': 'SEC01-BP05', 'status': 'NON_COMPLIANT', 'finding': 'Reducir el alcance de la gestión de seguridad', 'severity': 'MEDIUM', 'evidence': 'Manual security processes still in use for 30% of controls', 'remediation': 'Implement Infrastructure as Code for security policies', 'risk': 'Human error in security management'},
                {'bp': 'SEC01-BP06', 'status': 'COMPLIANT', 'finding': 'Automatizar la implementación de controles', 'severity': 'LOW', 'evidence': 'CloudFormation and Terraform templates deployed automatically', 'remediation': 'Current state compliant', 'risk': 'No risk'},
                {'bp': 'SEC01-BP07', 'status': 'PENDING_REVIEW', 'finding': 'Identificar amenazas mediante threat modeling', 'severity': 'MEDIUM', 'evidence': 'Threat model last updated 3 months ago; should be reviewed quarterly', 'remediation': 'Update threat model and conduct quarterly reviews', 'risk': 'Outdated threat assessment'},
                {'bp': 'SEC01-BP08', 'status': 'COMPLIANT', 'finding': 'Evaluar nuevos servicios de seguridad', 'severity': 'LOW', 'evidence': 'New AWS security features reviewed in monthly architecture meetings', 'remediation': 'Current state compliant', 'risk': 'No risk'}
            ]
        }
    
    
    def _get_sec02_question(self):
        """SEC02: Autenticación - 6 BPs"""
        return {
            'question_id': 'SEC02',
            'title': 'Autenticación - ¿Cómo se gestiona la autenticación?',
            'description': 'How do you manage authentication for people and machines?',
            'score': 85,
            'bps_evaluated': 6,
            'status': 'COMPLIANT',
            'findings': [
                {'bp': 'SEC02-BP01', 'status': 'COMPLIANT', 'finding': 'Utilizar mecanismos de autenticación fuertes', 'severity': 'LOW', 'evidence': 'MFA enabled for 98% of console users', 'remediation': 'Current state compliant', 'risk': 'No risk'},
                {'bp': 'SEC02-BP02', 'status': 'NON_COMPLIANT', 'finding': 'Utilizar credenciales temporales en lugar de claves de acceso de largo plazo', 'severity': 'HIGH', 'evidence': '5 active long-term access keys exceeding 90 days', 'remediation': 'Migrate to STS temporary credentials or use IAM roles', 'risk': 'Credential compromise and unauthorized access'},
                {'bp': 'SEC02-BP03', 'status': 'COMPLIANT', 'finding': 'Almacenar y usar secretos de forma segura', 'severity': 'LOW', 'evidence': 'AWS Secrets Manager managing all database credentials', 'remediation': 'Current state compliant', 'risk': 'No risk'},
                {'bp': 'SEC02-BP04', 'status': 'COMPLIANT', 'finding': 'Confíe en un proveedor de identidad centralizado', 'severity': 'LOW', 'evidence': 'AWS IAM Identity Center configured; SSO enforced', 'remediation': 'Current state compliant', 'risk': 'No risk'},
                {'bp': 'SEC02-BP05', 'status': 'PENDING_REVIEW', 'finding': 'Auditar y rotar credenciales', 'severity': 'MEDIUM', 'evidence': 'Manual credential rotation quarterly; automation in progress', 'remediation': 'Implement automatic key rotation policies', 'risk': 'Old credentials may remain in use'},
                {'bp': 'SEC02-BP06', 'status': 'COMPLIANT', 'finding': 'Emplear grupos de usuarios para gestionar permisos', 'severity': 'LOW', 'evidence': 'User groups configured by role and department', 'remediation': 'Current state compliant', 'risk': 'No risk'}
            ]
        }
    
    
    def _get_sec03_question(self):
        """SEC03: Permisos - 9 BPs"""
        return {
            'question_id': 'SEC03',
            'title': 'Permisos - ¿Cómo se gestionan los permisos?',
            'description': 'How do you manage permissions for people and machines?',
            'score': 72,
            'bps_evaluated': 9,
            'status': 'PARTIAL',
            'findings': [
                {'bp': 'SEC03-BP01', 'status': 'COMPLIANT', 'finding': 'Definir los requisitos de acceso requeridos', 'severity': 'LOW', 'evidence': 'Access matrix documented and reviewed quarterly', 'remediation': 'Current state compliant', 'risk': 'No risk'},
                {'bp': 'SEC03-BP02', 'status': 'NON_COMPLIANT', 'finding': 'Otorgar acceso con privilegios mínimos', 'severity': 'CRITICAL', 'evidence': '8 users with unnecessary administrative permissions', 'remediation': 'Apply principle of least privilege; implement role-based access', 'risk': 'Excessive permission scope increases breach impact'},
                {'bp': 'SEC03-BP03', 'status': 'COMPLIANT', 'finding': 'Establecer y mantener un proceso de acceso de emergencia', 'severity': 'LOW', 'evidence': 'Break-glass procedure documented and tested annually', 'remediation': 'Current state compliant', 'risk': 'No risk'},
                {'bp': 'SEC03-BP04', 'status': 'PENDING_REVIEW', 'finding': 'Reducir permisos de acceso de manera continua', 'severity': 'MEDIUM', 'evidence': 'Quarterly permission reviews; some unused roles not removed', 'remediation': 'Implement automated unused role detection and removal', 'risk': 'Permission creep and accumulation of unused access'},
                {'bp': 'SEC03-BP05', 'status': 'COMPLIANT', 'finding': 'Definir y hacer cumplir las barreras de permisos', 'severity': 'LOW', 'evidence': 'IAM permission boundaries configured on all developer roles', 'remediation': 'Current state compliant', 'risk': 'No risk'},
                {'bp': 'SEC03-BP06', 'status': 'COMPLIANT', 'finding': 'Gestionar el acceso en función del ciclo de vida', 'severity': 'LOW', 'evidence': 'Automated provisioning/deprovisioning for joiners/leavers', 'remediation': 'Current state compliant', 'risk': 'No risk'},
                {'bp': 'SEC03-BP07', 'status': 'NON_COMPLIANT', 'finding': 'Analizar el acceso público y entre cuentas', 'severity': 'MEDIUM', 'evidence': '2 S3 buckets with unintended public read access; cross-account policies not reviewed', 'remediation': 'Restrict public access and validate cross-account access controls', 'risk': 'Data exposure and unauthorized cross-account access'},
                {'bp': 'SEC03-BP08', 'status': 'COMPLIANT', 'finding': 'Compartir recursos de forma segura dentro de la organización', 'severity': 'LOW', 'evidence': 'Resource-based policies properly configured for organization sharing', 'remediation': 'Current state compliant', 'risk': 'No risk'},
                {'bp': 'SEC03-BP09', 'status': 'PENDING_REVIEW', 'finding': 'Compartir recursos con terceros de forma segura', 'severity': 'MEDIUM', 'evidence': 'External ID validation implemented; review of third-party accounts needed', 'remediation': 'Audit and document all third-party resource access', 'risk': 'Unauthorized third-party access to resources'}
            ]
        }
    
    
    def _get_sec04_question(self):
        """SEC04: Detección - 4 BPs"""
        return {
            'question_id': 'SEC04',
            'title': 'Detección - ¿Cómo se detectan e investigan eventos?',
            'description': 'How do you detect and investigate security events?',
            'score': 75,
            'bps_evaluated': 4,
            'status': 'PARTIAL',
            'findings': [
                {'bp': 'SEC04-BP01', 'status': 'NON_COMPLIANT', 'finding': 'Registrar actividades de cuenta', 'severity': 'HIGH', 'evidence': 'CloudTrail not enabled in 8 of 15 accounts', 'remediation': 'Enable multi-region CloudTrail in all accounts', 'risk': 'Undetected unauthorized activities'},
                {'bp': 'SEC04-BP02', 'status': 'COMPLIANT', 'finding': 'Proteger, mantener y analizar registros', 'severity': 'LOW', 'evidence': 'CloudTrail logs encrypted and stored with MFA delete', 'remediation': 'Current state compliant', 'risk': 'No risk'},
                {'bp': 'SEC04-BP03', 'status': 'COMPLIANT', 'finding': 'Alertas y notificaciones de actividad', 'severity': 'LOW', 'evidence': 'CloudWatch alarms configured for suspicious activities', 'remediation': 'Current state compliant', 'risk': 'No risk'},
                {'bp': 'SEC04-BP04', 'status': 'PENDING_REVIEW', 'finding': 'Análisis y automatización de respuesta', 'severity': 'MEDIUM', 'evidence': 'Manual incident response procedures; automation partially implemented', 'remediation': 'Implement AWS Lambda for automated incident response', 'risk': 'Delayed incident response and manual inefficiencies'}
            ]
        }
    
    def _get_sec05_question(self):
        """SEC05: Protección de Red - 4 BPs"""
        return {
            'question_id': 'SEC05',
            'title': 'Protección de Red - ¿Cómo protege su red?',
            'description': 'How do you protect your network resources?',
            'score': 79,
            'bps_evaluated': 4,
            'status': 'PARTIAL',
            'findings': [
                {'bp': 'SEC05-BP01', 'status': 'COMPLIANT', 'finding': 'Crear una red de perímetro protegida', 'severity': 'LOW', 'evidence': 'VPCs properly segregated by environment', 'remediation': 'Current state compliant', 'risk': 'No risk'},
                {'bp': 'SEC05-BP02', 'status': 'NON_COMPLIANT', 'finding': 'Implementar inspección de paquetes', 'severity': 'CRITICAL', 'evidence': '2 security groups allow unrestricted SSH/RDP (0.0.0.0/0)', 'remediation': 'Restrict SSH/RDP to known IP ranges; implement VPC Flow Logs', 'risk': 'Unauthorized network access and lateral movement'},
                {'bp': 'SEC05-BP03', 'status': 'COMPLIANT', 'finding': 'Automatizar el descubrimiento de topología de red', 'severity': 'LOW', 'evidence': 'VPC Flow Logs enabled and aggregating to CloudWatch', 'remediation': 'Current state compliant', 'risk': 'No risk'},
                {'bp': 'SEC05-BP04', 'status': 'PENDING_REVIEW', 'finding': 'Proteger recursos con WAF', 'severity': 'MEDIUM', 'evidence': 'WAF rules applied to ALB but need coverage for API Gateway', 'remediation': 'Extend WAF coverage to all public APIs', 'risk': 'Application-level attacks not prevented'}
            ]
        }
    
    def _get_sec06_question(self):
        """SEC06: Protección de Recursos - 5 BPs"""
        return {
            'question_id': 'SEC06',
            'title': 'Protección de Recursos - ¿Cómo protege sus recursos?',
            'description': 'How do you protect your compute resources?',
            'score': 81,
            'bps_evaluated': 5,
            'status': 'COMPLIANT',
            'findings': [
                {'bp': 'SEC06-BP01', 'status': 'COMPLIANT', 'finding': 'Implementar protección de punto final', 'severity': 'LOW', 'evidence': 'SSM Session Manager restricts shell access; GuardDuty enabled', 'remediation': 'Current state compliant', 'risk': 'No risk'},
                {'bp': 'SEC06-BP02', 'status': 'NON_COMPLIANT', 'finding': 'Vulnerabilidades de aplicación y parches', 'severity': 'MEDIUM', 'evidence': '3 EC2 instances missing critical OS patches (30+ days old)', 'remediation': 'Implement Patch Manager and enable automatic patching', 'risk': 'Known vulnerabilities exploitable by attackers'},
                {'bp': 'SEC06-BP03', 'status': 'COMPLIANT', 'finding': 'Cambios en la configuración de recursos', 'severity': 'LOW', 'evidence': 'AWS Config tracking all resource changes; rules enforced', 'remediation': 'Current state compliant', 'risk': 'No risk'},
                {'bp': 'SEC06-BP04', 'status': 'COMPLIANT', 'finding': 'Aislamiento de carga de trabajo', 'severity': 'LOW', 'evidence': 'EC2 instances in private subnets; no direct internet access', 'remediation': 'Current state compliant', 'risk': 'No risk'},
                {'bp': 'SEC06-BP05', 'status': 'COMPLIANT', 'finding': 'Gestión de acceso administrativo', 'severity': 'LOW', 'evidence': 'SSH/RDP restricted to bastion hosts; logging enabled', 'remediation': 'Current state compliant', 'risk': 'No risk'}
            ]
        }
    
    def _get_sec07_question(self):
        """SEC07: Clasificación de Datos - 4 BPs"""
        return {
            'question_id': 'SEC07',
            'title': 'Clasificación de Datos - ¿Cómo clasifica sus datos?',
            'description': 'How do you classify your data?',
            'score': 84,
            'bps_evaluated': 4,
            'status': 'COMPLIANT',
            'findings': [
                {'bp': 'SEC07-BP01', 'status': 'COMPLIANT', 'finding': 'Identificar tipos de datos en su carga de trabajo', 'severity': 'LOW', 'evidence': 'Data inventory documented; classification schema defined', 'remediation': 'Current state compliant', 'risk': 'No risk'},
                {'bp': 'SEC07-BP02', 'status': 'PENDING_REVIEW', 'finding': 'Definir seguridad de datos por clasificación', 'severity': 'MEDIUM', 'evidence': 'Security policies exist; not fully automated for all data types', 'remediation': 'Automate data classification using Macie and tagging', 'risk': 'Inconsistent protection of sensitive data'},
                {'bp': 'SEC07-BP03', 'status': 'COMPLIANT', 'finding': 'Análisis de exposición de datos', 'severity': 'LOW', 'evidence': 'Macie enabled; monthly data exposure scans performed', 'remediation': 'Current state compliant', 'risk': 'No risk'},
                {'bp': 'SEC07-BP04', 'status': 'COMPLIANT', 'finding': 'Redacción de datos', 'severity': 'LOW', 'evidence': 'Sensitive data redacted in logs and backups', 'remediation': 'Current state compliant', 'risk': 'No risk'}
            ]
        }
    
    def _get_sec08_question(self):
        """SEC08: Datos en Reposo - 4 BPs"""
        return {
            'question_id': 'SEC08',
            'title': 'Datos en Reposo - ¿Cómo protege sus datos en reposo?',
            'description': 'How do you protect data at rest?',
            'score': 91,
            'bps_evaluated': 4,
            'status': 'COMPLIANT',
            'findings': [
                {'bp': 'SEC08-BP01', 'status': 'NON_COMPLIANT', 'finding': 'Implementar el cifrado de datos en reposo', 'severity': 'HIGH', 'evidence': '3 S3 buckets without default encryption; 1 RDS instance unencrypted', 'remediation': 'Enable KMS encryption on all storage resources', 'risk': 'Unencrypted sensitive data at rest'},
                {'bp': 'SEC08-BP02', 'status': 'COMPLIANT', 'finding': 'Gestión de claves de cifrado', 'severity': 'LOW', 'evidence': 'KMS keys with automatic rotation; access logging enabled', 'remediation': 'Current state compliant', 'risk': 'No risk'},
                {'bp': 'SEC08-BP03', 'status': 'COMPLIANT', 'finding': 'Almacenamiento seguro de secretos', 'severity': 'LOW', 'evidence': 'All secrets encrypted with Secrets Manager', 'remediation': 'Current state compliant', 'risk': 'No risk'},
                {'bp': 'SEC08-BP04', 'status': 'COMPLIANT', 'finding': 'Confidencialidad y disponibilidad de datos', 'severity': 'LOW', 'evidence': 'Backup and recovery procedures tested; RTO/RPO defined', 'remediation': 'Current state compliant', 'risk': 'No risk'}
            ]
        }
    
    def _get_sec09_question(self):
        """SEC09: Datos en Tránsito - 3 BPs"""
        return {
            'question_id': 'SEC09',
            'title': 'Datos en Tránsito - ¿Cómo protege sus datos en tránsito?',
            'description': 'How do you protect data in transit?',
            'score': 93,
            'bps_evaluated': 3,
            'status': 'COMPLIANT',
            'findings': [
                {'bp': 'SEC09-BP01', 'status': 'COMPLIANT', 'finding': 'Implementar el cifrado de datos en tránsito', 'severity': 'LOW', 'evidence': 'TLS 1.2+ enforced on all APIs and ALBs', 'remediation': 'Current state compliant', 'risk': 'No risk'},
                {'bp': 'SEC09-BP02', 'status': 'PENDING_REVIEW', 'finding': 'Autenticar componentes de comunicación de datos', 'severity': 'MEDIUM', 'evidence': 'mTLS implemented in some services; needs expansion', 'remediation': 'Extend mTLS to all internal service-to-service communication', 'risk': 'Man-in-the-middle attacks between services'},
                {'bp': 'SEC09-BP03', 'status': 'COMPLIANT', 'finding': 'Cifrar datos en tránsito en redes públicas', 'severity': 'LOW', 'evidence': 'VPN encryption enforced; Site-to-site uses 256-bit encryption', 'remediation': 'Current state compliant', 'risk': 'No risk'}
            ]
        }
    
    def _get_sec10_question(self):
        """SEC10: Respuesta a Incidentes - 8 BPs"""
        return {
            'question_id': 'SEC10',
            'title': 'Respuesta a Incidentes - ¿Cómo anticipa y responde a incidentes?',
            'description': 'How do you anticipate and respond to incidents?',
            'score': 68,
            'bps_evaluated': 8,
            'status': 'PARTIAL',
            'findings': [
                {'bp': 'SEC10-BP01', 'status': 'PENDING_REVIEW', 'finding': 'Plan de respuesta a incidentes', 'severity': 'MEDIUM', 'evidence': 'IR playbook exists but last updated 8 months ago', 'remediation': 'Update IR plan quarterly and schedule tabletop exercises', 'risk': 'Outdated procedures may not address current threats'},
                {'bp': 'SEC10-BP02', 'status': 'COMPLIANT', 'finding': 'Simular respuesta a incidentes', 'severity': 'LOW', 'evidence': 'Annual incident simulation drills performed', 'remediation': 'Current state compliant', 'risk': 'No risk'},
                {'bp': 'SEC10-BP03', 'status': 'NON_COMPLIANT', 'finding': 'Prepararse para respuestas a incidentes', 'severity': 'HIGH', 'evidence': 'No dedicated incident response team; roles not defined', 'remediation': 'Establish formal incident response team with defined roles', 'risk': 'Uncoordinated incident response; delayed mitigation'},
                {'bp': 'SEC10-BP04', 'status': 'COMPLIANT', 'finding': 'Post-incidentes/análisis raíz', 'severity': 'LOW', 'evidence': 'Post-incident reviews documented for past incidents', 'remediation': 'Current state compliant', 'risk': 'No risk'},
                {'bp': 'SEC10-BP05', 'status': 'NON_COMPLIANT', 'finding': 'Plan y prueba de recuperación de desastres', 'severity': 'HIGH', 'evidence': 'No DR drill in the last 12 months; recovery time unknown', 'remediation': 'Schedule comprehensive DR exercise and document RTO/RPO', 'risk': 'Unknown recovery capabilities; extended downtime risk'},
                {'bp': 'SEC10-BP06', 'status': 'COMPLIANT', 'finding': 'Notificación de incidentes', 'severity': 'LOW', 'evidence': 'Incident notification templates and contact lists maintained', 'remediation': 'Current state compliant', 'risk': 'No risk'},
                {'bp': 'SEC10-BP07', 'status': 'PENDING_REVIEW', 'finding': 'Disponibilidad de herramientas de investigación', 'severity': 'MEDIUM', 'evidence': 'Basic investigation tools available; advanced forensics tools needed', 'remediation': 'Implement AWS Forensics tools and maintain jump hosts', 'risk': 'Limited forensic investigation capabilities'},
                {'bp': 'SEC10-BP08', 'status': 'COMPLIANT', 'finding': 'Acuerdos de apoyo', 'severity': 'LOW', 'evidence': 'AWS Premium Support and incident response SLAs documented', 'remediation': 'Current state compliant', 'risk': 'No risk'}
            ]
        }
    
    def _get_sec11_question(self):
        """SEC11: Seguridad de Aplicaciones - 8 BPs"""
        return {
            'question_id': 'SEC11',
            'title': 'Seguridad de Aplicaciones - ¿Cómo incorpora seguridad en el ciclo de vida?',
            'description': 'How do you build and deploy secure applications?',
            'score': 77,
            'bps_evaluated': 8,
            'status': 'PARTIAL',
            'findings': [
                {'bp': 'SEC11-BP01', 'status': 'COMPLIANT', 'finding': 'Requisitos de seguridad en el código', 'severity': 'LOW', 'evidence': 'Security requirements documented in design specs', 'remediation': 'Current state compliant', 'risk': 'No risk'},
                {'bp': 'SEC11-BP02', 'status': 'PENDING_REVIEW', 'finding': 'Análisis de seguridad del código fuente', 'severity': 'MEDIUM', 'evidence': 'SAST tools partially integrated; not mandatory in pipeline', 'remediation': 'Enforce mandatory SAST analysis in CI/CD pipeline', 'risk': 'Vulnerable code patterns not caught early'},
                {'bp': 'SEC11-BP03', 'status': 'NON_COMPLIANT', 'finding': 'Prueba de penetración', 'severity': 'MEDIUM', 'evidence': 'No regular penetration testing program; last test 18 months ago', 'remediation': 'Implement annual penetration testing or implement DAST in pipeline', 'risk': 'Unknown application vulnerabilities'},
                {'bp': 'SEC11-BP04', 'status': 'COMPLIANT', 'finding': 'Gestión de dependencias', 'severity': 'LOW', 'evidence': 'Dependency scanning with SBOM generation in build pipeline', 'remediation': 'Current state compliant', 'risk': 'No risk'},
                {'bp': 'SEC11-BP05', 'status': 'PENDING_REVIEW', 'finding': 'Endurecimiento de imagen de contenedor', 'severity': 'MEDIUM', 'evidence': 'Container images scanned; hardening policies not fully enforced', 'remediation': 'Implement container image signing and policy enforcement', 'risk': 'Deployment of vulnerable or unsigned container images'},
                {'bp': 'SEC11-BP06', 'status': 'COMPLIANT', 'finding': 'Gestión de distribución de aplicaciones', 'severity': 'LOW', 'evidence': 'Canary deployments and automated rollbacks configured', 'remediation': 'Current state compliant', 'risk': 'No risk'},
                {'bp': 'SEC11-BP07', 'status': 'NON_COMPLIANT', 'finding': 'Auditoría de cambios de compilación', 'severity': 'MEDIUM', 'evidence': 'Build changes logged; audit trail not immutable', 'remediation': 'Implement immutable audit logging for all build changes', 'risk': 'Build tampering not detectable'},
                {'bp': 'SEC11-BP08', 'status': 'PENDING_REVIEW', 'finding': 'Certificados y secretos en código', 'severity': 'HIGH', 'evidence': 'Secret scanning implemented but 5 old hardcoded secrets found', 'remediation': 'Rotate all hardcoded credentials and enforce pre-commit scanning', 'risk': 'Exposed credentials and keys in version control'}
            ]
        }
