"""Signal generation orchestrator.

Coordinates technical analysis, AI sentiment, scoring, target calculation,
and AI reasoning to produce complete trading signals and persist them.
"""

import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import pandas as pd
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.market_data import MarketData
from app.models.signal import Signal
from app.services.ai_engine.reasoner import AIReasoner
from app.services.ai_engine.sentiment import AISentimentEngine
from app.services.analysis.indicators import TechnicalAnalyzer
from app.services.signal_gen.scorer import compute_final_confidence
from app.services.signal_gen.targets import calculate_targets

logger = logging.getLogger(__name__)

# Minimum data points needed for meaningful analysis
MIN_DATA_POINTS = 50

# Symbols that map to short display names
SYMBOL_DISPLAY = {
    ".NS": "stock",  # suffix check
    "USDT": "crypto",  # suffix check
    "/": "forex",  # contains check
}


def detect_market_type(symbol: str) -> str:
    """Detect market type from symbol string."""
    if symbol.endswith(".NS"):
        return "stock"
    if symbol.endswith("USDT"):
        return "crypto"
    if "/" in symbol:
        return "forex"
    return "stock"


class SignalGenerator:
    """Orchestrate signal generation for all tracked symbols.

    Args:
        db: Async database session.
        redis_client: Optional Redis client for sentiment caching.
    """

    def __init__(self, db: AsyncSession, redis_client: Any | None = None) -> None:
        self.db = db
        self.settings = get_settings()
        self.sentiment_engine = AISentimentEngine(redis_client=redis_client)
        self.reasoner = AIReasoner()

    async def generate_all(self) -> list[Signal]:
        """Generate signals for all tracked symbols across all markets.

        Returns:
            List of newly created Signal objects.
        """
        all_symbols = (
            [(s, "stock") for s in self.settings.tracked_stocks]
            + [(s, "crypto") for s in self.settings.tracked_crypto]
            + [(s, "forex") for s in self.settings.tracked_forex]
        )

        signals: list[Signal] = []
        for symbol, market_type in all_symbols:
            try:
                signal = await self.generate_for_symbol(symbol, market_type)
                if signal:
                    signals.append(signal)
            except Exception:
                logger.exception("Failed to generate signal for %s", symbol)

        logger.info("Generated %d signals out of %d symbols", len(signals), len(all_symbols))
        return signals

    async def generate_for_symbol(
        self, symbol: str, market_type: str
    ) -> Signal | None:
        """Generate a signal for a single symbol.

        Args:
            symbol: Market symbol.
            market_type: stock, crypto, or forex.

        Returns:
            Signal object if generated, None if insufficient data or HOLD.
        """
        # 1. Fetch recent market data
        df = await self._fetch_market_data(symbol)
        if df is None or len(df) < MIN_DATA_POINTS:
            logger.info(
                "Insufficient data for %s (%d points, need %d)",
                symbol,
                len(df) if df is not None else 0,
                MIN_DATA_POINTS,
            )
            return None

        # 2. Run technical analysis
        analyzer = TechnicalAnalyzer(df)
        technical_data = analyzer.full_analysis()

        # 3. Run AI sentiment analysis
        sentiment_data = await self.sentiment_engine.analyze_sentiment(symbol, market_type)

        # 4. Score and determine signal type
        confidence, signal_type = compute_final_confidence(technical_data, sentiment_data)

        # Skip HOLD signals — only generate actionable signals
        if signal_type == "HOLD":
            logger.debug("HOLD signal for %s (confidence=%d), skipping", symbol, confidence)
            return None

        # 5. Calculate target and stop-loss
        current_price = Decimal(str(df["close"].iloc[-1]))
        targets = calculate_targets(
            current_price=current_price,
            atr_data=technical_data.get("atr", {}),
            signal_type=signal_type,
            market_type=market_type,
        )

        # 6. Generate AI reasoning
        ai_reasoning = await self.reasoner.generate_reasoning(
            symbol=symbol,
            signal_type=signal_type,
            confidence=confidence,
            technical_data=technical_data,
            sentiment_data=sentiment_data,
        )

        # 7. Create and persist signal
        signal = Signal(
            symbol=symbol,
            market_type=market_type,
            signal_type=signal_type,
            confidence=confidence,
            current_price=current_price,
            target_price=targets["target_price"],
            stop_loss=targets["stop_loss"],
            timeframe=targets["timeframe"],
            ai_reasoning=ai_reasoning,
            technical_data=technical_data,
            sentiment_data=sentiment_data,
            is_active=True,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )

        self.db.add(signal)
        await self.db.flush()

        logger.info(
            "Signal: %s %s — %s (confidence=%d, target=%s, stop=%s)",
            signal_type,
            symbol,
            market_type,
            confidence,
            targets["target_price"],
            targets["stop_loss"],
        )

        return signal

    async def _fetch_market_data(self, symbol: str) -> pd.DataFrame | None:
        """Fetch the latest OHLCV data from the database for a symbol.

        Returns a pandas DataFrame sorted by timestamp ascending, or None.
        """
        stmt = (
            select(
                MarketData.open,
                MarketData.high,
                MarketData.low,
                MarketData.close,
                MarketData.volume,
                MarketData.timestamp,
            )
            .where(MarketData.symbol == symbol)
            .order_by(MarketData.timestamp.desc())
            .limit(250)  # ~1 year of daily data
        )

        result = await self.db.execute(stmt)
        rows = result.all()

        if not rows:
            return None

        df = pd.DataFrame(rows, columns=["open", "high", "low", "close", "volume", "timestamp"])
        # Convert Decimal columns to float for pandas calculations
        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = df[col].astype(float)

        # Sort ascending by time for indicator calculations
        df = df.sort_values("timestamp").reset_index(drop=True)
        return df
