"""Backtesting Celery task.

Replays historical market data through the signal generation algorithm
and records performance metrics.
"""

import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.config import get_settings
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


def _run_backtest_sync(backtest_id: str, days: int) -> dict:
    """Execute a backtest against historical market data.

    Strategy: uses RSI + SMA crossover signals on daily candles.
    - Buy when RSI < 35 and price > SMA20
    - Sell when RSI > 65 and price < SMA20
    - Target = entry + 2×ATR, Stop = entry - 1×ATR

    Returns dict of computed metrics.
    """
    settings = get_settings()
    engine = create_engine(settings.database_url_sync, pool_pre_ping=True)

    try:
        with Session(engine) as session:
            # Mark as running
            session.execute(
                text("UPDATE backtest_runs SET status = 'running' WHERE id = :bid"),
                {"bid": backtest_id},
            )
            session.commit()

            # Get backtest config
            row = session.execute(
                text("SELECT symbol, market_type FROM backtest_runs WHERE id = :bid"),
                {"bid": backtest_id},
            ).fetchone()

            if not row:
                return {"error": "Backtest not found"}

            symbol, market_type = row[0], row[1]
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=days)

            # Fetch historical candles
            candles = session.execute(
                text(
                    "SELECT open, high, low, close, volume, timestamp "
                    "FROM market_data "
                    "WHERE symbol = :sym AND timestamp >= :start AND timestamp <= :end "
                    "ORDER BY timestamp ASC"
                ),
                {"sym": symbol, "start": start_date, "end": end_date},
            ).fetchall()

            if len(candles) < 30:
                session.execute(
                    text(
                        "UPDATE backtest_runs SET status = 'failed', "
                        "error_message = :msg WHERE id = :bid"
                    ),
                    {"msg": f"Insufficient data: {len(candles)} candles (need 30+)", "bid": backtest_id},
                )
                session.commit()
                return {"error": "Insufficient data"}

            # Compute indicators and simulate trades
            closes = [float(c[3]) for c in candles]
            highs = [float(c[1]) for c in candles]
            lows = [float(c[2]) for c in candles]

            trades = []
            position = None  # None or {"entry": float, "target": float, "stop": float}

            for i in range(20, len(closes)):
                price = closes[i]

                # SMA20
                sma20 = sum(closes[i - 20:i]) / 20

                # RSI14
                if i >= 14:
                    gains = []
                    losses_list = []
                    for j in range(i - 13, i + 1):
                        change = closes[j] - closes[j - 1]
                        if change > 0:
                            gains.append(change)
                            losses_list.append(0)
                        else:
                            gains.append(0)
                            losses_list.append(abs(change))
                    avg_gain = sum(gains) / 14
                    avg_loss = sum(losses_list) / 14
                    if avg_loss == 0:
                        rsi = 100.0
                    else:
                        rs = avg_gain / avg_loss
                        rsi = 100 - (100 / (1 + rs))
                else:
                    rsi = 50.0

                # ATR14
                if i >= 14:
                    tr_values = []
                    for j in range(i - 13, i + 1):
                        tr = max(
                            highs[j] - lows[j],
                            abs(highs[j] - closes[j - 1]),
                            abs(lows[j] - closes[j - 1]),
                        )
                        tr_values.append(tr)
                    atr = sum(tr_values) / 14
                else:
                    atr = highs[i] - lows[i]

                # Check existing position
                if position is not None:
                    if price >= position["target"]:
                        trades.append({
                            "entry": position["entry"],
                            "exit": position["target"],
                            "result": "win",
                            "return_pct": (position["target"] - position["entry"]) / position["entry"] * 100,
                        })
                        position = None
                    elif price <= position["stop"]:
                        trades.append({
                            "entry": position["entry"],
                            "exit": position["stop"],
                            "result": "loss",
                            "return_pct": (position["stop"] - position["entry"]) / position["entry"] * 100,
                        })
                        position = None

                # Entry signal: RSI < 35 and price > SMA20
                if position is None and rsi < 35 and price > sma20 and atr > 0:
                    position = {
                        "entry": price,
                        "target": price + (atr * 2),
                        "stop": price - atr,
                    }

            # Close any remaining position at last price
            if position is not None:
                last_price = closes[-1]
                ret = (last_price - position["entry"]) / position["entry"] * 100
                trades.append({
                    "entry": position["entry"],
                    "exit": last_price,
                    "result": "win" if ret > 0 else "loss",
                    "return_pct": ret,
                })

            # Compute metrics
            total_signals = len(trades)
            wins = sum(1 for t in trades if t["result"] == "win")
            losses = sum(1 for t in trades if t["result"] == "loss")
            win_rate = (wins / total_signals * 100) if total_signals > 0 else 0
            returns = [t["return_pct"] for t in trades]
            avg_return = sum(returns) / len(returns) if returns else 0
            total_return = sum(returns)

            # Max drawdown
            cumulative = 0.0
            peak = 0.0
            max_drawdown = 0.0
            for r in returns:
                cumulative += r
                if cumulative > peak:
                    peak = cumulative
                dd = peak - cumulative
                if dd > max_drawdown:
                    max_drawdown = dd

            # Update backtest row
            session.execute(
                text(
                    "UPDATE backtest_runs SET "
                    "status = 'completed', "
                    "start_date = :sd, end_date = :ed, "
                    "total_signals = :ts, wins = :w, losses = :l, "
                    "win_rate = :wr, avg_return_pct = :ar, "
                    "total_return_pct = :tr, max_drawdown_pct = :md, "
                    "completed_at = :now "
                    "WHERE id = :bid"
                ),
                {
                    "sd": start_date,
                    "ed": end_date,
                    "ts": total_signals,
                    "w": wins,
                    "l": losses,
                    "wr": round(win_rate, 2),
                    "ar": round(avg_return, 4),
                    "tr": round(total_return, 4),
                    "md": round(max_drawdown, 4),
                    "now": datetime.now(timezone.utc),
                    "bid": backtest_id,
                },
            )
            session.commit()

            return {
                "total_signals": total_signals,
                "wins": wins,
                "losses": losses,
                "win_rate": round(win_rate, 2),
                "avg_return_pct": round(avg_return, 4),
                "total_return_pct": round(total_return, 4),
                "max_drawdown_pct": round(max_drawdown, 4),
            }

    except Exception as e:
        logger.exception("Backtest %s failed", backtest_id)
        try:
            with Session(engine) as session:
                session.execute(
                    text(
                        "UPDATE backtest_runs SET status = 'failed', "
                        "error_message = :msg WHERE id = :bid"
                    ),
                    {"msg": str(e)[:500], "bid": backtest_id},
                )
                session.commit()
        except Exception:
            logger.exception("Failed to update backtest status to failed")
        return {"error": str(e)}
    finally:
        engine.dispose()


@celery_app.task(name="app.tasks.backtest_tasks.run_backtest")
def run_backtest(backtest_id: str, days: int = 90) -> dict:
    """Execute a backtest for a symbol over the given lookback period."""
    logger.info("Starting backtest %s (%d days)", backtest_id, days)
    return _run_backtest_sync(backtest_id, days)
