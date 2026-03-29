"""Seed script — populate dummy data for dry run.

Assumes tables already exist (via Alembic migrations).
Run: cd backend && PYTHONPATH=. alembic upgrade head  (if tables don't exist)
"""

import asyncio
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# ── Database URL from env or default for local dev ──
import os
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/signalflow",
)


async def main() -> None:
    engine = create_async_engine(DATABASE_URL, echo=False)

    # ──────────── Seed dummy data ────────────
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    now = datetime.now(timezone.utc)

    async with session_factory() as session:
        # ── Clear old seed data ──
        await session.execute(text("DELETE FROM signal_history"))
        await session.execute(text("DELETE FROM signals"))
        await session.execute(text("DELETE FROM market_data"))
        await session.commit()

        # ──────────── Market Data (recent candles) ────────────
        market_rows = []

        # Indian Stocks
        stocks = [
            ("RELIANCE.NS", "stock", 2920, 2950, 2910, 2945, 12_500_000),
            ("HDFCBANK.NS", "stock", 1670, 1695, 1665, 1682, 8_300_000),
            ("TCS.NS", "stock", 3780, 3820, 3770, 3810, 3_200_000),
            ("INFY.NS", "stock", 1520, 1545, 1510, 1538, 6_100_000),
            ("ITC.NS", "stock", 445, 452, 443, 449, 15_800_000),
            ("ICICIBANK.NS", "stock", 1120, 1140, 1115, 1135, 7_400_000),
        ]
        for sym, mt, o, h, l, c, v in stocks:
            for i in range(20):
                ts = now - timedelta(hours=i)
                drift = (20 - i) * 0.002  # slight uptrend
                market_rows.append(
                    f"('{sym}', '{mt}', {o * (1 + drift):.8f}, {h * (1 + drift):.8f}, "
                    f"{l * (1 + drift):.8f}, {c * (1 + drift):.8f}, {v}, "
                    f"'{ts.isoformat()}')"
                )

        # Crypto
        cryptos = [
            ("BTCUSDT", "crypto", 97500, 98200, 96800, 97842, 45_000),
            ("ETHUSDT", "crypto", 3350, 3420, 3320, 3395, 320_000),
            ("SOLUSDT", "crypto", 168, 175, 165, 172, 2_800_000),
        ]
        for sym, mt, o, h, l, c, v in cryptos:
            for i in range(20):
                ts = now - timedelta(hours=i)
                drift = (20 - i) * 0.003
                market_rows.append(
                    f"('{sym}', '{mt}', {o * (1 + drift):.8f}, {h * (1 + drift):.8f}, "
                    f"{l * (1 + drift):.8f}, {c * (1 + drift):.8f}, {v}, "
                    f"'{ts.isoformat()}')"
                )

        # Forex
        forex_pairs = [
            ("USD/INR", "forex", 83.10, 83.25, 83.02, 83.15, None),
            ("EUR/USD", "forex", 1.0850, 1.0880, 1.0830, 1.0865, None),
            ("GBP/JPY", "forex", 188.50, 189.20, 188.10, 188.85, None),
        ]
        for sym, mt, o, h, l, c, v in forex_pairs:
            for i in range(20):
                ts = now - timedelta(hours=i)
                drift = (20 - i) * 0.0005
                vol_part = f"{v}" if v else "NULL"
                market_rows.append(
                    f"('{sym}', '{mt}', {o * (1 + drift):.8f}, {h * (1 + drift):.8f}, "
                    f"{l * (1 + drift):.8f}, {c * (1 + drift):.8f}, {vol_part}, "
                    f"'{ts.isoformat()}')"
                )

        # Bulk insert market data
        values_str = ",\n".join(market_rows)
        await session.execute(text(f"""
            INSERT INTO market_data (symbol, market_type, open, high, low, close, volume, timestamp)
            VALUES {values_str}
        """))
        print(f"✅ Inserted {len(market_rows)} market data rows")

        # ──────────── Signals ────────────
        signals_data = [
            # Indian Stocks
            {
                "id": str(uuid.uuid4()),
                "symbol": "HDFCBANK.NS",
                "market_type": "stock",
                "signal_type": "STRONG_BUY",
                "confidence": 92,
                "current_price": "1682.00",
                "target_price": "1780.00",
                "stop_loss": "1630.00",
                "timeframe": "2-4 weeks",
                "ai_reasoning": "Credit growth accelerating at 17.2% YoY. Net Interest Margin expanded to 3.6%, beating estimates. FII buying resumed with ₹1,200 Cr inflow this week. Technical breakout above 200-day SMA with rising volume confirms bullish momentum.",
                "technical_data": '{"rsi": {"value": 62.7, "signal": "neutral"}, "macd": {"value": 12.3, "signal": "bullish", "histogram": 4.1}, "bollinger": {"percent_b": 0.78, "signal": "neutral"}, "volume": {"ratio": 1.45, "signal": "high"}, "sma_cross": {"signal": "bullish", "sma_20": 1665, "sma_50": 1640}}',
                "sentiment_data": '{"score": 85, "key_factors": ["strong credit growth", "NIM expansion", "FII buying"], "market_impact": "positive"}',
                "created_at": now - timedelta(hours=2),
            },
            {
                "id": str(uuid.uuid4()),
                "symbol": "RELIANCE.NS",
                "market_type": "stock",
                "signal_type": "BUY",
                "confidence": 74,
                "current_price": "2945.00",
                "target_price": "3100.00",
                "stop_loss": "2860.00",
                "timeframe": "3-5 weeks",
                "ai_reasoning": "Jio subscriber additions strong at 8.2M for Q4. Retail segment EBITDA grew 19% QoQ. Oil-to-chemicals margin stable despite crude volatility. Watch for AGM announcement on new energy investments.",
                "technical_data": '{"rsi": {"value": 58.3, "signal": "neutral"}, "macd": {"value": 8.7, "signal": "bullish", "histogram": 2.3}, "bollinger": {"percent_b": 0.62, "signal": "neutral"}, "volume": {"ratio": 1.12, "signal": "normal"}, "sma_cross": {"signal": "bullish", "sma_20": 2920, "sma_50": 2890}}',
                "sentiment_data": '{"score": 72, "key_factors": ["Jio growth", "retail expansion", "AGM catalyst"], "market_impact": "positive"}',
                "created_at": now - timedelta(hours=4),
            },
            {
                "id": str(uuid.uuid4()),
                "symbol": "INFY.NS",
                "market_type": "stock",
                "signal_type": "HOLD",
                "confidence": 48,
                "current_price": "1538.00",
                "target_price": "1580.00",
                "stop_loss": "1490.00",
                "timeframe": "1-2 weeks",
                "ai_reasoning": "Mixed signals — deal pipeline strong at $4.6B TCV but attrition rising to 14.2%. Guidance conservative at 4-6% revenue growth. RSI neutral, MACD flat. Wait for next quarterly guidance update before committing.",
                "technical_data": '{"rsi": {"value": 49.2, "signal": "neutral"}, "macd": {"value": -1.2, "signal": "neutral", "histogram": 0.3}, "bollinger": {"percent_b": 0.45, "signal": "neutral"}, "volume": {"ratio": 0.95, "signal": "normal"}, "sma_cross": {"signal": "neutral", "sma_20": 1535, "sma_50": 1540}}',
                "sentiment_data": '{"score": 50, "key_factors": ["strong TCV", "rising attrition", "conservative guidance"], "market_impact": "neutral"}',
                "created_at": now - timedelta(hours=6),
            },
            # Crypto
            {
                "id": str(uuid.uuid4()),
                "symbol": "BTCUSDT",
                "market_type": "crypto",
                "signal_type": "STRONG_BUY",
                "confidence": 88,
                "current_price": "97842.00",
                "target_price": "105000.00",
                "stop_loss": "93500.00",
                "timeframe": "1-3 weeks",
                "ai_reasoning": "Bitcoin breaking above $97K resistance with conviction. ETF inflows hit $1.2B this week — strongest since January. On-chain data shows accumulation by long-term holders. Hash rate at all-time high signals miner confidence. Next target is psychological $100K barrier.",
                "technical_data": '{"rsi": {"value": 68.5, "signal": "neutral"}, "macd": {"value": 1250, "signal": "bullish", "histogram": 420}, "bollinger": {"percent_b": 0.85, "signal": "overbought"}, "volume": {"ratio": 1.8, "signal": "high"}, "sma_cross": {"signal": "bullish", "sma_20": 95200, "sma_50": 91800}}',
                "sentiment_data": '{"score": 91, "key_factors": ["ETF inflows $1.2B", "LTH accumulation", "hash rate ATH"], "market_impact": "positive"}',
                "created_at": now - timedelta(hours=1),
            },
            {
                "id": str(uuid.uuid4()),
                "symbol": "ETHUSDT",
                "market_type": "crypto",
                "signal_type": "BUY",
                "confidence": 71,
                "current_price": "3395.00",
                "target_price": "3650.00",
                "stop_loss": "3200.00",
                "timeframe": "2-4 weeks",
                "ai_reasoning": "ETH/BTC ratio recovering from multi-month lows. Pectra upgrade on track for Q2 driving developer sentiment. Staking yield stable at 3.8%. Layer-2 TVL growing 12% MoM suggests increasing network utility.",
                "technical_data": '{"rsi": {"value": 55.8, "signal": "neutral"}, "macd": {"value": 45, "signal": "bullish", "histogram": 18}, "bollinger": {"percent_b": 0.58, "signal": "neutral"}, "volume": {"ratio": 1.25, "signal": "normal"}, "sma_cross": {"signal": "bullish", "sma_20": 3320, "sma_50": 3250}}',
                "sentiment_data": '{"score": 73, "key_factors": ["ETH/BTC recovery", "Pectra upgrade", "L2 TVL growth"], "market_impact": "positive"}',
                "created_at": now - timedelta(hours=3),
            },
            {
                "id": str(uuid.uuid4()),
                "symbol": "SOLUSDT",
                "market_type": "crypto",
                "signal_type": "SELL",
                "confidence": 32,
                "current_price": "172.00",
                "target_price": "152.00",
                "stop_loss": "182.00",
                "timeframe": "1-2 weeks",
                "ai_reasoning": "SOL showing bearish divergence on daily RSI despite price holding. MEV revenue declining as Jito controversy reduces tip volume. Network outage concerns persist — 3 partial outages in last 30 days. Risk-reward unfavorable at current levels.",
                "technical_data": '{"rsi": {"value": 71.2, "signal": "overbought"}, "macd": {"value": -2.5, "signal": "bearish", "histogram": -1.8}, "bollinger": {"percent_b": 0.92, "signal": "overbought"}, "volume": {"ratio": 0.78, "signal": "low"}, "sma_cross": {"signal": "bearish", "sma_20": 175, "sma_50": 178}}',
                "sentiment_data": '{"score": 28, "key_factors": ["bearish RSI divergence", "MEV decline", "outage concerns"], "market_impact": "negative"}',
                "created_at": now - timedelta(hours=5),
            },
            # Forex
            {
                "id": str(uuid.uuid4()),
                "symbol": "USD/INR",
                "market_type": "forex",
                "signal_type": "HOLD",
                "confidence": 45,
                "current_price": "83.1500",
                "target_price": "83.5000",
                "stop_loss": "82.7500",
                "timeframe": "1 week",
                "ai_reasoning": "RBI actively managing USD/INR in tight 82.80-83.30 range. FX reserves at $635B provide strong intervention capacity. US Fed rate path remains uncertain — markets pricing 2 cuts in 2026. Sideways action expected until next FOMC meeting.",
                "technical_data": '{"rsi": {"value": 50.5, "signal": "neutral"}, "macd": {"value": 0.02, "signal": "neutral", "histogram": 0.01}, "bollinger": {"percent_b": 0.52, "signal": "neutral"}, "volume": {"ratio": 0.90, "signal": "normal"}, "sma_cross": {"signal": "neutral", "sma_20": 83.12, "sma_50": 83.08}}',
                "sentiment_data": '{"score": 48, "key_factors": ["RBI intervention", "range-bound", "Fed uncertainty"], "market_impact": "neutral"}',
                "created_at": now - timedelta(hours=7),
            },
            {
                "id": str(uuid.uuid4()),
                "symbol": "EUR/USD",
                "market_type": "forex",
                "signal_type": "BUY",
                "confidence": 67,
                "current_price": "1.0865",
                "target_price": "1.1050",
                "stop_loss": "1.0750",
                "timeframe": "2-3 weeks",
                "ai_reasoning": "ECB holding rates while Fed signals cuts — interest rate differential narrowing supports EUR. Eurozone PMI surprised at 51.2 (above 50 = expansion). Technical base forming at 1.0800 support with bullish MACD crossover.",
                "technical_data": '{"rsi": {"value": 56.3, "signal": "neutral"}, "macd": {"value": 0.0012, "signal": "bullish", "histogram": 0.0005}, "bollinger": {"percent_b": 0.65, "signal": "neutral"}, "volume": {"ratio": 1.15, "signal": "normal"}, "sma_cross": {"signal": "bullish", "sma_20": 1.0840, "sma_50": 1.0810}}',
                "sentiment_data": '{"score": 68, "key_factors": ["rate differential", "PMI surprise", "technical base"], "market_impact": "positive"}',
                "created_at": now - timedelta(hours=8),
            },
        ]

        for s in signals_data:
            await session.execute(text("""
                INSERT INTO signals (id, symbol, market_type, signal_type, confidence,
                    current_price, target_price, stop_loss, timeframe, ai_reasoning,
                    technical_data, sentiment_data, is_active, created_at)
                VALUES (:id, :symbol, :market_type, :signal_type, :confidence,
                    :current_price, :target_price, :stop_loss, :timeframe, :ai_reasoning,
                    CAST(:technical_data AS jsonb), CAST(:sentiment_data AS jsonb), true, :created_at)
            """), s)
        print(f"✅ Inserted {len(signals_data)} signals")

        # ──────────── Signal History (past resolved signals) ────────────
        resolved_signals = [
            {
                "id": str(uuid.uuid4()),
                "symbol": "TCS.NS",
                "market_type": "stock",
                "signal_type": "BUY",
                "confidence": 78,
                "current_price": "3700.00",
                "target_price": "3850.00",
                "stop_loss": "3620.00",
                "timeframe": "2-3 weeks",
                "ai_reasoning": "Strong Q3 deal wins. Resolved — target hit.",
                "technical_data": '{"rsi": {"value": 60, "signal": "neutral"}}',
                "is_active": False,
                "created_at": now - timedelta(days=10),
            },
            {
                "id": str(uuid.uuid4()),
                "symbol": "BTCUSDT",
                "market_type": "crypto",
                "signal_type": "STRONG_BUY",
                "confidence": 85,
                "current_price": "92000.00",
                "target_price": "98000.00",
                "stop_loss": "88000.00",
                "timeframe": "1-2 weeks",
                "ai_reasoning": "ETF momentum. Resolved — target hit.",
                "technical_data": '{"rsi": {"value": 65, "signal": "neutral"}}',
                "is_active": False,
                "created_at": now - timedelta(days=7),
            },
            {
                "id": str(uuid.uuid4()),
                "symbol": "GBP/JPY",
                "market_type": "forex",
                "signal_type": "SELL",
                "confidence": 30,
                "current_price": "190.50",
                "target_price": "187.00",
                "stop_loss": "192.00",
                "timeframe": "1 week",
                "ai_reasoning": "BoJ intervention risk. Resolved — hit stop-loss.",
                "technical_data": '{"rsi": {"value": 42, "signal": "neutral"}}',
                "is_active": False,
                "created_at": now - timedelta(days=5),
            },
        ]

        for s in resolved_signals:
            await session.execute(text("""
                INSERT INTO signals (id, symbol, market_type, signal_type, confidence,
                    current_price, target_price, stop_loss, timeframe, ai_reasoning,
                    technical_data, is_active, created_at)
                VALUES (:id, :symbol, :market_type, :signal_type, :confidence,
                    :current_price, :target_price, :stop_loss, :timeframe, :ai_reasoning,
                    CAST(:technical_data AS jsonb), false, :created_at)
            """), s)

        # Signal history entries for resolved signals
        history_entries = [
            {
                "signal_id": resolved_signals[0]["id"],
                "outcome": "hit_target",
                "exit_price": "3852.00",
                "return_pct": "4.1100",
                "resolved_at": now - timedelta(days=3),
            },
            {
                "signal_id": resolved_signals[1]["id"],
                "outcome": "hit_target",
                "exit_price": "98150.00",
                "return_pct": "6.6800",
                "resolved_at": now - timedelta(days=2),
            },
            {
                "signal_id": resolved_signals[2]["id"],
                "outcome": "hit_stop",
                "exit_price": "192.10",
                "return_pct": "-0.8400",
                "resolved_at": now - timedelta(days=1),
            },
        ]

        for h in history_entries:
            await session.execute(text("""
                INSERT INTO signal_history (id, signal_id, outcome, exit_price, return_pct, resolved_at)
                VALUES (:id, :signal_id, :outcome, :exit_price, :return_pct, :resolved_at)
            """), {"id": str(uuid.uuid4()), **h})
        print(f"✅ Inserted {len(history_entries)} history entries")

        await session.commit()

    await engine.dispose()
    print("\n🚀 Database seeded! Ready for dry run.")
    print("   Backend: http://localhost:8000")
    print("   Frontend: http://localhost:3000")


if __name__ == "__main__":
    asyncio.run(main())
