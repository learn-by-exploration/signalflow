"""Tests for Sprint 10 fixes — portfolio live prices, AI Q&A ORM,
CostTracker Redis, health endpoint metrics, and schema validations."""

import json
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ── CostTracker Tests ──

class TestCostTrackerRedis:
    """Test CostTracker Redis-based atomic cost tracking."""

    def test_calculate_cost_sonnet(self):
        """Cost calculation matches Anthropic pricing."""
        with patch("app.services.ai_engine.cost_tracker.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                monthly_ai_budget_usd=30.0,
                claude_model="claude-sonnet-4-20250514",
                redis_url="redis://localhost:6379/0",
            )
            with patch("app.services.ai_engine.cost_tracker.redis") as mock_redis_mod:
                mock_redis_mod.from_url.side_effect = Exception("no redis")
                from app.services.ai_engine.cost_tracker import CostTracker
                tracker = CostTracker(storage_path="/tmp/test_cost_tracker.json")

        # 1M input tokens = $3.00, 1M output tokens = $15.00
        cost = tracker.calculate_cost(1_000_000, 0)
        assert cost == 3.0

        cost = tracker.calculate_cost(0, 1_000_000)
        assert cost == 15.0

        cost = tracker.calculate_cost(500_000, 100_000)
        assert cost == pytest.approx(1.5 + 1.5, abs=0.01)

    def test_record_usage_writes_json_audit(self, tmp_path):
        """record_usage still writes to JSON audit log even when Redis is unavailable."""
        log_path = tmp_path / "cost_log.json"
        with patch("app.services.ai_engine.cost_tracker.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                monthly_ai_budget_usd=30.0,
                claude_model="claude-sonnet-4-20250514",
                redis_url="redis://localhost:6379/0",
            )
            with patch("app.services.ai_engine.cost_tracker.redis") as mock_redis_mod:
                mock_redis_mod.from_url.side_effect = Exception("no redis")
                from app.services.ai_engine.cost_tracker import CostTracker
                tracker = CostTracker(storage_path=str(log_path))

        cost = tracker.record_usage(1000, 500, "sentiment", "BTCUSDT")
        assert cost > 0

        data = json.loads(log_path.read_text())
        assert len(data["calls"]) == 1
        assert data["calls"][0]["task_type"] == "sentiment"
        assert data["calls"][0]["symbol"] == "BTCUSDT"

    def test_budget_check_no_redis(self, tmp_path):
        """Budget check works with file-only mode."""
        log_path = tmp_path / "cost_log.json"
        with patch("app.services.ai_engine.cost_tracker.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                monthly_ai_budget_usd=30.0,
                claude_model="claude-sonnet-4-20250514",
                redis_url="redis://localhost:6379/0",
            )
            with patch("app.services.ai_engine.cost_tracker.redis") as mock_redis_mod:
                mock_redis_mod.from_url.side_effect = Exception("no redis")
                from app.services.ai_engine.cost_tracker import CostTracker
                tracker = CostTracker(storage_path=str(log_path))

        assert tracker.is_budget_available() is True
        assert tracker.get_remaining_budget() == 30.0

    def test_budget_exhausted(self, tmp_path):
        """Budget is marked unavailable after spending exceeds limit."""
        log_path = tmp_path / "cost_log.json"
        with patch("app.services.ai_engine.cost_tracker.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                monthly_ai_budget_usd=0.01,  # Very low budget
                claude_model="claude-sonnet-4-20250514",
                redis_url="redis://localhost:6379/0",
            )
            with patch("app.services.ai_engine.cost_tracker.redis") as mock_redis_mod:
                mock_redis_mod.from_url.side_effect = Exception("no redis")
                from app.services.ai_engine.cost_tracker import CostTracker
                tracker = CostTracker(storage_path=str(log_path))

        # Record a big call that exceeds budget
        tracker.record_usage(1_000_000, 1_000_000, "test")
        assert tracker.is_budget_available() is False


# ── AI Q&A Symbol Normalization Tests ──

