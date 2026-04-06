"""Price alert monitoring Celery task.

Checks active price alerts against latest market data and triggers
Telegram notifications when thresholds are crossed.
"""

import asyncio
import logging
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import create_engine, text, update
from sqlalchemy.orm import Session

from app.config import get_settings
from app.services.alerts.telegram_bot import send_telegram_message
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


def _check_alerts_sync() -> list[dict]:
    """Check all active, untriggered price alerts against latest prices.

    Uses atomic UPDATE...WHERE to prevent duplicate triggers when multiple
    workers check the same alert concurrently.

    Returns list of triggered alerts with details for notification.
    """
    settings = get_settings()
    engine = create_engine(settings.database_url_sync, pool_pre_ping=True)
    triggered = []

    try:
        with Session(engine) as session:
            # Fetch active, untriggered alerts
            alerts = session.execute(
                text(
                    "SELECT pa.id, pa.telegram_chat_id, pa.symbol, pa.market_type, "
                    "pa.condition, pa.threshold "
                    "FROM price_alerts pa "
                    "WHERE pa.is_active = true AND pa.is_triggered = false"
                )
            ).fetchall()

            if not alerts:
                return []

            for alert in alerts:
                alert_id, chat_id, symbol, market_type, condition, threshold = alert

                # Get latest price for this symbol
                price_row = session.execute(
                    text(
                        "SELECT close FROM market_data "
                        "WHERE symbol = :sym ORDER BY timestamp DESC LIMIT 1"
                    ),
                    {"sym": symbol},
                ).fetchone()

                if not price_row:
                    continue

                current_price = Decimal(str(price_row[0]))
                threshold_d = Decimal(str(threshold))

                should_trigger = (
                    (condition == "above" and current_price >= threshold_d)
                    or (condition == "below" and current_price <= threshold_d)
                )

                if should_trigger:
                    # Atomic UPDATE with WHERE is_triggered=false to prevent double-trigger
                    result = session.execute(
                        text(
                            "UPDATE price_alerts SET is_triggered = true, "
                            "triggered_at = :now "
                            "WHERE id = :aid AND is_triggered = false "
                            "RETURNING id"
                        ),
                        {"now": datetime.now(timezone.utc), "aid": str(alert_id)},
                    )
                    # Only proceed if WE were the one to mark it triggered
                    if result.fetchone() is not None:
                        triggered.append({
                            "chat_id": chat_id,
                            "symbol": symbol,
                            "market_type": market_type,
                            "condition": condition,
                            "threshold": str(threshold),
                            "current_price": str(current_price),
                        })

            if triggered:
                session.commit()

    finally:
        engine.dispose()

    return triggered


async def _notify_triggered_alerts(triggered: list[dict]) -> int:
    """Send Telegram notifications for triggered price alerts."""
    sent = 0
    for alert in triggered:
        emoji = "📈" if alert["condition"] == "above" else "📉"
        symbol = alert["symbol"].replace(".NS", "").replace("USDT", "")
        msg = (
            f"{emoji} Price Alert Triggered!\n\n"
            f"{symbol} is now {alert['condition']} {alert['threshold']}\n"
            f"Current price: {alert['current_price']}\n\n"
            f"Set new alerts with /alert"
        )
        try:
            await send_telegram_message(alert["chat_id"], msg)
            sent += 1
        except Exception:
            logger.exception("Failed to send price alert to chat_id=%s", alert["chat_id"])
    return sent


@celery_app.task(
    name="app.tasks.price_alert_tasks.check_price_alerts",
    bind=True,
    autoretry_for=(ConnectionError,),
    retry_backoff=True,
    retry_backoff_max=60,
    retry_jitter=True,
    max_retries=2,
)
def check_price_alerts(self) -> dict:
    """Check all price alerts and send notifications for triggered ones."""
    logger.info("Checking price alerts")
    triggered = _check_alerts_sync()
    if triggered:
        sent = asyncio.run(_notify_triggered_alerts(triggered))
        logger.info("Triggered %d price alerts, sent %d notifications", len(triggered), sent)
        return {"triggered": len(triggered), "sent": sent}
    return {"triggered": 0, "sent": 0}
