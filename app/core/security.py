import uuid
from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from app.core.config import get_settings
from app.core.exceptions import UnauthorizedError

settings = get_settings()
hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return hasher.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    try:
        return hasher.verify(hashed, password)
    except (VerificationError, InvalidHashError):
        return False


def _encode(subject: int, token_type: str, expires_at: datetime, extra: dict) -> tuple[str, str]:
    jti = uuid.uuid4().hex
    payload = {
        "sub": str(subject),
        "type": token_type,
        "jti": jti,
        "iat": datetime.now(timezone.utc),
        "exp": expires_at,
        **extra,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm), jti


def create_access_token(user_id: int, role: str) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    token, _ = _encode(user_id, "access", expires_at, {"role": role})
    return token


def create_refresh_token(user_id: int) -> tuple[str, str, datetime]:
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
    token, jti = _encode(user_id, "refresh", expires_at, {})
    return token, jti, expires_at.replace(tzinfo=None)


def decode_token(token: str, expected_type: str) -> dict:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except jwt.PyJWTError:
        raise UnauthorizedError("Invalid or expired token")
    if payload.get("type") != expected_type or not payload.get("sub"):
        raise UnauthorizedError("Invalid token type")
    return payload
