"""Alert dispatch Celery tasks — morning brief and evening wrap."""

import logging

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.alert_tasks.morning_brief")
def morning_brief() -> dict:
    """Send morning market brief via Telegram at 8:00 AM IST."""
    logger.info("Generating morning brief")
    # Phase 3: Will call briefing generator + Telegram dispatch
    return {"status": "ok", "message": "Morning brief placeholder — Phase 3"}


@celery_app.task(name="app.tasks.alert_tasks.evening_wrap")
def evening_wrap() -> dict:
    """Send evening market wrap via Telegram at 4:00 PM IST."""
    logger.info("Generating evening wrap")
    # Phase 3: Will call briefing generator + Telegram dispatch
    return {"status": "ok", "message": "Evening wrap placeholder — Phase 3"}
