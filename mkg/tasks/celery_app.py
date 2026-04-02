# mkg/tasks/celery_app.py
"""Celery application configuration for MKG.

Dummy broker (in-memory) for development. Swap BROKER_URL
to Redis for production.
"""

from celery import Celery

app = Celery(
    "mkg",
    broker="memory://",
    backend="cache+memory://",
)

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)
