"""Alert configuration endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.alert_config import AlertConfig
from app.schemas.alert import AlertConfigCreate, AlertConfigData, AlertConfigUpdate, WatchlistUpdate

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("/config", response_model=dict)
async def get_alert_config(
    telegram_chat_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get alert preferences by Telegram chat ID."""
    result = await db.execute(
        select(AlertConfig).where(AlertConfig.telegram_chat_id == telegram_chat_id)
    )
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="Alert config not found")
    return {"data": AlertConfigData.model_validate(config)}


@router.post("/config", response_model=dict, status_code=201)
async def create_alert_config(
    payload: AlertConfigCreate,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Create a new alert configuration."""
    config = AlertConfig(
        telegram_chat_id=payload.telegram_chat_id,
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
    config_id: UUID,
    payload: AlertConfigUpdate,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Update an existing alert configuration."""
    result = await db.execute(select(AlertConfig).where(AlertConfig.id == config_id))
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="Alert config not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(config, field, value)

    await db.flush()
    await db.refresh(config)
    return {"data": AlertConfigData.model_validate(config)}


@router.get("/watchlist", response_model=dict)
async def get_watchlist(
    telegram_chat_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get a user's watchlist by chat ID."""
    result = await db.execute(
        select(AlertConfig).where(AlertConfig.telegram_chat_id == telegram_chat_id)
    )
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="Alert config not found")
    watchlist = config.watchlist if isinstance(config.watchlist, list) else []
    return {"data": watchlist}


@router.post("/watchlist", response_model=dict)
async def update_watchlist(
    telegram_chat_id: int,
    payload: WatchlistUpdate,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Add or remove a symbol from a user's watchlist."""
    result = await db.execute(
        select(AlertConfig).where(AlertConfig.telegram_chat_id == telegram_chat_id)
    )
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="Alert config not found")

    watchlist = list(config.watchlist) if isinstance(config.watchlist, list) else []
    symbol_upper = payload.symbol.upper().strip()

    if payload.action == "add":
        if symbol_upper not in watchlist:
            watchlist.append(symbol_upper)
    elif payload.action == "remove":
        watchlist = [s for s in watchlist if s != symbol_upper]
    else:
        raise HTTPException(status_code=400, detail="action must be 'add' or 'remove'")

    config.watchlist = watchlist
    await db.flush()
    await db.refresh(config)
    return {"data": watchlist}
