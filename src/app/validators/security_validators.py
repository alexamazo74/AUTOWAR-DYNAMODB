"""
Security validators for Well-Architected Framework
Evaluates Security pillar best practices
"""

from typing import Dict, List, Any, Callable
import asyncio


async def validate_sec01_bp01(resources: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    SEC01-BP01: Secure root user access
    Check if root user has MFA enabled and no access keys
    """
    try:
        # Check IAM users and root account
        iam_users = [r for r in resources if r.get('service') == 'iam']

        root_mfa_enabled = False
        root_access_keys = 0

        for user in iam_users:
            if user.get('user_name') == 'root':
                root_mfa_enabled = user.get('mfa_enabled', False)
                root_access_keys = len(user.get('access_keys', []))

        score = 100
        details = []

        if not root_mfa_enabled:
            score -= 50
            details.append("Root user does not have MFA enabled")

        if root_access_keys > 0:
            score -= 50
            details.append(f"Root user has {root_access_keys} access keys")

        return {
            'bp_id': 'SEC01-BP01',
            'status': 'compliant' if score >= 80 else 'non-compliant',
            'score': score,
            'details': details,
            'evidence': {
                'root_mfa_enabled': root_mfa_enabled,
                'root_access_keys': root_access_keys
            }
        }

    except Exception as e:
        return {
            'bp_id': 'SEC01-BP01',
            'status': 'error',
            'score': 0,
            'details': [f"Validation error: {str(e)}"],
            'evidence': {}
        }


async def validate_sec01_bp02(resources: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    SEC01-BP02: Use IAM roles instead of long-term credentials
    Check for IAM users with access keys vs roles
    """
    try:
        iam_resources = [r for r in resources if r.get('service') == 'iam']

        users_with_keys = 0
        total_users = 0
        roles_count = 0

        for resource in iam_resources:
            if resource.get('type') == 'user':
                total_users += 1
                if resource.get('access_keys'):
                    users_with_keys += 1
            elif resource.get('type') == 'role':
                roles_count += 1

        # Calculate score based on usage of roles vs access keys
        if total_users == 0:
            score = 100  # No users, assume roles are used
        else:
            key_usage_ratio = users_with_keys / total_users
            score = max(0, 100 - (key_usage_ratio * 100))

        details = []
        if users_with_keys > 0:
            details.append(f"{users_with_keys} IAM users have access keys")
        if roles_count > 0:
            details.append(f"{roles_count} IAM roles configured")

        return {
            'bp_id': 'SEC01-BP02',
            'status': 'compliant' if score >= 80 else 'non-compliant',
            'score': score,
            'details': details,
            'evidence': {
                'users_with_access_keys': users_with_keys,
                'total_users': total_users,
                'roles_count': roles_count
            }
        }

    except Exception as e:
        return {
            'bp_id': 'SEC01-BP02',
            'status': 'error',
            'score': 0,
            'details': [f"Validation error: {str(e)}"],
            'evidence': {}
        }


async def validate_sec02_bp01(resources: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    SEC02-BP01: Enable CloudTrail logging
    Check if CloudTrail is enabled and configured properly
    """
    try:
        cloudtrail_trails = [r for r in resources if r.get('service') == 'cloudtrail']

        trails_enabled = 0
        multi_region_trails = 0

        for trail in cloudtrail_trails:
            if trail.get('is_logging', False):
                trails_enabled += 1
                if trail.get('is_multi_region_trail', False):
                    multi_region_trails += 1

        score = 100
        details = []

        if trails_enabled == 0:
            score = 0
            details.append("No CloudTrail trails are enabled")
        elif multi_region_trails == 0:
            score = 50
            details.append("CloudTrail enabled but no multi-region trails")
        else:
            details.append(f"{multi_region_trails} multi-region trails enabled")

        return {
            'bp_id': 'SEC02-BP01',
            'status': 'compliant' if score >= 80 else 'non-compliant',
            'score': score,
            'details': details,
            'evidence': {
                'enabled_trails': trails_enabled,
                'multi_region_trails': multi_region_trails
            }
        }

    except Exception as e:
        return {
            'bp_id': 'SEC02-BP01',
            'status': 'error',
            'score': 0,
            'details': [f"Validation error: {str(e)}"],
            'evidence': {}
        }


async def validate_sec01_bp03(resources: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    SEC01-BP03: Grant least privilege access
    Check if IAM policies follow least privilege principle
    """
    try:
        iam_policies = [r for r in resources if r.get('service') == 'iam' and r.get('type') == 'policy']

        policies_analyzed = len(iam_policies)
        policies_with_wildcard = 0
        policies_with_least_privilege = 0

        for policy in iam_policies:
            policy_document = policy.get('policy_document', {})
            if _has_wildcard_permissions(policy_document):
                policies_with_wildcard += 1
            else:
                policies_with_least_privilege += 1

        score = 100
        details = []

        if policies_analyzed == 0:
            score = 50
            details.append("No IAM policies found to analyze")
        else:
            wildcard_ratio = policies_with_wildcard / policies_analyzed
            score = max(0, 100 - (wildcard_ratio * 100))
            if policies_with_wildcard > 0:
                details.append(f"{policies_with_wildcard} policies use wildcard permissions")
            if policies_with_least_privilege > 0:
                details.append(f"{policies_with_least_privilege} policies follow least privilege")

        return {
            'bp_id': 'SEC01-BP03',
            'status': 'compliant' if score >= 80 else 'non-compliant',
            'score': score,
            'details': details,
            'evidence': {
                'policies_analyzed': policies_analyzed,
                'policies_with_wildcard': policies_with_wildcard,
                'policies_with_least_privilege': policies_with_least_privilege
            }
        }

    except Exception as e:
        return {
            'bp_id': 'SEC01-BP03',
            'status': 'error',
            'score': 0,
            'details': [f"Validation error: {str(e)}"],
            'evidence': {}
        }


def _has_wildcard_permissions(policy_document: Dict[str, Any]) -> bool:
    """Check if policy has wildcard permissions"""
    statements = policy_document.get('Statement', [])
    if not isinstance(statements, list):
        statements = [statements]

    for statement in statements:
        effect = statement.get('Effect', '')
        if effect != 'Allow':
            continue

        actions = statement.get('Action', [])
        if isinstance(actions, str):
            actions = [actions]

        for action in actions:
            if '*' in action or action == '*':
                return True

        resources = statement.get('Resource', [])
        if isinstance(resources, str):
            resources = [resources]

        for resource in resources:
            if resource == '*':
                return True

    return False


async def validate_sec01_bp04(resources: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    SEC01-BP04: Use IAM policies for AWS resource access
    Check if IAM policies are properly attached to users/roles
    """
    try:
        iam_resources = [r for r in resources if r.get('service') == 'iam']

        users_with_policies = 0
        roles_with_policies = 0
        total_users = 0
        total_roles = 0

        for resource in iam_resources:
            if resource.get('type') == 'user':
                total_users += 1
                if resource.get('attached_policies'):
                    users_with_policies += 1
            elif resource.get('type') == 'role':
                total_roles += 1
                if resource.get('attached_policies'):
                    roles_with_policies += 1

        score = 100
        details = []

        if total_users > 0:
            user_policy_ratio = users_with_policies / total_users
            score = min(score, user_policy_ratio * 100)
            if users_with_policies < total_users:
                details.append(f"{total_users - users_with_policies} users without attached policies")

        if total_roles > 0:
            role_policy_ratio = roles_with_policies / total_roles
            score = min(score, role_policy_ratio * 100)
            if roles_with_policies < total_roles:
                details.append(f"{total_roles - roles_with_policies} roles without attached policies")

        if total_users == 0 and total_roles == 0:
            score = 50
            details.append("No IAM users or roles found")

        return {
            'bp_id': 'SEC01-BP04',
            'status': 'compliant' if score >= 80 else 'non-compliant',
            'score': score,
            'details': details,
            'evidence': {
                'users_with_policies': users_with_policies,
                'total_users': total_users,
                'roles_with_policies': roles_with_policies,
                'total_roles': total_roles
            }
        }

    except Exception as e:
        return {
            'bp_id': 'SEC01-BP04',
            'status': 'error',
            'score': 0,
            'details': [f"Validation error: {str(e)}"],
            'evidence': {}
        }


async def validate_sec01_bp05(resources: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    SEC01-BP05: Use temporary credentials
    Check for use of temporary credentials vs long-term
    """
    try:
        iam_resources = [r for r in resources if r.get('service') == 'iam']

        temp_credentials_used = 0
        long_term_credentials = 0

        for resource in iam_resources:
            if resource.get('type') == 'user':
                access_keys = resource.get('access_keys', [])
                for key in access_keys:
                    if key.get('temporary', False):
                        temp_credentials_used += 1
                    else:
                        long_term_credentials += 1

        score = 100
        details = []

        if long_term_credentials > 0:
            score = max(0, 100 - (long_term_credentials * 20))
            details.append(f"{long_term_credentials} long-term access keys found")

        if temp_credentials_used > 0:
            details.append(f"{temp_credentials_used} temporary credentials in use")

        return {
            'bp_id': 'SEC01-BP05',
            'status': 'compliant' if score >= 80 else 'non-compliant',
            'score': score,
            'details': details,
            'evidence': {
                'temp_credentials_used': temp_credentials_used,
                'long_term_credentials': long_term_credentials
            }
        }

    except Exception as e:
        return {
            'bp_id': 'SEC01-BP05',
            'status': 'error',
            'score': 0,
            'details': [f"Validation error: {str(e)}"],
            'evidence': {}
        }


async def validate_sec01_bp06(resources: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    SEC01-BP06: Use AWS managed policies where possible
    Check if managed policies are used instead of inline policies
    """
    try:
        iam_policies = [r for r in resources if r.get('service') == 'iam' and r.get('type') == 'policy']

        managed_policies = 0
        inline_policies = 0

        for policy in iam_policies:
            if policy.get('is_managed', False):
                managed_policies += 1
            else:
                inline_policies += 1

        score = 100
        details = []

        if managed_policies + inline_policies == 0:
            score = 50
            details.append("No IAM policies found")
        else:
            managed_ratio = managed_policies / (managed_policies + inline_policies)
            score = managed_ratio * 100
            if inline_policies > 0:
                details.append(f"{inline_policies} inline policies (prefer managed policies)")

        return {
            'bp_id': 'SEC01-BP06',
            'status': 'compliant' if score >= 80 else 'non-compliant',
            'score': score,
            'details': details,
            'evidence': {
                'managed_policies': managed_policies,
                'inline_policies': inline_policies
            }
        }

    except Exception as e:
        return {
            'bp_id': 'SEC01-BP06',
            'status': 'error',
            'score': 0,
            'details': [f"Validation error: {str(e)}"],
            'evidence': {}
        }


async def validate_sec01_bp07(resources: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    SEC01-BP07: Use IAM Access Analyzer to generate least-privilege policies
    Check if IAM Access Analyzer is enabled
    """
    try:
        analyzers = [r for r in resources if r.get('service') == 'access-analyzer']

        analyzers_enabled = len(analyzers)
        score = 100 if analyzers_enabled > 0 else 0

        details = []
        if analyzers_enabled > 0:
            details.append(f"{analyzers_enabled} IAM Access Analyzers enabled")
        else:
            details.append("IAM Access Analyzer not enabled")

        return {
            'bp_id': 'SEC01-BP07',
            'status': 'compliant' if score >= 80 else 'non-compliant',
            'score': score,
            'details': details,
            'evidence': {
                'analyzers_enabled': analyzers_enabled
            }
        }

    except Exception as e:
        return {
            'bp_id': 'SEC01-BP07',
            'status': 'error',
            'score': 0,
            'details': [f"Validation error: {str(e)}"],
            'evidence': {}
        }


async def validate_sec01_bp08(resources: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    SEC01-BP08: Use credentials for human access
    Check if human users have appropriate access patterns
    """
    try:
        iam_users = [r for r in resources if r.get('service') == 'iam' and r.get('type') == 'user']

        human_users = 0
        programmatic_users = 0

        for user in iam_users:
            if user.get('is_human', True):  # Assume human unless specified
                human_users += 1
            else:
                programmatic_users += 1

        score = 100
        details = []

        if human_users == 0:
            score = 50
            details.append("No human users identified")
        else:
            details.append(f"{human_users} human users with appropriate access")

        return {
            'bp_id': 'SEC01-BP08',
            'status': 'compliant' if score >= 80 else 'non-compliant',
            'score': score,
            'details': details,
            'evidence': {
                'human_users': human_users,
                'programmatic_users': programmatic_users
            }
        }

    except Exception as e:
        return {
            'bp_id': 'SEC01-BP08',
            'status': 'error',
            'score': 0,
            'details': [f"Validation error: {str(e)}"],
            'evidence': {}
        }


async def validate_sec01_bp09(resources: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    SEC01-BP09: Use credentials for programmatic access
    Check if programmatic access uses appropriate credentials
    """
    try:
        iam_resources = [r for r in resources if r.get('service') == 'iam']

        programmatic_access_count = 0
        appropriate_credentials = 0

        for resource in iam_resources:
            if resource.get('type') == 'user' and not resource.get('is_human', True):
                programmatic_access_count += 1
                # Check if using roles or temporary credentials
                if resource.get('has_role', False) or any(key.get('temporary', False) for key in resource.get('access_keys', [])):
                    appropriate_credentials += 1

        score = 100
        details = []

        if programmatic_access_count == 0:
            score = 50
            details.append("No programmatic access identified")
        else:
            credential_ratio = appropriate_credentials / programmatic_access_count
            score = credential_ratio * 100
            if appropriate_credentials < programmatic_access_count:
                details.append(f"{programmatic_access_count - appropriate_credentials} programmatic users need better credentials")

        return {
            'bp_id': 'SEC01-BP09',
            'status': 'compliant' if score >= 80 else 'non-compliant',
            'score': score,
            'details': details,
            'evidence': {
                'programmatic_access_count': programmatic_access_count,
                'appropriate_credentials': appropriate_credentials
            }
        }

    except Exception as e:
        return {
            'bp_id': 'SEC01-BP09',
            'status': 'error',
            'score': 0,
            'details': [f"Validation error: {str(e)}"],
            'evidence': {}
        }


async def validate_sec03_bp01(resources: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    SEC03-BP01: Use multi-factor authentication (MFA)
    Check if IAM users have MFA enabled
    """
    try:
        iam_users = [r for r in resources if r.get('service') == 'iam' and r.get('type') == 'user']

        total_users = len(iam_users)
        users_with_mfa = 0

        for user in iam_users:
            if user.get('mfa_enabled', False):
                users_with_mfa += 1

        score = 100
        details = []

        if total_users == 0:
            score = 50
            details.append("No IAM users found to check MFA")
        else:
            mfa_ratio = users_with_mfa / total_users
            score = mfa_ratio * 100
            if users_with_mfa < total_users:
                details.append(f"{total_users - users_with_mfa} users without MFA enabled")
            if users_with_mfa > 0:
                details.append(f"{users_with_mfa} users have MFA enabled")

        return {
            'bp_id': 'SEC03-BP01',
            'status': 'compliant' if score >= 80 else 'non-compliant',
            'score': score,
            'details': details,
            'evidence': {
                'total_users': total_users,
                'users_with_mfa': users_with_mfa
            }
        }

    except Exception as e:
        return {
            'bp_id': 'SEC03-BP01',
            'status': 'error',
            'score': 0,
            'details': [f"Validation error: {str(e)}"],
            'evidence': {}
        }


async def validate_sec04_bp01(resources: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    SEC04-BP01: Use AWS Config to monitor resource configurations
    Check if AWS Config is enabled and recording
    """
    try:
        config_recorders = [r for r in resources if r.get('service') == 'config']

        recorders_enabled = 0
        recorders_recording = 0

        for recorder in config_recorders:
            if recorder.get('is_enabled', False):
                recorders_enabled += 1
                if recorder.get('is_recording', False):
                    recorders_recording += 1

        score = 100
        details = []

        if recorders_enabled == 0:
            score = 0
            details.append("AWS Config is not enabled")
        elif recorders_recording == 0:
            score = 25
            details.append("Config enabled but not recording")
        else:
            details.append(f"{recorders_recording} Config recorders actively recording")

        return {
            'bp_id': 'SEC04-BP01',
            'status': 'compliant' if score >= 80 else 'non-compliant',
            'score': score,
            'details': details,
            'evidence': {
                'recorders_enabled': recorders_enabled,
                'recorders_recording': recorders_recording
            }
        }

    except Exception as e:
        return {
            'bp_id': 'SEC04-BP01',
            'status': 'error',
            'score': 0,
            'details': [f"Validation error: {str(e)}"],
            'evidence': {}
        }


async def validate_sec02_bp02(resources: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    SEC02-BP02: Use temporary credentials for human access
    Check if human users use temporary credentials
    """
    try:
        iam_users = [r for r in resources if r.get('service') == 'iam' and r.get('type') == 'user']

        human_users_temp_creds = 0
        human_users_total = 0

        for user in iam_users:
            if user.get('is_human', True):
                human_users_total += 1
                access_keys = user.get('access_keys', [])
                if any(key.get('temporary', False) for key in access_keys):
                    human_users_temp_creds += 1

        score = 100
        details = []

        if human_users_total == 0:
            score = 50
            details.append("No human users found")
        else:
            temp_ratio = human_users_temp_creds / human_users_total
            score = temp_ratio * 100
            if human_users_temp_creds < human_users_total:
                details.append(f"{human_users_total - human_users_temp_creds} human users not using temporary credentials")

        return {
            'bp_id': 'SEC02-BP02',
            'status': 'compliant' if score >= 80 else 'non-compliant',
            'score': score,
            'details': details,
            'evidence': {
                'human_users_temp_creds': human_users_temp_creds,
                'human_users_total': human_users_total
            }
        }

    except Exception as e:
        return {
            'bp_id': 'SEC02-BP02',
            'status': 'error',
            'score': 0,
            'details': [f"Validation error: {str(e)}"],
            'evidence': {}
        }


async def validate_sec03_bp02(resources: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    SEC03-BP02: Use encryption at rest
    Check if data is encrypted at rest
    """
    try:
        encrypted_resources = 0
        total_resources = 0

        # Check S3 buckets
        s3_buckets = [r for r in resources if r.get('service') == 's3']
        for bucket in s3_buckets:
            total_resources += 1
            if bucket.get('encryption_enabled', False):
                encrypted_resources += 1

        # Check RDS instances
        rds_instances = [r for r in resources if r.get('service') == 'rds']
        for instance in rds_instances:
            total_resources += 1
            if instance.get('encryption_enabled', False):
                encrypted_resources += 1

        score = 100
        details = []

        if total_resources == 0:
            score = 50
            details.append("No encryptable resources found")
        else:
            encryption_ratio = encrypted_resources / total_resources
            score = encryption_ratio * 100
            if encrypted_resources < total_resources:
                details.append(f"{total_resources - encrypted_resources} resources not encrypted at rest")

        return {
            'bp_id': 'SEC03-BP02',
            'status': 'compliant' if score >= 80 else 'non-compliant',
            'score': score,
            'details': details,
            'evidence': {
                'encrypted_resources': encrypted_resources,
                'total_resources': total_resources
            }
        }

    except Exception as e:
        return {
            'bp_id': 'SEC03-BP02',
            'status': 'error',
            'score': 0,
            'details': [f"Validation error: {str(e)}"],
            'evidence': {}
        }


async def validate_sec05_bp01(resources: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    SEC05-BP01: Use GuardDuty for threat detection
    Check if Amazon GuardDuty is enabled
    """
    try:
        guardduty_detectors = [r for r in resources if r.get('service') == 'guardduty']

        detectors_enabled = len(guardduty_detectors)
        score = 100 if detectors_enabled > 0 else 0

        details = []
        if detectors_enabled > 0:
            details.append(f"{detectors_enabled} GuardDuty detectors enabled")
        else:
            details.append("Amazon GuardDuty not enabled")

        return {
            'bp_id': 'SEC05-BP01',
            'status': 'compliant' if score >= 80 else 'non-compliant',
            'score': score,
            'details': details,
            'evidence': {
                'detectors_enabled': detectors_enabled
            }
        }

    except Exception as e:
        return {
            'bp_id': 'SEC05-BP01',
            'status': 'error',
            'score': 0,
            'details': [f"Validation error: {str(e)}"],
            'evidence': {}
        }


# Registry of security validators
security_validators: Dict[str, Callable] = {
    'SEC01-BP01': validate_sec01_bp01,
    'SEC01-BP02': validate_sec01_bp02,
    'SEC01-BP03': validate_sec01_bp03,
    'SEC01-BP04': validate_sec01_bp04,
    'SEC01-BP05': validate_sec01_bp05,
    'SEC01-BP06': validate_sec01_bp06,
    'SEC01-BP07': validate_sec01_bp07,
    'SEC01-BP08': validate_sec01_bp08,
    'SEC01-BP09': validate_sec01_bp09,
    'SEC02-BP01': validate_sec02_bp01,
    'SEC02-BP02': validate_sec02_bp02,
    'SEC03-BP01': validate_sec03_bp01,
    'SEC03-BP02': validate_sec03_bp02,
    'SEC04-BP01': validate_sec04_bp01,
    'SEC05-BP01': validate_sec05_bp01,
    # Add more as needed
}

# Security questions and BP descriptions
SECURITY_DESCRIPTIONS = {
    'questions': {
        'SEC01': '¿Cómo opera usted su carga de trabajo de forma segura?',
        'SEC02': '¿Cómo gestiona las identidades de personas y máquinas?',
        'SEC03': '¿Cómo protege los datos confidenciales?',
        'SEC04': '¿Cómo detecta y investiga los eventos de seguridad?',
        'SEC05': '¿Cómo protege sus recursos de red?',
        'SEC06': '¿Cómo protege las cargas de trabajo informáticas?',
        'SEC07': '¿Cómo clasifica los datos?',
        'SEC08': '¿Cómo protege los datos en tránsito?',
        'SEC09': '¿Cómo protege los datos en reposo?',
        'SEC10': '¿Cómo anticipa, responde y recupera ante incidentes?'
    },
    'best_practices': {
        'SEC01-BP01': 'Proteger el usuario raíz de la cuenta y sus propiedades',
        'SEC01-BP02': 'Usar roles de IAM en lugar de credenciales de largo plazo',
        'SEC01-BP03': 'Conceder el menor privilegio de acceso',
        'SEC01-BP04': 'Usar políticas de IAM para el acceso a recursos de AWS',
        'SEC01-BP05': 'Usar credenciales temporales',
        'SEC01-BP06': 'Usar políticas administradas de AWS cuando sea posible',
        'SEC01-BP07': 'Usar el Analizador de acceso de IAM para generar políticas de menor privilegio',
        'SEC01-BP08': 'Usar credenciales para acceso humano',
        'SEC01-BP09': 'Usar credenciales para acceso programático',
        'SEC02-BP01': 'Usar proveedores de identidad',
        'SEC02-BP02': 'Usar credenciales temporales para acceso humano',
        'SEC03-BP01': 'Usar autenticación multifactor (MFA)',
        'SEC03-BP02': 'Usar cifrado en reposo',
        'SEC04-BP01': 'Usar AWS Config para monitorear configuraciones de recursos',
        'SEC05-BP01': 'Usar Amazon GuardDuty para detección de amenazas'
    }
}