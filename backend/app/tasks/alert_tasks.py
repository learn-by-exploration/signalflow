"""Alert dispatch Celery tasks — morning brief and evening wrap.

Generates AI briefings and dispatches them to all active Telegram subscribers.
"""

import asyncio
import logging
from typing import Any

from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session

from app.config import get_settings
from app.services.ai_engine.briefing import BriefingGenerator
from app.services.alerts.dispatcher import AlertDispatcher
from app.services.alerts.formatter import format_morning_brief, format_evening_wrap
from app.services.alerts.telegram_bot import send_telegram_message
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


def _get_active_subscribers() -> list[dict]:
    """Fetch all active alert configs from the database."""
    settings = get_settings()
    engine = create_engine(settings.database_url_sync, pool_pre_ping=True)
    try:
        with Session(engine) as session:
            rows = session.execute(
                text(
                    "SELECT telegram_chat_id, markets, min_confidence, "
                    "signal_types, quiet_hours, is_active "
                    "FROM alert_configs WHERE is_active = true"
                )
            ).fetchall()
            return [
                {
                    "telegram_chat_id": r[0],
                    "markets": r[1] if isinstance(r[1], list) else ["stock", "crypto", "forex"],
                    "min_confidence": r[2],
                    "signal_types": r[3] if isinstance(r[3], list) else ["STRONG_BUY", "BUY", "SELL", "STRONG_SELL"],
                    "quiet_hours": r[4],
                    "is_active": r[5],
                }
                for r in rows
            ]
    finally:
        engine.dispose()


def _get_market_summary() -> dict[str, Any]:
    """Fetch a market summary for briefing generation."""
    settings = get_settings()
    engine = create_engine(settings.database_url_sync, pool_pre_ping=True)
    try:
        with Session(engine) as session:
            # Get latest prices for key symbols
            summary: dict[str, Any] = {}
            for symbol in ["RELIANCE.NS", "HDFCBANK.NS", "BTCUSDT", "ETHUSDT", "USD/INR", "EUR/USD"]:
                row = session.execute(
                    text(
                        "SELECT close, timestamp FROM market_data "
                        "WHERE symbol = :sym ORDER BY timestamp DESC LIMIT 1"
                    ),
                    {"sym": symbol},
                ).fetchone()
                if row:
                    summary[symbol] = {"close": str(row[0]), "timestamp": str(row[1])}
            return summary
    finally:
        engine.dispose()


def _get_active_signals_summary() -> str:
    """Fetch and summarize active signals for briefings."""
    settings = get_settings()
    engine = create_engine(settings.database_url_sync, pool_pre_ping=True)
    try:
        with Session(engine) as session:
            rows = session.execute(
                text(
                    "SELECT symbol, signal_type, confidence FROM signals "
                    "WHERE is_active = true ORDER BY confidence DESC LIMIT 5"
                )
            ).fetchall()
            if not rows:
                return "No active signals."
            lines = []
            for r in rows:
                lines.append(f"{r[0]}: {r[1]} ({r[2]}%)")
            return "\n".join(lines)
    finally:
        engine.dispose()


async def _morning_brief_async() -> dict:
    """Generate and dispatch morning brief."""
    briefing = BriefingGenerator()
    market_data = _get_market_summary()
    signals_summary = _get_active_signals_summary()

    brief_text = await briefing.morning_brief(
        market_data=market_data,
        signals_summary=signals_summary,
    )

    formatted = format_morning_brief(brief_text)

    subscribers = _get_active_subscribers()
    dispatcher = AlertDispatcher(send_telegram_message)
    sent = await dispatcher.dispatch_broadcast(formatted, subscribers)

    return {"status": "ok", "sent": sent, "subscribers": len(subscribers)}


async def _evening_wrap_async() -> dict:
    """Generate and dispatch evening wrap."""
    briefing = BriefingGenerator()
    market_data = _get_market_summary()
    signals_summary = _get_active_signals_summary()

    wrap_text = await briefing.evening_wrap(
        performance_data=market_data,
        signal_outcomes=signals_summary,
    )

    formatted = format_evening_wrap(wrap_text)

    subscribers = _get_active_subscribers()
    dispatcher = AlertDispatcher(send_telegram_message)
    sent = await dispatcher.dispatch_broadcast(formatted, subscribers)

    return {"status": "ok", "sent": sent, "subscribers": len(subscribers)}


@celery_app.task(name="app.tasks.alert_tasks.morning_brief")
def morning_brief() -> dict:
    """Send morning market brief via Telegram at 8:00 AM IST."""
    logger.info("Generating morning brief")
    return asyncio.run(_morning_brief_async())


@celery_app.task(name="app.tasks.alert_tasks.evening_wrap")
def evening_wrap() -> dict:
    """Send evening market wrap via Telegram at 4:00 PM IST."""
    logger.info("Generating evening wrap")
    return asyncio.run(_evening_wrap_async())
