"""Multi-timeframe signal confirmation.

Uses a graduated confirmation matrix to adjust confidence
based on agreement between primary and confirmation timeframes.
"""

import logging
from typing import Any

from app.services.analysis.indicators import TechnicalAnalyzer

logger = logging.getLogger(__name__)

# Confirmation timeframe mapping
CONFIRMATION_TIMEFRAMES = {
    "stock": {"primary": "1d", "confirmation": "1w"},
    "crypto": {"primary": "1d", "confirmation": "1d"},  # use daily as confirmation for 4h primary
    "forex": {"primary": "1d", "confirmation": "4h"},
}

# Minimum data points for confirmation TF (lower than primary since candles are larger)
MIN_CONFIRMATION_POINTS = 20


def compute_confirmation_score(df_confirmation: "pd.DataFrame") -> float:
    """Compute a simplified technical score from the confirmation timeframe.

    Uses only RSI + SMA crossover (skip Bollinger and volume — noisy on higher TFs).

    Args:
        df_confirmation: OHLCV DataFrame for the confirmation timeframe.

    Returns:
        Score 0-100 representing the confirmation timeframe's signal direction.
    """
    import pandas as pd

    if df_confirmation is None or len(df_confirmation) < MIN_CONFIRMATION_POINTS:
        return 50.0  # Neutral — insufficient data

    analyzer = TechnicalAnalyzer(df_confirmation)

    # Compute only RSI and SMA for confirmation (less noisy on higher TFs)
    rsi_data = analyzer.compute_rsi()
    sma_data = analyzer.compute_sma_cross()

    rsi_strength = rsi_data.get("strength", 50) if rsi_data else 50
    sma_strength = sma_data.get("strength", 50) if sma_data else 50

    # Equal weight for confirmation
    return (rsi_strength * 0.5) + (sma_strength * 0.5)


def apply_mtf_confirmation(
    primary_confidence: int,
    primary_signal_type: str,
    confirmation_score: float,
) -> tuple[int, str]:
    """Apply graduated multi-timeframe confirmation matrix.

    Args:
        primary_confidence: Confidence from primary timeframe (0-100).
        primary_signal_type: Signal type from primary timeframe.
        confirmation_score: Technical score from confirmation timeframe (0-100).

    Returns:
        Tuple of (adjusted_confidence, adjusted_signal_type).
    """
    # If confirmation data was unavailable (neutral score), don't modify
    if confirmation_score == 50.0:
        return primary_confidence, primary_signal_type

    is_bullish_primary = primary_signal_type in ("STRONG_BUY", "BUY")
    is_bearish_primary = primary_signal_type in ("STRONG_SELL", "SELL")

    if is_bullish_primary:
        if confirmation_score > 50:
            # Confirmed — keep as is
            logger.info(
                "MTF confirmed bullish: primary=%s/%d, conf_score=%.1f",
                primary_signal_type, primary_confidence, confirmation_score,
            )
            return primary_confidence, primary_signal_type
        elif confirmation_score >= 40:
            # Neutral confirmation — downgrade STRONG_BUY to BUY, reduce confidence
            adjusted_confidence = max(36, int(primary_confidence * 0.85))
            adjusted_type = "BUY" if primary_signal_type == "STRONG_BUY" else primary_signal_type
            logger.info(
                "MTF neutral on bullish: downgraded %s/%d → %s/%d",
                primary_signal_type, primary_confidence,
                adjusted_type, adjusted_confidence,
            )
            return adjusted_confidence, adjusted_type
        else:
            # Conflicting — force HOLD
            logger.info(
                "MTF conflict: primary %s but conf_score=%.1f (bearish), forcing HOLD",
                primary_signal_type, confirmation_score,
            )
            return 50, "HOLD"

    elif is_bearish_primary:
        if confirmation_score < 50:
            # Confirmed bearish
            logger.info(
                "MTF confirmed bearish: primary=%s/%d, conf_score=%.1f",
                primary_signal_type, primary_confidence, confirmation_score,
            )
            return primary_confidence, primary_signal_type
        elif confirmation_score <= 60:
            # Neutral confirmation — reduce confidence
            adjusted_confidence = max(21, int(primary_confidence * 0.85))
            adjusted_type = "SELL" if primary_signal_type == "STRONG_SELL" else primary_signal_type
            logger.info(
                "MTF neutral on bearish: downgraded %s/%d → %s/%d",
                primary_signal_type, primary_confidence,
                adjusted_type, adjusted_confidence,
            )
            return adjusted_confidence, adjusted_type
        else:
            # Conflicting — force HOLD
            logger.info(
                "MTF conflict: primary %s but conf_score=%.1f (bullish), forcing HOLD",
                primary_signal_type, confirmation_score,
            )
            return 50, "HOLD"

    # HOLD signals pass through without modification
    return primary_confidence, primary_signal_type
