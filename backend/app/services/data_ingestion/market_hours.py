"""Market hours checking utilities for all three markets."""

from datetime import datetime, time
import pytz

IST = pytz.timezone("Asia/Kolkata")


def _now_ist() -> datetime:
    """Get current datetime in IST."""
    return datetime.now(IST)


def is_nse_open() -> bool:
    """Check if NSE/BSE is currently in trading hours (9:15 AM – 3:30 PM IST, Mon-Fri).

    Includes a 15-minute buffer on both sides.
    """
    now = _now_ist()
    # weekday: 0=Monday, 6=Sunday
    if now.weekday() >= 5:
        return False
    market_open = time(9, 0)   # 15 min buffer before 9:15
    market_close = time(15, 45)  # 15 min buffer after 3:30
    return market_open <= now.time() <= market_close


def is_forex_open() -> bool:
    """Check if forex market is open (24/5, Sun 5:30 PM – Sat 3:30 AM IST).

    Simplified: closed all day Saturday and most of Sunday.
    """
    now = _now_ist()
    weekday = now.weekday()
    current_time = now.time()

    # Saturday: fully closed
    if weekday == 5:
        return False
    # Sunday: open only after 5:30 PM IST
    if weekday == 6:
        return current_time >= time(17, 30)
    # Monday-Friday: open all day
    return True


def is_crypto_open() -> bool:
    """Crypto markets are always open (24/7)."""
    return True
