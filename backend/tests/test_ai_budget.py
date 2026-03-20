"""Tests for AI task budget optimization and market-hours gating."""

from unittest.mock import patch

from app.tasks.ai_tasks import _is_forex_market_hours, _is_stock_market_hours


class TestMarketHoursGating:
    """Test that sentiment analysis respects market hours."""

    @patch("app.tasks.ai_tasks.datetime")
    def test_stock_market_open_weekday(self, mock_dt) -> None:
        """Stocks should be analyzed during NSE hours (Mon-Fri 9-16 IST)."""
        from datetime import datetime
        from zoneinfo import ZoneInfo

        mock_now = datetime(2026, 3, 20, 10, 30, tzinfo=ZoneInfo("Asia/Kolkata"))  # Friday 10:30
        mock_dt.now.return_value = mock_now
        assert _is_stock_market_hours() is True

    @patch("app.tasks.ai_tasks.datetime")
    def test_stock_market_closed_weekend(self, mock_dt) -> None:
        from datetime import datetime
        from zoneinfo import ZoneInfo

        mock_now = datetime(2026, 3, 21, 10, 30, tzinfo=ZoneInfo("Asia/Kolkata"))  # Saturday
        mock_dt.now.return_value = mock_now
        assert _is_stock_market_hours() is False

    @patch("app.tasks.ai_tasks.datetime")
    def test_stock_market_closed_night(self, mock_dt) -> None:
        from datetime import datetime
        from zoneinfo import ZoneInfo

        mock_now = datetime(2026, 3, 20, 22, 0, tzinfo=ZoneInfo("Asia/Kolkata"))  # Friday 10 PM
        mock_dt.now.return_value = mock_now
        assert _is_stock_market_hours() is False

    @patch("app.tasks.ai_tasks.datetime")
    def test_forex_open_weekday(self, mock_dt) -> None:
        from datetime import datetime
        from zoneinfo import ZoneInfo

        mock_now = datetime(2026, 3, 18, 14, 0, tzinfo=ZoneInfo("Asia/Kolkata"))  # Wednesday
        mock_dt.now.return_value = mock_now
        assert _is_forex_market_hours() is True

    @patch("app.tasks.ai_tasks.datetime")
    def test_forex_closed_saturday(self, mock_dt) -> None:
        from datetime import datetime
        from zoneinfo import ZoneInfo

        mock_now = datetime(2026, 3, 21, 10, 0, tzinfo=ZoneInfo("Asia/Kolkata"))  # Saturday 10 AM
        mock_dt.now.return_value = mock_now
        assert _is_forex_market_hours() is False

    @patch("app.tasks.ai_tasks.datetime")
    def test_forex_closed_sunday_morning(self, mock_dt) -> None:
        from datetime import datetime
        from zoneinfo import ZoneInfo

        mock_now = datetime(2026, 3, 22, 10, 0, tzinfo=ZoneInfo("Asia/Kolkata"))  # Sunday 10 AM
        mock_dt.now.return_value = mock_now
        assert _is_forex_market_hours() is False
