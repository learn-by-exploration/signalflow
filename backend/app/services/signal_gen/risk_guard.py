"""Portfolio-level risk controls for signal generation.

Enforces sector concentration limits, market-level caps, and
cross-market directional checks before emitting new signals.
"""

import logging
from collections import Counter
from typing import Any

from app.config import get_settings

logger = logging.getLogger(__name__)


def check_risk_limits(
    symbol: str,
    market_type: str,
    signal_type: str,
    active_signals: list[dict[str, Any]],
    adx_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Check if a proposed signal violates portfolio risk controls.

    Args:
        symbol: The symbol for the proposed signal.
        market_type: "stock", "crypto", or "forex".
        signal_type: "STRONG_BUY", "BUY", "SELL", etc.
        active_signals: List of currently active signal dicts.
        adx_data: ADX indicator output for the symbol.

    Returns:
        Dict with 'allowed' (bool), 'reason' (str or None), and
        'warnings' (list of advisory strings).
    """
    settings = get_settings()
    warnings: list[str] = []
    is_buy = signal_type in ("STRONG_BUY", "BUY")

    # 1. Sector concentration (stocks only)
    if market_type == "stock":
        sector = settings.sector_map.get(symbol)
        if sector:
            same_sector_count = sum(
                1 for s in active_signals
                if s.get("market_type") == "stock"
                and settings.sector_map.get(s.get("symbol", "")) == sector
                and s.get("signal_type") in ("STRONG_BUY", "BUY")
            )
            if is_buy and same_sector_count >= settings.max_concurrent_per_sector:
                return {
                    "allowed": False,
                    "reason": f"Sector limit reached: {same_sector_count} active {sector} signals (max {settings.max_concurrent_per_sector})",
                    "warnings": warnings,
                }

    # 2. Market-level cap
    same_market_buy_count = sum(
        1 for s in active_signals
        if s.get("market_type") == market_type
        and s.get("signal_type") in ("STRONG_BUY", "BUY")
    )
    if is_buy and same_market_buy_count >= settings.max_concurrent_per_market:
        return {
            "allowed": False,
            "reason": f"Market limit reached: {same_market_buy_count} active {market_type} BUY signals (max {settings.max_concurrent_per_market})",
            "warnings": warnings,
        }

    # 3. Cross-market check: if 3+ BUY signals across stocks AND crypto, suppress
    stock_buys = sum(
        1 for s in active_signals
        if s.get("market_type") == "stock"
        and s.get("signal_type") in ("STRONG_BUY", "BUY")
    )
    crypto_buys = sum(
        1 for s in active_signals
        if s.get("market_type") == "crypto"
        and s.get("signal_type") in ("STRONG_BUY", "BUY")
    )
    if is_buy and stock_buys >= 3 and crypto_buys >= 3:
        return {
            "allowed": False,
            "reason": "Cross-market exposure too high: 3+ active BUY signals in both stocks and crypto",
            "warnings": warnings,
        }

    # 4. ADX directional check
    if adx_data and adx_data.get("value") is not None:
        adx_val = adx_data["value"]
        plus_di = adx_data.get("plus_di", 0)
        minus_di = adx_data.get("minus_di", 0)
        if adx_val > 25 and minus_di > plus_di and is_buy:
            return {
                "allowed": False,
                "reason": f"Strong downtrend detected (ADX={adx_val:.1f}, -DI > +DI). Suppressing BUY signal.",
                "warnings": warnings,
            }

    # 5. Position sizing advisory
    total_active = len(active_signals)
    if total_active >= 4:
        warnings.append(
            f"Consider reduced position size ({total_active} active positions)"
        )

    return {"allowed": True, "reason": None, "warnings": warnings}
