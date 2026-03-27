"""Shadow mode: run old vs new signal pipeline side-by-side.

When SHADOW_MODE=true, the signal generator runs both v1.3 (old) and
v1.4 (new) scoring logic and logs both results for comparison.
After 30 days, analyze which pipeline produces higher win rates.

Shadow results are stored in Redis (lightweight, no schema changes).
"""

import json
import logging
import time
from typing import Any

logger = logging.getLogger(__name__)

# Redis key prefix for shadow comparisons
SHADOW_KEY_PREFIX = "shadow:comparison"
SHADOW_TTL = 90 * 24 * 3600  # 90 days retention

# V1.3 scoring weights (pre-v1.4 values)
V13_TECH_WEIGHT = 0.50
V13_CHAIN_WEIGHT = 0.35
V13_SENT_WEIGHT = 0.15
V13_NO_CHAIN_TECH = 0.60
V13_NO_CHAIN_SENT = 0.40
V13_NO_AI_CAP = 60


def compute_v13_confidence(
    technical_score: float,
    sentiment_score: float,
    has_chain: bool = False,
    chain_score: float = 0.0,
    has_ai: bool = True,
) -> int:
    """Compute confidence using V1.3 scoring weights.

    Args:
        technical_score: Technical analysis score 0-100.
        sentiment_score: Sentiment score 0-100.
        has_chain: Whether event chain data is available.
        chain_score: Event chain derived score 0-100.
        has_ai: Whether AI was used (affects cap).

    Returns:
        V1.3 confidence score 0-100.
    """
    if not has_ai:
        return min(int(technical_score), V13_NO_AI_CAP)

    if has_chain:
        raw = (
            technical_score * V13_TECH_WEIGHT
            + chain_score * V13_CHAIN_WEIGHT
            + sentiment_score * V13_SENT_WEIGHT
        )
    else:
        raw = technical_score * V13_NO_CHAIN_TECH + sentiment_score * V13_NO_CHAIN_SENT

    return max(0, min(100, int(raw)))


def log_shadow_comparison(
    redis_client: Any,
    symbol: str,
    market_type: str,
    v13_confidence: int,
    v14_confidence: int,
    v13_signal_type: str,
    v14_signal_type: str,
    technical_score: float,
    sentiment_score: float,
) -> None:
    """Log a shadow comparison result to Redis.

    Args:
        redis_client: Redis client (sync or None).
        symbol: Market symbol.
        market_type: stock/crypto/forex.
        v13_confidence: V1.3 confidence score.
        v14_confidence: V1.4 confidence score.
        v13_signal_type: Signal type under v1.3 rules.
        v14_signal_type: Signal type under v1.4 rules.
        technical_score: Raw technical score.
        sentiment_score: Raw sentiment score.
    """
    if redis_client is None:
        return

    comparison = {
        "symbol": symbol,
        "market_type": market_type,
        "v13_confidence": v13_confidence,
        "v14_confidence": v14_confidence,
        "v13_signal_type": v13_signal_type,
        "v14_signal_type": v14_signal_type,
        "technical_score": technical_score,
        "sentiment_score": sentiment_score,
        "timestamp": time.time(),
        "confidence_diff": v14_confidence - v13_confidence,
        "signal_changed": v13_signal_type != v14_signal_type,
    }

    try:
        key = f"{SHADOW_KEY_PREFIX}:{symbol}:{int(time.time())}"
        redis_client.setex(key, SHADOW_TTL, json.dumps(comparison))
    except Exception:
        logger.debug("shadow_log_failed", symbol=symbol)


def get_shadow_summary(redis_client: Any) -> dict[str, Any]:
    """Aggregate shadow comparison results for analysis.

    Args:
        redis_client: Redis client.

    Returns:
        Summary with avg confidence diff, signal agreement rate, etc.
    """
    if redis_client is None:
        return {"error": "Redis not available", "comparisons": 0}

    try:
        keys = list(redis_client.scan_iter(f"{SHADOW_KEY_PREFIX}:*", count=1000))
        if not keys:
            return {"comparisons": 0, "message": "No shadow data collected yet"}

        comparisons = []
        for key in keys[:5000]:  # Cap at 5000 to avoid memory issues
            data = redis_client.get(key)
            if data:
                comparisons.append(json.loads(data))

        if not comparisons:
            return {"comparisons": 0}

        total = len(comparisons)
        avg_diff = sum(c["confidence_diff"] for c in comparisons) / total
        signal_changes = sum(1 for c in comparisons if c["signal_changed"])

        # Group by market
        by_market: dict[str, list] = {}
        for c in comparisons:
            mt = c["market_type"]
            by_market.setdefault(mt, []).append(c)

        market_summary = {}
        for mt, items in by_market.items():
            market_summary[mt] = {
                "count": len(items),
                "avg_confidence_diff": round(
                    sum(i["confidence_diff"] for i in items) / len(items), 2
                ),
                "signal_change_rate": round(
                    sum(1 for i in items if i["signal_changed"]) / len(items), 4
                ),
            }

        return {
            "comparisons": total,
            "avg_confidence_diff": round(avg_diff, 2),
            "signal_change_rate": round(signal_changes / total, 4),
            "by_market": market_summary,
            "v14_higher_pct": round(
                sum(1 for c in comparisons if c["confidence_diff"] > 0) / total, 4
            ),
            "v14_lower_pct": round(
                sum(1 for c in comparisons if c["confidence_diff"] < 0) / total, 4
            ),
        }

    except Exception:
        logger.exception("shadow_summary_failed")
        return {"error": "Failed to compute summary"}


def confidence_to_signal_type(confidence: int) -> str:
    """Map confidence score to signal type string."""
    if confidence >= 80:
        return "STRONG_BUY"
    elif confidence >= 65:
        return "BUY"
    elif confidence >= 36:
        return "HOLD"
    elif confidence >= 21:
        return "SELL"
    return "STRONG_SELL"
