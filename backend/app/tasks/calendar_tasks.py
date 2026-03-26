"""Event calendar seeding task — populates known earnings and central bank events."""

import logging

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.event_calendar import EventCalendar
from app.services.earnings_calendar import build_earnings_events, build_central_bank_events
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.calendar_tasks.seed_calendar_events")
def seed_calendar_events() -> dict:
    """Seed upcoming earnings dates and central bank events into event_calendar.

    Idempotent — checks for existing events by title before inserting.
    """
    settings = get_settings()
    engine = create_engine(settings.database_url_sync, pool_pre_ping=True)

    all_events = build_earnings_events() + build_central_bank_events()
    inserted = 0

    try:
        with Session(engine) as session:
            for evt_data in all_events:
                # Check if event already exists (by title + scheduled_at)
                existing = session.execute(
                    select(EventCalendar.id).where(
                        EventCalendar.title == evt_data["title"],
                        EventCalendar.scheduled_at == evt_data["scheduled_at"],
                    )
                ).scalar_one_or_none()

                if existing is not None:
                    continue

                event = EventCalendar(
                    title=evt_data["title"],
                    event_type=evt_data["event_type"],
                    scheduled_at=evt_data["scheduled_at"],
                    affected_symbols=evt_data.get("affected_symbols"),
                    affected_markets=evt_data.get("affected_markets"),
                    impact_magnitude=evt_data.get("impact_magnitude", 3),
                    is_recurring=evt_data.get("is_recurring", False),
                    recurrence_rule=evt_data.get("recurrence_rule"),
                )
                session.add(event)
                inserted += 1

            session.commit()

        logger.info("Calendar seed: inserted %d events (%d already existed)", inserted, len(all_events) - inserted)
        return {"status": "ok", "inserted": inserted, "total": len(all_events)}
    finally:
        engine.dispose()
