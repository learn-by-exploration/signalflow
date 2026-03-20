"""Telegram message formatter for signals, briefs, and market snapshots.

Produces formatted strings with emoji coding per CLAUDE.md spec.
"""

from decimal import Decimal


def _format_price(price: Decimal | str, market_type: str = "stock") -> str:
    """Format price with appropriate precision."""
    p = Decimal(str(price))
    if market_type == "forex":
        return f"{p:.4f}"
    if market_type == "crypto" and p >= 1000:
        return f"{p:,.2f}"
    if market_type == "crypto":
        return f"{p:.4f}"
    return f"₹{p:,.2f}"


def _confidence_bar(confidence: int) -> str:
    """Create a text-based progress bar for confidence."""
    filled = round(confidence / 10)
    return "█" * filled + "░" * (10 - filled)


def _clean_symbol(symbol: str) -> str:
    """Remove .NS and USDT suffixes for display."""
    return symbol.replace(".NS", "").replace("USDT", "")


def format_signal_alert(signal: dict) -> str:
    """Format a signal for Telegram delivery.

    Args:
        signal: Dict with signal fields (symbol, market_type, signal_type,
                confidence, current_price, target_price, stop_loss, timeframe,
                ai_reasoning, technical_data).

    Returns:
        Formatted Telegram message string.
    """
    signal_type = signal["signal_type"]
    is_buy = "BUY" in signal_type
    emoji = "🟢" if is_buy else "🔴" if "SELL" in signal_type else "🟡"
    market_type = signal.get("market_type", "stock")

    price = _format_price(signal["current_price"], market_type)
    target = _format_price(signal["target_price"], market_type)
    stop = _format_price(signal["stop_loss"], market_type)
    conf = signal["confidence"]
    bar = _confidence_bar(conf)

    # Technical indicator summary
    tech = signal.get("technical_data", {})
    rsi_val = tech.get("rsi", {}).get("value", "—")
    macd_sig = tech.get("macd", {}).get("signal", "—")
    macd_label = "Bullish" if macd_sig == "buy" else "Bearish" if macd_sig == "sell" else "Neutral"
    vol_ratio = tech.get("volume", {}).get("ratio", "—")
    vol_label = f"{vol_ratio}x" if vol_ratio != "—" else "—"

    lines = [
        f"{emoji} {signal_type.replace('_', ' ')} — {_clean_symbol(signal['symbol'])}",
        "",
        f"💰 Price: {price}",
        f"📊 Confidence: {bar} {conf}%",
        "",
        f"🎯 Target: {target}  |  🛑 Stop: {stop}",
        f"⏱ Timeframe: {signal.get('timeframe', '—')}",
        "",
        f"🤖 AI: {signal.get('ai_reasoning', 'No reasoning available.')}",
        "",
        f"RSI: {rsi_val} | MACD: {macd_label} | Vol: {vol_label}",
    ]

    return "\n".join(lines)


def format_morning_brief(brief_text: str) -> str:
    """Format a morning briefing for Telegram."""
    return f"☀️ Morning Brief\n\n{brief_text}"


def format_evening_wrap(wrap_text: str) -> str:
    """Format an evening wrap for Telegram."""
    return f"🌙 Evening Wrap\n\n{wrap_text}"


def format_market_snapshot(stocks: list, crypto: list, forex: list) -> str:
    """Format a quick market snapshot for /markets command.

    Args:
        stocks: List of dicts with symbol, price, change_pct.
        crypto: List of dicts with symbol, price, change_pct.
        forex: List of dicts with symbol, price, change_pct.
    """
    lines = ["📈 Market Snapshot", ""]

    if stocks:
        lines.append("Stocks:")
        for s in stocks[:5]:
            pct = float(s.get("change_pct", 0))
            arrow = "↑" if pct >= 0 else "↓"
            lines.append(f"  {_clean_symbol(s['symbol'])} — {_format_price(s['price'])} {arrow}{abs(pct):.2f}%")
        lines.append("")

    if crypto:
        lines.append("Crypto:")
        for c in crypto[:5]:
            pct = float(c.get("change_pct", 0))
            arrow = "↑" if pct >= 0 else "↓"
            lines.append(f"  {_clean_symbol(c['symbol'])} — ${float(c['price']):,.2f} {arrow}{abs(pct):.2f}%")
        lines.append("")

    if forex:
        lines.append("Forex:")
        for f_ in forex[:5]:
            pct = float(f_.get("change_pct", 0))
            arrow = "↑" if pct >= 0 else "↓"
            lines.append(f"  {f_['symbol']} — {float(f_['price']):.4f} {arrow}{abs(pct):.2f}%")

    return "\n".join(lines)


