"""Technical analysis Celery tasks."""

import logging

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.analysis_tasks.run_analysis")
def run_analysis() -> dict:
    """Run technical indicators on latest market data for all tracked symbols."""
    logger.info("Running technical analysis")
    # Phase 2: Will call TechnicalAnalyzer for each symbol
    return {"status": "ok", "message": "Analysis placeholder — Phase 2"}
