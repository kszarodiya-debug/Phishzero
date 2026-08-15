"""Environment-driven authentication configuration."""

from dataclasses import dataclass
import os
from urllib.parse import urlsplit


ALLOWED_JWT_ALGORITHMS = frozenset({"HS256", "HS384", "HS512"})
DEFAULT_FRONTEND_ORIGINS = (
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:4173",
    "http://127.0.0.1:4173",
    "http://localhost:4174",
    "http://127.0.0.1:4174",
)


@dataclass(frozen=True)
class JWTSettings:
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int


def get_jwt_settings() -> JWTSettings:
    """Load and validate JWT settings without providing a fallback secret."""
    secret_key = os.getenv("JWT_SECRET_KEY")
    if not secret_key:
        raise RuntimeError("JWT_SECRET_KEY environment variable is required")
    if len(secret_key) < 32:
        raise RuntimeError("JWT_SECRET_KEY must be at least 32 characters long")

    algorithm = os.getenv("JWT_ALGORITHM", "HS256")
    if algorithm not in ALLOWED_JWT_ALGORITHMS:
        raise RuntimeError("JWT_ALGORITHM must be one of HS256, HS384, or HS512")
    expire_minutes_raw = os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30")
    try:
        expire_minutes = int(expire_minutes_raw)
    except ValueError as exc:
        raise RuntimeError("JWT_ACCESS_TOKEN_EXPIRE_MINUTES must be an integer") from exc
    if expire_minutes <= 0:
        raise RuntimeError("JWT_ACCESS_TOKEN_EXPIRE_MINUTES must be greater than zero")

    return JWTSettings(
        secret_key=secret_key,
        algorithm=algorithm,
        access_token_expire_minutes=expire_minutes,
    )


def get_frontend_origins() -> tuple[str, ...]:
    """Load explicit browser origins and reject unsafe wildcard credentials."""
    configured = os.getenv("FRONTEND_ORIGINS")
    values = tuple(
        origin.strip()
        for origin in (configured.split(",") if configured else DEFAULT_FRONTEND_ORIGINS)
        if origin.strip()
    )
    if not values or "*" in values:
        raise RuntimeError("FRONTEND_ORIGINS must contain explicit origins; wildcard origins are not allowed")
    for origin in values:
        parsed = urlsplit(origin)
        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.netloc
            or parsed.path not in {"", "/"}
            or parsed.username is not None
            or parsed.password is not None
            or parsed.query
            or parsed.fragment
        ):
            raise RuntimeError("FRONTEND_ORIGINS contains an invalid origin")
    return values


def get_max_request_bytes() -> int:
    """Return the bounded HTTP request size used by the application middleware."""
    raw_value = os.getenv("MAX_REQUEST_BYTES", str(6 * 1024 * 1024))
    try:
        value = int(raw_value)
    except ValueError as exc:
        raise RuntimeError("MAX_REQUEST_BYTES must be an integer") from exc
    if value < 1024 or value > 50 * 1024 * 1024:
        raise RuntimeError("MAX_REQUEST_BYTES must be between 1024 and 52428800")
    return value
