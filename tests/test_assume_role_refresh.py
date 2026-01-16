import json


class FakeTable:
    def __init__(self):
        self.items = []
        self.updated = []

    def scan(self):
        return {"Items": self.items}

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


def test_assume_role_refresh(monkeypatch):
    # item due for rotation with role_arn
    item = {
        "id": "r1",
        "client_id": "c1",
        "rotation_interval_days": 1,
        "last_rotated_ts": 0,
        "role_arn": "arn:aws:iam::123456:user/test",
        "external_id": None,
    }

    fake_table = FakeTable()
    fake_table.items = [item]

    import src.lambdas.credentials_maintenance as lam

    # monkeypatch dynamo resource
    monkeypatch.setattr(
        lam, "dynamo", type("D", (), {"Table": lambda name: fake_table})
    )

    # monkeypatch assume_role from credentials_manager
    def fake_assume(role_arn, session_name, external_id=None, duration_seconds=3600):
        return {
            "credentials": {
                "AccessKeyId": "A",
                "SecretAccessKey": "S",
                "SessionToken": "T",
                "expiration": int(9999999999),
            }
        }

    import src.app.credentials_manager as cm

    monkeypatch.setattr(cm, "assume_role", fake_assume)

    res = lam.handler({}, {})
    body = json.loads(res["body"])
    assert body["rotation_marked"] >= 1
    assert len(fake_table.updated) >= 1
