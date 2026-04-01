# mkg/api/errors.py
"""Structured error handling for MKG API.

Provides:
- Consistent error envelope for all HTTP errors
- Pydantic ValidationError → 422 with field-level details
- Unhandled exceptions → 500 with safe message (no stack leak)
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("mkg.api")


def _build_error(
    status_code: int,
    error: str,
    detail: str | list[dict[str, Any]],
    request: Request | None = None,
) -> JSONResponse:
    """Build a consistent error response."""
    body: dict[str, Any] = {
        "error": error,
        "detail": detail,
        "status_code": status_code,
    }
    # Attach request ID if available
    if request:
        request_id = getattr(request.state, "request_id", None)
        if request_id:
            body["request_id"] = request_id
    return JSONResponse(status_code=status_code, content=body)


def register_error_handlers(app: FastAPI) -> None:
    """Register global exception handlers on the FastAPI app."""

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        return _build_error(
            status_code=exc.status_code,
            error=_status_label(exc.status_code),
            detail=str(exc.detail),
            request=request,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        errors = []
        for err in exc.errors():
            errors.append({
                "field": " → ".join(str(loc) for loc in err.get("loc", [])),
                "message": err.get("msg", ""),
                "type": err.get("type", ""),
            })
        return _build_error(
            status_code=422,
            error="ValidationError",
            detail=errors if errors else str(exc),
            request=request,
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logger.exception("Unhandled exception: %s", exc)
        return _build_error(
            status_code=500,
            error="InternalServerError",
            detail="An unexpected error occurred",
            request=request,
        )


def _status_label(code: int) -> str:
    """Map HTTP status code to a short label."""
    labels = {
        400: "BadRequest",
        401: "Unauthorized",
        403: "Forbidden",
        404: "NotFound",
        405: "MethodNotAllowed",
        409: "Conflict",
        422: "ValidationError",
        429: "TooManyRequests",
        500: "InternalServerError",
    }
    return labels.get(code, "Error")
