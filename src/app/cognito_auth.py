import os
import time
from typing import Dict
import httpx
from jose import jwt
from jose.utils import base64url_decode
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from fastapi import Header, HTTPException, status

COGNITO_REGION = os.getenv("COGNITO_REGION") or os.getenv("AWS_REGION", "us-east-1")
COGNITO_USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID")
COGNITO_APP_CLIENT_ID = os.getenv("COGNITO_APP_CLIENT_ID")

_JWKS_CACHE: Dict = {"keys": None, "fetched_at": 0}
_JWKS_TTL = 60 * 60  # 1 hour


def _jwks_url():
    if not COGNITO_USER_POOL_ID:
        raise RuntimeError("COGNITO_USER_POOL_ID not configured")
    return f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}/.well-known/jwks.json"


def _fetch_jwks():
    now = int(time.time())
    if _JWKS_CACHE["keys"] and now - _JWKS_CACHE["fetched_at"] < _JWKS_TTL:
        return _JWKS_CACHE["keys"]
    url = _jwks_url()
    r = httpx.get(url, timeout=10.0)
    r.raise_for_status()
    jwks = r.json()
    _JWKS_CACHE["keys"] = jwks["keys"]
    _JWKS_CACHE["fetched_at"] = now
    return _JWKS_CACHE["keys"]


def _jwk_to_pem(jwk_dict: Dict) -> bytes:
    n = int.from_bytes(base64url_decode(jwk_dict["n"]), "big")
    e = int.from_bytes(base64url_decode(jwk_dict["e"]), "big")
    public_numbers = rsa.RSAPublicNumbers(e, n)
    public_key = public_numbers.public_key()
    pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return pem


def verify_jwt_token(token: str) -> Dict:
    if not COGNITO_USER_POOL_ID or not COGNITO_APP_CLIENT_ID:
        raise RuntimeError(
            "Cognito configuration missing: set COGNITO_USER_POOL_ID and COGNITO_APP_CLIENT_ID"
        )
    headers = jwt.get_unverified_header(token)
    kid = headers.get("kid")
    keys = _fetch_jwks()
    key = None
    for k in keys:
        if k.get("kid") == kid:
            key = k
            break
    if not key:
        raise ValueError("Public key not found in JWKS")
    public_pem = _jwk_to_pem(key)
    issuer = (
        f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}"
    )
    claims = jwt.decode(
        token,
        public_pem,
        algorithms=["RS256"],
        audience=COGNITO_APP_CLIENT_ID,
        issuer=issuer,
    )
    return claims


def require_cognito_auth(authorization: str | None = Header(None)) -> Dict:
    """FastAPI dependency to require a valid Cognito JWT Bearer token.

    Returns the token claims on success or raises HTTPException(401) on failure.
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
        )
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header",
        )
    token = authorization.split(" ", 1)[1]
    try:
        claims = verify_jwt_token(token)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token: {e}"
        )
    return claims
