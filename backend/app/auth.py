"""API key authentication for backend endpoints."""

from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader

from app.config import get_settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def require_api_key(
    api_key: str | None = Security(api_key_header),
) -> str:
    """Validate API key from X-API-Key header.

    If no API_SECRET_KEY is configured (dev without key), allow all requests.
    In production, set API_SECRET_KEY to enforce authentication.
    """
    settings = get_settings()
    if not settings.api_secret_key:
        return "anonymous"
    if not api_key or api_key != settings.api_secret_key:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return api_key
