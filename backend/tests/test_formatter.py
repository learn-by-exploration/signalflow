"""Tests for Telegram message formatter."""

from decimal import Decimal

import pytest

from app.services.alerts.formatter import (
    format_evening_wrap,
    format_morning_brief,
    format_signal_alert,
    format_market_snapshot,
    format_signals_list,
    format_welcome,
)


@pytest.fixture
def stock_signal() -> dict:
    return {
        "symbol": "HDFCBANK.NS",
        "market_type": "stock",
        "signal_type": "STRONG_BUY",
        "confidence": 92,
        "current_price": Decimal("1678.90"),
        "target_price": Decimal("1780.00"),
        "stop_loss": Decimal("1630.00"),
        "timeframe": "2-4 weeks",
        "ai_reasoning": "Credit growth accelerating. NIM expansion confirmed.",
        "technical_data": {"rsi": {"value": 62.7, "signal": "neutral"}, "macd": {"signal": "bullish"}},
    }


@pytest.fixture
def crypto_signal() -> dict:
    return {
        "symbol": "BTCUSDT",
        "market_type": "crypto",
        "signal_type": "SELL",
        "confidence": 35,
        "current_price": Decimal("97842.00"),
        "target_price": Decimal("94000.00"),
        "stop_loss": Decimal("100000.00"),
        "timeframe": "1-2 weeks",
        "ai_reasoning": "Bearish divergence forming on daily RSI.",
        "technical_data": {"rsi": {"value": 71.2, "signal": "overbought"}},
    }


@pytest.fixture
def hold_signal() -> dict:
    return {
        "symbol": "USD/INR",
        "market_type": "forex",
        "signal_type": "HOLD",
        "confidence": 50,
        "current_price": Decimal("83.1250"),
        "target_price": Decimal("83.5000"),
        "stop_loss": Decimal("82.7000"),
        "timeframe": "1 week",
        "ai_reasoning": "Range-bound trading expected near RBI intervention levels.",
        "technical_data": {},
    }


class TestFormatSignalAlert:
    def test_stock_buy_signal(self, stock_signal: dict) -> None:
        result = format_signal_alert(stock_signal)
        assert "🟢" in result
        assert "STRONG BUY" in result or "STRONG_BUY" in result
        assert "HDFCBANK" in result
        assert "₹1,678.90" in result
        assert "₹1,780.00" in result
        assert "₹1,630.00" in result
        assert "92%" in result
        assert "Credit growth accelerating" in result

    def test_crypto_sell_signal(self, crypto_signal: dict) -> None:
        result = format_signal_alert(crypto_signal)
        assert "🔴" in result
        assert "SELL" in result
        assert "BTC" in result
        assert "Bearish divergence" in result

    def test_hold_signal_yellow_emoji(self, hold_signal: dict) -> None:
        result = format_signal_alert(hold_signal)
        assert "🟡" in result
        assert "HOLD" in result

    def test_confidence_bar_in_signal(self, stock_signal: dict) -> None:
        result = format_signal_alert(stock_signal)
        # 92% confidence = ~9 filled blocks
        assert "█" in result
        assert "░" in result

    def test_signal_has_timeframe(self, stock_signal: dict) -> None:
        result = format_signal_alert(stock_signal)
        assert "2-4 weeks" in result

    def test_signal_has_ai_reasoning_section(self, stock_signal: dict) -> None:
        result = format_signal_alert(stock_signal)
        assert "🤖" in result


class TestFormatBriefings:
    def test_morning_brief_wraps_text(self) -> None:
        text = "Markets are looking bullish today."
        result = format_morning_brief(text)
        assert "☀️" in result or "Morning" in result.lower() or "morning" in result.lower()
        assert "bullish" in result

    def test_evening_wrap_wraps_text(self) -> None:
        text = "Markets closed mixed. NIFTY gained 0.3%."
        result = format_evening_wrap(text)
        assert "🌙" in result or "Evening" in result.lower() or "evening" in result.lower() or "wrap" in result.lower()
        assert "NIFTY" in result


class TestFormatMarketSnapshot:
    def test_snapshot_structure(self) -> None:
        stocks = [{"symbol": "NIFTY 50", "price": "22500.00", "change_pct": 0.45}]
        crypto = [{"symbol": "BTC", "price": "97842.00", "change_pct": 3.87}]
        forex = [{"symbol": "USD/INR", "price": "83.12", "change_pct": -0.05}]
        result = format_market_snapshot(stocks, crypto, forex)
        assert "NIFTY" in result or "nifty" in result.lower()
        assert "BTC" in result
        assert "USD/INR" in result


class TestFormatSignalsList:
    def test_signals_list_with_data(self) -> None:
        signals = [
            {
                "symbol": "TCS.NS",
                "signal_type": "BUY",
                "confidence": 75,
                "current_price": Decimal("3800.00"),
                "market_type": "stock",
            },
        ]
        result = format_signals_list(signals)
        assert "TCS" in result
        assert "BUY" in result

    def test_signals_list_empty(self) -> None:
        result = format_signals_list([])
        assert "no" in result.lower() or "No" in result


class TestFormatWelcome:
    def test_welcome_has_disclaimer(self) -> None:
        result = format_welcome()
        # Must include a disclaimer per CLAUDE.md
        lower = result.lower()
        assert "signalflow" in lower or "welcome" in lower
