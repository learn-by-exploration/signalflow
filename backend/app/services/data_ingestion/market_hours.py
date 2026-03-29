"""Market hours checking utilities for all three markets."""

from datetime import date, datetime, time

import pytz

IST = pytz.timezone("Asia/Kolkata")

# NSE holidays for 2026 (from NSE circular)
# Update annually at the start of each year
NSE_HOLIDAYS_2026 = {
    date(2026, 1, 26),   # Republic Day
    date(2026, 2, 17),   # Maha Shivaratri
    date(2026, 3, 30),   # Holi
    date(2026, 3, 31),   # Id-Ul-Fitr (tentative)
    date(2026, 4, 2),    # Ram Navami
    date(2026, 4, 3),    # Good Friday
    date(2026, 4, 14),   # Dr. Ambedkar Jayanti
    date(2026, 5, 1),    # Maharashtra Day
    date(2026, 6, 7),    # Id-Ul-Adha (Bakri Id, tentative)
    date(2026, 7, 7),    # Muharram (tentative)
    date(2026, 8, 15),   # Independence Day
    date(2026, 9, 5),    # Milad-Un-Nabi (tentative)
    date(2026, 10, 2),   # Mahatma Gandhi Jayanti
    date(2026, 10, 20),  # Dussehra
    date(2026, 11, 9),   # Diwali (Laxmi Pujan)
    date(2026, 11, 10),  # Diwali Balipratipada
    date(2026, 11, 30),  # Guru Nanak Jayanti
    date(2026, 12, 25),  # Christmas
}


def _now_ist() -> datetime:
    """Get current datetime in IST."""
    return datetime.now(IST)


def is_nse_open() -> bool:
    """Check if NSE/BSE is currently in trading hours (9:15 AM – 3:30 PM IST, Mon-Fri).

    Includes a 15-minute buffer on both sides.
    Also checks for NSE holidays.
    """
    now = _now_ist()
    # weekday: 0=Monday, 6=Sunday
    if now.weekday() >= 5:
        return False
    # Check NSE holidays
    if now.date() in NSE_HOLIDAYS_2026:
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
