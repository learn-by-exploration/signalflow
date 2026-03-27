"""Backtesting Celery task.

Replays historical market data through the PRODUCTION signal generation
algorithm (TechnicalAnalyzer + scorer) with rolling walk-forward windows,
slippage, and benchmark comparison.
"""

import logging
import math
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.config import get_settings
from app.services.analysis.indicators import TechnicalAnalyzer
from app.services.signal_gen.scorer import compute_final_confidence
from app.services.signal_gen.targets import calculate_targets
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)

# Walk-forward defaults
TRAIN_DAYS = 60
TEST_DAYS = 30
MIN_WINDOWS = 2  # Minimum walk-forward windows
DEFAULT_SLIPPAGE_BPS = 10  # 0.1% per trade


def _simulate_trades(
    df: pd.DataFrame,
    symbol: str,
    market_type: str,
    slippage_bps: int,
) -> list[dict]:
    """Run production pipeline on a DataFrame window and simulate trades.

    Uses TechnicalAnalyzer.full_analysis() + compute_final_confidence() for parity.
    Sentiment is fixed at 50 (no AI in backtest).
    """
    if len(df) < 50:
        return []

    analyzer = TechnicalAnalyzer(df)
    technical_data = analyzer.full_analysis()
    # Fixed neutral sentiment in backtest
    sentiment_data = {"score": 50, "key_factors": ["backtest_neutral"]}

    confidence, signal_type = compute_final_confidence(technical_data, sentiment_data)

    if signal_type == "HOLD":
        return []

    current_price = float(df["close"].iloc[-1])
    atr_data = technical_data.get("atr", {})

    targets = calculate_targets(
        current_price=Decimal(str(current_price)),
        atr_data=atr_data,
        signal_type=signal_type,
        market_type=market_type,
    )

    target_price = float(targets["target_price"])
    stop_loss = float(targets["stop_loss"])

    # Apply slippage to entry
    slippage_mult = slippage_bps / 10000
    if signal_type in ("BUY", "STRONG_BUY"):
        entry_price = current_price * (1 + slippage_mult)
    else:
        entry_price = current_price * (1 - slippage_mult)

    return [{
        "signal_type": signal_type,
        "confidence": confidence,
        "entry": entry_price,
        "target": target_price,
        "stop": stop_loss,
        "timestamp": df["timestamp"].iloc[-1],
    }]


def _resolve_trades(
    trades: list[dict],
    df_future: pd.DataFrame,
) -> list[dict]:
    """Resolve trade outcomes against future price data."""
    resolved = []
    for trade in trades:
        is_buy = trade["signal_type"] in ("BUY", "STRONG_BUY")
        entry = trade["entry"]
        target = trade["target"]
        stop = trade["stop"]

        result = "expired"
        exit_price = float(df_future["close"].iloc[-1]) if len(df_future) > 0 else entry
        return_pct = 0.0

        for _, row in df_future.iterrows():
            price = float(row["close"])
            high = float(row["high"])
            low = float(row["low"])

            if is_buy:
                if high >= target:
                    result = "win"
                    exit_price = target
                    break
                elif low <= stop:
                    result = "loss"
                    exit_price = stop
                    break
            else:
                if low <= target:
                    result = "win"
                    exit_price = target
                    break
                elif high >= stop:
                    result = "loss"
                    exit_price = stop
                    break

        if is_buy:
            return_pct = (exit_price - entry) / entry * 100
        else:
            return_pct = (entry - exit_price) / entry * 100

        resolved.append({
            **trade,
            "exit": exit_price,
            "result": result,
            "return_pct": return_pct,
        })

    return resolved


def _compute_sharpe(returns: list[float], risk_free_rate: float = 0.0) -> float:
    """Compute annualized Sharpe ratio from a list of per-trade returns."""
    if len(returns) < 2:
        return 0.0
    mean_ret = sum(returns) / len(returns)
    variance = sum((r - mean_ret) ** 2 for r in returns) / (len(returns) - 1)
    std = math.sqrt(variance)
    if std == 0:
        return 0.0
    # Annualize assuming ~252 trading days, ~1 trade per day rough approximation
    return (mean_ret - risk_free_rate) / std * math.sqrt(min(len(returns), 252))


