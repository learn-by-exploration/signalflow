# mkg/tasks/scheduler.py
"""Celery Beat schedule for MKG tasks.

Matches the SignalFlow scheduling pattern.
"""

from celery.schedules import crontab

MKG_BEAT_SCHEDULE = {
    # ── News Ingestion ──
    "mkg-fetch-news": {
        "task": "mkg.tasks.fetch_news",
        "schedule": 300.0,  # Every 5 minutes
    },

    # ── Weight Maintenance ──
    "mkg-weight-decay": {
        "task": "mkg.tasks.run_weight_decay",
        "schedule": 3600.0,  # Every hour
    },

    # ── Prediction Resolution ──
    "mkg-resolve-predictions": {
        "task": "mkg.tasks.resolve_predictions",
        "schedule": 900.0,  # Every 15 minutes
    },

    # ── Health Check ──
    "mkg-health-check": {
        "task": "mkg.tasks.health_check",
        "schedule": 300.0,  # Every 5 minutes
    },
}