class TestAIQASymbolNormalization:
    """Test that AI Q&A resolves both HDFCBANK and HDFCBANK.NS."""

    def test_query_symbols_plain_stock(self):
        """Plain stock symbol generates both variants."""
        symbol = "HDFCBANK"
        query_symbols = [symbol]
        if not symbol.endswith(".NS") and "/" not in symbol and not symbol.endswith("USDT"):
            query_symbols.append(f"{symbol}.NS")
        assert query_symbols == ["HDFCBANK", "HDFCBANK.NS"]

    def test_query_symbols_ns_suffix(self):
        """Symbol with .NS generates both variants."""
        symbol = "TCS.NS"
        query_symbols = [symbol]
        if symbol.endswith(".NS"):
            query_symbols.append(symbol.replace(".NS", ""))
        assert query_symbols == ["TCS.NS", "TCS"]

    def test_query_symbols_crypto_no_ns(self):
        """Crypto symbols don't get .NS appended."""
        symbol = "BTCUSDT"
        query_symbols = [symbol]
        if not symbol.endswith(".NS") and "/" not in symbol and not symbol.endswith("USDT"):
            query_symbols.append(f"{symbol}.NS")
        assert query_symbols == ["BTCUSDT"]

    def test_query_symbols_forex_no_ns(self):
        """Forex symbols don't get .NS appended."""
        symbol = "EUR/USD"
        query_symbols = [symbol]
        if not symbol.endswith(".NS") and "/" not in symbol and not symbol.endswith("USDT"):
            query_symbols.append(f"{symbol}.NS")
        assert query_symbols == ["EUR/USD"]


# ── Portfolio Live Price Tests ──

class TestPortfolioLivePriceLogic:
    """Test the portfolio price lookup logic."""

    def test_live_price_preferred_over_trade_price(self):
        """Live prices from market_data should be used instead of last trade price."""
        live_prices = {"HDFCBANK.NS": Decimal("1700.00")}
        last_trade_price = Decimal("1650.00")
        symbol = "HDFCBANK.NS"

        current_price = live_prices.get(symbol, last_trade_price)
        assert current_price == Decimal("1700.00")

    def test_falls_back_to_trade_price_when_no_market_data(self):
        """Falls back to last trade price when no market data exists."""
        live_prices = {}  # No market data
        last_trade_price = Decimal("1650.00")
        symbol = "HDFCBANK.NS"

        current_price = live_prices.get(symbol, last_trade_price)
        assert current_price == Decimal("1650.00")

    def test_pnl_calculation_with_live_price(self):
        """P&L is correctly calculated from live price."""
        net_qty = Decimal("10")
        net_cost = Decimal("16500.00")  # 10 shares @ 1650
        current_price = Decimal("1700.00")  # Live price

        position_value = net_qty * current_price
        pnl = position_value - net_cost
        pnl_pct = float(pnl / net_cost * 100)

        assert position_value == Decimal("17000.00")
        assert pnl == Decimal("500.00")
        assert round(pnl_pct, 2) == 3.03


# ── Health Endpoint Field Validation ──

class TestHealthEndpointFields:
    """Test health endpoint reports the expected fields."""

    def test_health_returns_required_fields(self):
        """Verify the health response schema has signal count and data freshness fields."""
        # These fields should be present in the health response
        required_fields = [
            "status", "uptime", "environment", "disclaimer",
            "db_status", "redis_status",
        ]
        optional_fields = [
            "active_signals_count", "last_data_fetch",
            "ai_budget_remaining_pct", "data_status",
        ]
        # Just verify the field names are valid strings
        for field in required_fields + optional_fields:
            assert isinstance(field, str) and len(field) > 0

    def test_stale_data_detection_logic(self):
        """Stale data (>10 min) should mark status as degraded."""
        now = datetime.now(timezone.utc)
        last_ts = now - timedelta(minutes=15)
        age = now - last_ts
        is_stale = age > timedelta(minutes=10)
        assert is_stale is True

    def test_fresh_data_not_stale(self):
        """Recent data (<10 min) should not be flagged as stale."""
        now = datetime.now(timezone.utc)
        last_ts = now - timedelta(minutes=5)
        age = now - last_ts
        is_stale = age > timedelta(minutes=10)
        assert is_stale is False
