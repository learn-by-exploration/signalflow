"""API key authentication for backend endpoints."""

import logging

from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader

from app.config import get_settings

logger = logging.getLogger(__name__)

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def require_api_key(
    api_key: str | None = Security(api_key_header),
) -> str:
    """Validate API key from X-API-Key header.

    API_SECRET_KEY is required in all environments. If unset, requests are
    rejected with 401 to prevent unauthenticated access.
    """
    settings = get_settings()
    if not settings.api_secret_key:
        logger.error("API_SECRET_KEY not configured — rejecting request")
        raise HTTPException(
            status_code=401,
            detail="Server misconfiguration: API key not set",
        )
    if not api_key or api_key != settings.api_secret_key:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return api_key
