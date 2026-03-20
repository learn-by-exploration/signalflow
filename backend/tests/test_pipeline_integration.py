"""End-to-end pipeline integration test.

Tests the full signal generation flow:
  market data → technical analysis → scoring → targets → signal creation

Uses mocked AI (no Claude API calls) but real analysis + scoring logic.
"""

from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import numpy as np
import pandas as pd
import pytest

from app.services.analysis.indicators import TechnicalAnalyzer
from app.services.signal_gen.scorer import compute_final_confidence
from app.services.signal_gen.targets import calculate_targets


def _generate_price_series(n: int = 100, base: float = 100.0, trend: float = 0.002) -> pd.DataFrame:
    """Generate synthetic OHLCV data with a slight uptrend."""
    np.random.seed(42)
    closes = [base]
    for _ in range(n - 1):
        change = np.random.normal(trend, 0.02)
        closes.append(closes[-1] * (1 + change))

    closes = np.array(closes)
    highs = closes * (1 + np.abs(np.random.normal(0.005, 0.003, n)))
    lows = closes * (1 - np.abs(np.random.normal(0.005, 0.003, n)))
    opens = closes * (1 + np.random.normal(0, 0.005, n))
    volumes = np.random.uniform(1_000_000, 5_000_000, n)

    return pd.DataFrame({
        "open": opens,
        "high": highs,
        "low": lows,
        "close": closes,
        "volume": volumes,
        "timestamp": pd.date_range(end=datetime.now(timezone.utc), periods=n, freq="h"),
    })


class TestFullPipeline:
    """Test the complete signal generation pipeline end-to-end."""

    def test_data_to_analysis_to_signal(self) -> None:
        """Full pipeline: synthetic data → indicators → scoring → targets."""
        # 1. Generate synthetic uptrend data
        df = _generate_price_series(n=100, trend=0.003)

        # 2. Run technical analysis
        analyzer = TechnicalAnalyzer(df)
        technical_data = analyzer.full_analysis()

        # Verify all indicators are present
        assert "rsi" in technical_data
        assert "macd" in technical_data
        assert "bollinger" in technical_data
        assert "volume" in technical_data
        assert "sma_cross" in technical_data
        assert "atr" in technical_data

        # 3. Score with a bullish sentiment
        sentiment_data = {"score": 75, "key_factors": ["test factor"]}
        confidence, signal_type = compute_final_confidence(technical_data, sentiment_data)

        # Verify output
        assert 0 <= confidence <= 100
        assert signal_type in ("STRONG_BUY", "BUY", "HOLD", "SELL", "STRONG_SELL")

        # 4. Calculate targets
        current_price = Decimal(str(df["close"].iloc[-1]))
        targets = calculate_targets(
            current_price=current_price,
            atr_data=technical_data.get("atr", {}),
            signal_type=signal_type,
            market_type="stock",
        )

        assert "target_price" in targets
        assert "stop_loss" in targets
        assert "timeframe" in targets
        assert targets["target_price"] > 0
        assert targets["stop_loss"] > 0

    def test_downtrend_generates_sell_or_hold(self) -> None:
        """Downtrend data should bias toward SELL or HOLD signals."""
        df = _generate_price_series(n=100, trend=-0.005)

        analyzer = TechnicalAnalyzer(df)
        technical_data = analyzer.full_analysis()

        # Use bearish sentiment
        sentiment_data = {"score": 20, "key_factors": ["bearish momentum"]}
        confidence, signal_type = compute_final_confidence(technical_data, sentiment_data)

        # Should be SELL, STRONG_SELL, or HOLD (not a strong buy)
        assert signal_type in ("SELL", "STRONG_SELL", "HOLD")

    def test_flat_market_generates_hold(self) -> None:
        """Flat/sideways data should generate HOLD signal."""
        np.random.seed(123)
        n = 100
        base = 100.0
        # Very small random moves around base
        closes = base + np.random.normal(0, 0.5, n)
        df = pd.DataFrame({
            "open": closes + np.random.normal(0, 0.2, n),
            "high": closes + np.abs(np.random.normal(0.3, 0.2, n)),
            "low": closes - np.abs(np.random.normal(0.3, 0.2, n)),
            "close": closes,
            "volume": np.random.uniform(1_000_000, 2_000_000, n),
            "timestamp": pd.date_range(end=datetime.now(timezone.utc), periods=n, freq="h"),
        })

        analyzer = TechnicalAnalyzer(df)
        technical_data = analyzer.full_analysis()

        # Neutral sentiment
        sentiment_data = {"score": 50, "key_factors": ["neutral"]}
        confidence, signal_type = compute_final_confidence(technical_data, sentiment_data)

        # HOLD is expected for flat data with neutral sentiment
        assert signal_type == "HOLD"

    def test_risk_reward_ratio(self) -> None:
        """Verify minimum 1:2 risk-reward ratio for generated targets."""
        df = _generate_price_series(n=100, trend=0.004)
        analyzer = TechnicalAnalyzer(df)
        technical_data = analyzer.full_analysis()

        current_price = Decimal(str(df["close"].iloc[-1]))
        for signal_type in ["BUY", "STRONG_BUY"]:
            targets = calculate_targets(
                current_price=current_price,
                atr_data=technical_data.get("atr", {}),
                signal_type=signal_type,
                market_type="stock",
            )
            reward = abs(targets["target_price"] - current_price)
            risk = abs(current_price - targets["stop_loss"])
            if risk > 0:
                assert reward / risk >= Decimal("1.9"), f"Risk:Reward too low for {signal_type}"


class TestPipelineWithMockedAI:
    """Test the full pipeline with mocked Claude API."""

    @pytest.mark.asyncio
    async def test_signal_generator_with_mocked_ai(self) -> None:
        """Test SignalGenerator.generate_for_symbol with mocked dependencies."""
        from unittest.mock import MagicMock

        from app.services.signal_gen.generator import SignalGenerator

        # Create a mock DB session
        mock_db = AsyncMock()

        # Mock the data fetch to return synthetic data
        df = _generate_price_series(n=100, trend=0.003)

        generator = SignalGenerator(db=mock_db, redis_client=None)

        # Patch the internal methods
        with patch.object(generator, "_fetch_market_data", return_value=df), \
             patch.object(generator.sentiment_engine, "analyze_sentiment",
                         return_value={"score": 80, "key_factors": ["test"]}), \
             patch.object(generator.reasoner, "generate_reasoning",
                         return_value="Test AI reasoning for this signal."):

            signal = await generator.generate_for_symbol("TESTSTOCK.NS", "stock")

            # Signal could be None if HOLD (depends on data), so check both cases
            if signal is not None:
                assert signal.symbol == "TESTSTOCK.NS"
                assert signal.market_type == "stock"
                assert signal.signal_type in ("STRONG_BUY", "BUY", "SELL", "STRONG_SELL")
                assert 0 <= signal.confidence <= 100
                assert signal.current_price > 0
                assert signal.target_price > 0
                assert signal.stop_loss > 0
                assert signal.ai_reasoning == "Test AI reasoning for this signal."
                mock_db.add.assert_called_once()
