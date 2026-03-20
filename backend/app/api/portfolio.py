"""Portfolio/trade endpoints — log trades, view positions, P&L."""

from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.trade import Trade
from app.schemas.p3 import PortfolioSummary, TradeCreate, TradeData

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


@router.get("/trades", response_model=dict)
async def list_trades(
    telegram_chat_id: int,
    symbol: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """List trades for a user, optionally filtered by symbol."""
    query = select(Trade).where(Trade.telegram_chat_id == telegram_chat_id)
    if symbol:
        query = query.where(Trade.symbol.ilike(f"%{symbol}%"))
    query = query.order_by(Trade.created_at.desc()).limit(limit)
    result = await db.execute(query)
    trades = result.scalars().all()
    return {"data": [TradeData.model_validate(t) for t in trades]}


@router.post("/trades", response_model=dict, status_code=201)
async def log_trade(
    payload: TradeCreate,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Log a new trade."""
    trade = Trade(
        telegram_chat_id=payload.telegram_chat_id,
        symbol=payload.symbol.upper().strip(),
        market_type=payload.market_type,
        side=payload.side.lower(),
        quantity=payload.quantity,
        price=payload.price,
        notes=payload.notes,
        signal_id=payload.signal_id,
    )
    db.add(trade)
    await db.flush()
    await db.refresh(trade)
    return {"data": TradeData.model_validate(trade)}


@router.get("/summary", response_model=dict)
async def portfolio_summary(
    telegram_chat_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get aggregated portfolio positions and P&L.

    Calculates net position per symbol from buy/sell trades.
    Current value uses the last trade price as proxy (real-time pricing
    would require a market data lookup).
    """
    result = await db.execute(
        select(
            Trade.symbol,
            Trade.market_type,
            func.sum(
                case(
                    (Trade.side == "buy", Trade.quantity),
                    else_=-Trade.quantity,
                )
            ).label("net_qty"),
            func.sum(
                case(
                    (Trade.side == "buy", Trade.quantity * Trade.price),
                    else_=-Trade.quantity * Trade.price,
                )
            ).label("net_cost"),
            func.max(Trade.price).label("last_price"),
        )
        .where(Trade.telegram_chat_id == telegram_chat_id)
        .group_by(Trade.symbol, Trade.market_type)
    )
    rows = result.all()

    positions = []
    total_invested = Decimal("0")
    current_value = Decimal("0")

    for row in rows:
        net_qty = Decimal(str(row.net_qty or 0))
        net_cost = Decimal(str(row.net_cost or 0))
        last_price = Decimal(str(row.last_price or 0))

        if net_qty <= 0:
            continue  # Position fully closed

        position_value = net_qty * last_price
        avg_price = net_cost / net_qty if net_qty > 0 else Decimal("0")
        pnl = position_value - net_cost
        pnl_pct = float(pnl / net_cost * 100) if net_cost > 0 else 0.0

        positions.append({
            "symbol": row.symbol,
            "market_type": row.market_type,
            "quantity": str(net_qty),
            "avg_price": str(round(avg_price, 4)),
            "current_price": str(last_price),
            "value": str(round(position_value, 2)),
            "pnl": str(round(pnl, 2)),
            "pnl_pct": round(pnl_pct, 2),
        })

        total_invested += net_cost
        current_value += position_value

    total_pnl = current_value - total_invested
    total_pnl_pct = float(total_pnl / total_invested * 100) if total_invested > 0 else 0.0

    return {
        "data": PortfolioSummary(
            total_invested=total_invested,
            current_value=current_value,
            total_pnl=total_pnl,
            total_pnl_pct=round(total_pnl_pct, 2),
            positions=positions,
        )
    }
