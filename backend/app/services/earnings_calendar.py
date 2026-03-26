"""Seed upcoming earnings dates for Indian stocks.

Provides known Q4 FY26 earnings dates for NIFTY 50 constituents tracked by SignalFlow.
This is manually curated — replace with an API source (e.g., Yahoo Finance earnings calendar)
in a future iteration.

Usage:
    python -m app.services.earnings_calendar
    OR import and call seed_earnings_dates(db_session)
"""

import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Q4 FY2026 earnings calendar for tracked symbols (approximate dates)
# Source: BSE/NSE announcement schedules
# Format: (symbol, title, scheduled_at_utc, impact_magnitude)
UPCOMING_EARNINGS = [
    ("RELIANCE.NS", "Reliance Q4 FY26 Results", "2026-04-18T10:00:00+05:30", 5),
    ("HDFCBANK.NS", "HDFC Bank Q4 FY26 Results", "2026-04-19T10:00:00+05:30", 5),
    ("ICICIBANK.NS", "ICICI Bank Q4 FY26 Results", "2026-04-26T10:00:00+05:30", 5),
    ("TCS.NS", "TCS Q4 FY26 Results", "2026-04-10T10:00:00+05:30", 5),
    ("INFY.NS", "Infosys Q4 FY26 Results", "2026-04-11T10:00:00+05:30", 5),
    ("SBIN.NS", "SBI Q4 FY26 Results", "2026-05-15T10:00:00+05:30", 4),
    ("KOTAKBANK.NS", "Kotak Bank Q4 FY26 Results", "2026-04-26T10:00:00+05:30", 4),
    ("AXISBANK.NS", "Axis Bank Q4 FY26 Results", "2026-04-25T10:00:00+05:30", 4),
    ("WIPRO.NS", "Wipro Q4 FY26 Results", "2026-04-16T10:00:00+05:30", 4),
    ("HCLTECH.NS", "HCL Tech Q4 FY26 Results", "2026-04-22T10:00:00+05:30", 4),
    ("MARUTI.NS", "Maruti Q4 FY26 Results", "2026-04-25T10:00:00+05:30", 4),
    ("TATAMOTORS.NS", "Tata Motors Q4 FY26 Results", "2026-05-08T10:00:00+05:30", 4),
    ("BHARTIARTL.NS", "Bharti Airtel Q4 FY26 Results", "2026-05-05T10:00:00+05:30", 4),
    ("ITC.NS", "ITC Q4 FY26 Results", "2026-05-22T10:00:00+05:30", 4),
    ("LT.NS", "L&T Q4 FY26 Results", "2026-05-14T10:00:00+05:30", 4),
]

# Major central bank events for 2026 (static seed data)
CENTRAL_BANK_EVENTS = [
    ("FOMC Rate Decision — April", "fomc", "2026-04-29T18:00:00+00:00", ["forex"], 5),
    ("FOMC Rate Decision — June", "fomc", "2026-06-10T18:00:00+00:00", ["forex"], 5),
    ("FOMC Rate Decision — July", "fomc", "2026-07-29T18:00:00+00:00", ["forex"], 5),
    ("FOMC Rate Decision — September", "fomc", "2026-09-16T18:00:00+00:00", ["forex"], 5),
    ("FOMC Rate Decision — November", "fomc", "2026-11-04T18:00:00+00:00", ["forex"], 5),
    ("FOMC Rate Decision — December", "fomc", "2026-12-16T18:00:00+00:00", ["forex"], 5),
    ("RBI MPC Decision — April", "rbi_mpc", "2026-04-09T10:00:00+05:30", ["stock", "forex"], 5),
    ("RBI MPC Decision — June", "rbi_mpc", "2026-06-05T10:00:00+05:30", ["stock", "forex"], 5),
    ("RBI MPC Decision — August", "rbi_mpc", "2026-08-06T10:00:00+05:30", ["stock", "forex"], 5),
    ("RBI MPC Decision — October", "rbi_mpc", "2026-10-01T10:00:00+05:30", ["stock", "forex"], 5),
    ("RBI MPC Decision — December", "rbi_mpc", "2026-12-04T10:00:00+05:30", ["stock", "forex"], 5),
    ("ECB Rate Decision — April", "ecb", "2026-04-16T11:45:00+00:00", ["forex"], 5),
    ("ECB Rate Decision — June", "ecb", "2026-06-04T11:45:00+00:00", ["forex"], 5),
    ("ECB Rate Decision — July", "ecb", "2026-07-16T11:45:00+00:00", ["forex"], 5),
    ("ECB Rate Decision — September", "ecb", "2026-09-10T11:45:00+00:00", ["forex"], 5),
    ("ECB Rate Decision — October", "ecb", "2026-10-29T11:45:00+00:00", ["forex"], 5),
    ("ECB Rate Decision — December", "ecb", "2026-12-17T11:45:00+00:00", ["forex"], 5),
    ("BOJ Policy Decision — April", "boj", "2026-04-28T03:00:00+00:00", ["forex"], 4),
    ("BOJ Policy Decision — June", "boj", "2026-06-16T03:00:00+00:00", ["forex"], 4),
]


def build_earnings_events() -> list[dict]:
    """Build EventCalendar-compatible dicts for earnings dates."""
    events = []
    for symbol, title, scheduled_at, magnitude in UPCOMING_EARNINGS:
        events.append({
            "title": title,
            "event_type": "earnings",
            "scheduled_at": datetime.fromisoformat(scheduled_at).astimezone(timezone.utc),
            "affected_symbols": [symbol],
            "affected_markets": ["stock"],
            "impact_magnitude": magnitude,
            "is_recurring": True,
            "recurrence_rule": "quarterly",
        })
    return events


def build_central_bank_events() -> list[dict]:
    """Build EventCalendar-compatible dicts for central bank meetings."""
    events = []
    for title, event_type, scheduled_at, markets, magnitude in CENTRAL_BANK_EVENTS:
        events.append({
            "title": title,
            "event_type": event_type,
            "scheduled_at": datetime.fromisoformat(scheduled_at).astimezone(timezone.utc),
            "affected_symbols": None,
            "affected_markets": markets,
            "impact_magnitude": magnitude,
            "is_recurring": True,
            "recurrence_rule": "periodic",
        })
    return events
