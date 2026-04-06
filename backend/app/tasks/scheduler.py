"""Celery Beat schedule definition."""

import random

from celery.schedules import crontab


def _jittered(base_seconds: float, jitter_pct: float = 0.1) -> float:
    """Add up to ±jitter_pct random jitter to a schedule interval."""
    jitter = base_seconds * jitter_pct * (2 * random.random() - 1)
    return max(10.0, base_seconds + jitter)

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
    # ── Multi-Timeframe Data (Confirmation) ──
    "fetch-crypto-daily": {
        "task": "app.tasks.data_tasks.fetch_crypto_daily",
        "schedule": 3600.0,  # Every hour — daily candle doesn't change fast
    },
    "fetch-forex-4h": {
        "task": "app.tasks.data_tasks.fetch_forex_4h",
        "schedule": 900.0,  # Every 15 min — 4h candle
    },
    # ── Analysis ──
    "run-technical-analysis": {
        "task": "app.tasks.analysis_tasks.run_analysis",
        "schedule": _jittered(300.0),
    },
    # ── AI Engine ──
    # Sentiment runs every 60 min (budget-sustainable).
    # The task itself gates by market hours for stocks/forex.
    "run-sentiment-analysis": {
        "task": "app.tasks.ai_tasks.run_sentiment",
        "schedule": _jittered(3600.0),
    },
    # ── Signal Generation ──
    "generate-signals": {
        "task": "app.tasks.signal_tasks.generate_signals",
        "schedule": _jittered(300.0),
    },
    # ── Digests ──
    "morning-brief": {
        "task": "app.tasks.alert_tasks.morning_brief",
        "schedule": crontab(hour=9, minute=30),  # After NSE opens at 9:15 AM IST
    },
    "evening-wrap": {
        "task": "app.tasks.alert_tasks.evening_wrap",
        "schedule": crontab(hour=16, minute=0),
    },
    "weekly-digest": {
        "task": "app.tasks.alert_tasks.weekly_digest",
        "schedule": crontab(hour=18, minute=0, day_of_week=0),  # Sunday 6 PM IST
    },
    # ── Signal Resolution (check targets/stops every 15 min) ──
    "resolve-signals": {
        "task": "app.tasks.signal_tasks.resolve_expired",
        "schedule": 900.0,
    },
    # ── Price Alerts ──
    "check-price-alerts": {
        "task": "app.tasks.price_alert_tasks.check_price_alerts",
        "schedule": 60.0,
    },
    # ── Maintenance ──
    "health-check": {
        "task": "app.tasks.data_tasks.health_check",
        "schedule": 300.0,
    },
    # ── Event Chain Maintenance ──
    "expire-stale-events": {
        "task": "app.tasks.ai_tasks.expire_stale_events",
        "schedule": 3600.0,  # Every hour
    },
    # ── Calendar Seeding (refresh known events daily) ──
    "seed-calendar-events": {
        "task": "app.tasks.calendar_tasks.seed_calendar_events",
        "schedule": crontab(hour=6, minute=0),  # 6:00 AM IST daily
    },
    # ── Pipeline Health ──
    "pipeline-health-check": {
        "task": "app.tasks.alert_tasks.pipeline_health_check",
        "schedule": 900.0,  # Every 15 minutes
    },
    # ── Subscription Management ──
    "check-expired-subscriptions": {
        "task": "app.tasks.subscription_tasks.check_expired_subscriptions",
        "schedule": 3600.0,  # Every hour
    },
    # ── SEO Content Generation ──
    "generate-seo-pages": {
        "task": "app.tasks.seo_tasks.generate_seo_pages",
        "schedule": crontab(hour=8, minute=30),  # 8:30 AM IST daily (after morning brief)
    },
    # ── Engagement ──
    "free-tier-weekly-digest": {
        "task": "app.tasks.engagement_tasks.send_free_tier_digest",
        "schedule": crontab(hour=18, minute=30, day_of_week=0),  # Sunday 6:30 PM IST
    },
    "reengagement-nudge": {
        "task": "app.tasks.engagement_tasks.send_reengagement_nudge",
        "schedule": crontab(hour=10, minute=0, day_of_week=3),  # Wednesday 10 AM IST
    },
    # ── Data Retention (cleanup old market data) ──
    "cleanup-old-market-data": {
        "task": "app.tasks.data_tasks.cleanup_old_market_data",
        "schedule": crontab(hour=3, minute=0),  # 3:00 AM IST daily
    },
    # ── Database Backup ──
    "scheduled-backup": {
        "task": "app.tasks.data_tasks.scheduled_backup",
        "schedule": crontab(hour=2, minute=0),  # 2:00 AM IST daily
    },
}
