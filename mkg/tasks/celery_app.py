# mkg/tasks/celery_app.py
"""Celery application configuration for MKG.

Uses Redis broker when REDIS_URL is set (production), falls back to
in-memory broker for development/testing.
"""

import os

from celery import Celery

_broker = os.environ.get("REDIS_URL", "memory://")
_backend = os.environ.get("REDIS_URL", "cache+memory://")

app = Celery(
    "mkg",
    broker=_broker,
    backend=_backend,
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
