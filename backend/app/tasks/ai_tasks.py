"""AI sentiment analysis Celery tasks."""

import logging

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.ai_tasks.run_sentiment")
def run_sentiment() -> dict:
    """Run Claude AI sentiment analysis on recent news for all tracked symbols."""
    logger.info("Running sentiment analysis")
    # Phase 2: Will call AISentimentEngine
    return {"status": "ok", "message": "Sentiment placeholder — Phase 2"}
