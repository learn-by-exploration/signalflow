"""AI Q&A endpoint — ask Claude about a symbol."""

import logging

import httpx
from fastapi import APIRouter, Depends, Request
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.rate_limit import limiter
from app.schemas.p3 import AskQuestion
from app.services.ai_engine.cost_tracker import CostTracker
from app.services.ai_engine.prompts import SYMBOL_QA_PROMPT

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

    # Gather context: latest market data
    market_row = await db.execute(
        text(
            "SELECT close, high, low, volume, timestamp FROM market_data "
            "WHERE symbol = :sym ORDER BY timestamp DESC LIMIT 1"
        ),
        {"sym": symbol},
    )
    md = market_row.fetchone()
    market_data = (
        f"Price: {md[0]}, High: {md[1]}, Low: {md[2]}, Volume: {md[3]}, As of: {md[4]}"
        if md
        else "No recent market data available."
    )

    # Gather context: active signals
    sig_rows = await db.execute(
        text(
            "SELECT signal_type, confidence, current_price, target_price, stop_loss "
            "FROM signals WHERE symbol = :sym AND is_active = true "
            "ORDER BY created_at DESC LIMIT 3"
        ),
        {"sym": symbol},
    )
    sigs = sig_rows.fetchall()
    if sigs:
        sig_lines = [
            f"{r[0]} ({r[1]}%) — Price: {r[2]}, Target: {r[3]}, Stop: {r[4]}"
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
        question=payload.question,
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

    except Exception:
        logger.exception("Claude API error for symbol Q&A: %s", symbol)
        return {
            "data": {
                "answer": (
                    f"I couldn't analyze {symbol} right now. "
                    f"Here's the raw data: {market_data}. {signals_info}"
                ),
                "source": "fallback",
            }
        }
