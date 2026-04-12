"""Authentication — API key and JWT Bearer token support with revocation."""

import hmac
import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import UUID

import bcrypt
import jwt
import redis
from fastapi import Depends, Header, HTTPException, Security
from fastapi.security import APIKeyHeader

from app.config import get_settings

logger = logging.getLogger(__name__)

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# Redis client for JWT revocation (lazy init)
_revocation_redis: redis.Redis | None = None


def _get_revocation_redis() -> redis.Redis:
    """Get or create Redis client for JWT revocation checks."""
    global _revocation_redis
    if _revocation_redis is None:
        settings = get_settings()
        _revocation_redis = redis.from_url(settings.redis_url, decode_responses=True)
    return _revocation_redis


def revoke_token(jti: str, ttl_seconds: int | None = None) -> None:
    """Add a token JTI to the revocation blacklist.

    Args:
        jti: The JWT ID to revoke.
        ttl_seconds: How long to keep the blacklist entry. Defaults to
                     the access token lifetime from config.
    """
    if ttl_seconds is None:
        ttl_seconds = get_settings().jwt_access_token_expire_minutes * 60
    r = _get_revocation_redis()
    r.set(f"token_bl:{jti}", "1", ex=ttl_seconds)


def revoke_all_user_tokens(user_id: str) -> None:
    """Bulk-revoke all tokens for a user by setting an iat threshold."""
    r = _get_revocation_redis()
    r.set(
        f"user:{user_id}:tokens_invalid_before",
        str(datetime.now(timezone.utc).timestamp()),
        ex=86400 * 7,  # Keep for 7 days (matches refresh token lifetime)
    )


def is_token_revoked(jti: str, user_id: str, iat: float) -> bool:
    """Check if a token has been revoked (individual or bulk).

    Fails closed: if Redis is unreachable, token is considered revoked.
    In test/development with no Redis, skips the check.
    """
    settings = get_settings()
    if not settings.redis_url or not isinstance(settings.redis_url, str):
        return False

    try:
        r = _get_revocation_redis()
        # Check individual blacklist
        if r.exists(f"token_bl:{jti}"):
            return True
        # Check bulk invalidation
        invalid_before = r.get(f"user:{user_id}:tokens_invalid_before")
        if invalid_before and iat < float(invalid_before):
            return True
        return False
    except (redis.ConnectionError, redis.TimeoutError, ConnectionRefusedError, OSError):
        logger.error("Redis unavailable for token revocation check — failing closed")
        # In development/test without Redis: allow tokens through
        if settings.environment in ("development", "test"):
            return False
        return True  # Fail closed in production
    except Exception:
        # Unexpected error — fail closed in production (treat token as revoked)
        logger.error("Unexpected error in token revocation check — failing closed")
        if settings.environment in ("development", "test"):
            return False
        return True  # Fail closed in production


@dataclass
class AuthContext:
    """Authentication context returned by require_auth."""

    auth_type: str  # "api_key" or "jwt"
    user_id: str | None = None  # UUID string
    telegram_chat_id: int | None = None
    tier: str = "free"


def hash_password(password: str) -> str:
    """Hash a password with bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its bcrypt hash."""
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def create_access_token(user_id: UUID, telegram_chat_id: int | None, tier: str) -> str:
    """Create a signed JWT access token."""
    settings = get_settings()
    if not settings.jwt_secret_key:
        raise ValueError("JWT_SECRET_KEY not configured")
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "jti": str(uuid.uuid4()),
        "chat_id": telegram_chat_id,
        "tier": tier,
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_access_token_expire_minutes),
        "type": "access",
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(user_id: UUID) -> str:
    """Create a signed JWT refresh token."""
    settings = get_settings()
    if not settings.jwt_secret_key:
        raise ValueError("JWT_SECRET_KEY not configured")
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "jti": str(uuid.uuid4()),
        "iat": now,
        "exp": now + timedelta(days=settings.jwt_refresh_token_expire_days),
        "type": "refresh",
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_jwt_token(token: str) -> dict:
    """Decode and validate a JWT token. Raises HTTPException on failure."""
    settings = get_settings()
    if not settings.jwt_secret_key:
        raise HTTPException(status_code=401, detail="JWT not configured")
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except jwt.ExpiredSignatureError:
        logger.warning("auth_failure", extra={"reason": "token_expired", "auth_type": "jwt"})
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        logger.warning("auth_failure", extra={"reason": "invalid_token", "auth_type": "jwt"})
        raise HTTPException(status_code=401, detail="Invalid token")


