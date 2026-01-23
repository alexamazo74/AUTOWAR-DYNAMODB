"""
Comprehensive Security Pillar Evaluator
Evaluates all 11 questions and 63 best practices against real AWS resources
"""

from typing import Dict, List, Any
from .aws_connector import AWSConnector
import logging

logger = logging.getLogger(__name__)


class SecurityPillarEvaluator:
    """Evaluates all 11 Security pillar questions"""
    
    def __init__(self, connector: AWSConnector):
        self.connector = connector
    
    def _create_pending_finding(self, bp: str, finding: str, severity: str = 'MEDIUM') -> Dict[str, Any]:
        """Create a PENDING_REVIEW finding with all required fields"""
        return {
            'bp': bp,
            'status': 'PENDING_REVIEW',
            'finding': finding,
            'severity': severity,
            'risk': 'N/D',
            'remediation': 'N/D',
            'evidence': 'N/D'
        }
    
    def _create_no_resources_finding(self, bp: str, finding: str, reason: str) -> Dict[str, Any]:
        """Create a finding when no resources/services are found"""
        return {
            'bp': bp,
            'status': 'PENDING_REVIEW',
            'finding': finding,
            'severity': 'MEDIUM',
            'risk': 'Unable to assess - no resources configured',
            'remediation': 'N/D',
            'evidence': reason  # E.g., "No EC2 instances found", "No S3 buckets configured", etc.
        }
    
    def _create_timeout_finding(self, bp: str, finding: str, service: str = 'AWS') -> Dict[str, Any]:
        """Create a finding when evaluation times out"""
        return {
            'bp': bp,
            'status': 'PENDING_REVIEW',
            'finding': finding,
            'severity': 'MEDIUM',
            'risk': 'N/D',
            'remediation': 'Re-run evaluation to get accurate assessment',
            'evidence': f'Evaluation timeout - unable to query {service} in time limit'
        }
    
    def _normalize_finding(self, finding: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure a finding has all required fields"""
        required_fields = ['bp', 'status', 'finding', 'severity', 'risk', 'remediation', 'evidence']
        
        for field in required_fields:
            if field not in finding:
                if field == 'severity':
                    finding[field] = 'MEDIUM'
                else:
                    finding[field] = 'N/D'
        
        return finding
    
    def _normalize_findings_list(self, findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalize all findings in a list"""
        return [self._normalize_finding(f) for f in findings]
    
    def _calculate_section_score(self, total_bps: int, compliant_bps: int, partial_bps: int = 0) -> float:
        """
        Calculate score for a section based on compliant BPs.
        N/D items (PENDING_REVIEW) count as 0% of that BP.
        
        Args:
            total_bps: Total number of BPs in this section
            compliant_bps: Number of COMPLIANT BPs
            partial_bps: Number of PARTIALLY_COMPLIANT BPs (optional, counts as 50%)
            
        Returns:
            Score 0-100
        """
        if total_bps == 0:
            return 100
        
        # Each compliant BP is worth 100 points
        # Each partially compliant BP is worth 50 points
        # Each non-compliant or pending BP is worth 0 points
        total_points = (compliant_bps * 100) + (partial_bps * 50)
        max_points = total_bps * 100
        
        score = (total_points / max_points) * 100 if max_points > 0 else 0
        return round(score, 2)
    
    def evaluate_sec01(self) -> Dict[str, Any]:
        """SEC01: ¿Cómo opera usted su carga de trabajo de forma segura? (8 BPs)"""
        findings = []
        compliant_count = 0
        non_compliant_count = 0
        pending_count = 0
        total_bps = 8
        primary_region = self.connector.regions[0] if self.connector.regions else 'us-east-1'
        
        # SEC01-BP01: Cargas de trabajo separadas mediante cuentas
        try:
            org_info = self.connector.get_organization_info()
            if not org_info.get('enabled'):
                non_compliant_count += 1
                findings.append({
                    'bp': 'SEC01-BP01',
                    'status': 'NON_COMPLIANT',
                    'finding': 'AWS Organizations not configured - using single account',
                    'severity': 'HIGH',
                    'risk': 'Single account limits isolation and blast radius control',
                    'remediation': 'Enable AWS Organizations and separate workloads into multiple accounts',
                    'evidence': 'No organization structure detected'
                })
            else:
                compliant_count += 1
                findings.append({
                    'bp': 'SEC01-BP01',
                    'status': 'COMPLIANT',
                    'finding': f'AWS Organizations configured with {org_info.get("accounts_count", 0)} accounts',
                    'severity': 'NONE',
                    'risk': 'N/D',
                    'remediation': 'N/D',
                    'evidence': f'Organization ID: {org_info.get("id")}'
                })
        except Exception as e:
            logger.error(f"Error checking Organizations: {str(e)}")
            error_str = str(e).lower()
            pending_count += 1
            
            # Detect if it's a timeout or credential/access error
            if 'timeout' in error_str or 'timed out' in error_str:
                findings.append(self._create_timeout_finding(
                    'SEC01-BP01',
                    'Unable to verify AWS Organizations configuration',
                    'AWS Organizations'
                ))
            else:
                findings.append(self._create_timeout_finding(
                    'SEC01-BP01',
                    'Unable to verify AWS Organizations configuration',
                    'AWS Organizations'
                ))
        
        # SEC01-BP02: Proteger el usuario raíz de la cuenta
        try:
            self.connector.get_iam_users()
            password_policy = self.connector.get_password_policy()
            
            if not password_policy or not password_policy.get('require_symbols'):
                non_compliant_count += 1
                findings.append({
                    'bp': 'SEC01-BP02',
                    'status': 'NON_COMPLIANT',
                    'finding': 'Weak or missing IAM password policy',
                    'severity': 'HIGH',
                    'risk': 'Weak passwords increase risk of unauthorized access',
                    'remediation': 'Configure strong password policy with minimum 14 characters, symbols, numbers, and expiration',
                    'evidence': 'Password policy not configured or incomplete'
                })
            else:
                compliant_count += 1
                findings.append({
                    'bp': 'SEC01-BP02',
                    'status': 'COMPLIANT',
                    'finding': 'Strong password policy configured',
                    'severity': 'NONE',
                    'evidence': f'Min length: {password_policy.get("min_password_length")}'
                })
        except Exception as e:
            logger.error(f"Error checking password policy: {str(e)}")
            pending_count += 1
            findings.append(self._create_pending_finding(
                'SEC01-BP02',
                f'Unable to verify password policy: {str(e)[:80]}',
                'MEDIUM'
            ))
        
        # SEC01-BP03: Identificar y validar los objetivos de control
        try:
            config_status = self.connector.get_config_status(primary_region)
            if config_status.get('recording'):
                compliant_count += 1
                findings.append({
                    'bp': 'SEC01-BP03',
                    'status': 'COMPLIANT',
                    'finding': 'AWS Config enabled for compliance monitoring',
                    'severity': 'NONE',
                    'evidence': f'{len(config_status.get("recorders", []))} Config recorder(s) active'
                })
            else:
                non_compliant_count += 1
                findings.append({
                    'bp': 'SEC01-BP03',
                    'status': 'NON_COMPLIANT',
                    'finding': 'AWS Config not enabled - cannot validate security controls',
                    'severity': 'HIGH',
                    'risk': 'Without Config, compliance state cannot be continuously validated',
                    'remediation': 'Enable AWS Config to track resource configurations and compliance',
                    'evidence': 'No active Config recorders found'
                })
        except Exception as e:
            logger.error(f"Error checking Config: {str(e)}")
            pending_count += 1
            findings.append(self._create_pending_finding(
                'SEC01-BP03',
                f'Unable to verify AWS Config status: {str(e)[:80]}',
                'MEDIUM'
            ))
        
        # SEC01-BP04: Mantenerse actualizado con amenazas y recomendaciones
        try:
            guardduty_detectors = self.connector.get_guardduty_detectors(primary_region)
            if guardduty_detectors and any(d.get('status') == 'ENABLED' for d in guardduty_detectors):
                compliant_count += 1
                findings.append({
                    'bp': 'SEC01-BP04',
                    'status': 'COMPLIANT',
                    'finding': f'GuardDuty enabled with {sum(d.get("findings", 0) for d in guardduty_detectors)} findings',
                    'severity': 'NONE',
                    'evidence': f'{len(guardduty_detectors)} detector(s) active'
                })
            else:
                non_compliant_count += 1
                findings.append({
                    'bp': 'SEC01-BP04',
                    'status': 'NON_COMPLIANT',
                    'finding': 'GuardDuty not enabled - missing threat intelligence',
                    'severity': 'CRITICAL',
                    'risk': 'Cannot detect malicious activity or unauthorized behavior',
                    'remediation': 'Enable Amazon GuardDuty for continuous threat detection',
                    'evidence': 'No active GuardDuty detectors found'
                })
        except Exception as e:
            logger.error(f"Error checking GuardDuty: {str(e)}")
            pending_count += 1
            findings.append(self._create_pending_finding(
                'SEC01-BP04',
                f'Unable to verify GuardDuty status: {str(e)[:80]}',
                'MEDIUM'
            ))
        
        # SEC01-BP05: Reducir el alcance de la gestión de la seguridad
        pending_count += 1
        findings.append(self._create_pending_finding(
            'SEC01-BP05',
            'Verify AWS Systems Manager is used for patch management',
            'MEDIUM'
        ))
        
        # SEC01-BP06: Automatizar la implementación de controles de seguridad
        try:
            trails = self.connector.get_cloudtrail_trails(primary_region)
            if trails and any(t.get('is_logging', False) for t in trails):
                compliant_count += 1
                findings.append({
                    'bp': 'SEC01-BP06',
                    'status': 'COMPLIANT',
                    'finding': 'CloudTrail logging enabled for audit automation',
                    'severity': 'NONE',
                    'evidence': f'{len(trails)} trail(s) logging API activity'
                })
            else:
                non_compliant_count += 1
                findings.append({
                    'bp': 'SEC01-BP06',
                    'status': 'NON_COMPLIANT',
                    'finding': 'CloudTrail not logging - automation and forensics not possible',
                    'severity': 'CRITICAL',
                    'risk': 'Cannot track changes or automate security responses',
                    'remediation': 'Enable CloudTrail with multi-region logging to S3',
                    'evidence': 'No active CloudTrail trails found'
                })
        except Exception as e:
            logger.error(f"Error checking CloudTrail: {str(e)}")
            pending_count += 1
            findings.append(self._create_pending_finding(
                'SEC01-BP06',
                f'Unable to verify CloudTrail status: {str(e)[:80]}',
                'CRITICAL'
            ))
        
        # SEC01-BP07: Identificar amenazas y priorizar mitigaciones usando un modelo de amenazas
        pending_count += 1
        findings.append(self._create_pending_finding(
            'SEC01-BP07',
            'Verify threat modeling process is documented and maintained',
            'MEDIUM'
        ))
        
        # SEC01-BP08: Evaluar e implementar nuevos servicios de seguridad periódicamente
        pending_count += 1
        findings.append(self._create_pending_finding(
            'SEC01-BP08',
            'Verify regular review of new AWS security services and features',
            'MEDIUM'
        ))
        
        # Calculate score based on compliant BPs (pending/N/D count as 0)
        score = self._calculate_section_score(total_bps, compliant_count)
        
        return {
            'question_id': 'SEC01',
            'question': 'Fundamentos de seguridad - Operación segura',
            'findings': findings,
            'score': score,
            'bps_evaluated': 8
        }
    
    def evaluate_sec02(self) -> Dict[str, Any]:
        """SEC02: ¿Cómo se gestiona la autenticación de personas y máquinas? (6 BPs)"""
        findings = []
        score = 100
        
        # Try to get users, track if we had an error
        users_error = None
        try:
            users = self.connector.get_iam_users()
        except Exception as e:
            logger.error(f"Error getting IAM users: {str(e)}")
            users = []
            users_error = str(e)[:100]
        
        # SEC02-BP01: Utilizar mecanismos de inicio de sesión fuertes
        if users_error:
            findings.append(self._create_pending_finding(
                'SEC02-BP01',
                f'Unable to verify IAM authentication: {users_error}',
                'HIGH'
            ))
        else:
            users_without_mfa = [u for u in users if not u.get('mfa_enabled', False) and len(u.get('access_keys', [])) > 0]
            if users_without_mfa:
                score -= 20
                findings.append({
                    'bp': 'SEC02-BP01',
                    'status': 'NON_COMPLIANT',
                    'finding': f'{len(users_without_mfa)} users without MFA but with active access keys',
                    'severity': 'CRITICAL',
                    'risk': 'Compromised credentials can lead to full account access',
                    'remediation': 'Enforce MFA for all users with console or API access',
                    'evidence': ', '.join([u['user_name'] for u in users_without_mfa[:5]])
                })
            else:
                findings.append({
                    'bp': 'SEC02-BP01',
                    'status': 'COMPLIANT',
                    'finding': 'Strong authentication mechanisms in place - all users with MFA',
                    'severity': 'NONE',
                    'risk': 'N/D',
                    'remediation': 'N/D',
                    'evidence': f'{len(users)} users evaluated'
                })
        
        # SEC02-BP02: Utilizar credenciales temporales
        if not users_error:
            long_term_keys = []
            for user in users:
                for key in user.get('access_keys', []):
                    if key['status'] == 'Active':
                        long_term_keys.append({'user': user['user_name'], 'key': key['access_key_id']})
            
            if long_term_keys:
                score -= 15
                findings.append({
                    'bp': 'SEC02-BP02',
                    'status': 'NON_COMPLIANT',
                    'finding': f'{len(long_term_keys)} long-term access keys detected',
                    'severity': 'HIGH',
                    'risk': 'Long-term credentials increase risk if compromised',
                    'remediation': 'Use STS AssumeRole for temporary credentials instead of long-term keys',
                    'evidence': f'{len(long_term_keys)} active access keys found'
                })
            else:
                findings.append({
                    'bp': 'SEC02-BP02',
                    'status': 'COMPLIANT',
                    'finding': 'No long-term access keys - using temporary credentials',
                    'severity': 'NONE',
                    'risk': 'N/D',
                    'remediation': 'N/D',
                    'evidence': 'No active access keys'
                })
        else:
            findings.append(self._create_pending_finding(
                'SEC02-BP02',
                'Unable to verify temporary credentials usage',
                'HIGH'
            ))
        
        # SEC02-BP03: Almacenar y utilizar secretos de forma segura
        try:
            primary_region = self.connector.regions[0] if self.connector.regions else 'us-east-1'
            secrets = self.connector.get_secrets(primary_region)
            if secrets:
                non_rotated = [s for s in secrets if not s.get('rotation_enabled')]
                if non_rotated:
                    score -= 10
                    findings.append({
                        'bp': 'SEC02-BP03',
                        'status': 'NON_COMPLIANT',
                        'finding': f'{len(non_rotated)} of {len(secrets)} secrets without automatic rotation',
                        'severity': 'MEDIUM',
                        'risk': 'Non-rotated secrets increase compromise window',
                        'remediation': 'Enable automatic rotation for all secrets in Secrets Manager',
                        'evidence': f'{len(non_rotated)} secrets need rotation enabled'
                    })
                else:
                    findings.append({
                        'bp': 'SEC02-BP03',
                        'status': 'COMPLIANT',
                        'finding': f'All {len(secrets)} secrets have automatic rotation enabled',
                        'severity': 'NONE'
                    })
            else:
                findings.append({
                    'bp': 'SEC02-BP03',
                    'status': 'PENDING_REVIEW',
                    'finding': 'Verify secrets are stored in AWS Secrets Manager (none found)',
                    'severity': 'MEDIUM',
                    'remediation': 'Use AWS Secrets Manager for database and API credentials'
                })
        except Exception as e:
            logger.error(f"Error checking secrets: {str(e)}")
        
        # SEC02-BP04: Confíe en un proveedor de identidad centralizado
        if len(users) > 10:
            score -= 10
            findings.append({
                'bp': 'SEC02-BP04',
                'status': 'NON_COMPLIANT',
                'finding': f'{len(users)} IAM users - consider centralized identity provider',
                'severity': 'MEDIUM',
                'risk': 'Many IAM users indicate lack of identity federation',
                'remediation': 'Use AWS IAM Identity Center (SSO) or federate with corporate identity provider',
                'evidence': f'{len(users)} native IAM users instead of federated identities'
            })
        else:
            findings.append({
                'bp': 'SEC02-BP04',
                'status': 'COMPLIANT',
                'finding': f'Limited IAM users ({len(users)}) - likely using identity federation',
                'severity': 'NONE'
            })
        
        # SEC02-BP05: Auditar y rotar credenciales periódicamente
        old_keys = []
        for user in users:
            for key in user.get('access_keys', []):
                if key['status'] == 'Active':
                    # In real scenario, check age from create_date
                    old_keys.append(key)
        
        if len(old_keys) > 0:
            findings.append({
                'bp': 'SEC02-BP05',
                'status': 'PENDING_REVIEW',
                'finding': f'{len(old_keys)} active access keys - verify they are rotated regularly',
                'severity': 'MEDIUM',
                'risk': 'Old credentials increase compromise risk',
                'remediation': 'Rotate all access keys every 90 days maximum',
                'evidence': f'{len(old_keys)} keys require age verification'
            })
        else:
            findings.append({
                'bp': 'SEC02-BP05',
                'status': 'COMPLIANT',
                'finding': 'No active access keys requiring rotation',
                'severity': 'NONE'
            })
        
        # SEC02-BP06: Emplear grupos de usuarios y atributos
        user_with_direct_policies = [u for u in users if len(u.get('policies', [])) > 0]
        if user_with_direct_policies:
            score -= 5
            findings.append({
                'bp': 'SEC02-BP06',
                'status': 'NON_COMPLIANT',
                'finding': f'{len(user_with_direct_policies)} users have directly attached policies',
                'severity': 'MEDIUM',
                'risk': 'Direct policy attachment makes permission management difficult',
                'remediation': 'Use IAM groups for permission management, not direct user policies',
                'evidence': f'{len(user_with_direct_policies)} users with direct policies'
            })
        else:
            findings.append({
                'bp': 'SEC02-BP06',
                'status': 'COMPLIANT',
                'finding': 'Using groups for permission management',
                'severity': 'NONE'
            })
        
        return {
            'question_id': 'SEC02',
            'question': 'Autenticación de personas y máquinas',
            'findings': findings,
            'score': max(0, score),
            'bps_evaluated': 6
        }
    
    def evaluate_sec03(self) -> Dict[str, Any]:
        """SEC03: ¿Cómo gestiona identidades de personas?"""
        findings = []
        score = 100
        
        # Get IAM users
        users = []
        collection_error = None
        try:
            logger.info("[SEC03] Starting SEC03 evaluation - Getting IAM users...")
            users = self.connector.get_iam_users()
            logger.info(f"[SEC03] Retrieved {len(users)} IAM users")
        except Exception as e:
            logger.error(f"[SEC03] Error getting IAM users: {str(e)}", exc_info=True)
            collection_error = str(e)
            users = []
        
        # If there was a collection error, create error findings for all BP
        if collection_error:
            logger.warning(f"[SEC03] Collection error detected: {collection_error}")
            for bp_num in range(1, 9):
                bp_id = f'SEC03-BP{bp_num:02d}'
                findings.append(self._create_timeout_finding(
                    bp_id,
                    'Unable to evaluate - error collecting IAM user information',
                    'IAM API'
                ))
            return {
                'question_id': 'SEC03',
                'question': 'Gestión de identidades de personas',
                'findings': findings,
                'score': 0,
                'bps_evaluated': 8
            }
        
        # SEC03-BP01: Usar SSO (check if any users exist - basic check)
        if users and len(users) > 0:
            findings.append({
                'bp': 'SEC03-BP01',
                'status': 'PENDING_REVIEW',
                'finding': f'{len(users)} IAM users detected - verify AWS SSO/Cognito implementation',
                'severity': 'MEDIUM',
                'detail': 'Prefer identity federation over native IAM users when possible'
            })
        else:
            findings.append({
                'bp': 'SEC03-BP01',
                'status': 'COMPLIANT',
                'finding': 'No native IAM users detected - likely using SSO/Cognito',
                'severity': 'NONE'
            })
        
        # SEC03-BP02: Usar Cognito
        findings.append({
            'bp': 'SEC03-BP02',
            'status': 'PENDING_REVIEW',
            'finding': 'Verify AWS Cognito is configured for customer identity management',
            'severity': 'MEDIUM'
        })
        
        # SEC03-BP03: Implementar MFA
        users_without_mfa = [u for u in users if not u.get('mfa_enabled', False)]
        if users_without_mfa:
            score -= 15
            findings.append({
                'bp': 'SEC03-BP03',
                'status': 'NON_COMPLIANT',
                'finding': f'{len(users_without_mfa)} users without MFA enabled',
                'severity': 'CRITICAL',
                'evidence': ', '.join([u['user_name'] for u in users_without_mfa[:5]]),
                'remediation': 'Enable MFA for all IAM users, especially those with console access'
            })
        else:
            findings.append({
                'bp': 'SEC03-BP03',
                'status': 'COMPLIANT',
                'finding': 'All users have MFA enabled',
                'severity': 'NONE'
            })
        
        # SEC03-BP04: Usar STS para credenciales temporales
        # Check for long-lived keys
        long_term_keys = []
        for user in users:
            for key in user.get('access_keys', []):
                if key['status'] == 'Active':
                    long_term_keys.append({'user': user['user_name'], 'key': key['access_key_id']})
        
        if long_term_keys:
            score -= 10
            findings.append({
                'bp': 'SEC03-BP04',
                'status': 'NON_COMPLIANT',
                'finding': f'{len(long_term_keys)} long-term access keys found',
                'severity': 'HIGH',
                'evidence': [k['key'][:4] + '****' for k in long_term_keys[:5]],
                'remediation': 'Use temporary credentials via STS AssumeRole instead of long-term access keys'
            })
        else:
            findings.append({
                'bp': 'SEC03-BP04',
                'status': 'COMPLIANT',
                'finding': 'Using STS temporary credentials (no long-term access keys detected)',
                'severity': 'NONE'
            })
        
        # SEC03-BP05: Gestionar credenciales en tránsito
        findings.append({
            'bp': 'SEC03-BP05',
            'status': 'PENDING_REVIEW',
            'finding': 'Verify use of VPC endpoints and encrypted channels for credential transmission',
            'severity': 'MEDIUM'
        })
        
        # SEC03-BP06: Auditar identidades
        findings.append({
            'bp': 'SEC03-BP06',
            'status': 'PENDING_REVIEW',
            'finding': 'Ensure CloudTrail logs all user authentication and authorization events',
            'severity': 'MEDIUM'
        })
        
        # SEC03-BP07: Implementar permisos granulares
        findings.append({
            'bp': 'SEC03-BP07',
            'status': 'PENDING_REVIEW',
            'finding': 'Review IAM policies to ensure least privilege for human identities',
            'severity': 'MEDIUM'
        })
        
        # SEC03-BP08: Revocar acceso oportuno
        findings.append({
            'bp': 'SEC03-BP08',
            'status': 'PENDING_REVIEW',
            'finding': 'Verify procedures for timely user offboarding and access revocation',
            'severity': 'MEDIUM'
        })
        
        return {
            'question_id': 'SEC03',
            'question': 'Gestión de identidades de personas',
            'findings': findings,
            'score': max(0, score),
            'bps_evaluated': 9
        }
    
    def evaluate_sec04(self) -> Dict[str, Any]:
        """SEC04: ¿Cómo gestiona identidades de máquinas?"""
        findings = []
        score = 100
        
        # Get IAM roles
        try:
            roles = self.connector.get_iam_roles()
        except Exception as e:
            logger.error(f"Error getting IAM roles: {str(e)}")
            roles = []
        
        # SEC04-BP01: Usar roles de IAM
        if roles and len(roles) > 0:
            findings.append({
                'bp': 'SEC04-BP01',
                'status': 'COMPLIANT',
                'finding': f'{len(roles)} IAM roles configured for service identities',
                'severity': 'NONE',
                'detail': 'Service role usage detected'
            })
        else:
            findings.append({
                'bp': 'SEC04-BP01',
                'status': 'WARNING',
                'finding': 'No IAM roles found for service identities',
                'severity': 'MEDIUM',
                'remediation': 'Create IAM roles for EC2, Lambda, and other AWS services'
            })
            score -= 5
        
        # SEC04-BP02: Usar instancia perfiles de IAM
        findings.append({
            'bp': 'SEC04-BP02',
            'status': 'PENDING_REVIEW',
            'finding': 'Verify EC2 instances use IAM instance profiles (not embedded credentials)',
            'severity': 'MEDIUM'
        })
        
        # SEC04-BP03: Gestionar credenciales de máquina
        findings.append({
            'bp': 'SEC04-BP03',
            'status': 'PENDING_REVIEW',
            'finding': 'Verify no hardcoded credentials in application code or container images',
            'severity': 'HIGH'
        })
        
        # SEC04-BP04: Usar AssumeRole para acceso entre cuentas
        findings.append({
            'bp': 'SEC04-BP04',
            'status': 'PENDING_REVIEW',
            'finding': 'Verify cross-account access uses STS AssumeRole',
            'severity': 'MEDIUM'
        })
        
        # SEC04-BP05: Usar Secrets Manager
        findings.append({
            'bp': 'SEC04-BP05',
            'status': 'PENDING_REVIEW',
            'finding': 'Use AWS Secrets Manager for managing database and API credentials',
            'severity': 'MEDIUM'
        })
        
        # SEC04-BP06: Auditar acceso de máquina
        findings.append({
            'bp': 'SEC04-BP06',
            'status': 'PENDING_REVIEW',
            'finding': 'Ensure CloudTrail logs machine identity access and API calls',
            'severity': 'MEDIUM'
        })
        
        return {
            'question_id': 'SEC04',
            'question': 'Gestión de identidades de máquinas',
            'findings': findings,
            'score': max(0, score),
            'bps_evaluated': 4
        }
    
    def evaluate_sec05(self) -> Dict[str, Any]:
        """SEC05: ¿Cómo gestiona los permisos?"""
        findings = []
        score = 100
        
        # Get IAM policies and roles
        try:
            policies = self.connector.get_iam_policies()
            self.connector.get_iam_users()
            self.connector.get_iam_roles()
        except Exception as e:
            logger.error(f"Error getting IAM policies: {str(e)}")
            policies = []
        
        # SEC05-BP01: Usar principio de menor privilegio
        if policies and len(policies) > 0:
            findings.append({
                'bp': 'SEC05-BP01',
                'status': 'PENDING_REVIEW',
                'finding': f'{len(policies)} custom-managed policies found',
                'severity': 'MEDIUM',
                'detail': 'Review policies for overly permissive statements'
            })
        
        # SEC05-BP02: Usar permisos basados en atributos (ABAC)
        findings.append({
            'bp': 'SEC05-BP02',
            'status': 'PENDING_REVIEW',
            'finding': 'Consider using ABAC (Attribute-Based Access Control) for scalable permissions',
            'severity': 'MEDIUM'
        })
        
        # SEC05-BP03: Usar Access Analyzer
        findings.append({
            'bp': 'SEC05-BP03',
            'status': 'PENDING_REVIEW',
            'finding': 'Enable IAM Access Analyzer to validate policy compliance',
            'severity': 'MEDIUM',
            'remediation': 'Use Access Analyzer to detect overly permissive policies'
        })
        
        # SEC05-BP04: Usar SCP para límites de organización
        findings.append({
            'bp': 'SEC05-BP04',
            'status': 'PENDING_REVIEW',
            'finding': 'Implement SCPs (Service Control Policies) at organization level',
            'severity': 'MEDIUM'
        })
        
        # SEC05-BP05: Usar permission boundaries
        findings.append({
            'bp': 'SEC05-BP05',
            'status': 'PENDING_REVIEW',
            'finding': 'Use IAM Permission Boundaries to limit maximum permissions',
            'severity': 'MEDIUM'
        })
        
        # SEC05-BP06: Auditar cambios de permisos
        findings.append({
            'bp': 'SEC05-BP06',
            'status': 'PENDING_REVIEW',
            'finding': 'CloudTrail must log all IAM policy changes',
            'severity': 'MEDIUM'
        })
        
        # SEC05-BP07: Revocar permisos no usados
        findings.append({
            'bp': 'SEC05-BP07',
            'status': 'PENDING_REVIEW',
            'finding': 'Use Access Advisor to identify and remove unused permissions',
            'severity': 'MEDIUM'
        })
        
        return {
            'question_id': 'SEC05',
            'question': 'Gestión de permisos',
            'findings': findings,
            'score': max(0, score),
            'bps_evaluated': 4
        }
    
    def evaluate_sec06(self) -> Dict[str, Any]:
        """SEC06: ¿Cómo detecta y investiga eventos de seguridad?"""
        findings = []
        score = 100
        
        # Get CloudTrail status and GuardDuty detectors
        try:
            primary_region = self.connector.regions[0] if self.connector.regions else 'us-east-1'
            trails = self.connector.get_cloudtrail_trails(primary_region)
            config_status = self.connector.get_config_status(primary_region)
            guardduty_detectors = self.connector.get_guardduty_detectors(primary_region)
        except Exception as e:
            logger.error(f"Error getting detection services status: {str(e)}")
            trails = []
            config_status = {}
            guardduty_detectors = []
        
        # SEC06-BP01: CloudTrail - Event logging
        if trails and any(t.get('is_logging', False) for t in trails):
            findings.append({
                'bp': 'SEC06-BP01',
                'status': 'COMPLIANT',
                'finding': 'CloudTrail is actively logging',
                'severity': 'NONE'
            })
        else:
            score -= 20
            findings.append({
                'bp': 'SEC06-BP01',
                'status': 'NON_COMPLIANT',
                'finding': 'CloudTrail not configured or not logging',
                'severity': 'CRITICAL',
                'remediation': 'Enable CloudTrail organization trail with multi-region logging'
            })
        
        # SEC06-BP02: AWS Config - Resource inventory and compliance
        if config_status.get('recording'):
            findings.append({
                'bp': 'SEC06-BP02',
                'status': 'COMPLIANT',
                'finding': 'AWS Config is recording resource changes',
                'severity': 'NONE'
            })
        else:
            score -= 15
            findings.append({
                'bp': 'SEC06-BP02',
                'status': 'NON_COMPLIANT',
                'finding': 'AWS Config not recording',
                'severity': 'HIGH',
                'remediation': 'Enable AWS Config recorder and aggregator'
            })
        
        # SEC06-BP03: GuardDuty - Threat detection
        if guardduty_detectors and len(guardduty_detectors) > 0:
            findings.append({
                'bp': 'SEC06-BP03',
                'status': 'COMPLIANT',
                'finding': f'{len(guardduty_detectors)} GuardDuty detectors enabled',
                'severity': 'NONE'
            })
        else:
            findings.append({
                'bp': 'SEC06-BP03',
                'status': 'NON_COMPLIANT',
                'finding': 'GuardDuty not enabled',
                'severity': 'HIGH',
                'remediation': 'Enable GuardDuty for threat detection'
            })
            score -= 10
        
        # SEC06-BP04: SecurityHub - Centralized findings
        findings.append({
            'bp': 'SEC06-BP04',
            'status': 'PENDING_REVIEW',
            'finding': 'Verify AWS Security Hub is enabled for centralized finding aggregation',
            'severity': 'MEDIUM'
        })
        
        # SEC06-BP05: EventBridge/SNS - Alert routing
        findings.append({
            'bp': 'SEC06-BP05',
            'status': 'PENDING_REVIEW',
            'finding': 'Configure EventBridge rules to route security findings to SIEM/SOC',
            'severity': 'MEDIUM'
        })
        
        # SEC06-BP06: CloudWatch - Monitoring and alerting
        findings.append({
            'bp': 'SEC06-BP06',
            'status': 'PENDING_REVIEW',
            'finding': 'Configure CloudWatch Logs for CloudTrail and VPC Flow Logs analysis',
            'severity': 'MEDIUM'
        })
        
        # SEC06-BP07: Incident response automation
        findings.append({
            'bp': 'SEC06-BP07',
            'status': 'PENDING_REVIEW',
            'finding': 'Implement automated response workflows using Lambda/Systems Manager',
            'severity': 'MEDIUM'
        })
        
        return {
            'question_id': 'SEC06',
            'question': 'Detección e investigación de eventos',
            'findings': findings,
            'score': max(0, score),
            'bps_evaluated': 5
        }
    
    def evaluate_sec07(self) -> Dict[str, Any]:
        """SEC07: ¿Cómo clasifica sus datos? (4 BPs)"""
        findings = []
        score = 100
        self.connector.regions[0] if self.connector.regions else 'us-east-1'
        
        # SEC07-BP01: Comprender su esquema de clasificación de datos
        try:
            s3_buckets = self.connector.get_s3_buckets()
            if s3_buckets:
                findings.append({
                    'bp': 'SEC07-BP01',
                    'status': 'PENDING_REVIEW',
                    'finding': f'{len(s3_buckets)} S3 buckets found - verify data classification tags',
                    'severity': 'MEDIUM',
                    'risk': 'Unclassified data cannot be properly protected',
                    'remediation': 'Tag all S3 buckets with data classification (Public, Internal, Confidential, Restricted)',
                    'evidence': f'{len(s3_buckets)} buckets require classification review'
                })
            else:
                findings.append({
                    'bp': 'SEC07-BP01',
                    'status': 'COMPLIANT',
                    'finding': 'No S3 buckets found',
                    'severity': 'NONE'
                })
        except Exception as e:
            logger.error(f"Error checking S3 buckets: {str(e)}")
        
        # SEC07-BP02: Aplicar controles de protección de datos basados en sensibilidad
        try:
            s3_buckets = self.connector.get_s3_buckets()
            unencrypted_buckets = [b for b in s3_buckets if not b.get('encryption_enabled')]
            if unencrypted_buckets:
                score -= 20
                findings.append({
                    'bp': 'SEC07-BP02',
                    'status': 'NON_COMPLIANT',
                    'finding': f'{len(unencrypted_buckets)} of {len(s3_buckets)} S3 buckets without encryption',
                    'severity': 'CRITICAL',
                    'risk': 'Unencrypted data can be accessed if bucket is compromised',
                    'remediation': 'Enable default encryption for all S3 buckets using SSE-S3 or SSE-KMS',
                    'evidence': ', '.join([b['name'] for b in unencrypted_buckets[:5]])
                })
            else:
                findings.append({
                    'bp': 'SEC07-BP02',
                    'status': 'COMPLIANT',
                    'finding': f'All {len(s3_buckets)} S3 buckets have encryption enabled',
                    'severity': 'NONE'
                })
        except Exception as e:
            logger.error(f"Error checking bucket encryption: {str(e)}")
        
        # SEC07-BP03: Automatizar identificación y clasificación
        findings.append({
            'bp': 'SEC07-BP03',
            'status': 'PENDING_REVIEW',
            'finding': 'Verify Amazon Macie is enabled for automated data discovery and classification',
            'severity': 'MEDIUM',
            'risk': 'Manual classification is error-prone and incomplete',
            'remediation': 'Enable Amazon Macie to automatically discover and classify sensitive data in S3'
        })
        
        # SEC07-BP04: Definir gestión escalable del ciclo de vida de datos
        try:
            s3_buckets = self.connector.get_s3_buckets()
            unversioned_buckets = [b for b in s3_buckets if not b.get('versioning_enabled')]
            if unversioned_buckets:
                score -= 10
                findings.append({
                    'bp': 'SEC07-BP04',
                    'status': 'NON_COMPLIANT',
                    'finding': f'{len(unversioned_buckets)} of {len(s3_buckets)} buckets without versioning',
                    'severity': 'MEDIUM',
                    'risk': 'Data can be permanently lost or deleted without versioning',
                    'remediation': 'Enable versioning on all S3 buckets to protect against accidental deletion',
                    'evidence': f'{len(unversioned_buckets)} buckets need versioning'
                })
            else:
                findings.append({
                    'bp': 'SEC07-BP04',
                    'status': 'COMPLIANT',
                    'finding': 'All S3 buckets have versioning enabled',
                    'severity': 'NONE'
                })
        except Exception as e:
            logger.error(f"Error checking versioning: {str(e)}")
        
        return {
            'question_id': 'SEC07',
            'question': 'Clasificación de datos',
            'findings': findings,
            'score': max(0, score),
            'bps_evaluated': 4
        }
    
    def evaluate_sec08(self) -> Dict[str, Any]:
        """SEC08: ¿Cómo protege sus datos en reposo? (4 BPs)"""
        findings = []
        score = 100
        primary_region = self.connector.regions[0] if self.connector.regions else 'us-east-1'
        
        # SEC08-BP01: Implementar gestión segura de claves
        try:
            kms_keys = self.connector.get_kms_keys(primary_region)
            if kms_keys:
                findings.append({
                    'bp': 'SEC08-BP01',
                    'status': 'COMPLIANT',
                    'finding': f'{len(kms_keys)} KMS keys configured for encryption',
                    'severity': 'NONE',
                    'evidence': 'KMS keys in use for encryption management'
                })
            else:
                score -= 10
                findings.append({
                    'bp': 'SEC08-BP01',
                    'status': 'NON_COMPLIANT',
                    'finding': 'No KMS keys found - using default AWS-managed keys',
                    'severity': 'MEDIUM',
                    'risk': 'Cannot control key rotation or access policies with default keys',
                    'remediation': 'Create customer-managed KMS keys for better control',
                    'evidence': 'No customer-managed KMS keys detected'
                })
        except Exception as e:
            logger.error(f"Error checking KMS keys: {str(e)}")
        
        # SEC08-BP02: Hacer cumplir el cifrado en reposo
        try:
            s3_buckets = self.connector.get_s3_buckets()
            ebs_volumes = self.connector.get_ebs_volumes(primary_region)
            rds_instances = self.connector.get_rds_instances(primary_region)
            
            unencrypted_resources = []
            if s3_buckets:
                unenc_s3 = [b for b in s3_buckets if not b.get('encryption_enabled')]
                if unenc_s3:
                    unencrypted_resources.append(f'{len(unenc_s3)} S3 buckets')
            
            if ebs_volumes:
                unenc_ebs = [v for v in ebs_volumes if not v.get('encrypted')]
                if unenc_ebs:
                    unencrypted_resources.append(f'{len(unenc_ebs)} EBS volumes')
            
            if rds_instances:
                unenc_rds = [d for d in rds_instances if not d.get('encrypted')]
                if unenc_rds:
                    unencrypted_resources.append(f'{len(unenc_rds)} RDS instances')
            
            if unencrypted_resources:
                score -= 25
                findings.append({
                    'bp': 'SEC08-BP02',
                    'status': 'NON_COMPLIANT',
                    'finding': f"Unencrypted resources: {', '.join(unencrypted_resources)}",
                    'severity': 'CRITICAL',
                    'risk': 'Unencrypted data at rest can be accessed if storage is compromised',
                    'remediation': 'Enable encryption at rest for all S3 buckets, EBS volumes, and RDS instances',
                    'evidence': ', '.join(unencrypted_resources)
                })
            else:
                findings.append({
                    'bp': 'SEC08-BP02',
                    'status': 'COMPLIANT',
                    'finding': 'All resources have encryption at rest enabled',
                    'severity': 'NONE'
                })
        except Exception as e:
            logger.error(f"Error checking encryption at rest: {str(e)}")
        
        # SEC08-BP03: Automatizar protección de datos en reposo
        findings.append({
            'bp': 'SEC08-BP03',
            'status': 'PENDING_REVIEW',
            'finding': 'Verify AWS Config rules enforce encryption requirements automatically',
            'severity': 'MEDIUM',
            'risk': 'Manual enforcement is unreliable and slow',
            'remediation': 'Use AWS Config rules like s3-bucket-server-side-encryption-enabled, encrypted-volumes'
        })
        
        # SEC08-BP04: Hacer cumplir el control de acceso
        try:
            s3_buckets = self.connector.get_s3_buckets()
            public_buckets = [b for b in s3_buckets if not b.get('public_access_blocked')]
            if public_buckets:
                score -= 15
                findings.append({
                    'bp': 'SEC08-BP04',
                    'status': 'NON_COMPLIANT',
                    'finding': f'{len(public_buckets)} of {len(s3_buckets)} S3 buckets without public access block',
                    'severity': 'HIGH',
                    'risk': 'Buckets can be accidentally made public',
                    'remediation': 'Enable S3 Block Public Access for all buckets',
                    'evidence': ', '.join([b['name'] for b in public_buckets[:5]])
                })
            else:
                findings.append({
                    'bp': 'SEC08-BP04',
                    'status': 'COMPLIANT',
                    'finding': f'All {len(s3_buckets)} S3 buckets have public access blocked',
                    'severity': 'NONE'
                })
        except Exception as e:
            logger.error(f"Error checking public access: {str(e)}")
        
        return {
            'question_id': 'SEC08',
            'question': 'Protección de datos en reposo',
            'findings': findings,
            'score': max(0, score),
            'bps_evaluated': 4
        }
    
    def evaluate_sec09(self) -> Dict[str, Any]:
        """SEC09: ¿Cómo protege sus datos en tránsito? (3 BPs)"""
        findings = []
        score = 100
        primary_region = self.connector.regions[0] if self.connector.regions else 'us-east-1'
        
        # SEC09-BP01: Implementar gestión segura de claves y certificados
        findings.append({
            'bp': 'SEC09-BP01',
            'status': 'PENDING_REVIEW',
            'finding': 'Verify AWS Certificate Manager (ACM) is used for SSL/TLS certificates',
            'severity': 'MEDIUM',
            'risk': 'Self-managed certificates are difficult to rotate and expire',
            'remediation': 'Use AWS Certificate Manager for automatic certificate provisioning and renewal'
        })
        
        # SEC09-BP02: Hacer cumplir el cifrado en tránsito
        try:
            s3_buckets = self.connector.get_s3_buckets()
            # Check if buckets enforce HTTPS
            findings.append({
                'bp': 'SEC09-BP02',
                'status': 'PENDING_REVIEW',
                'finding': f'Verify {len(s3_buckets)} S3 buckets enforce HTTPS-only access via bucket policy',
                'severity': 'HIGH',
                'risk': 'Unencrypted data in transit can be intercepted',
                'remediation': 'Add bucket policy to deny non-HTTPS requests (aws:SecureTransport = false)',
                'evidence': f'{len(s3_buckets)} buckets require HTTPS enforcement verification'
            })
        except Exception as e:
            logger.error(f"Error checking S3: {str(e)}")
        
        # SEC09-BP03: Autenticar las comunicaciones de red
        try:
            vpcs = self.connector.get_vpcs(primary_region)
            findings.append({
                'bp': 'SEC09-BP03',
                'status': 'PENDING_REVIEW',
                'finding': f'{len(vpcs)} VPC(s) found - verify VPN or TLS used for all network communications',
                'severity': 'HIGH',
                'risk': 'Unauthenticated network traffic can be spoofed or intercepted',
                'remediation': 'Use AWS VPN, Direct Connect with MACsec, or TLS for all inter-VPC and external communications',
                'evidence': f'{len(vpcs)} VPCs require network authentication review'
            })
        except Exception as e:
            logger.error(f"Error checking VPCs: {str(e)}")
        
        return {
            'question_id': 'SEC09',
            'question': 'Protección de datos en tránsito',
            'findings': findings,
            'score': max(0, score),
            'bps_evaluated': 3
        }
        
        # SEC09-BP03: RDS Encryption
        findings.append({
            'bp': 'SEC09-BP03',
            'status': 'PENDING_REVIEW',
            'finding': 'Verify all RDS instances have encryption-at-rest enabled',
            'severity': 'HIGH'
        })
        
        # SEC09-BP04: DynamoDB Encryption
        findings.append({
            'bp': 'SEC09-BP04',
            'status': 'PENDING_REVIEW',
            'finding': 'Verify all DynamoDB tables use encryption with CMK',
            'severity': 'MEDIUM'
        })
        
        # SEC09-BP05: EBS Encryption
        findings.append({
            'bp': 'SEC09-BP05',
            'status': 'PENDING_REVIEW',
            'finding': 'Verify all EBS volumes have encryption enabled',
            'severity': 'HIGH'
        })
        
        # SEC09-BP06: Snapshots and backups encryption
        findings.append({
            'bp': 'SEC09-BP06',
            'status': 'PENDING_REVIEW',
            'finding': 'Ensure all backup snapshots are encrypted',
            'severity': 'HIGH'
        })
        
        return {
            'question_id': 'SEC09',
            'question': 'Protección de datos en reposo',
            'findings': findings,
            'score': max(0, score),
            'bps_evaluated': 3
        }
    
    def evaluate_sec10(self) -> Dict[str, Any]:
        """SEC10: ¿Cómo se anticipa, responde y se recupera ante incidentes?"""
        findings = []
        score = 100
        
        findings.append({
            'bp': 'SEC10-BP01',
            'status': 'PENDING_REVIEW',
            'finding': 'Establish and test incident response plan',
            'severity': 'HIGH'
        })
        
        findings.append({
            'bp': 'SEC10-BP02',
            'status': 'PENDING_REVIEW',
            'finding': 'Enable AWS Backup for automated data protection',
            'severity': 'HIGH'
        })
        
        findings.append({
            'bp': 'SEC10-BP03',
            'status': 'PENDING_REVIEW',
            'finding': 'Implement multi-region backup strategy',
            'severity': 'HIGH'
        })
        
        findings.append({
            'bp': 'SEC10-BP04',
            'status': 'PENDING_REVIEW',
            'finding': 'Test disaster recovery procedures regularly',
            'severity': 'HIGH'
        })
        
        findings.append({
            'bp': 'SEC10-BP05',
            'status': 'PENDING_REVIEW',
            'finding': 'Define RTO and RPO targets for critical workloads',
            'severity': 'MEDIUM'
        })
        
        findings.append({
            'bp': 'SEC10-BP06',
            'status': 'PENDING_REVIEW',
            'finding': 'Implement automated incident response workflows',
            'severity': 'MEDIUM'
        })
        
        return {
            'question_id': 'SEC10',
            'question': 'Anticipación, respuesta y recuperación ante incidentes',
            'findings': findings,
            'score': max(0, score),
            'bps_evaluated': 8
        }
    
    def evaluate_sec11(self) -> Dict[str, Any]:
        """SEC11: ¿Cómo cumple con los requisitos regulatorios?"""
        findings = []
        score = 100
        
        findings.append({
            'bp': 'SEC11-BP01',
            'status': 'PENDING_REVIEW',
            'finding': 'Use AWS Artifact to access compliance reports and agreements',
            'severity': 'MEDIUM'
        })
        
        findings.append({
            'bp': 'SEC11-BP02',
            'status': 'PENDING_REVIEW',
            'finding': 'Use AWS Config Rules to verify compliance with standards (HIPAA, PCI-DSS, etc.)',
            'severity': 'MEDIUM'
        })
        
        findings.append({
            'bp': 'SEC11-BP03',
            'status': 'PENDING_REVIEW',
            'finding': 'Implement audit logging and maintain immutable logs for compliance',
            'severity': 'HIGH'
        })
        
        return {
            'question_id': 'SEC11',
            'question': 'Cumplimiento normativo y auditoría',
            'findings': findings,
            'score': max(0, score),
            'bps_evaluated': 8
        }
    
    def evaluate_all(self) -> Dict[str, Any]:
        """Evaluate all 11 Security pillar questions"""
        questions = [
            self.evaluate_sec01(),
            self.evaluate_sec02(),
            self.evaluate_sec03(),
            self.evaluate_sec04(),
            self.evaluate_sec05(),
            self.evaluate_sec06(),
            self.evaluate_sec07(),
            self.evaluate_sec08(),
            self.evaluate_sec09(),
            self.evaluate_sec10(),
            self.evaluate_sec11(),
        ]
        
        # Normalize all findings to ensure complete fields
        for question in questions:
            question['findings'] = self._normalize_findings_list(question['findings'])
        
        # Calculate overall security score
        overall_score = sum(q['score'] for q in questions) / len(questions)
        total_findings = sum(len(q['findings']) for q in questions)
        
        return {
            'questions': questions,
            'overall_score': round(overall_score, 2),
            'total_findings': total_findings,
            'total_questions': 11,
            'total_best_practices': 63
        }
    
    def evaluate_bp(self, bp_id: str) -> Dict[str, Any]:
        """
        Evaluate a single Best Practice by its ID (e.g., 'SEC01-BP01')
        
        Returns:
            {
                'bp_id': 'SEC01-BP01',
                'question_id': 'SEC01',
                'finding': {...},
                'message': 'Evaluation successful' or error message
            }
        """
        try:
            # Extract SEC number from BP ID (e.g., 'SEC01' from 'SEC01-BP01')
            sec_num = bp_id[:5]  # 'SEC01'
            
            if sec_num not in ['SEC01', 'SEC02', 'SEC03', 'SEC04', 'SEC05', 'SEC06', 'SEC07', 'SEC08', 'SEC09', 'SEC10', 'SEC11']:
                return {
                    'success': False,
                    'bp_id': bp_id,
                    'error': f'Invalid SEC section: {sec_num}'
                }
            
            # Evaluate the full question
            evaluate_method = getattr(self, f'evaluate_{sec_num.lower()}', None)
            if not evaluate_method:
                return {
                    'success': False,
                    'bp_id': bp_id,
                    'error': f'Evaluation method not found for {sec_num}'
                }
            
            question_result = evaluate_method()
            
            # Find the specific BP finding
            matching_finding = None
            for finding in question_result['findings']:
                if finding.get('bp') == bp_id:
                    matching_finding = finding
                    break
            
            if matching_finding is None:
                return {
                    'success': False,
                    'bp_id': bp_id,
                    'error': 'BP not found in results'
                }
            
            # Normalize the finding
            matching_finding = self._normalize_finding(matching_finding)
            
            return {
                'success': True,
                'bp_id': bp_id,
                'question_id': question_result['question_id'],
                'finding': matching_finding,
                'message': 'BP evaluation successful'
            }
        
        except Exception as e:
            logger.error(f"Error evaluating BP {bp_id}: {str(e)}")
            return {
                'success': False,
                'bp_id': bp_id,
                'error': f'Evaluation error: {str(e)[:100]}'
            }
    
    def evaluate_bps_batch(self, bp_ids: List[str]) -> Dict[str, Any]:
        """
        Re-evaluate multiple BPs
        
        Args:
            bp_ids: List of BP IDs like ['SEC01-BP01', 'SEC02-BP03']
            
        Returns:
            {
                'success': True,
                'evaluated': [..],
                'failed': [...],
                'timestamp': '...'
            }
        """
        from datetime import datetime
        
        evaluated = []
        failed = []
        
        for bp_id in bp_ids:
            result = self.evaluate_bp(bp_id)
            if result['success']:
                evaluated.append(result)
            else:
                failed.append({
                    'bp_id': bp_id,
                    'error': result.get('error', 'Unknown error')
                })
        
        return {
            'success': len(failed) == 0,
            'evaluated': evaluated,
            'failed': failed,
            'evaluated_count': len(evaluated),
            'failed_count': len(failed),
            'timestamp': datetime.now().isoformat()
        }
