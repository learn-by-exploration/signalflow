"""Authentication endpoints — register, login, refresh, profile."""

import hashlib
import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID as PyUUID

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import (
    AuthContext,
    create_access_token,
    create_refresh_token,
    decode_jwt_token,
    get_current_user,
    hash_password,
    verify_password,
)
from app.config import get_settings
from app.database import get_db
from app.models.user import RefreshToken, User
from app.rate_limit import limiter
from app.schemas.auth import (
    ChangePasswordRequest,
    DeleteAccountRequest,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserProfile,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

# ── Account lockout constants ──
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION_SECONDS = 900  # 15 minutes
FAILED_LOGIN_KEY_PREFIX = "failed_login:"
LOCKOUT_KEY_PREFIX = "account_locked:"


@router.post("/register", response_model=dict, status_code=201)
@limiter.limit("5/minute")
async def register(
    request: Request,
    payload: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Register a new user account."""
    # Check for existing user
    result = await db.execute(select(User).where(User.email == payload.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")

    # Check telegram_chat_id uniqueness if provided
    if payload.telegram_chat_id:
        result = await db.execute(
            select(User).where(User.telegram_chat_id == payload.telegram_chat_id)
        )
        if result.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Telegram chat ID already linked")

    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        telegram_chat_id=payload.telegram_chat_id,
        tier="free",
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)

    # Generate tokens
    settings = get_settings()
    access_token = create_access_token(user.id, user.telegram_chat_id, user.tier)
    refresh_token = create_refresh_token(user.id)

    # Store refresh token hash
    token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
    db_token = RefreshToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.jwt_refresh_token_expire_days),
    )
    db.add(db_token)

    return {
        "data": {
            "user": UserProfile.model_validate(user).model_dump(mode="json"),
            "tokens": TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=settings.jwt_access_token_expire_minutes * 60,
            ).model_dump(),
        }
    }


@router.post("/login", response_model=dict)
@limiter.limit("10/minute")
async def login(
    request: Request,
    payload: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Authenticate and receive JWT tokens."""
    settings = get_settings()

    # ── Account lockout check via Redis ──
    lockout_key = f"{LOCKOUT_KEY_PREFIX}{payload.email}"
    failed_key = f"{FAILED_LOGIN_KEY_PREFIX}{payload.email}"
    try:
        redis_client = aioredis.from_url(settings.redis_url)
        is_locked = await redis_client.get(lockout_key)
        if is_locked:
            ttl = await redis_client.ttl(lockout_key)
            logger.warning("Login attempt on locked account: %s", payload.email)
            raise HTTPException(
                status_code=429,
                detail=f"Account temporarily locked due to too many failed attempts. Try again in {max(ttl, 1)} seconds.",
            )
    except (ConnectionError, OSError, Exception) as exc:
        if isinstance(exc, HTTPException):
            raise
        redis_client = None  # Redis unavailable — skip lockout check

    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(payload.password, user.password_hash):
        # ── Track failed attempt ──
        if redis_client:
            try:
                attempts = await redis_client.incr(failed_key)
                await redis_client.expire(failed_key, LOCKOUT_DURATION_SECONDS)
                if attempts >= MAX_FAILED_ATTEMPTS:
                    await redis_client.setex(lockout_key, LOCKOUT_DURATION_SECONDS, "1")
                    await redis_client.delete(failed_key)
                    logger.warning(
                        "Account locked after %d failed attempts: %s",
                        MAX_FAILED_ATTEMPTS,
                        payload.email,
                    )
                    raise HTTPException(
                        status_code=429,
                        detail=f"Account temporarily locked after {MAX_FAILED_ATTEMPTS} failed attempts. Try again in {LOCKOUT_DURATION_SECONDS // 60} minutes.",
                    )
            except (ConnectionError, OSError, Exception) as exc:
                if isinstance(exc, HTTPException):
                    raise
                pass  # Redis down — still raise invalid credentials
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")

    # ── Clear failed attempts on success ──
    if redis_client:
        try:
            await redis_client.delete(failed_key)
            await redis_client.delete(lockout_key)
        except (ConnectionError, OSError, Exception):
            pass

    # Generate tokens
    settings = get_settings()
    access_token = create_access_token(user.id, user.telegram_chat_id, user.tier)
    refresh_token = create_refresh_token(user.id)

    # Store refresh token hash
    token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
    db_token = RefreshToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.jwt_refresh_token_expire_days),
    )
    db.add(db_token)

    return {
        "data": {
            "user": UserProfile.model_validate(user).model_dump(mode="json"),
            "tokens": TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=settings.jwt_access_token_expire_minutes * 60,
            ).model_dump(),
        }
    }


