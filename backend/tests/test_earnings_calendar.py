"""Tests for earnings_calendar service module."""

from datetime import datetime, timezone

import pytest

from app.services.earnings_calendar import (
    CENTRAL_BANK_EVENTS,
    UPCOMING_EARNINGS,
    build_central_bank_events,
    build_earnings_events,
)


class TestUpcomingEarningsData:
    """Validate the static UPCOMING_EARNINGS data."""

    def test_earnings_list_not_empty(self):
        assert len(UPCOMING_EARNINGS) > 0

    def test_earnings_tuple_format(self):
        """Each entry must be (symbol, title, datetime_str, magnitude)."""
        for entry in UPCOMING_EARNINGS:
            assert len(entry) == 4
            symbol, title, dt_str, magnitude = entry
            assert isinstance(symbol, str)
            assert symbol.endswith(".NS")
            assert isinstance(title, str)
            assert isinstance(dt_str, str)
            assert isinstance(magnitude, int)
            assert magnitude > 0

    def test_earnings_dates_parseable(self):
        """All datetime strings must be valid ISO format."""
        for _symbol, _title, dt_str, _mag in UPCOMING_EARNINGS:
            dt = datetime.fromisoformat(dt_str)
            assert dt.tzinfo is not None


class TestCentralBankEventsData:
    """Validate the static CENTRAL_BANK_EVENTS data."""

    def test_events_not_empty(self):
        assert len(CENTRAL_BANK_EVENTS) > 0

    def test_events_tuple_format(self):
        """Each entry must be (title, event_type, datetime_str, markets, magnitude)."""
        for entry in CENTRAL_BANK_EVENTS:
            assert len(entry) == 5
            title, event_type, dt_str, markets, magnitude = entry
            assert isinstance(title, str)
            assert isinstance(event_type, str)
            assert isinstance(dt_str, str)
            assert isinstance(markets, list)
            assert all(m in ("stock", "crypto", "forex") for m in markets)
            assert isinstance(magnitude, int)

    def test_event_dates_parseable(self):
        for _title, _etype, dt_str, _markets, _mag in CENTRAL_BANK_EVENTS:
            dt = datetime.fromisoformat(dt_str)
            assert dt.tzinfo is not None


class TestBuildEarningsEvents:
    """Test the build_earnings_events helper."""

    def test_returns_list_of_dicts(self):
        events = build_earnings_events()
        assert isinstance(events, list)
        assert len(events) == len(UPCOMING_EARNINGS)

    def test_event_dict_keys(self):
        events = build_earnings_events()
        expected_keys = {
            "title", "event_type", "scheduled_at", "affected_symbols",
            "affected_markets", "impact_magnitude", "is_recurring", "recurrence_rule",
        }
        for event in events:
            assert set(event.keys()) == expected_keys

    def test_event_type_is_earnings(self):
        for event in build_earnings_events():
            assert event["event_type"] == "earnings"

    def test_scheduled_at_is_utc_datetime(self):
        for event in build_earnings_events():
            assert isinstance(event["scheduled_at"], datetime)
            assert event["scheduled_at"].tzinfo == timezone.utc

    def test_affected_symbols_is_list(self):
        for event in build_earnings_events():
            assert isinstance(event["affected_symbols"], list)
            assert len(event["affected_symbols"]) == 1

    def test_affected_markets_is_stock(self):
        for event in build_earnings_events():
            assert event["affected_markets"] == ["stock"]


class TestBuildCentralBankEvents:
    """Test the build_central_bank_events helper."""

    def test_returns_list_of_dicts(self):
        events = build_central_bank_events()
        assert isinstance(events, list)
        assert len(events) == len(CENTRAL_BANK_EVENTS)

    def test_event_dict_keys(self):
        events = build_central_bank_events()
        expected_keys = {
            "title", "event_type", "scheduled_at", "affected_symbols",
            "affected_markets", "impact_magnitude", "is_recurring", "recurrence_rule",
        }
        for event in events:
            assert set(event.keys()) == expected_keys

    def test_scheduled_at_is_utc_datetime(self):
        for event in build_central_bank_events():
            assert isinstance(event["scheduled_at"], datetime)
            assert event["scheduled_at"].tzinfo == timezone.utc

    def test_event_types(self):
        valid_types = {"fomc", "rbi_mpc", "ecb", "boj"}
        for event in build_central_bank_events():
            assert event["event_type"] in valid_types

    def test_affected_symbols_is_none(self):
        """Central bank events affect markets, not specific symbols."""
        for event in build_central_bank_events():
            assert event["affected_symbols"] is None
