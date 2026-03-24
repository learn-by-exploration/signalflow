"""Tests for signal feedback loop — adaptive weight computation."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.signal_gen.feedback import (
    DEFAULT_WEIGHTS,
    LEARNING_RATE,
    MIN_SIGNALS_FOR_ADJUSTMENT,
    compute_adaptive_weights,
    compute_indicator_accuracy,
    get_market_accuracy_summary,
)


class TestDefaultWeights:
    """Test that default weights are properly defined."""

    def test_weights_sum_to_one(self):
        total = sum(DEFAULT_WEIGHTS.values())
        assert abs(total - 1.0) < 0.001

    def test_all_indicators_present(self):
        expected = {"rsi", "macd", "bollinger", "volume", "sma_cross"}
        assert set(DEFAULT_WEIGHTS.keys()) == expected

    def test_learning_rate_between_zero_and_one(self):
        assert 0.0 < LEARNING_RATE <= 1.0

    def test_min_signals_is_positive(self):
        assert MIN_SIGNALS_FOR_ADJUSTMENT > 0


class TestComputeAdaptiveWeights:
    """Test the adaptive weight computation."""

    @pytest.mark.asyncio
    async def test_returns_defaults_when_insufficient_data(self):
        """When not enough resolved signals, return default weights."""
        mock_db = AsyncMock()
        # Return empty results (no resolved signals)
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        weights = await compute_adaptive_weights(mock_db)
        assert weights == DEFAULT_WEIGHTS

    @pytest.mark.asyncio
    async def test_weights_always_sum_to_one(self):
        """Adaptive weights must always sum to 1.0."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        weights = await compute_adaptive_weights(mock_db)
        total = sum(weights.values())
        assert abs(total - 1.0) < 0.001

    @pytest.mark.asyncio
    async def test_returns_dict_with_correct_keys(self):
        """Returned weights must have the same keys as DEFAULT_WEIGHTS."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        weights = await compute_adaptive_weights(mock_db)
        assert set(weights.keys()) == set(DEFAULT_WEIGHTS.keys())


class TestComputeIndicatorAccuracy:
    """Test per-indicator accuracy computation."""

    @pytest.mark.asyncio
    async def test_empty_history_returns_empty(self):
        """No resolved signals → no indicator stats."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        accuracy = await compute_indicator_accuracy(mock_db)
        assert accuracy == {}

    @pytest.mark.asyncio
    async def test_accepts_market_filter(self):
        """Should accept a market_type filter without error."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        accuracy = await compute_indicator_accuracy(mock_db, market_type="crypto")
        assert isinstance(accuracy, dict)


class TestMarketAccuracySummary:
    """Test per-market accuracy summary."""

    @pytest.mark.asyncio
    async def test_empty_when_no_data(self):
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        summary = await get_market_accuracy_summary(mock_db)
        assert summary == {}
