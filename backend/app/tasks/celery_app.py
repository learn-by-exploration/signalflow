"""Celery application configuration."""

from celery import Celery

from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "signalflow",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "app.tasks.data_tasks",
        "app.tasks.analysis_tasks",
        "app.tasks.ai_tasks",
        "app.tasks.signal_tasks",
        "app.tasks.alert_tasks",
        "app.tasks.price_alert_tasks",
        "app.tasks.backtest_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_soft_time_limit=300,       # 5 min soft limit (raises SoftTimeLimitExceeded)
    task_time_limit=600,            # 10 min hard kill
    worker_max_tasks_per_child=100, # Restart worker after 100 tasks to prevent memory leaks
)

# Load beat schedule
from app.tasks.scheduler import CELERY_BEAT_SCHEDULE  # noqa: E402

celery_app.conf.beat_schedule = CELERY_BEAT_SCHEDULE