@router.post("/refresh", response_model=dict)
@limiter.limit("20/minute")
async def refresh(
    request: Request,
    payload: RefreshRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Exchange a valid refresh token for a new token pair (token rotation)."""
    # Decode refresh token
    decoded = decode_jwt_token(payload.refresh_token)
    if decoded.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid token type")

    # Verify refresh token exists and is not revoked
    token_hash = hashlib.sha256(payload.refresh_token.encode()).hexdigest()
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.is_revoked.is_(False),
        )
    )
    db_token = result.scalar_one_or_none()
    if not db_token:
        raise HTTPException(status_code=401, detail="Refresh token revoked or not found")

    # Revoke old refresh token (rotation)
    db_token.is_revoked = True

    # Fetch user
    user_id = PyUUID(decoded["sub"]) if isinstance(decoded["sub"], str) else decoded["sub"]
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or deactivated")

    # Issue new token pair
    settings = get_settings()
    new_access = create_access_token(user.id, user.telegram_chat_id, user.tier)
    new_refresh = create_refresh_token(user.id)

    new_token_hash = hashlib.sha256(new_refresh.encode()).hexdigest()
    new_db_token = RefreshToken(
        user_id=user.id,
        token_hash=new_token_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.jwt_refresh_token_expire_days),
    )
    db.add(new_db_token)

    return {
        "data": {
            "tokens": TokenResponse(
                access_token=new_access,
                refresh_token=new_refresh,
                expires_in=settings.jwt_access_token_expire_minutes * 60,
            ).model_dump(),
        }
    }


@router.post("/logout", response_model=dict)
async def logout(
    payload: RefreshRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Revoke a refresh token."""
    token_hash = hashlib.sha256(payload.refresh_token.encode()).hexdigest()
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    db_token = result.scalar_one_or_none()
    if db_token:
        db_token.is_revoked = True
    return {"data": "logged_out"}


@router.get("/profile", response_model=dict)
async def get_profile(
    user: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get current user's profile."""
    user_id = PyUUID(user.user_id) if isinstance(user.user_id, str) else user.user_id
    result = await db.execute(select(User).where(User.id == user_id))
    db_user = result.scalar_one_or_none()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"data": UserProfile.model_validate(db_user).model_dump(mode="json")}


@router.post("/logout-all", response_model=dict)
async def logout_all(
    user: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Revoke ALL refresh tokens for the current user (logout everywhere)."""
    user_id = PyUUID(user.user_id) if isinstance(user.user_id, str) else user.user_id
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.user_id == user_id,
            RefreshToken.is_revoked.is_(False),
        )
    )
    tokens = result.scalars().all()
    for token in tokens:
        token.is_revoked = True
    logger.info("Revoked %d refresh tokens for user %s", len(tokens), user_id)
    return {"data": {"revoked_count": len(tokens)}}


@router.put("/password", response_model=dict)
async def change_password(
    payload: ChangePasswordRequest,
    user: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Change the current user's password."""
    user_id = PyUUID(user.user_id) if isinstance(user.user_id, str) else user.user_id
    result = await db.execute(select(User).where(User.id == user_id))
    db_user = result.scalar_one_or_none()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    if not verify_password(payload.current_password, db_user.password_hash):
        raise HTTPException(status_code=401, detail="Current password is incorrect")

    if payload.current_password == payload.new_password:
        raise HTTPException(status_code=400, detail="New password must be different from current password")

    db_user.password_hash = hash_password(payload.new_password)
    logger.info("Password changed for user %s", user_id)
    return {"data": "password_changed"}


@router.delete("/account", response_model=dict)
async def delete_account(
    payload: DeleteAccountRequest,
    user: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Permanently delete the current user's account and all associated data."""
    if not payload.confirm:
        raise HTTPException(status_code=400, detail="Must confirm account deletion")

    user_id = PyUUID(user.user_id) if isinstance(user.user_id, str) else user.user_id
    result = await db.execute(select(User).where(User.id == user_id))
    db_user = result.scalar_one_or_none()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    if not verify_password(payload.password, db_user.password_hash):
        raise HTTPException(status_code=401, detail="Password is incorrect")

    # Cascade delete associated data
    from app.models.alert_config import AlertConfig
    from app.models.price_alert import PriceAlert
    from app.models.trade import Trade

    # Delete refresh tokens
    tokens_result = await db.execute(
        select(RefreshToken).where(RefreshToken.user_id == user_id)
    )
    for token in tokens_result.scalars().all():
        await db.delete(token)

    # Delete alert configs
    configs_result = await db.execute(
        select(AlertConfig).where(AlertConfig.user_id == user_id)
    )
    for config in configs_result.scalars().all():
        await db.delete(config)

    # Delete price alerts
    alerts_result = await db.execute(
        select(PriceAlert).where(PriceAlert.user_id == user_id)
    )
    for alert in alerts_result.scalars().all():
        await db.delete(alert)

    # Delete trades
    trades_result = await db.execute(
        select(Trade).where(Trade.user_id == user_id)
    )
    for trade in trades_result.scalars().all():
        await db.delete(trade)

    # Delete the user
    await db.delete(db_user)

    logger.info("Account deleted for user %s (%s)", user_id, db_user.email)
    return {"data": "account_deleted"}
