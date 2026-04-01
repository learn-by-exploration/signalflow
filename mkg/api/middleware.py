# mkg/api/middleware.py
"""Production middleware for MKG API.

Provides:
- Request ID generation (X-Request-ID header)
- API key authentication (X-API-Key or Bearer token)
- Structured request logging
- Rate limiting via SlowAPI
"""

from __future__ import annotations

import hmac
import logging
import os
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

logger = logging.getLogger("mkg.api")

# Paths that bypass authentication
AUTH_BYPASS_PATHS = frozenset({"/health", "/metrics", "/docs", "/openapi.json", "/redoc"})


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Attach a unique request ID to every request/response.

    If the client sends X-Request-ID, it is preserved.
    Otherwise a UUID4 is generated.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class APIKeyAuthMiddleware(BaseHTTPMiddleware):
    """Validate API key on protected endpoints.

    When MKG_API_KEY env var is set, all /api/* endpoints require either:
    - X-API-Key: <key>
    - Authorization: Bearer <key>

    When MKG_API_KEY is NOT set (dev mode), auth is disabled.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        api_key = os.environ.get("MKG_API_KEY")

        # Auth disabled in dev mode
        if not api_key:
            return await call_next(request)

        path = request.url.path

        # Bypass auth for system endpoints
        if path in AUTH_BYPASS_PATHS or not path.startswith("/api/"):
            return await call_next(request)

        # Check X-API-Key header
        provided_key = request.headers.get("x-api-key")

        # Check Authorization: Bearer <key>
        if not provided_key:
            auth_header = request.headers.get("authorization", "")
            if auth_header.startswith("Bearer "):
                provided_key = auth_header[7:]

        if not provided_key or not hmac.compare_digest(provided_key, api_key):
            request_id = getattr(request.state, "request_id", None)
            return JSONResponse(
                status_code=401,
                content={
                    "error": "Unauthorized",
                    "detail": "Invalid or missing API key",
                    "status_code": 401,
                    "request_id": request_id,
                },
            )

        return await call_next(request)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log every request with method, path, status, and duration."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000
        request_id = getattr(request.state, "request_id", "-")
        logger.info(
            "%s %s → %d (%.1fms) [%s]",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            request_id,
        )
        return response


def setup_rate_limiting(app: FastAPI) -> None:
    """Configure rate limiting via SlowAPI.

    Falls back gracefully if slowapi is not installed.
    Rate limits:
    - Default: 100/minute per client IP
    - Write endpoints: 30/minute per client IP
    """
    try:
        from slowapi import Limiter, _rate_limit_exceeded_handler
        from slowapi.errors import RateLimitExceeded
        from slowapi.util import get_remote_address

        limiter = Limiter(
            key_func=get_remote_address,
            default_limits=["100/minute"],
            storage_uri=os.environ.get("REDIS_URL", "memory://"),
        )
        app.state.limiter = limiter
        app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    except ImportError:
        logger.warning("slowapi not installed — rate limiting disabled")
