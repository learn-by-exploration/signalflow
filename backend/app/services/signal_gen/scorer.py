"""Signal confidence scoring algorithm.

Combines technical indicator signals with AI sentiment and event chain
analysis to produce a final confidence score and signal type.
"""

import logging
import math
from typing import Any

from app.services.ai_engine.event_chain import compute_chain_score

logger = logging.getLogger(__name__)

# Weights from CLAUDE.md scoring formula
TECHNICAL_WEIGHTS = {
    "rsi": 0.20,
    "macd": 0.25,
    "bollinger": 0.15,
    "volume": 0.15,
    "sma_cross": 0.25,
}

# Chain-aware blend: 50% technical + 35% event chain + 15% sentiment residual
TECHNICAL_BLEND = 0.50
CHAIN_BLEND = 0.35
SENTIMENT_BLEND = 0.15

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


def compute_technical_score(
    technical_data: dict[str, Any],
    weights: dict[str, float] | None = None,
) -> float:
    """Compute weighted average technical score from indicator outputs.

    Args:
        technical_data: Output of TechnicalAnalyzer.full_analysis().
        weights: Optional adaptive weights. Defaults to TECHNICAL_WEIGHTS.

    Returns:
        Technical score 0-100.
    """
    active_weights = weights if weights is not None else TECHNICAL_WEIGHTS
    total_weight = 0.0
    weighted_sum = 0.0

    for indicator_key, weight in active_weights.items():
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
    adaptive_weights: dict[str, float] | None = None,
) -> tuple[int, str]:
    """Compute final confidence and signal type.

    Uses chain-aware formula:
        final = (technical × 0.50) + (chain_score × 0.35) + (sentiment × 0.15)
    Falls back to technical only (capped at 60%) if no AI data.

    Args:
        technical_data: Output of TechnicalAnalyzer.full_analysis().
        sentiment_data: Output of AISentimentEngine.analyze_sentiment(), or None.
        adaptive_weights: Optional feedback-loop-adjusted technical weights.

    Returns:
        Tuple of (confidence 0-100, signal_type string).
    """
    tech_score = compute_technical_score(technical_data, weights=adaptive_weights)

    has_sentiment = (
        sentiment_data is not None
        and not sentiment_data.get("fallback_reason")
        and sentiment_data.get("confidence_in_analysis", 0) > 0
    )

    if has_sentiment:
        sent_score = float(sentiment_data["sentiment_score"])

        # Build chain events from extracted event data
        chain_events = _extract_chain_events(sentiment_data)
        chain_features = compute_chain_score(chain_events)
        chain_score = float(chain_features["chain_score"])

        if chain_events:
            # Full chain-aware scoring
            final = (
                tech_score * TECHNICAL_BLEND
                + chain_score * CHAIN_BLEND
                + sent_score * SENTIMENT_BLEND
            )
        else:
            # No chains extracted — fallback to 60/40 tech/sentiment
            final = tech_score * 0.60 + sent_score * 0.40
    else:
        # No AI → use technical only, capped per CLAUDE.md
        final = tech_score
        # Push towards center and cap distance from 50
        distance_from_center = abs(final - 50)
        max_distance = NO_AI_CONFIDENCE_CAP - 50  # 10
        if distance_from_center > max_distance:
            direction = 1 if final > 50 else -1
            final = 50 + direction * max_distance

    # Guard against NaN/Infinity from corrupted inputs
    if math.isnan(final) or math.isinf(final):
        logger.warning("Final score is %s, falling back to neutral 50", final)
        final = 50.0

    confidence = max(0, min(100, int(round(final))))

    # Determine signal type from thresholds
    signal_type = "HOLD"
    for threshold, stype in SIGNAL_THRESHOLDS:
        if confidence >= threshold:
            signal_type = stype
            break

    return confidence, signal_type


def _extract_chain_events(sentiment_data: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract chain-compatible event dicts from sentiment engine output.

    The sentiment engine returns events under the 'events' key when
    the EVENT_CHAIN_PROMPT is used. Convert them into the format
    expected by compute_chain_score.
    """
    events = sentiment_data.get("events", [])
    if not events:
        return []

    chain_events = []
    for evt in events:
        chain_events.append({
            "direction": evt.get("sentiment_direction", "neutral"),
            "magnitude": min(float(evt.get("impact_magnitude", 3)) / 5.0, 1.0),
            "confidence": float(evt.get("confidence", 50)),
            "hours_since": float(evt.get("hours_since", 0)),
            "category": evt.get("event_category", "sector"),
        })
    return chain_events
