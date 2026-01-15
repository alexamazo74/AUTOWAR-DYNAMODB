import pytest
import src.app.credentials_manager as cm


def test_validate_keys(monkeypatch):
    class FakeSTS:
        def get_caller_identity(self):
            return {"Account": "123"}
    monkeypatch.setattr(cm, "_sts_client", lambda region_name=None, aws_access_key_id=None, aws_secret_access_key=None, aws_session_token=None: FakeSTS())
    res = cm.validate_keys("AKIA", "SECRET", None, "us-east-1")
    assert res["Account"] == "123"


def test_store_secret_for_keys_create(monkeypatch):
    class FakeSM:
        def create_secret(self, Name, SecretString):
            return {"ARN": "arn:aws:secretsmanager:region:acct:secret:mysecret"}
    monkeypatch.setattr('boto3.client', lambda service_name, region_name=None: FakeSM())
    arn = cm.store_secret_for_keys("client-1", "AKIA", "SEC", None, "us-east-1")
    assert arn.startswith("arn:aws:secretsmanager")


def test_register_credential_record(monkeypatch):
    captured = {}
    class FakeTable:
        def put_item(self, Item):
            captured['item'] = Item
    monkeypatch.setattr(cm, "get_table", lambda name: FakeTable())
    rec = {"type": "role", "role_arn": "arn:..."}
    saved = cm.register_credential_record("client-1", rec)
    assert saved["client_id"] == "client-1"
    assert 'id' in saved
    assert captured['item']['client_id'] == 'client-1'
