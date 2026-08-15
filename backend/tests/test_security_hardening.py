import asyncio
from pathlib import Path
import secrets

import pytest
from fastapi import Request
from fastapi.testclient import TestClient

from app.core.config import get_frontend_origins, get_jwt_settings
from app.core.rate_limit import InMemoryRateLimiter
from app.db.database import engine
from app.main import SecurityMiddleware, app, unhandled_exception_handler
from app.services.risk_engine import _safe_error_message


def test_jwt_algorithm_is_allowlisted(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
    monkeypatch.setenv("JWT_ALGORITHM", "none")

    with pytest.raises(RuntimeError, match="JWT_ALGORITHM"):
        get_jwt_settings()


def test_cors_wildcard_and_non_origin_values_are_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("FRONTEND_ORIGINS", "*")

    with pytest.raises(RuntimeError, match="wildcard"):
        get_frontend_origins()

    monkeypatch.setenv("FRONTEND_ORIGINS", "https://user:password@example.test")
    with pytest.raises(RuntimeError, match="invalid origin"):
        get_frontend_origins()


def test_rate_limiter_blocks_after_limit() -> None:
    limiter = InMemoryRateLimiter()

    assert limiter.allow("local-client", limit=1, window_seconds=60)[0] is True
    allowed, retry_after = limiter.allow("local-client", limit=1, window_seconds=60)

    assert allowed is False
    assert retry_after >= 1


def test_security_middleware_returns_429_for_limited_auth_requests(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RATE_LIMIT_AUTH_REQUESTS", "1")
    middleware = SecurityMiddleware(_empty_asgi_app)
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/api/auth/login",
        "headers": [(b"content-length", b"0")],
        "client": ("127.0.0.1", 1234),
    }

    first_messages: list[dict[str, object]] = []
    second_messages: list[dict[str, object]] = []

    async def send_first(message: dict[str, object]) -> None:
        first_messages.append(message)

    async def send_second(message: dict[str, object]) -> None:
        second_messages.append(message)

    asyncio.run(middleware(scope, _empty_receive, send_first))
    asyncio.run(middleware(scope, _empty_receive, send_second))

    assert _status_code(first_messages) == 204
    assert _status_code(second_messages) == 429


def test_sqlite_foreign_keys_are_enabled() -> None:
    with engine.connect() as connection:
        assert connection.exec_driver_sql("PRAGMA foreign_keys").scalar() == 1


def test_error_diagnostics_do_not_return_paths_or_input() -> None:
    message = _safe_error_message(FileNotFoundError(Path("C:/private/model.joblib")))

    assert message == "Component analysis unavailable."
    assert "private" not in message
    assert "model.joblib" not in message


def test_unhandled_exception_response_is_generic() -> None:
    request = Request({"type": "http", "method": "GET", "path": "/api/health", "headers": []})

    response = asyncio.run(
        unhandled_exception_handler(request, RuntimeError("secret internal path"))
    )

    assert response.status_code == 500
    assert response.body == b'{"detail":"An internal server error occurred."}'
    assert b"secret" not in response.body


def test_unhandled_exception_logging_excludes_exception_details(
    caplog: pytest.LogCaptureFixture,
) -> None:
    request = Request({"type": "http", "method": "GET", "path": "/api/health", "headers": []})

    with caplog.at_level("ERROR", logger="phishguard.app"):
        asyncio.run(
            unhandled_exception_handler(
                request,
                RuntimeError("password=super-secret jwt=do-not-log"),
            )
        )

    assert "RuntimeError" in caplog.text
    assert "super-secret" not in caplog.text
    assert "do-not-log" not in caplog.text


def test_oversized_request_is_rejected_before_route_processing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
    with TestClient(app) as client:
        response = client.post("/api/health", content=b"x" * (6 * 1024 * 1024 + 1))

    assert response.status_code == 413
    assert "stack" not in response.text.lower()


async def _empty_receive() -> dict[str, object]:
    return {"type": "http.request", "body": b"", "more_body": False}


async def _empty_asgi_app(scope, receive, send) -> None:
    await send({"type": "http.response.start", "status": 204, "headers": []})
    await send({"type": "http.response.body", "body": b""})


def _status_code(messages: list[dict[str, object]]) -> int:
    start = next(message for message in messages if message["type"] == "http.response.start")
    return int(start["status"])
