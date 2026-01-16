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


# Registry of security validators
security_validators: Dict[str, Callable] = {
    'SEC01-BP01': validate_sec01_bp01,
    'SEC01-BP02': validate_sec01_bp02,
    'SEC02-BP01': validate_sec02_bp01,
    # Add more as needed
}