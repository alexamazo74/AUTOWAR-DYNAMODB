import os
import json
import time
import boto3
from typing import Dict, Any
from botocore.exceptions import ClientError
from src.app.credentials_manager import assume_role

AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
TABLE_NAME = os.getenv('AUTOWAR_CREDENTIALS_TABLE', 'autowar-aws-credentials')

dynamo = boto3.resource('dynamodb', region_name=AWS_REGION)
secrets = boto3.client('secretsmanager', region_name=AWS_REGION)
sns_client = None
if os.getenv('CREDENTIALS_ALERT_TOPIC_ARN'):
    sns_client = boto3.client('sns', region_name=AWS_REGION)


def _now_ts() -> int:
    return int(time.time())


def handler(event, context):
    table = dynamo.Table(TABLE_NAME)
    resp = table.scan()
    items = resp.get('Items', [])
    deleted = 0
    rotation_due = 0

    for item in items:
        expiry = item.get('expiry_ts')
        if expiry and int(expiry) <= _now_ts():
            # delete secret if present
            secret_arn = item.get('secret_arn')
            if secret_arn:
                try:
                    secrets.delete_secret(SecretId=secret_arn, ForceDeleteWithoutRecovery=True)
                except Exception:
                    pass
            # mark expired
            try:
                table.update_item(
                    Key={'id': item['id']},
                    UpdateExpression='SET #s = :s, deleted_at = :d',
                    ExpressionAttributeNames={'#s': 'status'},
                    ExpressionAttributeValues={':s': 'expired', ':d': _now_ts()},
                )
            except Exception:
                pass
            deleted += 1
            continue

        # rotation check and attempt rotation when due
        interval = item.get('rotation_interval_days')
        last = item.get('last_rotated_ts')
        if interval:
            try:
                interval = int(interval)
                last = int(last) if last else 0
                if _now_ts() >= last + interval * 24 * 3600:
                    secret_arn = item.get('secret_arn')
                    if secret_arn:
                        # try to rotate a Secrets Manager-stored IAM user secret
                        try:
                            secret_val = secrets.get_secret_value(SecretId=secret_arn)
                            secret_str = secret_val.get('SecretString')
                            if secret_str:
                                data = json.loads(secret_str)
                                iam_user = data.get('iam_user')
                                if iam_user:
                                    iam = boto3.client('iam')
                                    new_key = iam.create_access_key(UserName=iam_user)
                                    access_id = new_key['AccessKey']['AccessKeyId']
                                    secret_key = new_key['AccessKey']['SecretAccessKey']
                                    new_secret = {**data, 'access_key_id': access_id, 'secret_access_key': secret_key}
                                    secrets.put_secret_value(SecretId=secret_arn, SecretString=json.dumps(new_secret))
                                    # update Dynamo metadata
                                    try:
                                        table.update_item(
                                            Key={'id': item['id']},
                                            UpdateExpression='SET last_rotated_ts = :t REMOVE rotation_due',
                                            ExpressionAttributeValues={':t': int(_now_ts())},
                                        )
                                    except Exception:
                                        pass
                                    # prune old keys (best-effort)
                                    try:
                                        keys = iam.list_access_keys(UserName=iam_user)['AccessKeyMetadata']
                                        if len(keys) > 2:
                                            keys_sorted = sorted(keys, key=lambda k: k['CreateDate'])
                                            for old in keys_sorted[:-2]:
                                                try:
                                                    iam.delete_access_key(UserName=iam_user, AccessKeyId=old['AccessKeyId'])
                                                except Exception:
                                                    pass
                                    except Exception:
                                        pass
                                    rotation_due += 1
                                    continue
                        except ClientError as e:
                            # if rotation failed, still mark rotation_due for manual attention
                            try:
                                table.update_item(
                                    Key={'id': item['id']},
                                    UpdateExpression='SET rotation_due = :r',
                                    ExpressionAttributeValues={':r': int(_now_ts())},
                                )
                            except Exception:
                                pass
                            # publish alert if SNS configured
                            topic_arn = os.getenv('CREDENTIALS_ALERT_TOPIC_ARN')
                            if topic_arn and sns_client:
                                try:
                                    sns_client.publish(
                                        TopicArn=topic_arn,
                                        Subject='AutoWAR credential rotation failed',
                                        Message=json.dumps({
                                            'id': item.get('id'),
                                            'client_id': item.get('client_id'),
                                            'reason': str(e)
                                        })
                                    )
                                except Exception:
                                    pass
                            rotation_due += 1
                            continue
                    else:
                        # try to refresh AssumeRole-based session if role_arn present
                        role_arn = item.get('role_arn')
                        if role_arn:
                            try:
                                # assume_role will validate and return credentials with expiration
                                resp = assume_role(role_arn=role_arn, session_name=f"autowar-{item.get('id')}", external_id=item.get('external_id'), duration_seconds=int(item.get('duration_seconds', 3600)))
                                creds = resp.get('credentials', {})
                                expiry = creds.get('expiration')
                                # update table metadata
                                try:
                                    table.update_item(
                                        Key={'id': item['id']},
                                        UpdateExpression='SET expiry_ts = :e, last_rotated_ts = :t REMOVE rotation_due',
                                        ExpressionAttributeValues={':e': int(expiry) if isinstance(expiry, int) else int(expiry) if hasattr(expiry, 'timestamp') else expiry, ':t': int(_now_ts())},
                                    )
                                except Exception:
                                    pass
                                rotation_due += 1
                                continue
                            except Exception as e:
                                # mark rotation_due and publish alert
                                try:
                                    table.update_item(
                                        Key={'id': item['id']},
                                        UpdateExpression='SET rotation_due = :r',
                                        ExpressionAttributeValues={':r': int(_now_ts())},
                                    )
                                except Exception:
                                    pass
                                topic_arn = os.getenv('CREDENTIALS_ALERT_TOPIC_ARN')
                                if topic_arn and sns_client:
                                    try:
                                        sns_client.publish(
                                            TopicArn=topic_arn,
                                            Subject='AutoWAR credential refresh failed',
                                            Message=json.dumps({
                                                'id': item.get('id'),
                                                'client_id': item.get('client_id'),
                                                'reason': str(e)
                                            })
                                        )
                                    except Exception:
                                        pass
                                rotation_due += 1
                                continue
                        else:
                            # no secret or role to act on; mark for manual action
                            try:
                                table.update_item(
                                    Key={'id': item['id']},
                                    UpdateExpression='SET rotation_due = :r',
                                    ExpressionAttributeValues={':r': int(_now_ts())},
                                )
                            except Exception:
                                pass
                            rotation_due += 1
            except Exception:
                continue

    return {
        'statusCode': 200,
        'body': json.dumps({'expired_deleted': deleted, 'rotation_marked': rotation_due}),
    }
