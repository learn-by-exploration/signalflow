"""Signal confidence scoring algorithm.

Combines technical indicator signals with AI sentiment to produce
a final confidence score and signal type.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)

# Weights from CLAUDE.md scoring formula
TECHNICAL_WEIGHTS = {
    "rsi": 0.20,
    "macd": 0.25,
    "bollinger": 0.15,
    "volume": 0.15,
    "sma_cross": 0.25,
}

# Final blend: 60% technical + 40% AI (per CLAUDE.md)
TECHNICAL_BLEND = 0.60
SENTIMENT_BLEND = 0.40

# Signal thresholds from CLAUDE.md
SIGNAL_THRESHOLDS = [
    (80, "STRONG_BUY"),
    (65, "BUY"),
    (36, "HOLD"),
    (21, "SELL"),
    (0, "STRONG_SELL"),
]

# When AI is unavailable, cap confidence at 60%
NO_AI_CONFIDENCE_CAP = 60


def _indicator_to_score(indicator: dict[str, Any]) -> float:
    """Convert an indicator's signal and strength to a directional score 0-100.

    buy signals map strength to 50-100 range,
    sell signals map strength to 0-50 range,
    neutral stays at 50.
    """
    signal = indicator.get("signal", "neutral")
    strength = indicator.get("strength", 50)

    if signal == "buy":
        return 50 + (strength - 50) * (50 / 50)  # Maps 50-100 → 50-100
    elif signal == "sell":
        return 50 - (strength - 50) * (50 / 50)  # Maps 50-100 → 50-0
    return 50.0


def compute_technical_score(technical_data: dict[str, Any]) -> float:
    """Compute weighted average technical score from indicator outputs.

    Args:
        technical_data: Output of TechnicalAnalyzer.full_analysis().

    Returns:
        Technical score 0-100.
    """
    total_weight = 0.0
    weighted_sum = 0.0

    for indicator_key, weight in TECHNICAL_WEIGHTS.items():
        indicator = technical_data.get(indicator_key, {})
        if indicator.get("signal") is not None:
            score = _indicator_to_score(indicator)
            weighted_sum += score * weight
            total_weight += weight

    if total_weight == 0:
        return 50.0

    return weighted_sum / total_weight


def compute_final_confidence(
    technical_data: dict[str, Any],
    sentiment_data: dict[str, Any] | None,
) -> tuple[int, str]:
    """Compute final confidence and signal type.

    Uses formula: final = (technical × 0.60) + (sentiment × 0.40)
    If sentiment unavailable, uses technical only capped at 60%.

    Args:
        technical_data: Output of TechnicalAnalyzer.full_analysis().
        sentiment_data: Output of AISentimentEngine.analyze_sentiment(), or None.

    Returns:
        Tuple of (confidence 0-100, signal_type string).
    """
    tech_score = compute_technical_score(technical_data)

    has_sentiment = (
        sentiment_data is not None
        and not sentiment_data.get("fallback_reason")
        and sentiment_data.get("confidence_in_analysis", 0) > 0
    )

    if has_sentiment:
        sent_score = float(sentiment_data["sentiment_score"])
        final = tech_score * TECHNICAL_BLEND + sent_score * SENTIMENT_BLEND
    else:
        # No AI → use technical only, capped per CLAUDE.md
        final = tech_score
        # Push towards center and cap distance from 50
        distance_from_center = abs(final - 50)
        max_distance = NO_AI_CONFIDENCE_CAP - 50  # 10
        if distance_from_center > max_distance:
            direction = 1 if final > 50 else -1
            final = 50 + direction * max_distance

    confidence = max(0, min(100, int(round(final))))

    # Determine signal type from thresholds
    signal_type = "HOLD"
    for threshold, stype in SIGNAL_THRESHOLDS:
        if confidence >= threshold:
            signal_type = stype
            break

    return confidence, signal_type
