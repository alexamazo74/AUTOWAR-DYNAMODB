import json
from types import SimpleNamespace


def test_credentials_maintenance_rotation(monkeypatch):
    # Prepare a fake item that is due for rotation
    item = {
        "id": "cred-1",
        "client_id": "client-x",
        "rotation_interval_days": 1,
        "last_rotated_ts": 0,
        "secret_arn": "arn:aws:secretsmanager:us-east-1:123456:secret:cred-1",
    }

    class FakeTable:
        def __init__(self):
            self.updated = []

        def scan(self):
            return {"Items": [item]}

        def update_item(
            self,
            Key=None,
            UpdateExpression=None,
            ExpressionAttributeValues=None,
            ExpressionAttributeNames=None,
        ):
            self.updated.append(
                {
                    "Key": Key,
                    "UpdateExpression": UpdateExpression,
                    "Values": ExpressionAttributeValues,
                }
            )

    class FakeSecrets:
        def __init__(self):
            self.stored = {
                "SecretString": json.dumps(
                    {
                        "iam_user": "test-user",
                        "access_key_id": "OLD",
                        "secret_access_key": "OLD",
                    }
                )
            }

        def get_secret_value(self, SecretId):
            return self.stored

        def put_secret_value(self, SecretId, SecretString):
            self.stored = {"SecretString": SecretString}

        def delete_secret(self, SecretId, ForceDeleteWithoutRecovery=True):
            self.stored = {}

    class FakeIAM:
        def __init__(self):
            self.keys = []

        def create_access_key(self, UserName):
            ak = {
                "AccessKey": {"AccessKeyId": "NEWKEY", "SecretAccessKey": "NEWSECRET"}
            }
            self.keys.append({"AccessKeyId": "NEWKEY"})
            return ak

        def list_access_keys(self, UserName):
            return {"AccessKeyMetadata": self.keys}

        def delete_access_key(self, UserName, AccessKeyId):
            self.keys = [k for k in self.keys if k["AccessKeyId"] != AccessKeyId]

    fake_table = FakeTable()
    fake_secrets = FakeSecrets()
    fake_iam = FakeIAM()

    # Monkeypatch the dynamo resource/table and secrets/iam clients in the lambda module
    import src.lambdas.credentials_maintenance as lam

    monkeypatch.setattr(lam, "dynamo", SimpleNamespace(Table=lambda name: fake_table))
    monkeypatch.setattr(lam, "secrets", fake_secrets)
    monkeypatch.setattr(
        "boto3.client",
        lambda service_name: fake_iam if service_name == "iam" else fake_secrets,
    )

    result = lam.handler({}, {})
    body = json.loads(result["body"])
    assert body["rotation_marked"] >= 1
    # Ensure table update was called to set last_rotated_ts or rotation_due
    assert len(fake_table.updated) >= 1
