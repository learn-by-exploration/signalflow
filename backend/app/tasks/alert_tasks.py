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
from app.services.alerts.formatter import format_morning_brief, format_evening_wrap, format_weekly_digest
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


@celery_app.task(
    name="app.tasks.alert_tasks.morning_brief",
    bind=True,
    autoretry_for=(ConnectionError, TimeoutError),
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
    max_retries=3,
)
def morning_brief(self) -> dict:
    """Send morning market brief via Telegram at 8:00 AM IST."""
    logger.info("Generating morning brief")
    return asyncio.run(_morning_brief_async())


@celery_app.task(
    name="app.tasks.alert_tasks.evening_wrap",
    bind=True,
    autoretry_for=(ConnectionError, TimeoutError),
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
    max_retries=3,
)
def evening_wrap(self) -> dict:
    """Send evening market wrap via Telegram at 4:00 PM IST."""
    logger.info("Generating evening wrap")
    return asyncio.run(_evening_wrap_async())


def _get_weekly_stats() -> dict:
    """Fetch signal resolution stats for the past 7 days."""
    settings = get_settings()
    engine = create_engine(settings.database_url_sync, pool_pre_ping=True)
    try:
        with Session(engine) as session:
            rows = session.execute(
                text(
                    "SELECT sh.outcome, sh.return_pct, s.symbol "
                    "FROM signal_history sh "
                    "JOIN signals s ON sh.signal_id = s.id "
                    "WHERE sh.resolved_at >= NOW() - INTERVAL '7 days' "
                    "AND sh.outcome != 'pending'"
                )
            ).fetchall()

            if not rows:
                return {"total": 0}

            hit_target = sum(1 for r in rows if r[0] == "hit_target")
            hit_stop = sum(1 for r in rows if r[0] == "hit_stop")
            expired = sum(1 for r in rows if r[0] == "expired")
            returns = [float(r[1]) for r in rows if r[1] is not None]
            avg_return = sum(returns) / len(returns) if returns else 0.0
            resolved = hit_target + hit_stop
            win_rate = (hit_target / resolved * 100) if resolved > 0 else 0.0

            # Top winner / loser
            with_returns = [(r[2], float(r[1])) for r in rows if r[1] is not None]
            top_winner = None
            top_loser = None
            if with_returns:
                best = max(with_returns, key=lambda x: x[1])
                top_winner = {"symbol": best[0], "return_pct": best[1]}
                worst = min(with_returns, key=lambda x: x[1])
                top_loser = {"symbol": worst[0], "return_pct": worst[1]}

            return {
                "total": len(rows),
                "hit_target": hit_target,
                "hit_stop": hit_stop,
                "expired": expired,
                "win_rate": win_rate,
                "avg_return_pct": avg_return,
                "top_winner": top_winner,
                "top_loser": top_loser,
            }
    finally:
        engine.dispose()


async def _weekly_digest_async() -> dict:
    """Generate and dispatch weekly digest."""
    stats = _get_weekly_stats()
    formatted = format_weekly_digest(stats)

    subscribers = _get_active_subscribers()
    dispatcher = AlertDispatcher(send_telegram_message)
    sent = await dispatcher.dispatch_broadcast(formatted, subscribers)

    return {"status": "ok", "sent": sent, "subscribers": len(subscribers)}


@celery_app.task(
    name="app.tasks.alert_tasks.weekly_digest",
    bind=True,
    autoretry_for=(ConnectionError, TimeoutError),
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
    max_retries=3,
)
def weekly_digest(self) -> dict:
    """Send weekly performance digest every Sunday at 6:00 PM IST."""
    logger.info("Generating weekly digest")
    return asyncio.run(_weekly_digest_async())


@celery_app.task(name="app.tasks.alert_tasks.pipeline_health_check")
def pipeline_health_check() -> dict:
    """Alert admin if signal pipeline has stopped producing.

    Checks the most recent signal timestamp and sends a Telegram alert
    to the admin if no signal has been generated in 30+ minutes.
    """
    settings = get_settings()
    engine = create_engine(settings.database_url_sync, pool_pre_ping=True)
    try:
        with Session(engine) as session:
            row = session.execute(
                text("SELECT MAX(created_at) FROM signals")
            ).fetchone()

            if row and row[0]:
                from datetime import datetime, timezone, timedelta

                last_signal_time = row[0]
                if last_signal_time.tzinfo is None:
                    last_signal_time = last_signal_time.replace(tzinfo=timezone.utc)
                age_minutes = (datetime.now(timezone.utc) - last_signal_time).total_seconds() / 60

                if age_minutes > 30:
                    admin_chat_id = settings.telegram_default_chat_id
                    if admin_chat_id:
                        msg = (
                            f"⚠️ Pipeline Stale Alert\n\n"
                            f"No new signal generated in {int(age_minutes)} minutes.\n"
                            f"Last signal: {last_signal_time.strftime('%Y-%m-%d %H:%M UTC')}\n\n"
                            f"Check Celery worker and data ingestion tasks."
                        )
                        asyncio.run(send_telegram_message(int(admin_chat_id), msg))
                    return {"status": "stale", "minutes_since_last": int(age_minutes)}

                return {"status": "healthy", "minutes_since_last": int(age_minutes)}

            return {"status": "no_signals", "minutes_since_last": -1}
    finally:
        engine.dispose()
