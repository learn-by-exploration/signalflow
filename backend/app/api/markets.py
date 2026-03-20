"""Market overview endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.market_data import MarketData
from app.schemas.market import MarketOverviewResponse, MarketSnapshot

router = APIRouter(prefix="/markets", tags=["markets"])


@router.get("/overview", response_model=MarketOverviewResponse)
async def market_overview(db: AsyncSession = Depends(get_db)) -> MarketOverviewResponse:
    """Get live market snapshot across all three markets."""
    result: dict[str, list[MarketSnapshot]] = {"stocks": [], "crypto": [], "forex": []}

    for market_type, key in [("stock", "stocks"), ("crypto", "crypto"), ("forex", "forex")]:
        # Get the latest data point per symbol for this market type using a subquery
        latest_subq = (
            select(
                MarketData.symbol,
                func.max(MarketData.timestamp).label("max_ts"),
            )
            .where(MarketData.market_type == market_type)
            .group_by(MarketData.symbol)
            .subquery()
        )

        query = select(MarketData).join(
            latest_subq,
            (MarketData.symbol == latest_subq.c.symbol)
            & (MarketData.timestamp == latest_subq.c.max_ts),
        )

        rows = await db.execute(query)
        for row in rows.scalars().all():
            result[key].append(
                MarketSnapshot(
                    symbol=row.symbol,
                    price=row.close,
                    change_pct=(row.close - row.open) / row.open * 100 if row.open else 0,
                    volume=row.volume,
                    market_type=row.market_type,
                )
            )

    return MarketOverviewResponse(data=result)