def _compute_profit_factor(trades: list[dict]) -> float:
    """Compute profit factor (gross wins / gross losses)."""
    gross_wins = sum(t["return_pct"] for t in trades if t["return_pct"] > 0)
    gross_losses = abs(sum(t["return_pct"] for t in trades if t["return_pct"] < 0))
    if gross_losses == 0:
        return float("inf") if gross_wins > 0 else 0.0
    return gross_wins / gross_losses


def _run_backtest_sync(backtest_id: str, days: int) -> dict:
    """Execute a walk-forward backtest using PRODUCTION indicators + scoring.

    Strategy: Uses TechnicalAnalyzer.full_analysis() + compute_final_confidence()
    with fixed sentiment_score=50 (no AI in backtest).

    Walk-forward: 60-day train, 30-day test, rolling forward 30 days.
    Slippage: 10 bps (0.1%) per trade.

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

            if len(candles) < TRAIN_DAYS + TEST_DAYS:
                session.execute(
                    text(
                        "UPDATE backtest_runs SET status = 'failed', "
                        "error_message = :msg WHERE id = :bid"
                    ),
                    {
                        "msg": f"Insufficient data: {len(candles)} candles "
                               f"(need {TRAIN_DAYS + TEST_DAYS}+)",
                        "bid": backtest_id,
                    },
                )
                session.commit()
                return {"error": "Insufficient data"}

            # Build DataFrame
            df = pd.DataFrame(
                candles,
                columns=["open", "high", "low", "close", "volume", "timestamp"],
            )
            for col in ["open", "high", "low", "close", "volume"]:
                df[col] = df[col].astype(float)

            # Rolling walk-forward windows
            all_trades: list[dict] = []
            window_start = 0

            while window_start + TRAIN_DAYS + TEST_DAYS <= len(df):
                train_end = window_start + TRAIN_DAYS
                test_end = min(train_end + TEST_DAYS, len(df))

                train_df = df.iloc[window_start:train_end].reset_index(drop=True)
                test_df = df.iloc[train_end:test_end].reset_index(drop=True)

                # Generate signal on training window
                signals = _simulate_trades(
                    train_df, symbol, market_type, DEFAULT_SLIPPAGE_BPS
                )

                # Resolve against test window
                if signals:
                    resolved = _resolve_trades(signals, test_df)
                    all_trades.extend(resolved)

                # Roll forward by TEST_DAYS
                window_start += TEST_DAYS

            # Compute metrics
            total_signals = len(all_trades)
            wins = sum(1 for t in all_trades if t["result"] == "win")
            losses = sum(1 for t in all_trades if t["result"] == "loss")
            win_rate = (wins / total_signals * 100) if total_signals > 0 else 0
            returns = [t["return_pct"] for t in all_trades]
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

            sharpe = _compute_sharpe(returns)
            profit_factor = _compute_profit_factor(all_trades)

            # Buy-and-hold benchmark
            first_close = float(df["close"].iloc[0])
            last_close = float(df["close"].iloc[-1])
            bnh_return = ((last_close - first_close) / first_close * 100) if first_close > 0 else 0
            excess_return = total_return - bnh_return

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
                "sharpe_ratio": round(sharpe, 4),
                "profit_factor": round(profit_factor, 4),
                "buy_hold_return_pct": round(bnh_return, 4),
                "excess_return_pct": round(excess_return, 4),
                "walk_forward_windows": max(1, (len(df) - TRAIN_DAYS) // TEST_DAYS),
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


@celery_app.task(
    name="app.tasks.backtest_tasks.run_backtest",
    bind=True,
    autoretry_for=(ConnectionError,),
    retry_backoff=True,
    retry_backoff_max=120,
    retry_jitter=True,
    max_retries=1,
)
def run_backtest(self, backtest_id: str, days: int = 90) -> dict:
    """Execute a backtest for a symbol over the given lookback period."""
    logger.info("Starting backtest %s (%d days)", backtest_id, days)
    return _run_backtest_sync(backtest_id, days)
