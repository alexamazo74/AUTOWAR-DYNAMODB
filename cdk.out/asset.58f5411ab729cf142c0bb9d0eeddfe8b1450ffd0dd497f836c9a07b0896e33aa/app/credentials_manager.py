import os
import uuid
import time
import json
import boto3
from typing import Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from botocore.exceptions import ClientError
from .aws_connector import get_table

AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
SECRETS_PREFIX = os.getenv('AUTOWAR_SECRETS_PREFIX', 'autowar')


def _now_ts() -> int:
    return int(datetime.now(timezone.utc).timestamp())

def _sts_client(region_name: Optional[str] = None, aws_access_key_id: Optional[str] = None,
                aws_secret_access_key: Optional[str] = None, aws_session_token: Optional[str] = None):
    return boto3.client(
        'sts',
        region_name=region_name or AWS_REGION,
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        aws_session_token=aws_session_token,
    )

def assume_role(role_arn: str, session_name: str, external_id: Optional[str] = None,
                duration_seconds: int = 3600, region: Optional[str] = None) -> Dict[str, Any]:
    sts = _sts_client(region_name=region)
    params = {
        'RoleArn': role_arn,
        'RoleSessionName': session_name,
        'DurationSeconds': duration_seconds,
    }
    if external_id:
        params['ExternalId'] = external_id
    resp = sts.assume_role(**params)
    creds = resp['Credentials']
    # validate
    identity = None
    try:
        temp_sts = _sts_client(region_name=region,
                               aws_access_key_id=creds['AccessKeyId'],
                               aws_secret_access_key=creds['SecretAccessKey'],
                               aws_session_token=creds['SessionToken'])
        identity = temp_sts.get_caller_identity()
    except ClientError as e:
        raise
    return {
        'credentials': {
            'access_key': creds['AccessKeyId'],
            'secret_key': creds['SecretAccessKey'],
            'session_token': creds['SessionToken'],
            'expiration': int(creds['Expiration'].timestamp()) if hasattr(creds['Expiration'], 'timestamp') else creds['Expiration'],
        },
        'caller_identity': identity,
    }

def store_secret_for_keys(client_id: str, access_key: str, secret_key: str, session_token: Optional[str] = None,
                          region: Optional[str] = None) -> str:
    sm = boto3.client('secretsmanager', region_name=region or AWS_REGION)
    cred_id = str(uuid.uuid4())
    secret_name = f"{SECRETS_PREFIX}/{client_id}/{cred_id}"
    secret_value = {
        'access_key_id': access_key,
        'secret_access_key': secret_key,
    }
    if session_token:
        secret_value['session_token'] = session_token
    try:
        resp = sm.create_secret(Name=secret_name, SecretString=json.dumps(secret_value))
        return resp['ARN']
    except ClientError as e:
        # if already exists, put a new value
        if e.response.get('Error', {}).get('Code') == 'ResourceExistsException':
            resp = sm.put_secret_value(SecretId=secret_name, SecretString=json.dumps(secret_value))
            # ARN can be retrieved via describe
            desc = sm.describe_secret(SecretId=secret_name)
            return desc['ARN']
        raise

def validate_keys(access_key: str, secret_key: str, session_token: Optional[str] = None, region: Optional[str] = None) -> Dict[str, Any]:
    sts = _sts_client(region_name=region, aws_access_key_id=access_key,
                      aws_secret_access_key=secret_key, aws_session_token=session_token)
    return sts.get_caller_identity()

def register_credential_record(client_id: str, record: Dict[str, Any]) -> Dict[str, Any]:
    table = get_table('autowar-aws-credentials')
    item_id = str(uuid.uuid4())
    # Attach lifecycle metadata fields if not present
    now_ts = _now_ts()
    item = {
        'id': item_id,
        'client_id': client_id,
        'created_at': now_ts,
        'status': record.get('status', 'active'),
        'secret_arn': record.get('secret_arn'),
        'expiry_ts': record.get('expiry_ts'),
        'rotation_interval_days': record.get('rotation_interval_days'),
        'last_rotated_ts': record.get('last_rotated_ts', now_ts),
        **record,
    }
    table.put_item(Item=item)
    return item


def is_expired(item: Dict[str, Any]) -> bool:
    expiry = item.get('expiry_ts')
    if not expiry:
        return False
    return int(expiry) <= _now_ts()


def needs_rotation(item: Dict[str, Any]) -> bool:
    interval = item.get('rotation_interval_days')
    if not interval:
        return False
    last = item.get('last_rotated_ts')
    if not last:
        return True
    next_rotation = int(last) + int(interval) * 24 * 3600
    return _now_ts() >= next_rotation


def mark_expired(item_id: str) -> None:
    table = get_table('autowar-aws-credentials')
    table.update_item(
        Key={'id': item_id},
        UpdateExpression='SET #s = :s, deleted_at = :d',
        ExpressionAttributeNames={'#s': 'status'},
        ExpressionAttributeValues={':s': 'expired', ':d': _now_ts()},
    )


