"""Signal feedback loop — learns from signal outcomes to adjust scoring weights.

Analyzes resolved signals (hit_target vs hit_stop) to compute per-market accuracy
for each technical indicator. Adjusts weights toward indicators that perform better.

Usage:
    weights = await compute_adaptive_weights(db, market_type="crypto")
    # Returns adjusted TECHNICAL_WEIGHTS based on historical accuracy
"""

import logging
from collections import defaultdict
from typing import Any

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.signal import Signal
from app.models.signal_history import SignalHistory

logger = logging.getLogger(__name__)

# Default weights (baseline from CLAUDE.md)
DEFAULT_WEIGHTS = {
    "rsi": 0.20,
    "macd": 0.25,
    "bollinger": 0.15,
    "volume": 0.15,
    "sma_cross": 0.25,
}

# How strongly to shift toward learned weights vs defaults (0.0 = all default, 1.0 = all learned)
LEARNING_RATE = 0.4

# Minimum resolved signals needed to start adjusting weights
MIN_SIGNALS_FOR_ADJUSTMENT = 50

# Weight bounds — no single indicator can dominate or be zeroed out
MIN_WEIGHT = 0.05
MAX_WEIGHT = 0.40


async def compute_indicator_accuracy(
    db: AsyncSession,
    market_type: str | None = None,
    lookback_days: int = 90,
) -> dict[str, dict[str, float]]:
    """Compute accuracy metrics per indicator from resolved signals.

    For each resolved signal, check which indicators agreed with the signal direction
    and whether the signal hit target or stop. This gives per-indicator hit rates.

    Args:
        db: Database session.
        market_type: Filter to specific market (stock/crypto/forex), or None for all.
        lookback_days: How far back to analyze.

    Returns:
        Dict of {indicator_name: {correct: N, total: N, accuracy: float}}.
    """
    query = (
        select(Signal, SignalHistory)
        .join(SignalHistory, SignalHistory.signal_id == Signal.id)
        .where(
            SignalHistory.outcome.in_(["hit_target", "hit_stop"]),
            SignalHistory.resolved_at >= text(f"NOW() - INTERVAL '{lookback_days} days'"),
        )
    )

    if market_type:
        query = query.where(Signal.market_type == market_type)

    result = await db.execute(query)
    rows = result.all()

    indicator_stats: dict[str, dict[str, int]] = defaultdict(lambda: {"correct": 0, "total": 0})

    for signal, history in rows:
        tech_data = signal.technical_data or {}
        is_buy_signal = "BUY" in signal.signal_type
        hit_target = history.outcome == "hit_target"

        for indicator_key in DEFAULT_WEIGHTS:
            indicator = tech_data.get(indicator_key, {})
            ind_signal = indicator.get("signal")

            if ind_signal is None:
                continue

            indicator_stats[indicator_key]["total"] += 1

            # Indicator was "correct" if it agreed with the direction and the signal hit target,
            # or if it disagreed and the signal hit stop
            indicator_agreed = (ind_signal == "buy" and is_buy_signal) or (
                ind_signal == "sell" and not is_buy_signal
            )

            if (indicator_agreed and hit_target) or (not indicator_agreed and not hit_target):
                indicator_stats[indicator_key]["correct"] += 1

    # Compute accuracy ratios
    result_dict: dict[str, dict[str, float]] = {}
    for key, stats in indicator_stats.items():
        total = stats["total"]
        correct = stats["correct"]
        accuracy = correct / total if total > 0 else 0.5
        result_dict[key] = {
            "correct": float(correct),
            "total": float(total),
            "accuracy": accuracy,
        }

    return result_dict


async def compute_adaptive_weights(
    db: AsyncSession,
    market_type: str | None = None,
    lookback_days: int = 90,
) -> dict[str, float]:
    """Compute adjusted technical indicator weights based on historical accuracy.

    Blends default weights with accuracy-based weights using LEARNING_RATE.
    Only adjusts if we have enough resolved signals (MIN_SIGNALS_FOR_ADJUSTMENT).

    Args:
        db: Database session.
        market_type: Filter by market type, or None for all.
        lookback_days: Analysis window.

    Returns:
        Adjusted weights dict (same keys as DEFAULT_WEIGHTS).
    """
    accuracy = await compute_indicator_accuracy(db, market_type, lookback_days)

    # Check if we have enough data
    total_signals = sum(stats["total"] for stats in accuracy.values())
    if total_signals < MIN_SIGNALS_FOR_ADJUSTMENT:
        logger.info(
            "Feedback loop: insufficient data (%d signals, need %d). Using default weights.",
            total_signals,
            MIN_SIGNALS_FOR_ADJUSTMENT,
        )
        return dict(DEFAULT_WEIGHTS)

    # Compute accuracy-based weights (normalize accuracies to sum to 1.0)
    accuracy_values = {key: accuracy.get(key, {}).get("accuracy", 0.5) for key in DEFAULT_WEIGHTS}
    accuracy_sum = sum(accuracy_values.values())

    if accuracy_sum == 0:
        return dict(DEFAULT_WEIGHTS)

    learned_weights = {key: acc / accuracy_sum for key, acc in accuracy_values.items()}

    # Blend: adjusted = default * (1 - lr) + learned * lr
    adjusted = {}
    for key in DEFAULT_WEIGHTS:
        default = DEFAULT_WEIGHTS[key]
        learned = learned_weights.get(key, default)
        adjusted[key] = default * (1 - LEARNING_RATE) + learned * LEARNING_RATE

    # Normalize to sum to 1.0
    total = sum(adjusted.values())
    adjusted = {k: v / total for k, v in adjusted.items()}

    # Enforce weight bounds
    clamped = False
    for key in adjusted:
        if adjusted[key] < MIN_WEIGHT:
            adjusted[key] = MIN_WEIGHT
            clamped = True
        elif adjusted[key] > MAX_WEIGHT:
            adjusted[key] = MAX_WEIGHT
            clamped = True
    if clamped:
        # Re-normalize after clamping
        total = sum(adjusted.values())
        adjusted = {k: v / total for k, v in adjusted.items()}

    logger.info(
        "Feedback loop: adjusted weights for %s — %s",
        market_type or "all",
        {k: f"{v:.3f}" for k, v in adjusted.items()},
    )

    return adjusted


async def get_market_accuracy_summary(
    db: AsyncSession,
) -> dict[str, dict[str, Any]]:
    """Get accuracy summary per market type for dashboard/logging.

    Returns:
        Dict of {market_type: {total, hit_target, hit_stop, win_rate, indicator_accuracy}}.
    """
    stmt = select(
        Signal.market_type,
        func.count(SignalHistory.id).label("total"),
        func.count(SignalHistory.id).filter(SignalHistory.outcome == "hit_target").label("hits"),
        func.count(SignalHistory.id).filter(SignalHistory.outcome == "hit_stop").label("stops"),
    ).join(SignalHistory, SignalHistory.signal_id == Signal.id).where(
        SignalHistory.outcome.in_(["hit_target", "hit_stop"])
    ).group_by(Signal.market_type)

    result = await db.execute(stmt)
    rows = result.all()

    summary: dict[str, dict[str, Any]] = {}
    for row in rows:
        total = row.total or 0
        hits = row.hits or 0
        win_rate = (hits / total * 100) if total > 0 else 0.0
        summary[row.market_type] = {
            "total": total,
            "hit_target": hits,
            "hit_stop": row.stops or 0,
            "win_rate": round(win_rate, 1),
        }

    return summary