def format_signals_list(signals: list) -> str:
    """Format top 5 signals for /signals command."""
    if not signals:
        return "No active signals right now."

    lines = ["📊 Top Active Signals", ""]
    for s in signals[:5]:
        emoji = "🟢" if "BUY" in s["signal_type"] else "🔴" if "SELL" in s["signal_type"] else "🟡"
        lines.append(
            f"{emoji} {_clean_symbol(s['symbol'])} — {s['signal_type'].replace('_', ' ')} ({s['confidence']}%)"
        )

    return "\n".join(lines)


def format_welcome() -> str:
    """Format the /start welcome message."""
    return (
        "👋 Welcome to SignalFlow AI!\n\n"
        "I deliver AI-powered trading signals for:\n"
        "📈 Indian Stocks (NSE)\n"
        "🪙 Cryptocurrency\n"
        "💱 Forex\n\n"
        "Commands:\n"
        "/signals — Current active signals\n"
        "/markets — Quick market snapshot\n"
        "/watchlist — Manage your symbol watchlist\n"
        "/config — Alert preferences\n"
        "/history — Recent signal outcomes\n"
        "/tutorial — Learn how to read signals\n"
        "/stop — Pause alerts\n"
        "/resume — Resume alerts\n\n"
        "⚠️ Disclaimer: This is AI-generated analysis, not financial advice. "
        "Always do your own research before trading."
    )


def format_weekly_digest(stats: dict) -> str:
    """Format weekly performance digest for Telegram.

    Args:
        stats: Dict with total, hit_target, hit_stop, expired, win_rate,
               avg_return_pct, top_winner, top_loser.
    """
    total = stats.get("total", 0)
    if total == 0:
        return (
            "📊 Weekly Digest\n\n"
            "No signals were resolved this week. "
            "New signals are generated as market conditions evolve."
        )

    win_rate = stats.get("win_rate", 0)
    bar = "█" * round(win_rate / 10) + "░" * (10 - round(win_rate / 10))
    avg_ret = stats.get("avg_return_pct", 0)
    sign = "+" if avg_ret >= 0 else ""

    lines = [
        "📊 Weekly Digest",
        "",
        f"Signals resolved: {total}",
        f"🎯 Hit target: {stats.get('hit_target', 0)}",
        f"🛑 Hit stop: {stats.get('hit_stop', 0)}",
        f"⏰ Expired: {stats.get('expired', 0)}",
        "",
        f"Win rate: {bar} {win_rate:.1f}%",
        f"Avg return: {sign}{avg_ret:.2f}%",
    ]

    top_winner = stats.get("top_winner")
    if top_winner:
        lines.append(f"\n🏆 Best: {top_winner['symbol']} ({'+' if top_winner['return_pct'] >= 0 else ''}{top_winner['return_pct']:.2f}%)")

    top_loser = stats.get("top_loser")
    if top_loser:
        lines.append(f"📉 Worst: {top_loser['symbol']} ({'+' if top_loser['return_pct'] >= 0 else ''}{top_loser['return_pct']:.2f}%)")

    lines.append("\nKeep learning! Every signal is a lesson. 📚")

    return "\n".join(lines)


def format_tutorial() -> str:
    """Format the /tutorial guided onboarding message."""
    return (
        "📚 How to Read SignalFlow Signals\n\n"
        "Each signal has these parts:\n\n"
        "1️⃣ Signal Type\n"
        "🟢 STRONG BUY — High confidence buy opportunity\n"
        "🟢 BUY — Moderate buy opportunity\n"
        "🟡 HOLD — Wait and watch\n"
        "🔴 SELL — Consider exiting\n"
        "🔴 STRONG SELL — High confidence exit\n\n"
        "2️⃣ Confidence Score (0-100%)\n"
        "Higher = stronger signal. We recommend acting on 70%+ signals.\n\n"
        "3️⃣ Target & Stop-Loss\n"
        "🎯 Target — Price where you take profit\n"
        "🛑 Stop-Loss — Price where you exit to limit losses\n"
        "Always respect the stop-loss!\n\n"
        "4️⃣ AI Reasoning\n"
        "🤖 Explains WHY the signal was generated — "
        "which indicators and news drove the decision.\n\n"
        "5️⃣ Technical Indicators\n"
        "RSI — Momentum (>70 overbought, <30 oversold)\n"
        "MACD — Trend direction (Bullish/Bearish)\n"
        "Volume — Trading activity level\n\n"
        "💡 Tip: Start with paper trading (simulated) before using real money. "
        "Track your decisions in a journal.\n\n"
        "⚠️ Remember: These are AI-generated signals, not financial advice."
    )
