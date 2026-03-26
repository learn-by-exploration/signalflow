"""Alert configuration endpoints."""

from uuid import UUID as PyUUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import AuthContext, get_current_user
from app.config import get_settings
from app.database import get_db
from app.models.alert_config import AlertConfig
from app.rate_limit import limiter
from app.schemas.alert import AlertConfigCreate, AlertConfigData, AlertConfigUpdate, WatchlistUpdate

router = APIRouter(prefix="/alerts", tags=["alerts"])


def _user_config_filter(user: AuthContext):
    """Build a filter for alert configs belonging to the authenticated user."""
    conditions = []
    if user.user_id:
        uid = PyUUID(user.user_id) if isinstance(user.user_id, str) else user.user_id
        conditions.append(AlertConfig.user_id == uid)
    if user.telegram_chat_id:
        conditions.append(AlertConfig.telegram_chat_id == user.telegram_chat_id)
    if not conditions:
        return AlertConfig.id == None  # noqa: E711
    return or_(*conditions)


@router.get("/config", response_model=dict)
async def get_alert_config(
    user: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get alert preferences for the authenticated user."""
    result = await db.execute(
        select(AlertConfig).where(_user_config_filter(user))
    )
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="Alert config not found")
    return {"data": AlertConfigData.model_validate(config)}


@router.post("/config", response_model=dict, status_code=201)
@limiter.limit("10/minute")
async def create_alert_config(
    request: Request,
    payload: AlertConfigCreate,
    user: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Create a new alert configuration for the authenticated user."""
    # Check for existing config
    existing = await db.execute(
        select(AlertConfig).where(_user_config_filter(user))
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Alert config already exists for this user")

    config = AlertConfig(
        user_id=PyUUID(user.user_id) if isinstance(user.user_id, str) and user.user_id else user.user_id,
        telegram_chat_id=user.telegram_chat_id,
        username=payload.username,
        markets=payload.markets,
        min_confidence=payload.min_confidence,
        signal_types=payload.signal_types,
        quiet_hours=payload.quiet_hours,
    )
    db.add(config)
    await db.flush()
    await db.refresh(config)
    return {"data": AlertConfigData.model_validate(config)}


@router.put("/config/{config_id}", response_model=dict)
async def update_alert_config(
    config_id: PyUUID,
    payload: AlertConfigUpdate,
    user: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Update an existing alert configuration (must belong to user)."""
    result = await db.execute(
        select(AlertConfig).where(AlertConfig.id == config_id).with_for_update()
    )
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="Alert config not found")

    # Ownership check
    is_owner = False
    if user.user_id and config.user_id and str(config.user_id) == str(user.user_id):
        is_owner = True
    if user.telegram_chat_id and config.telegram_chat_id == user.telegram_chat_id:
        is_owner = True
    if not is_owner:
        raise HTTPException(status_code=403, detail="Not your alert config")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(config, field, value)

    await db.flush()
    await db.refresh(config)
    return {"data": AlertConfigData.model_validate(config)}


@router.get("/watchlist", response_model=dict)
async def get_watchlist(
    user: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get the authenticated user's watchlist."""
    result = await db.execute(
        select(AlertConfig).where(_user_config_filter(user))
    )
    config = result.scalar_one_or_none()
    if not config:
        # Auto-create a default config for web users
        config = AlertConfig(
            user_id=PyUUID(user.user_id) if isinstance(user.user_id, str) and user.user_id else user.user_id,
            telegram_chat_id=user.telegram_chat_id,
        )
        db.add(config)
        await db.flush()
        await db.refresh(config)
    watchlist = config.watchlist if isinstance(config.watchlist, list) else []
    return {"data": watchlist}


@router.post("/watchlist", response_model=dict)
async def update_watchlist(
    payload: WatchlistUpdate,
    user: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Add or remove a symbol from the authenticated user's watchlist."""
    result = await db.execute(
        select(AlertConfig).where(_user_config_filter(user))
    )
    config = result.scalar_one_or_none()
    if not config:
        # Auto-create for web users
        config = AlertConfig(
            user_id=PyUUID(user.user_id) if isinstance(user.user_id, str) and user.user_id else user.user_id,
            telegram_chat_id=user.telegram_chat_id,
        )
        db.add(config)
        await db.flush()
        await db.refresh(config)

    watchlist = list(config.watchlist) if isinstance(config.watchlist, list) else []
    symbol_upper = payload.symbol.upper().strip()

    # Validate symbol against tracked list
    if payload.action == "add":
        settings = get_settings()
        all_tracked = set(settings.tracked_stocks + settings.tracked_crypto + settings.tracked_forex)
        if symbol_upper not in all_tracked:
            raise HTTPException(
                status_code=400,
                detail=f"Symbol '{symbol_upper}' is not in the tracked symbols list",
            )

    if payload.action == "add":
        if symbol_upper not in watchlist:
            watchlist.append(symbol_upper)
    elif payload.action == "remove":
        watchlist = [s for s in watchlist if s != symbol_upper]

    config.watchlist = watchlist
    await db.flush()
    await db.refresh(config)
    return {"data": watchlist}
