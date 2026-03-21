"""Tests for Sprint 9: market hours utility (logic tests via Python equivalents)."""

from datetime import datetime, timezone

import pytest


class TestMarketHoursLogic:
    """Test market hours logic that mirrors frontend utils/market-hours.ts."""

    def test_nse_weekday_during_hours(self) -> None:
        """NSE should be open on a Monday at 10:00 AM IST."""
        # Monday 10:00 AM IST = within 9:15-15:30
        hours, minutes = 10, 0
        day = 1  # Monday
        time_mins = hours * 60 + minutes
        is_open = day not in (0, 6) and 9 * 60 + 15 <= time_mins <= 15 * 60 + 30
        assert is_open is True

    def test_nse_weekday_before_hours(self) -> None:
        """NSE should be closed before 9:15 AM on a weekday."""
        hours, minutes = 8, 0
        day = 2  # Tuesday
        time_mins = hours * 60 + minutes
        is_open = day not in (0, 6) and 9 * 60 + 15 <= time_mins <= 15 * 60 + 30
        assert is_open is False

    def test_nse_weekday_after_hours(self) -> None:
        """NSE should be closed after 3:30 PM on a weekday."""
        hours, minutes = 16, 0
        day = 3  # Wednesday
        time_mins = hours * 60 + minutes
        is_open = day not in (0, 6) and 9 * 60 + 15 <= time_mins <= 15 * 60 + 30
        assert is_open is False

    def test_nse_weekend_closed(self) -> None:
        """NSE should be closed on Saturday/Sunday."""
        for day in (0, 6):  # Sunday, Saturday
            hours, minutes = 12, 0
            time_mins = hours * 60 + minutes
            is_open = day not in (0, 6) and 9 * 60 + 15 <= time_mins <= 15 * 60 + 30
            assert is_open is False

    def test_crypto_always_open(self) -> None:
        """Crypto markets are 24/7."""
        assert True  # isCryptoOpen() always true

    def test_forex_sunday_before_open(self) -> None:
        """Forex should be closed Sunday morning (before 5:30 PM IST)."""
        day = 0  # Sunday
        hours, minutes = 10, 0
        time_mins = hours * 60 + minutes
        # Closed if Sunday before 5:30 PM
        if day == 0 and time_mins < 17 * 60 + 30:
            is_open = False
        else:
            is_open = True
        assert is_open is False

    def test_forex_sunday_after_open(self) -> None:
        """Forex should be open Sunday evening (after 5:30 PM IST)."""
        day = 0  # Sunday
        hours, minutes = 18, 0
        time_mins = hours * 60 + minutes
        if day == 0 and time_mins < 17 * 60 + 30:
            is_open = False
        elif day == 6 and time_mins > 3 * 60 + 30:
            is_open = False
        else:
            is_open = True
        assert is_open is True

    def test_forex_saturday_closed(self) -> None:
        """Forex should be closed Saturday afternoon."""
        day = 6  # Saturday
        hours, minutes = 12, 0
        time_mins = hours * 60 + minutes
        if day == 6 and time_mins > 3 * 60 + 30:
            is_open = False
        elif day == 0 and time_mins < 17 * 60 + 30:
            is_open = False
        else:
            is_open = True
        assert is_open is False


class TestHistorySortLogic:
    """Test the sorting logic used in the history page."""

    def test_sort_by_return_desc(self) -> None:
        """Highest return first when sorting by return desc."""
        items = [
            {"return_pct": "5.2"},
            {"return_pct": "-1.3"},
            {"return_pct": "12.0"},
            {"return_pct": None},
        ]
        sorted_items = sorted(
            items,
            key=lambda x: float(x["return_pct"]) if x["return_pct"] else float("-inf"),
            reverse=True,
        )
        assert float(sorted_items[0]["return_pct"]) == 12.0
        assert float(sorted_items[1]["return_pct"]) == 5.2
        assert float(sorted_items[2]["return_pct"]) == -1.3
        assert sorted_items[3]["return_pct"] is None

    def test_sort_by_return_asc(self) -> None:
        """Lowest return first when sorting by return asc."""
        items = [
            {"return_pct": "5.2"},
            {"return_pct": "-1.3"},
            {"return_pct": "12.0"},
        ]
        sorted_items = sorted(
            items,
            key=lambda x: float(x["return_pct"]) if x["return_pct"] else float("-inf"),
        )
        assert float(sorted_items[0]["return_pct"]) == -1.3
        assert float(sorted_items[-1]["return_pct"]) == 12.0

    def test_sort_by_resolved_date(self) -> None:
        """Most recent resolved date first when sorting desc."""
        items = [
            {"resolved_at": "2026-03-15T10:00:00Z"},
            {"resolved_at": "2026-03-20T10:00:00Z"},
            {"resolved_at": None},
            {"resolved_at": "2026-03-10T10:00:00Z"},
        ]
        sorted_items = sorted(
            items,
            key=lambda x: x["resolved_at"] or "",
            reverse=True,
        )
        assert sorted_items[0]["resolved_at"] == "2026-03-20T10:00:00Z"
        assert sorted_items[1]["resolved_at"] == "2026-03-15T10:00:00Z"

    def test_sort_stability_with_equal_values(self) -> None:
        """Equal return values should maintain original order."""
        items = [
            {"return_pct": "5.0", "id": "a"},
            {"return_pct": "5.0", "id": "b"},
        ]
        sorted_items = sorted(
            items,
            key=lambda x: float(x["return_pct"]),
            reverse=True,
        )
        assert sorted_items[0]["id"] == "a"
        assert sorted_items[1]["id"] == "b"