def mark_rotation_done(item_id: str) -> None:
    table = get_table('autowar-aws-credentials')
    table.update_item(
        Key={'id': item_id},
        UpdateExpression='SET last_rotated_ts = :t REMOVE rotation_due',
        ExpressionAttributeValues={':t': _now_ts()},
    )


def rotate_secret_placeholder(item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Placeholder rotation implementation: real rotation depends on credential type.
    For SecretsManager-stored static keys we could create a new secret and update the record.
    For AssumeRole-based credentials, rotation is simply re-validating or refreshing session.
    This function returns a lightweight rotation result dict.
    """
    # Delegate to a more specific rotation function when possible
    secret_arn = item.get('secret_arn')
    if secret_arn:
        try:
            return rotate_static_secret(secret_arn, item.get('id'))
        except Exception as e:
            return {'rotated': False, 'reason': str(e)}
    return {'rotated': False, 'reason': 'no_secret_arn'}


def rotate_static_secret(secret_arn: str, item_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Rotate a Secrets Manager secret that contains credentials for an IAM user when possible.
    Expected secret JSON structure: {"iam_user": "username", "access_key_id": "...", "secret_access_key": "..."}

    This function will:
    - read the secret
    - create a new access key for the `iam_user`
    - update the secret value with the new keys
    - update the DynamoDB record's `last_rotated_ts`

    Returns a dict describing the result.
    """
    sm = boto3.client('secretsmanager', region_name=AWS_REGION)
    iam = boto3.client('iam')

    # Fetch secret
    try:
        resp = sm.get_secret_value(SecretId=secret_arn)
    except ClientError as e:
        raise

    secret_str = resp.get('SecretString')
    if not secret_str:
        raise RuntimeError('empty secret')
    data = json.loads(secret_str)
    iam_user = data.get('iam_user')
    if not iam_user:
        raise RuntimeError('secret missing iam_user, cannot rotate automatically')

    # Create new access key
    new_key = iam.create_access_key(UserName=iam_user)
    access_id = new_key['AccessKey']['AccessKeyId']
    secret_key = new_key['AccessKey']['SecretAccessKey']

    # Update secret with new keys, preserve iam_user field
    new_secret = {**data, 'access_key_id': access_id, 'secret_access_key': secret_key}
    sm.put_secret_value(SecretId=secret_arn, SecretString=json.dumps(new_secret))

    # Update DynamoDB metadata if item_id provided
    if item_id:
        table = get_table('autowar-aws-credentials')
        table.update_item(
            Key={'id': item_id},
            UpdateExpression='SET last_rotated_ts = :t REMOVE rotation_due',
            ExpressionAttributeValues={':t': _now_ts()},
        )

    # Optionally delete old access keys to avoid accumulation (best-effort)
    try:
        keys = iam.list_access_keys(UserName=iam_user)['AccessKeyMetadata']
        # keep the most recent (the one we just created), delete older ones if > 2
        if len(keys) > 2:
            # sort by CreateDate
            keys_sorted = sorted(keys, key=lambda k: k['CreateDate'])
            for old in keys_sorted[:-2]:
                try:
                    iam.delete_access_key(UserName=iam_user, AccessKeyId=old['AccessKeyId'])
                except Exception:
                    pass
    except Exception:
        pass

    return {'rotated': True, 'secret_arn': secret_arn, 'new_access_key_id': access_id}


def refresh_assume_role_item(item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Refresh temporary credentials obtained via AssumeRole and update the credential record metadata.
    Expects `role_arn` in the item. Returns a result dict.
    """
    role_arn = item.get('role_arn')
    if not role_arn:
        raise RuntimeError('no role_arn present')

    session_name = f"autowar-{item.get('id') or uuid.uuid4()}"
    duration = int(item.get('duration_seconds', 3600))
    external_id = item.get('external_id')

    # Use existing assume_role helper which validates caller identity
    resp = assume_role(role_arn=role_arn, session_name=session_name, external_id=external_id, duration_seconds=duration)
    creds = resp.get('credentials', {})
    expires = creds.get('expiration')

    table = get_table('autowar-aws-credentials')
    update_values: Dict[str, Any] = {
        ':t': _now_ts(),
    }
    update_expr = 'SET last_rotated_ts = :t'
    if expires:
        update_expr += ', expiry_ts = :e'
        update_values[':e'] = int(expires) if isinstance(expires, int) else (int(expires) if isinstance(expires, int) else expires)

    table.update_item(
        Key={'id': item['id']},
        UpdateExpression=update_expr,
        ExpressionAttributeValues=update_values,
    )

    return {'refreshed': True, 'id': item.get('id'), 'expiry_ts': expires}
