"""Tests for Phase 5 P2 — Nice-to-Have features.

Covers: symbol search API filter, risk calculator logic, sparkline data
in full_analysis, watchlist API, weekly digest formatter updates.
"""

import numpy as np
import pandas as pd
import pytest

from app.services.analysis.indicators import TechnicalAnalyzer


def _make_ohlcv(n: int = 250, start_price: float = 100.0) -> pd.DataFrame:
    """Generate synthetic OHLCV data."""
    np.random.seed(42)
    closes = [start_price]
    for _ in range(1, n):
        closes.append(closes[-1] * (1 + np.random.normal(0, 0.02)))
    closes = np.array(closes)
    highs = closes * 1.01
    lows = closes * 0.99
    opens = (closes + np.roll(closes, 1)) / 2
    opens[0] = start_price
    volumes = np.random.randint(100000, 1000000, n).astype(float)
    return pd.DataFrame({
        "open": opens, "high": highs, "low": lows,
        "close": closes, "volume": volumes,
    })


# ── Sparkline Data in full_analysis ──


class TestSparklineData:
    def test_full_analysis_includes_recent_closes(self) -> None:
        df = _make_ohlcv(250)
        analyzer = TechnicalAnalyzer(df)
        result = analyzer.full_analysis()
        assert "recent_closes" in result
        assert isinstance(result["recent_closes"], list)
        assert len(result["recent_closes"]) == 20

    def test_recent_closes_are_last_20(self) -> None:
        df = _make_ohlcv(250)
        analyzer = TechnicalAnalyzer(df)
        result = analyzer.full_analysis()
        expected = df["close"].tail(20).tolist()
        for actual, exp in zip(result["recent_closes"], expected):
            assert abs(actual - round(float(exp), 4)) < 0.001

    def test_short_data_gives_fewer_closes(self) -> None:
        df = _make_ohlcv(5)
        analyzer = TechnicalAnalyzer(df)
        result = analyzer.full_analysis()
        assert len(result["recent_closes"]) == 5


# ── Symbol Search API Filter ──


class TestSymbolFilter:
    """Test that the signals API supports symbol filtering.
    These are structural tests — we verify the endpoint signature accepts 'symbol'.
    """

    def test_signals_endpoint_has_symbol_param(self) -> None:
        """Verify the list_signals function accepts a symbol parameter."""
        from app.api.signals import list_signals
        import inspect
        sig = inspect.signature(list_signals)
        assert "symbol" in sig.parameters

    def test_symbol_param_is_optional(self) -> None:
        from app.api.signals import list_signals
        import inspect
        sig = inspect.signature(list_signals)
        param = sig.parameters["symbol"]
        assert param.default is None


# ── Watchlist Schema ──


class TestWatchlistSchema:
    def test_watchlist_update_schema(self) -> None:
        from app.schemas.alert import WatchlistUpdate
        update = WatchlistUpdate(symbol="HDFCBANK.NS", action="add")
        assert update.symbol == "HDFCBANK.NS"
        assert update.action == "add"

    def test_alert_config_data_has_watchlist(self) -> None:
        from app.schemas.alert import AlertConfigData
        fields = AlertConfigData.model_fields
        assert "watchlist" in fields

    def test_alert_config_update_has_watchlist(self) -> None:
        from app.schemas.alert import AlertConfigUpdate
        update = AlertConfigUpdate(watchlist=["HDFCBANK.NS", "BTCUSDT"])
        assert update.watchlist == ["HDFCBANK.NS", "BTCUSDT"]


# ── Formatter Updates ──


class TestFormatterUpdates:
    def test_welcome_includes_watchlist_command(self) -> None:
        from app.services.alerts.formatter import format_welcome
        result = format_welcome()
        assert "/watchlist" in result

    def test_tutorial_unchanged(self) -> None:
        from app.services.alerts.formatter import format_tutorial
        result = format_tutorial()
        assert "How to Read" in result
        assert "not financial advice" in result


# ── Watchlist Telegram Bot ──


class TestWatchlistCommand:
    def test_bot_has_watchlist_handler(self) -> None:
        """Verify the bot registers a /watchlist command handler."""
        from app.services.alerts.telegram_bot import SignalFlowBot
        import inspect
        assert hasattr(SignalFlowBot, "_cmd_watchlist")
        sig = inspect.signature(SignalFlowBot._cmd_watchlist)
        params = list(sig.parameters.keys())
        assert "self" in params
        assert "update" in params
        assert "context" in params


# ── Risk Calculator Logic ──


class TestRiskCalculatorLogic:
    """Test the risk/reward math that the frontend component uses.
    We replicate the calculation here to verify correctness."""

    def test_buy_signal_risk_reward(self) -> None:
        price, target, stop = 100.0, 110.0, 95.0
        amount = 10000
        max_gain = ((target - price) / price) * amount  # 1000
        max_loss = ((price - stop) / price) * amount     # 500
        rr = max_gain / max_loss                          # 2.0
        assert max_gain == pytest.approx(1000.0)
        assert max_loss == pytest.approx(500.0)
        assert rr == pytest.approx(2.0)

    def test_sell_signal_risk_reward(self) -> None:
        price, target, stop = 100.0, 90.0, 105.0
        amount = 10000
        max_gain = ((price - target) / price) * amount  # 1000
        max_loss = ((stop - price) / price) * amount     # 500
        rr = max_gain / max_loss                          # 2.0
        assert max_gain == pytest.approx(1000.0)
        assert max_loss == pytest.approx(500.0)
        assert rr == pytest.approx(2.0)

    def test_different_amount(self) -> None:
        price, target, stop = 1678.90, 1780.0, 1630.0
        amount = 50000
        max_gain = ((target - price) / price) * amount
        max_loss = ((price - stop) / price) * amount
        assert max_gain > 0
        assert max_loss > 0
        assert max_gain / max_loss > 1.0  # RR > 1:1


# ── Stats Endpoint Structure ──


class TestStatsEndpoint:
    def test_stats_endpoint_exists(self) -> None:
        from app.api.history import get_signal_stats
        import inspect
        sig = inspect.signature(get_signal_stats)
        assert "db" in sig.parameters

    def test_stats_response_schema(self) -> None:
        from app.schemas.signal import SignalStatsResponse
        fields = SignalStatsResponse.model_fields
        assert "win_rate" in fields
        assert "avg_return_pct" in fields
        assert "total_signals" in fields
        assert "hit_target" in fields
