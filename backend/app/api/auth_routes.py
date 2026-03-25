"""Authentication endpoints — register, login, refresh, profile."""

import hashlib
import logging
from datetime import datetime, timedelta, timezone

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
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserProfile,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


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
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")

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
    user_id = decoded["sub"]
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
    result = await db.execute(select(User).where(User.id == user.user_id))
    db_user = result.scalar_one_or_none()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"data": UserProfile.model_validate(db_user).model_dump(mode="json")}
