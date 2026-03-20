"""Telegram bot for SignalFlow AI.

Handles /start, /signals, /config, /markets, /history, /stop, /resume commands.
Uses python-telegram-bot 20.x async API.
"""

import logging
from typing import Any

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

from app.config import get_settings
from app.services.alerts.formatter import (
    format_market_snapshot,
    format_signals_list,
    format_welcome,
)

logger = logging.getLogger(__name__)


class SignalFlowBot:
    """Telegram bot for delivering signals and responding to commands.

    Call build() to create the bot application, then run_polling() or
    attach the webhook.
    """

    def __init__(self) -> None:
        self.settings = get_settings()

    def build(self) -> Application:
        """Build and return the Telegram bot Application with all handlers."""
        app = Application.builder().token(self.settings.telegram_bot_token).build()

        app.add_handler(CommandHandler("start", self._cmd_start))
        app.add_handler(CommandHandler("signals", self._cmd_signals))
        app.add_handler(CommandHandler("markets", self._cmd_markets))
        app.add_handler(CommandHandler("config", self._cmd_config))
        app.add_handler(CommandHandler("history", self._cmd_history))
        app.add_handler(CommandHandler("stop", self._cmd_stop))
        app.add_handler(CommandHandler("resume", self._cmd_resume))
        app.add_handler(CallbackQueryHandler(self._handle_callback))

        return app

    async def _cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start — welcome message + store chat_id."""
        if update.effective_chat is None:
            return
        chat_id = update.effective_chat.id
        username = update.effective_user.username if update.effective_user else None

        logger.info("New user: chat_id=%s, username=%s", chat_id, username)

        # Store chat_id in database (via dispatcher later)
        context.bot_data["pending_registrations"] = context.bot_data.get("pending_registrations", {})
        context.bot_data["pending_registrations"][chat_id] = username

        await update.message.reply_text(format_welcome())

    async def _cmd_signals(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /signals — show top active signals."""
        if update.effective_chat is None:
            return
        # Fetch signals from the API (stored in bot_data by Celery tasks)
        signals = context.bot_data.get("active_signals", [])
        text = format_signals_list(signals)
        await update.message.reply_text(text)

    async def _cmd_markets(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /markets — quick market snapshot."""
        if update.effective_chat is None:
            return
        market_data = context.bot_data.get("market_data", {})
        text = format_market_snapshot(
            stocks=market_data.get("stocks", []),
            crypto=market_data.get("crypto", []),
            forex=market_data.get("forex", []),
        )
        await update.message.reply_text(text)

    async def _cmd_config(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /config — show inline keyboard for alert preferences."""
        if update.effective_chat is None:
            return
        keyboard = [
            [
                InlineKeyboardButton("📈 Stocks", callback_data="toggle_stock"),
                InlineKeyboardButton("🪙 Crypto", callback_data="toggle_crypto"),
                InlineKeyboardButton("💱 Forex", callback_data="toggle_forex"),
            ],
            [
                InlineKeyboardButton("Min Confidence: 60%", callback_data="conf_60"),
                InlineKeyboardButton("Min Confidence: 80%", callback_data="conf_80"),
            ],
        ]
        await update.message.reply_text(
            "⚙️ Alert Preferences\nTap to toggle markets or set minimum confidence:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    async def _cmd_history(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /history — recent signal outcomes."""
        if update.effective_chat is None:
            return
        history = context.bot_data.get("signal_history", [])
        if not history:
            await update.message.reply_text("No signal history available yet.")
            return

        lines = ["📜 Recent Signal Outcomes", ""]
        for h in history[:5]:
            outcome_emoji = {
                "hit_target": "🎯",
                "hit_stop": "🛑",
                "expired": "⏰",
                "pending": "⏳",
            }.get(h.get("outcome", "pending"), "❓")

            ret = h.get("return_pct")
            ret_str = f" ({'+' if ret and float(ret) >= 0 else ''}{ret}%)" if ret else ""
            lines.append(f"{outcome_emoji} {h.get('symbol', '?')}{ret_str}")

        await update.message.reply_text("\n".join(lines))

    async def _cmd_stop(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /stop — pause all alerts."""
        if update.effective_chat is None:
            return
        chat_id = update.effective_chat.id
        context.bot_data.setdefault("paused_chats", set()).add(chat_id)
        await update.message.reply_text("⏸ Alerts paused. Use /resume to restart.")

    async def _cmd_resume(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /resume — resume alerts."""
        if update.effective_chat is None:
            return
        chat_id = update.effective_chat.id
        paused = context.bot_data.get("paused_chats", set())
        paused.discard(chat_id)
        await update.message.reply_text("▶️ Alerts resumed! You'll receive signals again.")

    async def _handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle inline keyboard callbacks for /config."""
        query = update.callback_query
        if query is None:
            return
        await query.answer()

        data = query.data
        if data and data.startswith("toggle_"):
            market = data.replace("toggle_", "")
            await query.edit_message_text(f"Toggled {market} alerts. Use /config to see current settings.")
        elif data and data.startswith("conf_"):
            conf = data.replace("conf_", "")
            await query.edit_message_text(f"Minimum confidence set to {conf}%. Use /config to adjust.")


async def send_telegram_message(chat_id: int, text: str) -> None:
    """Send a message to a Telegram chat. Used by the dispatcher."""
    from telegram import Bot

    settings = get_settings()
    bot = Bot(token=settings.telegram_bot_token)
    await bot.send_message(chat_id=chat_id, text=text)
