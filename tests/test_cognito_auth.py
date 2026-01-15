import pytest
from fastapi import HTTPException
import src.app.cognito_auth as cognito_auth


def test_require_cognito_auth_missing():
    with pytest.raises(HTTPException) as exc:
        cognito_auth.require_cognito_auth(None)
    assert exc.value.status_code == 401


def test_require_cognito_auth_invalid(monkeypatch):
    def fake_verify(token):
        raise Exception("invalid")
    monkeypatch.setattr(cognito_auth, "verify_jwt_token", fake_verify)
    with pytest.raises(HTTPException) as exc:
        cognito_auth.require_cognito_auth("Bearer bad")
    assert exc.value.status_code == 401


def test_require_cognito_auth_valid(monkeypatch):
    monkeypatch.setattr(cognito_auth, "verify_jwt_token", lambda t: {"sub": "user1"})
    claims = cognito_auth.require_cognito_auth("Bearer good")
    assert claims["sub"] == "user1"
