"""Portfolio/trade endpoints — log trades, view positions, P&L."""

from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import func, select, case, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import AuthContext, get_current_user
from app.database import get_db
from app.models.market_data import MarketData
from app.models.trade import Trade
from app.rate_limit import limiter
from app.schemas.p3 import CurrencyBreakdown, PortfolioSummary, TradeCreate, TradeData

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


def _user_trade_filter(user: AuthContext):
    """Build a filter for trades belonging to the authenticated user."""
    conditions = []
    if user.user_id:
        uid = UUID(user.user_id) if isinstance(user.user_id, str) else user.user_id
        conditions.append(Trade.user_id == uid)
    if user.telegram_chat_id:
        conditions.append(Trade.telegram_chat_id == user.telegram_chat_id)
    if not conditions:
        # No identity available — match nothing
        return Trade.id == None  # noqa: E711
    return or_(*conditions)


@router.get("/trades", response_model=dict)
async def list_trades(
    user: AuthContext = Depends(get_current_user),
    symbol: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """List trades for the authenticated user, optionally filtered by symbol."""
    query = select(Trade).where(_user_trade_filter(user))
    if symbol:
        # Escape SQL LIKE wildcards to prevent pattern injection
        safe_symbol = symbol.replace("%", "").replace("_", "").strip()
        if safe_symbol:
            query = query.where(Trade.symbol.ilike(f"%{safe_symbol}%"))
    query = query.order_by(Trade.created_at.desc()).limit(limit)
    result = await db.execute(query)
    trades = result.scalars().all()
    return {"data": [TradeData.model_validate(t) for t in trades]}


@router.post("/trades", response_model=dict, status_code=201)
@limiter.limit("30/minute")
async def log_trade(
    request: Request,
    payload: TradeCreate,
    user: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Log a new trade for the authenticated user."""
    user_uuid = UUID(user.user_id) if user.user_id else None
    trade = Trade(
        user_id=user_uuid,
        telegram_chat_id=user.telegram_chat_id,
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
    user: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get aggregated portfolio positions and P&L.

    Calculates net position per symbol from buy/sell trades.
    Current value uses the latest close price from market_data for accurate P&L.
    Falls back to the last trade price if no market data exists for a symbol.
    """
    # Step 1: Aggregate trades per symbol
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
            func.max(Trade.price).label("last_trade_price"),
        )
        .where(_user_trade_filter(user))
        .group_by(Trade.symbol, Trade.market_type)
    )
    rows = result.all()

    # Step 2: Fetch latest market prices for all symbols in one query
    symbols = [row.symbol for row in rows]
    live_prices: dict[str, Decimal] = {}
    if symbols:
        # Subquery to get max timestamp per symbol
        latest_ts = (
            select(
                MarketData.symbol,
                func.max(MarketData.timestamp).label("max_ts"),
            )
            .where(MarketData.symbol.in_(symbols))
            .group_by(MarketData.symbol)
            .subquery()
        )
        price_result = await db.execute(
            select(MarketData.symbol, MarketData.close)
            .join(
                latest_ts,
                (MarketData.symbol == latest_ts.c.symbol)
                & (MarketData.timestamp == latest_ts.c.max_ts),
            )
        )
        for price_row in price_result.all():
            live_prices[price_row.symbol] = price_row.close

    positions = []
    total_invested = Decimal("0")
    current_value = Decimal("0")

    # Per-currency accumulators
    currency_map = {"stock": "INR", "crypto": "USD", "forex": "USD"}
    currency_totals: dict[str, dict] = {}

    for row in rows:
        net_qty = Decimal(str(row.net_qty or 0))
        net_cost = Decimal(str(row.net_cost or 0))
        # Use live market price; fall back to last trade price
        current_price = live_prices.get(row.symbol, Decimal(str(row.last_trade_price or 0)))

        if net_qty <= 0:
            continue  # Position fully closed

        position_value = net_qty * current_price
        avg_price = net_cost / net_qty if net_qty > 0 else Decimal("0")
        pnl = position_value - net_cost
        pnl_pct = float(pnl / net_cost * 100) if net_cost > 0 else 0.0

        positions.append({
            "symbol": row.symbol,
            "market_type": row.market_type,
            "quantity": str(net_qty),
            "avg_price": str(round(avg_price, 4)),
            "current_price": str(current_price),
            "value": str(round(position_value, 2)),
            "pnl": str(round(pnl, 2)),
            "pnl_pct": round(pnl_pct, 2),
        })

        total_invested += net_cost
        current_value += position_value

        # Accumulate per-currency
        currency = currency_map.get(row.market_type, "USD")
        key = f"{currency}:{row.market_type}"
        if key not in currency_totals:
            currency_totals[key] = {
                "currency": currency,
                "market_type": row.market_type,
                "invested": Decimal("0"),
                "current_value": Decimal("0"),
            }
        currency_totals[key]["invested"] += net_cost
        currency_totals[key]["current_value"] += position_value

    total_pnl = current_value - total_invested
    total_pnl_pct = float(total_pnl / total_invested * 100) if total_invested > 0 else 0.0

    # Build per-currency breakdowns
    by_currency = []
    for ct in currency_totals.values():
        ct_pnl = ct["current_value"] - ct["invested"]
        ct_pnl_pct = float(ct_pnl / ct["invested"] * 100) if ct["invested"] > 0 else 0.0
        by_currency.append(CurrencyBreakdown(
            currency=ct["currency"],
            market_type=ct["market_type"],
            invested=ct["invested"],
            current_value=ct["current_value"],
            pnl=ct_pnl,
            pnl_pct=round(ct_pnl_pct, 2),
        ))

    return {
        "data": PortfolioSummary(
            total_invested=total_invested,
            current_value=current_value,
            total_pnl=total_pnl,
            total_pnl_pct=round(total_pnl_pct, 2),
            positions=positions,
            by_currency=by_currency,
        )
    }