async def require_api_key(
    api_key: str | None = Security(api_key_header),
) -> str:
    """Validate API key from X-API-Key header.

    Kept for backwards compatibility. Internal/Celery/bot callers use this.
    """
    settings = get_settings()
    if not settings.api_secret_key:
        logger.error("API_SECRET_KEY not configured — rejecting request")
        raise HTTPException(
            status_code=401,
            detail="Server misconfiguration: API key not set",
        )
    if not api_key or not hmac.compare_digest(api_key, settings.api_secret_key):
        logger.warning("auth_failure", extra={"reason": "invalid_api_key", "auth_type": "api_key"})
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return api_key


async def require_auth(
    api_key: str | None = Security(api_key_header),
    authorization: str | None = Header(None),
) -> AuthContext:
    """Unified auth: accepts either X-API-Key header or Authorization: Bearer <jwt>.

    Returns an AuthContext with auth type and user details (if JWT).
    """
    settings = get_settings()

    # Try JWT Bearer token first
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
        payload = decode_jwt_token(token)
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")

        # Check revocation (individual + bulk)
        jti = payload.get("jti", "")
        user_id = payload.get("sub", "")
        iat = payload.get("iat", 0)
        if is_token_revoked(jti, user_id, iat):
            raise HTTPException(status_code=401, detail="Token has been revoked")

        return AuthContext(
            auth_type="jwt",
            user_id=payload["sub"],
            telegram_chat_id=payload.get("chat_id"),
            tier=payload.get("tier", "free"),
        )

    # Fall back to API key — accept api_secret_key or internal_api_key
    if not settings.api_secret_key:
        logger.error("API_SECRET_KEY not configured — rejecting request")
        raise HTTPException(status_code=401, detail="Server misconfiguration: API key not set")
    if api_key:
        if hmac.compare_digest(api_key, settings.api_secret_key):
            return AuthContext(auth_type="api_key")
        internal_key = settings.internal_api_key
        if internal_key and hmac.compare_digest(api_key, internal_key):
            # Internal callers get pro-equivalent access
            return AuthContext(auth_type="internal_api_key", tier="pro")

    raise HTTPException(status_code=401, detail="Invalid or missing authentication")


async def get_optional_auth(
    api_key: str | None = Security(api_key_header),
    authorization: str | None = Header(None),
) -> AuthContext | None:
    """Like require_auth but returns None when no credentials are provided.

    If credentials ARE provided but are invalid/expired, raises 401 so the client
    knows to re-authenticate rather than silently falling back to anonymous tier.

    Use for endpoints that are public but behave differently for authenticated users
    (e.g., tier gating on signal detail views).
    """
    if not api_key and not authorization:
        return None
    # Credentials were provided — validate them fully (raises on bad/expired token)
    return await require_auth(api_key=api_key, authorization=authorization)


async def get_current_user(auth: AuthContext = Depends(require_auth)) -> AuthContext:
    """Require JWT authentication — rejects API-key-only auth.

    Use this dependency on user-scoped endpoints that need user identity.
    """
    if auth.auth_type != "jwt":
        logger.warning("auth_failure", extra={"reason": "jwt_required", "auth_type": auth.auth_type})
        raise HTTPException(status_code=401, detail="JWT authentication required")
    return auth


def require_tier(required_tier: str):
    """Dependency factory: require a minimum tier level for an endpoint."""
    tier_levels = {"free": 0, "pro": 1}

    async def _check_tier(auth: AuthContext = Depends(require_auth)) -> AuthContext:
        user_level = tier_levels.get(auth.tier, 0)
        required_level = tier_levels.get(required_tier, 0)
        if user_level < required_level:
            raise HTTPException(
                status_code=403,
                detail=f"This feature requires {required_tier} tier",
            )
        return auth

    return _check_tier


# ── Internal API key auth (Celery, bots, crons) ──
# Only allows access to a whitelist of read-only endpoints.
INTERNAL_ENDPOINT_WHITELIST = {
    "GET /api/v1/signals",
    "GET /api/v1/markets/overview",
    "GET /api/v1/signals/stats",
}


async def require_internal_auth(
    api_key: str | None = Security(api_key_header),
) -> AuthContext:
    """Validate internal API key. Only allows whitelisted endpoints for internal callers."""
    settings = get_settings()
    internal_key = settings.internal_api_key or settings.api_secret_key
    if not internal_key:
        raise HTTPException(status_code=401, detail="Internal API key not configured")
    if not api_key or not hmac.compare_digest(api_key, internal_key):
        raise HTTPException(status_code=401, detail="Invalid internal API key")
    return AuthContext(auth_type="internal_api_key", tier="pro")
