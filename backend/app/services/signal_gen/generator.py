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
from app.models.event_calendar import EventCalendar
from app.services.ai_engine.reasoner import AIReasoner
from app.services.ai_engine.sentiment import AISentimentEngine
from app.services.analysis.indicators import TechnicalAnalyzer
from app.services.signal_gen.scorer import compute_final_confidence
from app.services.signal_gen.targets import calculate_targets
from app.services.signal_gen.feedback import compute_adaptive_weights
from app.services.signal_gen.mtf_confirmation import (
    CONFIRMATION_TIMEFRAMES,
    apply_mtf_confirmation,
    compute_confirmation_score,
)
from app.services.data_ingestion.validators import is_spot_only_candle

logger = logging.getLogger(__name__)

# Minimum data points needed for meaningful analysis
MIN_DATA_POINTS = 50

# Cooldown period: don't generate a new signal for the same symbol within this window
SIGNAL_COOLDOWN_HOURS = 1

# High-impact event types that suppress signal generation
HIGH_IMPACT_EVENT_TYPES = {"fomc", "rbi_mpc", "ecb", "boj", "rba", "boe"}

# Hours before/after a high-impact event to suppress signals
EVENT_SUPPRESSION_HOURS = 4


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
        self.sentiment_engine = AISentimentEngine(
            redis_client=redis_client, db_session=db
        )
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
        # 0. Cooldown check — skip if a recent signal exists for this symbol
        if await self._has_recent_signal(symbol):
            logger.debug("Cooldown active for %s, skipping", symbol)
            return None

        # 0b. Event suppression — skip forex/stock signals near high-impact events
        if await self._is_event_suppressed(symbol, market_type):
            logger.info(
                "High-impact event within %dh for %s, suppressing signal",
                EVENT_SUPPRESSION_HOURS,
                symbol,
            )
            return None

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

        # 1b. Skip spot-only data (e.g. CoinGecko fallback with fabricated OHLCV)
        last_row = df.iloc[-1]
        if is_spot_only_candle({
            "open": last_row["open"],
            "high": last_row["high"],
            "low": last_row["low"],
            "close": last_row["close"],
        }):
            logger.info("Spot-only data for %s, skipping technical analysis", symbol)
            return None

        # 2. Run technical analysis
        analyzer = TechnicalAnalyzer(df)
        technical_data = analyzer.full_analysis()

        # 3. Run AI sentiment analysis
        sentiment_data = await self.sentiment_engine.analyze_sentiment(symbol, market_type)

        # 3b. Get adaptive weights from feedback loop
        adaptive_weights = await compute_adaptive_weights(self.db, market_type)

        # 4. Score and determine signal type
        confidence, signal_type = compute_final_confidence(
            technical_data, sentiment_data, adaptive_weights=adaptive_weights
        )

        # 4b. Multi-timeframe confirmation
        tf_config = CONFIRMATION_TIMEFRAMES.get(market_type)
        if tf_config and tf_config["confirmation"] != tf_config["primary"]:
            df_confirm = await self._fetch_market_data(
                symbol, timeframe=tf_config["confirmation"]
            )
            if df_confirm is not None and len(df_confirm) >= 20:
                confirm_score = compute_confirmation_score(df_confirm)
                confidence, signal_type = apply_mtf_confirmation(
                    confidence, signal_type, confirm_score
                )

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

        # 8. Link signal to news events
        await self._link_news_events(signal.id, sentiment_data)

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

    async def _fetch_market_data(self, symbol: str, timeframe: str = "1d") -> pd.DataFrame | None:
        """Fetch the latest OHLCV data from the database for a symbol.

        Args:
            symbol: Market symbol to fetch data for.
            timeframe: Data timeframe — '1d', '4h', '1h', '1w'. Defaults to '1d'.

        Returns a pandas DataFrame sorted by timestamp ascending, or None.
        """
        # Normalize symbol: strip .NS suffix for DB lookup (indian_stocks stores without it)
        query_symbol = symbol.replace(".NS", "")

        stmt = (
            select(
                MarketData.open,
                MarketData.high,
                MarketData.low,
                MarketData.close,
                MarketData.volume,
                MarketData.timestamp,
            )
            .where(MarketData.symbol == query_symbol)
            .where(MarketData.timeframe == timeframe)
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

    async def _has_recent_signal(self, symbol: str) -> bool:
        """Check if a signal was generated for this symbol within the cooldown period.

        Uses FOR UPDATE SKIP LOCKED to prevent TOCTOU races — if another worker
        is already generating a signal for this symbol, we skip it.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(hours=SIGNAL_COOLDOWN_HOURS)
        stmt = (
            select(Signal.id)
            .where(Signal.symbol == symbol, Signal.created_at >= cutoff)
            .with_for_update(skip_locked=True)
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def _is_event_suppressed(self, symbol: str, market_type: str) -> bool:
        """Check if a high-impact economic event is scheduled near now.

        Suppresses forex signals within ±EVENT_SUPPRESSION_HOURS of FOMC, RBI MPC,
        ECB, BOJ, etc. Also suppresses stock signals near earnings for the specific symbol.

        Args:
            symbol: Market symbol.
            market_type: stock, crypto, or forex.

        Returns:
            True if signal generation should be suppressed.
        """
        # Crypto is never suppressed by central bank events
        if market_type == "crypto":
            return False

        now = datetime.now(timezone.utc)
        window_start = now - timedelta(hours=EVENT_SUPPRESSION_HOURS)
        window_end = now + timedelta(hours=EVENT_SUPPRESSION_HOURS)

        # Check for high-impact events affecting this market
        stmt = (
            select(EventCalendar.id)
            .where(
                EventCalendar.scheduled_at >= window_start,
                EventCalendar.scheduled_at <= window_end,
                EventCalendar.is_completed == False,  # noqa: E712
                EventCalendar.impact_magnitude >= 4,
            )
        )

        if market_type == "forex":
            # Suppress forex near any central bank event
            stmt = stmt.where(EventCalendar.event_type.in_(HIGH_IMPACT_EVENT_TYPES))
        elif market_type == "stock":
            # Suppress stock signals only for earnings events affecting this symbol
            stmt = stmt.where(
                EventCalendar.event_type == "earnings",
                EventCalendar.affected_symbols.contains([symbol]),
            )

        stmt = stmt.limit(1)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def _link_news_events(
        self, signal_id: Any, sentiment_data: dict[str, Any] | None
    ) -> None:
        """Create SignalNewsLink records to connect a signal to its news events."""
        if not sentiment_data:
            return

        news_event_ids = sentiment_data.get("news_event_ids", [])
        if not news_event_ids:
            return

        try:
            from app.models.signal_news_link import SignalNewsLink
            import uuid

            for event_id_str in news_event_ids[:10]:
                link = SignalNewsLink(
                    signal_id=signal_id,
                    news_event_id=uuid.UUID(event_id_str),
                )
                self.db.add(link)
            await self.db.flush()
        except Exception:
            logger.warning("Failed to link news events to signal %s", signal_id)
