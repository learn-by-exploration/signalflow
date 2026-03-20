"""Celery Beat schedule definition."""

from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    # ── Data Ingestion ──
    "fetch-indian-stocks": {
        "task": "app.tasks.data_tasks.fetch_indian_stocks",
        "schedule": 60.0,
    },
    "fetch-crypto-prices": {
        "task": "app.tasks.data_tasks.fetch_crypto",
        "schedule": 30.0,
    },
    "fetch-forex-rates": {
        "task": "app.tasks.data_tasks.fetch_forex",
        "schedule": 60.0,
    },
    # ── Analysis ──
    "run-technical-analysis": {
        "task": "app.tasks.analysis_tasks.run_analysis",
        "schedule": 300.0,
    },
    # ── AI Engine ──
    "run-sentiment-analysis": {
        "task": "app.tasks.ai_tasks.run_sentiment",
        "schedule": 900.0,
    },
    # ── Signal Generation ──
    "generate-signals": {
        "task": "app.tasks.signal_tasks.generate_signals",
        "schedule": 300.0,
    },
    # ── Digests ──
    "morning-brief": {
        "task": "app.tasks.alert_tasks.morning_brief",
        "schedule": crontab(hour=8, minute=0),
    },
    "evening-wrap": {
        "task": "app.tasks.alert_tasks.evening_wrap",
        "schedule": crontab(hour=16, minute=0),
    },
    # ── Maintenance ──
    "resolve-expired-signals": {
        "task": "app.tasks.signal_tasks.resolve_expired",
        "schedule": 3600.0,
    },
    "health-check": {
        "task": "app.tasks.data_tasks.health_check",
        "schedule": 300.0,
    },
}
