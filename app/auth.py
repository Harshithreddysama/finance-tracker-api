from datetime import datetime, timedelta, timezone
from typing import Optional
import hashlib
import hmac
import base64
import json

SECRET_KEY = "finance_tracker_secret_key_2026"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24


def hash_password(password: str) -> str:
    salt = "finance_tracker_salt"
    salted = f"{salt}{password}{salt}"
    return hashlib.sha256(salted.encode()).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return hash_password(plain_password) == hashed_password


def _base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")


def _base64url_decode(data: str) -> bytes:
    padding = 4 - len(data) % 4
    if padding != 4:
        data += "=" * padding
    return base64.urlsafe_b64decode(data)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    payload = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    payload["exp"] = expire.isoformat()
    header = _base64url_encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    body = _base64url_encode(json.dumps(payload).encode())
    signature_input = f"{header}.{body}".encode()
    signature = hmac.new(SECRET_KEY.encode(), signature_input, hashlib.sha256).digest()
    sig = _base64url_encode(signature)
    return f"{header}.{body}.{sig}"


def decode_access_token(token: str) -> Optional[dict]:
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        header, body, sig = parts
        signature_input = f"{header}.{body}".encode()
        expected_sig = _base64url_encode(
            hmac.new(SECRET_KEY.encode(), signature_input, hashlib.sha256).digest()
        )
        if not hmac.compare_digest(sig, expected_sig):
            return None
        payload = json.loads(_base64url_decode(body))
        exp = datetime.fromisoformat(payload["exp"])
        if datetime.now(timezone.utc) > exp:
            return None
        return payload
    except Exception:
        return None
