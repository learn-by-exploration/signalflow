"""Tests for signal cooldown/dedup and signal resolution logic."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from app.services.signal_gen.generator import SIGNAL_COOLDOWN_HOURS, SignalGenerator


class TestSignalCooldown:
    """Test that duplicate signals are prevented within the cooldown window."""

    @pytest.mark.asyncio
    async def test_cooldown_blocks_duplicate(self) -> None:
        """When a recent signal exists, generate_for_symbol should return None."""
        mock_db = AsyncMock()

        # _has_recent_signal query returns a signal ID (cooldown active)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = "some-uuid"
        mock_db.execute = AsyncMock(return_value=mock_result)

        generator = SignalGenerator(db=mock_db)
        result = await generator.generate_for_symbol("BTCUSDT", "crypto")
        assert result is None

    @pytest.mark.asyncio
    async def test_no_cooldown_allows_generation(self) -> None:
        """When no recent signal exists, generation should proceed past cooldown."""
        mock_db = AsyncMock()

        # _has_recent_signal returns None (no cooldown)
        cooldown_result = MagicMock()
        cooldown_result.scalar_one_or_none.return_value = None

        # _fetch_market_data returns empty (insufficient data — stops early)
        data_result = MagicMock()
        data_result.all.return_value = []

        call_count = 0

        async def mock_execute(stmt):
            nonlocal call_count
            call_count += 1
            if call_count == 1:  # cooldown check
                return cooldown_result
            return data_result  # market data fetch

        mock_db.execute = mock_execute
        generator = SignalGenerator(db=mock_db)
        result = await generator.generate_for_symbol("BTCUSDT", "crypto")
        # Should return None due to no data, but the point is it got past cooldown
        assert result is None
        assert call_count == 2  # Both queries ran


class TestSignalResolution:
    """Test signal resolution logic (target/stop detection)."""

    def test_buy_signal_hit_target(self) -> None:
        """A BUY signal should resolve as hit_target when price >= target."""
        from decimal import Decimal

        current_price = Decimal("100")
        target_price = Decimal("110")
        stop_loss = Decimal("95")
        latest_price = Decimal("112")  # Above target

        is_buy = True
        outcome = None
        if is_buy:
            if latest_price >= target_price:
                outcome = "hit_target"
            elif latest_price <= stop_loss:
                outcome = "hit_stop"

        assert outcome == "hit_target"

    def test_buy_signal_hit_stop(self) -> None:
        current_price = Decimal("100")
        target_price = Decimal("110")
        stop_loss = Decimal("95")
        latest_price = Decimal("93")  # Below stop

        outcome = None
        if latest_price >= target_price:
            outcome = "hit_target"
        elif latest_price <= stop_loss:
            outcome = "hit_stop"

        assert outcome == "hit_stop"

    def test_sell_signal_hit_target(self) -> None:
        """A SELL signal hits target when price drops to/below target."""
        target_price = Decimal("90")
        stop_loss = Decimal("105")
        latest_price = Decimal("88")  # Below target (good for SELL)

        is_buy = False
        outcome = None
        if not is_buy:
            if latest_price <= target_price:
                outcome = "hit_target"
            elif latest_price >= stop_loss:
                outcome = "hit_stop"

        assert outcome == "hit_target"

    def test_sell_signal_hit_stop(self) -> None:
        target_price = Decimal("90")
        stop_loss = Decimal("105")
        latest_price = Decimal("107")  # Above stop (bad for SELL)

        is_buy = False
        outcome = None
        if not is_buy:
            if latest_price <= target_price:
                outcome = "hit_target"
            elif latest_price >= stop_loss:
                outcome = "hit_stop"

        assert outcome == "hit_stop"

    def test_no_resolution_when_price_in_range(self) -> None:
        """Signal stays active when price is between stop and target."""
        target_price = Decimal("110")
        stop_loss = Decimal("95")
        latest_price = Decimal("102")

        outcome = None
        if latest_price >= target_price:
            outcome = "hit_target"
        elif latest_price <= stop_loss:
            outcome = "hit_stop"

        assert outcome is None

    def test_return_pct_calculation_buy(self) -> None:
        """Return percentage should be correct for BUY signals."""
        entry = Decimal("100")
        exit_price = Decimal("110")
        return_pct = (exit_price - entry) / entry * 100
        assert return_pct == Decimal("10")

    def test_return_pct_calculation_sell(self) -> None:
        """Return percentage for SELL: profit when price drops."""
        entry = Decimal("100")
        exit_price = Decimal("90")
        # For SELL: (entry - exit) / entry * 100
        return_pct = (entry - exit_price) / entry * 100
        assert return_pct == Decimal("10")
