"""Seed demo signals for new users.

Creates 5 realistic historical signals with pre-written AI reasoning
so new users never see an empty dashboard.
"""

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.orm import Session


DEMO_SIGNALS = [
    {
        "symbol": "HDFCBANK",
        "market_type": "stock",
        "signal_type": "STRONG_BUY",
        "confidence": 88,
        "current_price": Decimal("1678.90"),
        "target_price": Decimal("1780.00"),
        "stop_loss": Decimal("1630.00"),
        "timeframe": "2-4 weeks",
        "ai_reasoning": (
            "Credit growth accelerating at 18% YoY with expanding net interest margins. "
            "RSI at 62 with bullish MACD crossover confirms upward momentum. "
            "Watch for quarterly earnings as a confirmation catalyst."
        ),
        "technical_data": {
            "rsi": {"value": 62.3, "signal": "bullish", "strength": 70},
            "macd": {"value": 4.2, "signal": "bullish", "histogram": 1.8, "strength": 75},
            "bollinger": {"position": 0.72, "signal": "neutral", "strength": 55},
            "volume": {"ratio": 1.3, "signal": "bullish", "strength": 65},
            "sma_cross": {"signal": "bullish", "strength": 80},
            "atr": {"value": 28.5, "atr_pct": 1.7},
        },
        "sentiment_data": {"score": 78, "key_factors": ["Credit growth", "NIM expansion"]},
        "hours_ago": 6,
    },
    {
        "symbol": "BTCUSDT",
        "market_type": "crypto",
        "signal_type": "BUY",
        "confidence": 74,
        "current_price": Decimal("97842.00"),
        "target_price": Decimal("105000.00"),
        "stop_loss": Decimal("93500.00"),
        "timeframe": "1-2 weeks",
        "ai_reasoning": (
            "Bitcoin consolidating above key $95K support with increasing volume. "
            "MACD histogram turning positive on daily timeframe. "
            "Monitor ETF inflow data for confirmation of institutional buying."
        ),
        "technical_data": {
            "rsi": {"value": 55.1, "signal": "neutral", "strength": 52},
            "macd": {"value": 120.5, "signal": "bullish", "histogram": 45.3, "strength": 68},
            "bollinger": {"position": 0.58, "signal": "neutral", "strength": 50},
            "volume": {"ratio": 1.15, "signal": "neutral", "strength": 55},
            "sma_cross": {"signal": "bullish", "strength": 72},
            "atr": {"value": 2200, "atr_pct": 2.2},
        },
        "sentiment_data": {"score": 65, "key_factors": ["ETF inflows", "Support hold"]},
        "hours_ago": 12,
    },
    {
        "symbol": "EUR/USD",
        "market_type": "forex",
        "signal_type": "SELL",
        "confidence": 71,
        "current_price": Decimal("1.08520"),
        "target_price": Decimal("1.07800"),
        "stop_loss": Decimal("1.09100"),
        "timeframe": "3-5 days",
        "ai_reasoning": (
            "EUR/USD breaking below 20-day SMA with bearish RSI divergence. "
            "ECB dovish forward guidance contrasts with Fed hawkish stance. "
            "Key risk: upcoming US NFP data could reverse the move."
        ),
        "technical_data": {
            "rsi": {"value": 38.4, "signal": "bearish", "strength": 65},
            "macd": {"value": -0.0015, "signal": "bearish", "histogram": -0.0008, "strength": 62},
            "bollinger": {"position": 0.22, "signal": "bearish", "strength": 70},
            "volume": {"ratio": 1.0, "signal": "neutral", "strength": 50},
            "sma_cross": {"signal": "bearish", "strength": 68},
            "atr": {"value": 0.0062, "atr_pct": 0.57},
        },
        "sentiment_data": {"score": 35, "key_factors": ["ECB dovish", "USD strength"]},
        "hours_ago": 24,
    },
    {
        "symbol": "TCS",
        "market_type": "stock",
        "signal_type": "BUY",
        "confidence": 69,
        "current_price": Decimal("4125.50"),
        "target_price": Decimal("4350.00"),
        "stop_loss": Decimal("3980.00"),
        "timeframe": "2-3 weeks",
        "ai_reasoning": (
            "IT sector seeing deal pipeline recovery with large deal TCV up 22%. "
            "RSI recovering from oversold territory with volume confirmation. "
            "Watch for NASSCOM guidance revision as sector catalyst."
        ),
        "technical_data": {
            "rsi": {"value": 48.5, "signal": "neutral", "strength": 50},
            "macd": {"value": 8.3, "signal": "bullish", "histogram": 3.1, "strength": 60},
            "bollinger": {"position": 0.45, "signal": "neutral", "strength": 48},
            "volume": {"ratio": 1.4, "signal": "bullish", "strength": 70},
            "sma_cross": {"signal": "bullish", "strength": 65},
            "atr": {"value": 85, "atr_pct": 2.1},
        },
        "sentiment_data": {"score": 62, "key_factors": ["Deal pipeline", "TCV recovery"]},
        "hours_ago": 48,
    },
    {
        "symbol": "ETHUSDT",
        "market_type": "crypto",
        "signal_type": "STRONG_BUY",
        "confidence": 82,
        "current_price": Decimal("3450.00"),
        "target_price": Decimal("3800.00"),
        "stop_loss": Decimal("3250.00"),
        "timeframe": "1-3 weeks",
        "ai_reasoning": (
            "Ethereum showing strong accumulation pattern with DeFi TVL rising 15% this month. "
            "RSI bullish divergence on daily chart with increasing on-chain activity. "
            "Upcoming protocol upgrade could be a positive catalyst."
        ),
        "technical_data": {
            "rsi": {"value": 64.8, "signal": "bullish", "strength": 72},
            "macd": {"value": 35.2, "signal": "bullish", "histogram": 18.5, "strength": 78},
            "bollinger": {"position": 0.75, "signal": "bullish", "strength": 65},
            "volume": {"ratio": 1.5, "signal": "bullish", "strength": 75},
            "sma_cross": {"signal": "bullish", "strength": 80},
            "atr": {"value": 120, "atr_pct": 3.5},
        },
        "sentiment_data": {"score": 80, "key_factors": ["DeFi TVL growth", "Protocol upgrade"]},
        "hours_ago": 3,
    },
]


