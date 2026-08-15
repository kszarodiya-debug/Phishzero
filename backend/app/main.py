"""FastAPI application entrypoint and local security middleware."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from contextlib import asynccontextmanager
import logging
import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.types import Message, Receive, Scope, Send

from app.api.analysis import router as analysis_router
from app.api.auth import router as auth_router
from app.api.emails import router as emails_router
from app.api.public_analysis import router as public_analysis_router
from app.core.config import get_frontend_origins, get_jwt_settings, get_max_request_bytes
from app.core.rate_limit import InMemoryRateLimiter


logger = logging.getLogger("phishguard.app")


def _positive_int(name: str, default: int, *, maximum: int) -> int:
    raw_value = os.getenv(name, str(default))
    try:
        value = int(raw_value)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be an integer") from exc
    if value <= 0 or value > maximum:
        raise RuntimeError(f"{name} must be between 1 and {maximum}")
    return value


class SecurityMiddleware:
    """Apply bounded request sizes and process-local request throttling."""

    def __init__(self, app: Callable[[Scope, Receive, Send], Awaitable[None]]) -> None:
        self.app = app
        self.max_request_bytes = get_max_request_bytes()
        self.window_seconds = _positive_int("RATE_LIMIT_WINDOW_SECONDS", 60, maximum=3600)
        self.auth_limit = _positive_int("RATE_LIMIT_AUTH_REQUESTS", 30, maximum=10_000)
        self.api_limit = _positive_int("RATE_LIMIT_API_REQUESTS", 120, maximum=100_000)
        self.public_analysis_limit = _positive_int(
            "RATE_LIMIT_PUBLIC_ANALYSIS_REQUESTS", 20, maximum=10_000
        )
        self.rate_limiter = InMemoryRateLimiter()

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = {key.lower(): value for key, value in scope.get("headers", [])}
        content_length = headers.get(b"content-length")
        if content_length is not None:
            try:
                declared_length = int(content_length)
            except ValueError:
                await self._json_error(send, 400, "Invalid Content-Length header")
                return
            if declared_length < 0 or declared_length > self.max_request_bytes:
                await self._json_error(send, 413, "Request body exceeds the configured limit")
                return

        limit = self._rate_limit(scope)
        if limit is not None:
            client = scope.get("client")
            client_host = client[0] if client else "unknown"
            key = f"{client_host}:{scope.get('method', 'GET')}:{scope.get('path', '')}"
            allowed, retry_after = self.rate_limiter.allow(
                key,
                limit=limit,
                window_seconds=self.window_seconds,
            )
            if not allowed:
                response = JSONResponse(
                    status_code=429,
                    content={"detail": "Too many requests. Please try again later."},
                    headers={"Retry-After": str(retry_after), "Cache-Control": "no-store"},
                )
                await response(scope, receive, send)
                return

        if content_length is not None:
            await self.app(scope, receive, send)
            return

        body = bytearray()
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            if message["type"] != "http.request":
                continue
            body.extend(message.get("body", b""))
            if len(body) > self.max_request_bytes:
                await self._json_error(send, 413, "Request body exceeds the configured limit")
                return
            if not message.get("more_body", False):
                break

        replayed = False

        async def replay_body() -> Message:
            nonlocal replayed
            if replayed:
                return {"type": "http.disconnect"}
            replayed = True
            return {"type": "http.request", "body": bytes(body), "more_body": False}

        await self.app(scope, replay_body, send)

    def _rate_limit(self, scope: Scope) -> int | None:
        if scope.get("method") != "POST":
            return None
        path = scope.get("path", "")
        if path in {"/api/auth/login", "/api/auth/register"}:
            return self.auth_limit
        if path == "/api/public/analysis":
            return self.public_analysis_limit
        if path in {"/api/emails", "/api/analysis"}:
            return self.api_limit
        return None

    async def _json_error(self, send: Send, status_code: int, detail: str) -> None:
        response = JSONResponse(status_code=status_code, content={"detail": detail})
        await response({"type": "http", "method": "POST", "path": "/", "headers": []}, lambda: None, send)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Fail fast when security-critical runtime configuration is invalid."""
    get_jwt_settings()
    get_frontend_origins()
    get_max_request_bytes()
    yield


app = FastAPI(
    title="PhishZero API",
    description="Defensive email spam and phishing detection service.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(get_frontend_origins()),
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)
app.add_middleware(SecurityMiddleware)

app.include_router(auth_router)
app.include_router(emails_router)
app.include_router(analysis_router)
app.include_router(public_analysis_router)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, _exc: Exception) -> JSONResponse:
    """Return a generic error while logging only non-sensitive diagnostics."""
    logger.error(
        "Unhandled application error on %s (%s)",
        request.url.path,
        type(_exc).__name__,
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred."},
        headers={"Cache-Control": "no-store"},
    )


@app.get("/api/health")
def health_check() -> dict[str, str]:
    """Return a lightweight service health status."""
    return {
        "status": "ok",
        "service": "phishguard-ai",
    }
