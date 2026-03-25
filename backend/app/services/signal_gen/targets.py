"""Target price and stop-loss calculator using ATR.

For BUY/STRONG_BUY:
  target    = current_price + (ATR × 2.0)
  stop_loss = current_price - (ATR × 1.0)

For SELL/STRONG_SELL:
  target    = current_price - (ATR × 2.0)
  stop_loss = current_price + (ATR × 1.0)

Risk:Reward ratio is always ≥ 1:2
"""

import logging
from decimal import Decimal
from typing import Any

logger = logging.getLogger(__name__)

# ATR multipliers per CLAUDE.md
TARGET_ATR_MULTIPLIER = Decimal("2.0")
STOP_ATR_MULTIPLIER = Decimal("1.0")

# Default timeframes by market type
DEFAULT_TIMEFRAMES = {
    "stock": "2-4 weeks",
    "crypto": "3-7 days",
    "forex": "1-3 days",
}


def calculate_targets(
    current_price: Decimal,
    atr_data: dict[str, Any],
    signal_type: str,
    market_type: str,
) -> dict[str, Any]:
    """Calculate target price, stop-loss, and timeframe for a signal.

    Args:
        current_price: Current market price (Decimal).
        atr_data: ATR indicator output, must have 'value' key.
        signal_type: STRONG_BUY, BUY, HOLD, SELL, STRONG_SELL.
        market_type: stock, crypto, forex.

    Returns:
        Dict with target_price, stop_loss, timeframe (all as Decimal/str).
    """
    atr_value = atr_data.get("value")

    if atr_value is None or atr_value == 0:
        # Fallback: use 2% of current price as ATR estimate
        atr = current_price * Decimal("0.02")
        logger.warning("ATR unavailable, using 2%% fallback: %s", atr)
    else:
        atr = Decimal(str(atr_value))

    if signal_type in ("STRONG_BUY", "BUY"):
        target = current_price + (atr * TARGET_ATR_MULTIPLIER)
        stop_loss = current_price - (atr * STOP_ATR_MULTIPLIER)
    elif signal_type in ("STRONG_SELL", "SELL"):
        target = current_price - (atr * TARGET_ATR_MULTIPLIER)
        stop_loss = current_price + (atr * STOP_ATR_MULTIPLIER)
    else:
        # HOLD — set equidistant targets
        target = current_price + (atr * TARGET_ATR_MULTIPLIER)
        stop_loss = current_price - (atr * STOP_ATR_MULTIPLIER)

    # Ensure prices are non-negative
    target = max(Decimal("0"), target)
    stop_loss = max(Decimal("0"), stop_loss)

    # Enforce minimum Risk:Reward ratio of 1:2
    reward = abs(target - current_price)
    risk = abs(stop_loss - current_price)
    if risk > 0 and reward / risk < 2:
        # Widen target to maintain 1:2 R:R
        if signal_type in ("STRONG_BUY", "BUY"):
            target = current_price + (risk * 2)
        elif signal_type in ("STRONG_SELL", "SELL"):
            target = current_price - (risk * 2)
            target = max(Decimal("0"), target)

    timeframe = DEFAULT_TIMEFRAMES.get(market_type, "1-2 weeks")

    return {
        "target_price": target.quantize(Decimal("0.00000001")),
        "stop_loss": stop_loss.quantize(Decimal("0.00000001")),
        "timeframe": timeframe,
    }