def seed_demo_signals(engine) -> int:
    """Insert demo signals into the database.

    Args:
        engine: SQLAlchemy engine.

    Returns:
        Number of signals seeded.
    """
    import json

    now = datetime.now(timezone.utc)
    count = 0

    with Session(engine) as session:
        for sig in DEMO_SIGNALS:
            signal_id = str(uuid.uuid4())
            created_at = now - timedelta(hours=sig["hours_ago"])
            expires_at = created_at + timedelta(days=7)

            session.execute(
                text(
                    "INSERT INTO signals (id, symbol, market_type, signal_type, confidence, "
                    "current_price, target_price, stop_loss, timeframe, ai_reasoning, "
                    "technical_data, sentiment_data, is_active, created_at, expires_at) "
                    "VALUES (:id, :symbol, :market_type, :signal_type, :confidence, "
                    ":current_price, :target_price, :stop_loss, :timeframe, :ai_reasoning, "
                    ":technical_data, :sentiment_data, :is_active, :created_at, :expires_at) "
                    "ON CONFLICT DO NOTHING"
                ),
                {
                    "id": signal_id,
                    "symbol": sig["symbol"],
                    "market_type": sig["market_type"],
                    "signal_type": sig["signal_type"],
                    "confidence": sig["confidence"],
                    "current_price": str(sig["current_price"]),
                    "target_price": str(sig["target_price"]),
                    "stop_loss": str(sig["stop_loss"]),
                    "timeframe": sig["timeframe"],
                    "ai_reasoning": sig["ai_reasoning"],
                    "technical_data": json.dumps(sig["technical_data"]),
                    "sentiment_data": json.dumps(sig["sentiment_data"]),
                    "is_active": True,
                    "created_at": created_at,
                    "expires_at": expires_at,
                },
            )
            count += 1

        session.commit()

    return count


if __name__ == "__main__":
    from app.config import get_settings
    from sqlalchemy import create_engine

    settings = get_settings()
    engine = create_engine(settings.database_url_sync)
    n = seed_demo_signals(engine)
    print(f"Seeded {n} demo signals")
