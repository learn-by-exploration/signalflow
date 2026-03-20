"""Tests for target price and stop-loss calculator."""

from decimal import Decimal

import pytest

from app.services.signal_gen.targets import calculate_targets


class TestCalculateTargets:
    """Test target and stop-loss calculations."""

    def test_buy_signal_targets(self) -> None:
        result = calculate_targets(
            current_price=Decimal("100.00"),
            atr_data={"value": 5.0},
            signal_type="BUY",
            market_type="stock",
        )
        assert result["target_price"] == Decimal("110.00000000")  # 100 + 5*2
        assert result["stop_loss"] == Decimal("95.00000000")      # 100 - 5*1
        assert result["timeframe"] == "2-4 weeks"

    def test_strong_buy_same_as_buy(self) -> None:
        result = calculate_targets(
            current_price=Decimal("100.00"),
            atr_data={"value": 5.0},
            signal_type="STRONG_BUY",
            market_type="stock",
        )
        assert result["target_price"] > result["stop_loss"]

    def test_sell_signal_targets(self) -> None:
        result = calculate_targets(
            current_price=Decimal("100.00"),
            atr_data={"value": 5.0},
            signal_type="SELL",
            market_type="stock",
        )
        assert result["target_price"] == Decimal("90.00000000")   # 100 - 5*2
        assert result["stop_loss"] == Decimal("105.00000000")     # 100 + 5*1

    def test_strong_sell_same_as_sell(self) -> None:
        result = calculate_targets(
            current_price=Decimal("100.00"),
            atr_data={"value": 5.0},
            signal_type="STRONG_SELL",
            market_type="stock",
        )
        assert result["target_price"] < Decimal("100.00")
        assert result["stop_loss"] > Decimal("100.00")

    def test_hold_signal(self) -> None:
        result = calculate_targets(
            current_price=Decimal("100.00"),
            atr_data={"value": 5.0},
            signal_type="HOLD",
            market_type="stock",
        )
        assert result["target_price"] is not None
        assert result["stop_loss"] is not None

    def test_risk_reward_ratio(self) -> None:
        """Risk:Reward should always be >= 1:2."""
        result = calculate_targets(
            current_price=Decimal("100.00"),
            atr_data={"value": 5.0},
            signal_type="BUY",
            market_type="stock",
        )
        reward = result["target_price"] - Decimal("100.00")
        risk = Decimal("100.00") - result["stop_loss"]
        assert reward / risk >= 2  # 1:2 ratio

    def test_atr_fallback_when_none(self) -> None:
        result = calculate_targets(
            current_price=Decimal("100.00"),
            atr_data={"value": None},
            signal_type="BUY",
            market_type="stock",
        )
        # Should use 2% fallback
        assert result["target_price"] == Decimal("104.00000000")  # 100 + 2*2
        assert result["stop_loss"] == Decimal("98.00000000")      # 100 - 2*1

    def test_crypto_timeframe(self) -> None:
        result = calculate_targets(
            current_price=Decimal("50000.00"),
            atr_data={"value": 1000.0},
            signal_type="BUY",
            market_type="crypto",
        )
        assert result["timeframe"] == "3-7 days"

    def test_forex_timeframe(self) -> None:
        result = calculate_targets(
            current_price=Decimal("83.50"),
            atr_data={"value": 0.30},
            signal_type="SELL",
            market_type="forex",
        )
        assert result["timeframe"] == "1-3 days"

    def test_non_negative_prices(self) -> None:
        """Targets should never go negative."""
        result = calculate_targets(
            current_price=Decimal("1.00"),
            atr_data={"value": 5.0},
            signal_type="SELL",
            market_type="forex",
        )
        assert result["target_price"] >= 0
        assert result["stop_loss"] >= 0
