"""Password hashing and JWT helpers."""

from datetime import datetime, timedelta, timezone

import jwt
from jwt import InvalidTokenError
from pwdlib import PasswordHash

from app.core.config import get_jwt_settings


password_hasher = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """Hash a password with the recommended Argon2 configuration."""
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a plaintext password against a stored password hash."""
    return password_hasher.verify(password, password_hash)


def create_access_token(subject: str) -> str:
    """Create a short-lived JWT access token for a user subject."""
    settings = get_jwt_settings()
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> dict[str, object]:
    """Decode a JWT and require the claims used by the auth dependency."""
    settings = get_jwt_settings()
    return jwt.decode(
        token,
        settings.secret_key,
        algorithms=[settings.algorithm],
        options={"require": ["sub", "exp"]},
    )


__all__ = [
    "InvalidTokenError",
    "create_access_token",
    "decode_access_token",
    "hash_password",
    "verify_password",
]

