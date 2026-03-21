"""Tests for Sprint 8: accuracy trend schema, weekly win rate, signal detail navigation."""

from datetime import datetime, timezone

import pytest

from app.schemas.signal import WeeklyTrendItem


class TestWeeklyTrendItemSchema:
    """Test the WeeklyTrendItem Pydantic schema."""

    def test_basic_creation(self) -> None:
        item = WeeklyTrendItem(
            week="2026-W11",
            start_date="2026-03-09",
            total=12,
            hit_target=9,
            win_rate=75.0,
        )
        assert item.week == "2026-W11"
        assert item.total == 12
        assert item.hit_target == 9
        assert item.win_rate == 75.0

    def test_zero_total(self) -> None:
        item = WeeklyTrendItem(
            week="2026-W08",
            start_date="2026-02-16",
            total=0,
            hit_target=0,
            win_rate=0.0,
        )
        assert item.total == 0
        assert item.win_rate == 0.0

    def test_perfect_win_rate(self) -> None:
        item = WeeklyTrendItem(
            week="2026-W12",
            start_date="2026-03-16",
            total=5,
            hit_target=5,
            win_rate=100.0,
        )
        assert item.win_rate == 100.0


class TestWeeklyWinRateCalculation:
    """Test the win rate calculation logic used in the trend endpoint."""

    def test_normal_calculation(self) -> None:
        total, ht = 10, 7
        wr = (ht / total * 100) if total > 0 else 0.0
        assert wr == 70.0

    def test_zero_total_gives_zero(self) -> None:
        total, ht = 0, 0
        wr = (ht / total * 100) if total > 0 else 0.0
        assert wr == 0.0

    def test_all_misses(self) -> None:
        total, ht = 5, 0
        wr = (ht / total * 100) if total > 0 else 0.0
        assert wr == 0.0

    def test_rounding(self) -> None:
        total, ht = 3, 1
        wr = round((ht / total * 100), 1)
        assert wr == 33.3


class TestWeekFormatting:
    """Test ISO week formatting used in the trend endpoint."""

    def test_week_format(self) -> None:
        dt = datetime(2026, 3, 9, tzinfo=timezone.utc)
        week_str = dt.strftime("%G-W%V")
        assert week_str.startswith("2026-W")

    def test_start_date_format(self) -> None:
        dt = datetime(2026, 3, 9, tzinfo=timezone.utc)
        date_str = dt.strftime("%Y-%m-%d")
        assert date_str == "2026-03-09"

    def test_year_boundary_week(self) -> None:
        """ISO week at year boundary (Dec 29 2025 is W01 of 2026)."""
        dt = datetime(2025, 12, 29, tzinfo=timezone.utc)
        week_str = dt.strftime("%G-W%V")
        assert week_str == "2026-W01"
