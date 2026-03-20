"""Signal generation Celery tasks."""

import logging

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.signal_tasks.generate_signals")
def generate_signals() -> dict:
    """Generate trading signals from technical + AI analysis."""
    logger.info("Generating signals")
    # Phase 2: Will call SignalGenerator
    return {"status": "ok", "message": "Signal generation placeholder — Phase 2"}


@celery_app.task(name="app.tasks.signal_tasks.resolve_expired")
def resolve_expired() -> dict:
    """Resolve expired signals and update signal history."""
    logger.info("Resolving expired signals")
    # Phase 2: Will check active signals against current prices
    return {"status": "ok", "message": "Resolve placeholder — Phase 2"}
