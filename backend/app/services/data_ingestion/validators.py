"""OHLCV candle validation for market data integrity.

Validates that incoming candle data meets financial data quality standards
before persisting to the database.
"""

import logging
import math
from decimal import Decimal, InvalidOperation

logger = logging.getLogger(__name__)


def validate_candle(candle: dict, symbol: str = "") -> tuple[bool, str]:
    """Validate an OHLCV candle for data integrity.

    Checks:
    - All prices are parseable as Decimal
    - No negative prices
    - No NaN or Infinity values
    - high >= low
    - high >= max(open, close)
    - low <= min(open, close)

    Args:
        candle: Dict with 'open', 'high', 'low', 'close' keys (str or numeric).
        symbol: Symbol name for logging context.

    Returns:
        Tuple of (is_valid, error_message). If valid, error_message is empty.
    """
    try:
        o = Decimal(str(candle["open"]))
        h = Decimal(str(candle["high"]))
        l = Decimal(str(candle["low"]))
        c = Decimal(str(candle["close"]))
    except (InvalidOperation, ValueError, TypeError, KeyError) as e:
        return False, f"Invalid price value: {e}"

    # Reject NaN / Infinity (Decimal can represent these via float conversion)
    for label, val in [("open", o), ("high", h), ("low", l), ("close", c)]:
        try:
            f = float(val)
            if math.isnan(f) or math.isinf(f):
                return False, f"{label} is NaN or Infinity"
        except (ValueError, OverflowError):
            return False, f"{label} cannot be converted to float"

    # No negative prices
    if o < 0 or h < 0 or l < 0 or c < 0:
        return False, "Negative price detected"

    # High must be >= Low
    if h < l:
        return False, f"high ({h}) < low ({l})"

    # High must be >= both open and close
    if h < max(o, c):
        return False, f"high ({h}) < max(open={o}, close={c})"

    # Low must be <= both open and close
    if l > min(o, c):
        return False, f"low ({l}) > min(open={o}, close={c})"

    return True, ""


def is_spot_only_candle(candle: dict) -> bool:
    """Check if a candle is spot-only (all prices identical, from fallback API).

    Spot-only candles lack real OHLC data and should not be used for
    technical indicator calculation.
    """
    try:
        o = str(candle.get("open", ""))
        h = str(candle.get("high", ""))
        l = str(candle.get("low", ""))
        c = str(candle.get("close", ""))
        return o == h == l == c
    except Exception:
        return False
