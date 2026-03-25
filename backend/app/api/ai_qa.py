"""AI Q&A endpoint — ask Claude about a symbol."""

import logging

import httpx
from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models.market_data import MarketData
from app.models.signal import Signal
from app.rate_limit import limiter
from app.schemas.p3 import AskQuestion
from app.services.ai_engine.cost_tracker import CostTracker
from app.services.ai_engine.prompts import SYMBOL_QA_PROMPT
from app.services.ai_engine.sanitizer import sanitize_question

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/ask", response_model=dict)
@limiter.limit("5/minute")
async def ask_about_symbol(
    request: Request,
    payload: AskQuestion,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Ask an AI-powered question about a specific symbol.

    Uses Claude to answer based on available market data and active signals.
    """
    settings = get_settings()
    cost_tracker = CostTracker()
    symbol = payload.symbol.upper().strip()

    # Normalize Indian stock symbols: try both with and without .NS suffix
    query_symbols = [symbol]
    if not symbol.endswith(".NS") and "/" not in symbol and not symbol.endswith("USDT"):
        query_symbols.append(f"{symbol}.NS")
    elif symbol.endswith(".NS"):
        query_symbols.append(symbol.replace(".NS", ""))

    # Gather context: latest market data (ORM query)
    market_result = await db.execute(
        select(MarketData.close, MarketData.high, MarketData.low, MarketData.volume, MarketData.timestamp)
        .where(MarketData.symbol.in_(query_symbols))
        .order_by(MarketData.timestamp.desc())
        .limit(1)
    )
    md = market_result.first()
    market_data = (
        f"Price: {md.close}, High: {md.high}, Low: {md.low}, Volume: {md.volume}, As of: {md.timestamp}"
        if md
        else "No recent market data available."
    )

    # Gather context: active signals (ORM query)
    sig_result = await db.execute(
        select(Signal.signal_type, Signal.confidence, Signal.current_price, Signal.target_price, Signal.stop_loss)
        .where(Signal.symbol.in_(query_symbols), Signal.is_active.is_(True))
        .order_by(Signal.created_at.desc())
        .limit(3)
    )
    sigs = sig_result.all()
    if sigs:
        sig_lines = [
            f"{r.signal_type} ({r.confidence}%) — Price: {r.current_price}, Target: {r.target_price}, Stop: {r.stop_loss}"
            for r in sigs
        ]
        signals_info = "\n".join(sig_lines)
    else:
        signals_info = "No active signals for this symbol."

    # Check budget
    if not cost_tracker.is_budget_available():
        return {
            "data": {
                "answer": (
                    f"AI budget is currently exhausted for the month. "
                    f"Here's what I know: {market_data}. {signals_info}"
                ),
                "source": "fallback",
            }
        }

    # Determine market type from symbol
    market_type = "stock"
    if symbol.endswith("USDT") or symbol in ("BTC", "ETH", "SOL"):
        market_type = "crypto"
    elif "/" in symbol:
        market_type = "forex"

    prompt = SYMBOL_QA_PROMPT.format(
        symbol=symbol,
        market_type=market_type,
        market_data=market_data,
        signals_info=signals_info,
        question=sanitize_question(payload.question),
    )

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": settings.anthropic_api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": settings.claude_model,
                    "max_tokens": 300,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
            resp.raise_for_status()
            data = resp.json()

        usage = data.get("usage", {})
        cost_tracker.record_usage(
            input_tokens=usage.get("input_tokens", 0),
            output_tokens=usage.get("output_tokens", 0),
            task_type="symbol_qa",
            symbol=symbol,
        )

        answer = data["content"][0]["text"].strip()
        return {"data": {"answer": answer, "source": "claude"}}

    except Exception as exc:
        safe_msg = str(exc)
        if settings.anthropic_api_key:
            safe_msg = safe_msg.replace(settings.anthropic_api_key, "[REDACTED]")
        logger.error("Claude API error for symbol Q&A %s: %s", symbol, safe_msg)
        return {
            "data": {
                "answer": (
                    f"I couldn't analyze {symbol} right now. "
                    f"Here's the raw data: {market_data}. {signals_info}"
                ),
                "source": "fallback",
            }
        }
