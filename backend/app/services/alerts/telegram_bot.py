"""Telegram bot for SignalFlow AI.

Handles /start, /signals, /config, /markets, /history, /stop, /resume,
/tutorial, /watchlist, /ask, /alert, /trade, /portfolio commands.
Uses python-telegram-bot 20.x async API.

Registration and preferences are persisted to PostgreSQL via direct DB access.
"""

import logging
from decimal import Decimal, InvalidOperation

import httpx
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

from app.config import get_settings
from app.models.alert_config import AlertConfig
from app.models.price_alert import PriceAlert
from app.models.trade import Trade
from app.services.alerts.formatter import (
    format_market_snapshot,
    format_portfolio_summary,
    format_price_alert_created,
    format_signals_list,
    format_tutorial,
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
        self._engine = create_async_engine(
            self.settings.database_url, pool_pre_ping=True, pool_size=5,
        )
        self._session_factory = async_sessionmaker(
            self._engine, class_=AsyncSession, expire_on_commit=False,
        )

    def build(self) -> Application:
        """Build and return the Telegram bot Application with all handlers."""
        app = Application.builder().token(self.settings.telegram_bot_token).build()

        app.add_handler(CommandHandler("start", self._cmd_start))
        app.add_handler(CommandHandler("signals", self._cmd_signals))
        app.add_handler(CommandHandler("markets", self._cmd_markets))
        app.add_handler(CommandHandler("config", self._cmd_config))
        app.add_handler(CommandHandler("history", self._cmd_history))
        app.add_handler(CommandHandler("tutorial", self._cmd_tutorial))
        app.add_handler(CommandHandler("watchlist", self._cmd_watchlist))
        app.add_handler(CommandHandler("ask", self._cmd_ask))
        app.add_handler(CommandHandler("alert", self._cmd_alert))
        app.add_handler(CommandHandler("trade", self._cmd_trade))
        app.add_handler(CommandHandler("portfolio", self._cmd_portfolio))
        app.add_handler(CommandHandler("stop", self._cmd_stop))
        app.add_handler(CommandHandler("resume", self._cmd_resume))
        app.add_handler(CallbackQueryHandler(self._handle_callback))

        return app

    async def _get_or_create_config(self, chat_id: int, username: str | None = None) -> AlertConfig:
        """Get existing alert config or create a new one for this chat_id."""
        async with self._session_factory() as session:
            result = await session.execute(
                select(AlertConfig).where(AlertConfig.telegram_chat_id == chat_id)
            )
            config = result.scalar_one_or_none()
            if config is None:
                config = AlertConfig(
                    telegram_chat_id=chat_id,
                    username=username,
                    markets=["stock", "crypto", "forex"],
                    min_confidence=60,
                    signal_types=["STRONG_BUY", "BUY", "SELL", "STRONG_SELL"],
                    is_active=True,
                )
                session.add(config)
                await session.commit()
                await session.refresh(config)
                logger.info("Created alert config for chat_id=%s", chat_id)
            return config

    async def _cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start — welcome message + persist registration to DB."""
        if update.effective_chat is None:
            return
        chat_id = update.effective_chat.id
        username = update.effective_user.username if update.effective_user else None

        logger.info("New user: chat_id=%s, username=%s", chat_id, username)

        # Persist to database
        await self._get_or_create_config(chat_id, username)

        await update.message.reply_text(format_welcome())
        await update.message.reply_text(
            "💡 New here? Try /tutorial to learn how to read trading signals!"
        )

    async def _cmd_tutorial(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /tutorial — guided onboarding for new users."""
        if update.effective_chat is None:
            return
        await update.message.reply_text(format_tutorial())

    async def _cmd_watchlist(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /watchlist — view, add, or remove symbols.

        Usage:
            /watchlist            — show current watchlist
            /watchlist add HDFC   — add symbol
            /watchlist remove BTC — remove symbol
        """
        if update.effective_chat is None:
            return
        chat_id = update.effective_chat.id

        config = await self._get_or_create_config(chat_id)
        watchlist = list(config.watchlist) if isinstance(config.watchlist, list) else []

        args = context.args or []

        if len(args) == 0:
            if not watchlist:
                await update.message.reply_text(
                    "📋 Your watchlist is empty.\n\n"
                    "Add symbols with:\n/watchlist add HDFCBANK\n/watchlist add BTCUSDT"
                )
            else:
                symbols = ", ".join(watchlist)
                await update.message.reply_text(
                    f"📋 Your Watchlist ({len(watchlist)} symbols)\n\n{symbols}\n\n"
                    "Manage: /watchlist add SYMBOL or /watchlist remove SYMBOL"
                )
            return

        if len(args) < 2 or args[0].lower() not in ("add", "remove"):
            await update.message.reply_text(
                "Usage:\n/watchlist add HDFCBANK\n/watchlist remove BTCUSDT"
            )
            return

        action = args[0].lower()
        symbol = args[1].upper().strip()

        async with self._session_factory() as session:
            result = await session.execute(
                select(AlertConfig).where(AlertConfig.telegram_chat_id == chat_id)
            )
            db_config = result.scalar_one_or_none()
            if not db_config:
                await update.message.reply_text("Please /start first.")
                return

            current = list(db_config.watchlist) if isinstance(db_config.watchlist, list) else []

            if action == "add":
                if symbol in current:
                    await update.message.reply_text(f"{symbol} is already on your watchlist.")
                    return
                current.append(symbol)
                db_config.watchlist = current
                await session.commit()
                await update.message.reply_text(f"✅ Added {symbol} to your watchlist.")
            else:
                if symbol not in current:
                    await update.message.reply_text(f"{symbol} is not on your watchlist.")
                    return
                current.remove(symbol)
                db_config.watchlist = current
                await session.commit()
                await update.message.reply_text(f"🗑 Removed {symbol} from your watchlist.")

    async def _cmd_signals(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /signals — show top active signals from database."""
        if update.effective_chat is None:
            return

        try:
            async with self._session_factory() as session:
                result = await session.execute(
                    text(
                        "SELECT symbol, signal_type, confidence, current_price, "
                        "target_price, stop_loss, market_type "
                        "FROM signals WHERE is_active = true "
                        "ORDER BY confidence DESC LIMIT 5"
                    )
                )
                rows = result.fetchall()
                signals = [
                    {
                        "symbol": r[0],
                        "signal_type": r[1],
                        "confidence": r[2],
                        "current_price": str(r[3]),
                        "target_price": str(r[4]),
                        "stop_loss": str(r[5]),
                        "market_type": r[6],
                    }
                    for r in rows
                ]
        except Exception:
            logger.exception("Failed to fetch signals from DB")
            signals = []

        text_msg = format_signals_list(signals)
        await update.message.reply_text(text_msg)

    async def _cmd_markets(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /markets — quick market snapshot from database."""
        if update.effective_chat is None:
            return

        try:
            async with self._session_factory() as session:
                stocks = await self._get_market_snapshot(session, "stock")
                crypto = await self._get_market_snapshot(session, "crypto")
                forex = await self._get_market_snapshot(session, "forex")
        except Exception:
            logger.exception("Failed to fetch market data from DB")
            stocks, crypto, forex = [], [], []

        text_msg = format_market_snapshot(stocks=stocks, crypto=crypto, forex=forex)
        await update.message.reply_text(text_msg)

    async def _get_market_snapshot(self, session: AsyncSession, market_type: str) -> list[dict]:
        """Fetch latest prices for a market type."""
        result = await session.execute(
            text(
                "SELECT DISTINCT ON (symbol) symbol, close, timestamp "
                "FROM market_data WHERE market_type = :mt "
                "ORDER BY symbol, timestamp DESC"
            ),
            {"mt": market_type},
        )
        rows = result.fetchall()
        snapshots = []
        for r in rows:
            snapshots.append({
                "symbol": r[0],
                "price": str(r[1]),
                "change_pct": 0.0,
                "market_type": market_type,
            })
        return snapshots[:5]

    async def _cmd_ask(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /ask <symbol> <question> — AI-powered Q&A about a symbol.

        Usage: /ask HDFCBANK Is it a good time to buy?
        """
        if update.effective_chat is None:
            return
        args = context.args or []
        if len(args) < 2:
            await update.message.reply_text(
                "Usage: /ask <SYMBOL> <your question>\n"
                "Example: /ask HDFCBANK Is it a good time to buy?"
            )
            return

        symbol = args[0].upper().strip()
        question = " ".join(args[1:])

        await update.message.reply_text(f"🤖 Analyzing {symbol}...")

        settings = get_settings()
        try:
            # Always use localhost — telegram bot runs in the same container as the backend
            # (via supervisord), so localhost:PORT is always correct.
            api_url = f"http://localhost:{settings.api_port}/api/v1/ai/ask"
            async with httpx.AsyncClient(timeout=35.0) as client:
                resp = await client.post(
                    api_url,
                    json={"symbol": symbol, "question": question},
                )
                resp.raise_for_status()
                data = resp.json()
                answer = data.get("data", {}).get("answer", "No answer available.")
        except Exception:
            logger.exception("Failed to call AI Q&A for %s", symbol)
            answer = f"Sorry, I couldn't analyze {symbol} right now. Try again later."

        await update.message.reply_text(f"🤖 {symbol}\n\n{answer}")

    async def _cmd_alert(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /alert — set price alerts.

        Usage:
            /alert                      — list active alerts
            /alert BTCUSDT above 100000 — set an alert
        """
        if update.effective_chat is None:
            return
        chat_id = update.effective_chat.id
        args = context.args or []

        if len(args) == 0:
            # List existing alerts
            async with self._session_factory() as session:
                result = await session.execute(
                    select(PriceAlert)
                    .where(PriceAlert.telegram_chat_id == chat_id)
                    .where(PriceAlert.is_active.is_(True))
                    .where(PriceAlert.is_triggered.is_(False))
                )
                alerts = result.scalars().all()

            if not alerts:
                await update.message.reply_text(
                    "🔔 No active price alerts.\n\n"
                    "Set one: /alert BTCUSDT above 100000"
                )
            else:
                lines = ["🔔 Active Price Alerts", ""]
                for a in alerts:
                    sym = str(a.symbol).replace(".NS", "").replace("USDT", "")
                    lines.append(f"  {sym} {a.condition} {a.threshold}")
                await update.message.reply_text("\n".join(lines))
            return

        if len(args) != 3 or args[1].lower() not in ("above", "below"):
            await update.message.reply_text(
                "Usage: /alert <SYMBOL> <above|below> <price>\n"
                "Example: /alert BTCUSDT above 100000"
            )
            return

        symbol = args[0].upper().strip()
        condition = args[1].lower()
        try:
            threshold = Decimal(args[2])
        except InvalidOperation:
            await update.message.reply_text("Invalid price. Use a number like: 100000 or 1678.50")
            return

        async with self._session_factory() as session:
            alert = PriceAlert(
                telegram_chat_id=chat_id,
                symbol=symbol,
                market_type="crypto" if "USDT" in symbol else "forex" if "/" in symbol else "stock",
                condition=condition,
                threshold=threshold,
            )
            session.add(alert)
            await session.commit()

        await update.message.reply_text(
            format_price_alert_created(symbol, condition, str(threshold))
        )

    async def _cmd_trade(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /trade — log a buy or sell trade.

        Usage: /trade buy HDFCBANK 10 1678.90
        """
        if update.effective_chat is None:
            return
        chat_id = update.effective_chat.id
        args = context.args or []

        if len(args) < 4:
            await update.message.reply_text(
                "Usage: /trade <buy|sell> <SYMBOL> <QTY> <PRICE>\n"
                "Example: /trade buy HDFCBANK 10 1678.90"
            )
            return

        side = args[0].lower()
        if side not in ("buy", "sell"):
            await update.message.reply_text("First argument must be 'buy' or 'sell'.")
            return

        symbol = args[1].upper().strip()

        try:
            quantity = Decimal(args[2])
            price = Decimal(args[3])
        except InvalidOperation:
            await update.message.reply_text("Invalid quantity or price. Use numbers.")
            return

        market_type = "crypto" if "USDT" in symbol else "forex" if "/" in symbol else "stock"

        async with self._session_factory() as session:
            trade = Trade(
                telegram_chat_id=chat_id,
                symbol=symbol,
                market_type=market_type,
                side=side,
                quantity=quantity,
                price=price,
            )
            session.add(trade)
            await session.commit()

        emoji = "🟢" if side == "buy" else "🔴"
        total = quantity * price
        await update.message.reply_text(
            f"{emoji} Trade logged!\n\n"
            f"{side.upper()} {quantity} × {symbol} @ {price}\n"
            f"Total: {total:,.2f}\n\n"
            f"View your portfolio: /portfolio"
        )

    async def _cmd_portfolio(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /portfolio — view current positions and P&L."""
        if update.effective_chat is None:
            return
        chat_id = update.effective_chat.id

        async with self._session_factory() as session:
            from sqlalchemy import case, func

            result = await session.execute(
                select(
                    Trade.symbol,
                    Trade.market_type,
                    func.sum(
                        case(
                            (Trade.side == "buy", Trade.quantity),
                            else_=-Trade.quantity,
                        )
                    ).label("net_qty"),
                    func.sum(
                        case(
                            (Trade.side == "buy", Trade.quantity * Trade.price),
                            else_=-Trade.quantity * Trade.price,
                        )
                    ).label("net_cost"),
                )
                .where(Trade.telegram_chat_id == chat_id)
                .group_by(Trade.symbol, Trade.market_type)
            )
            rows = result.all()

        if not rows:
            await update.message.reply_text(
                "📊 No trades logged yet.\n\n"
                "Log your first trade: /trade buy HDFCBANK 10 1678.90"
            )
            return

        positions = []
        for row in rows:
            net_qty = float(row.net_qty or 0)
            if net_qty <= 0:
                continue
            net_cost = float(row.net_cost or 0)
            avg_price = net_cost / net_qty if net_qty > 0 else 0
            positions.append({
                "symbol": row.symbol,
                "quantity": net_qty,
                "avg_price": avg_price,
                "total_cost": net_cost,
            })

        if not positions:
            await update.message.reply_text("📊 All positions are closed. No open holdings.")
            return

        await update.message.reply_text(format_portfolio_summary(positions))

    async def _cmd_config(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /config — show current prefs + inline keyboard to modify."""
        if update.effective_chat is None:
            return
        chat_id = update.effective_chat.id

        config = await self._get_or_create_config(chat_id)
        markets = (
            config.markets if isinstance(config.markets, list)
            else ["stock", "crypto", "forex"]
        )
        min_conf = config.min_confidence

        stock_label = "📈 Stocks ✅" if "stock" in markets else "📈 Stocks ❌"
        crypto_label = "🪙 Crypto ✅" if "crypto" in markets else "🪙 Crypto ❌"
        forex_label = "💱 Forex ✅" if "forex" in markets else "💱 Forex ❌"

        keyboard = [
            [
                InlineKeyboardButton(stock_label, callback_data="toggle_stock"),
                InlineKeyboardButton(crypto_label, callback_data="toggle_crypto"),
                InlineKeyboardButton(forex_label, callback_data="toggle_forex"),
            ],
            [
                InlineKeyboardButton(
                    f"{'✅' if min_conf == 60 else '  '} Min Conf: 60%", callback_data="conf_60",
                ),
                InlineKeyboardButton(
                    f"{'✅' if min_conf == 80 else '  '} Min Conf: 80%", callback_data="conf_80",
                ),
            ],
        ]
        await update.message.reply_text(
            f"⚙️ Alert Preferences\n\n"
            f"Markets: {', '.join(markets)}\n"
            f"Min confidence: {min_conf}%\n\n"
            f"Tap to toggle:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    async def _cmd_history(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /history — recent signal outcomes from database."""
        if update.effective_chat is None:
            return

        try:
            async with self._session_factory() as session:
                result = await session.execute(
                    text(
                        "SELECT sh.outcome, sh.return_pct, sh.resolved_at, s.symbol "
                        "FROM signal_history sh "
                        "JOIN signals s ON sh.signal_id = s.id "
                        "ORDER BY sh.created_at DESC LIMIT 5"
                    )
                )
                rows = result.fetchall()
        except Exception:
            logger.exception("Failed to fetch signal history from DB")
            rows = []

        if not rows:
            await update.message.reply_text("No signal history available yet.")
            return

        lines = ["📜 Recent Signal Outcomes", ""]
        for r in rows:
            outcome, ret_pct, _resolved_at, symbol = r[0], r[1], r[2], r[3]
            outcome_emoji = {
                "hit_target": "🎯",
                "hit_stop": "🛑",
                "expired": "⏰",
                "pending": "⏳",
            }.get(outcome or "pending", "❓")

            ret_str = ""
            if ret_pct is not None:
                sign = "+" if float(ret_pct) >= 0 else ""
                ret_str = f" ({sign}{ret_pct}%)"
            lines.append(f"{outcome_emoji} {symbol}{ret_str}")

        await update.message.reply_text("\n".join(lines))

    async def _cmd_stop(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /stop — pause all alerts (persisted to DB)."""
        if update.effective_chat is None:
            return
        chat_id = update.effective_chat.id

        async with self._session_factory() as session:
            result = await session.execute(
                select(AlertConfig).where(AlertConfig.telegram_chat_id == chat_id)
            )
            config = result.scalar_one_or_none()
            if config:
                config.is_active = False
                await session.commit()

        await update.message.reply_text("⏸ Alerts paused. Use /resume to restart.")

    async def _cmd_resume(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /resume — resume alerts (persisted to DB)."""
        if update.effective_chat is None:
            return
        chat_id = update.effective_chat.id

        async with self._session_factory() as session:
            result = await session.execute(
                select(AlertConfig).where(AlertConfig.telegram_chat_id == chat_id)
            )
            config = result.scalar_one_or_none()
            if config:
                config.is_active = True
                await session.commit()

        await update.message.reply_text("▶️ Alerts resumed! You'll receive signals again.")

    async def _handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle inline keyboard callbacks for /config — persist changes to DB."""
        query = update.callback_query
        if query is None or query.message is None:
            return
        await query.answer()

        chat_id = query.message.chat_id
        data = query.data

        async with self._session_factory() as session:
            result = await session.execute(
                select(AlertConfig).where(AlertConfig.telegram_chat_id == chat_id)
            )
            config = result.scalar_one_or_none()
            if not config:
                await query.edit_message_text("Please send /start first to register.")
                return

            markets = (
                config.markets if isinstance(config.markets, list)
                else ["stock", "crypto", "forex"]
            )

            if data and data.startswith("toggle_"):
                market = data.replace("toggle_", "")
                if market in markets:
                    markets.remove(market)
                    action = "disabled"
                else:
                    markets.append(market)
                    action = "enabled"
                config.markets = markets
                await session.commit()
                await query.edit_message_text(
                    f"{'📈' if market == 'stock' else '🪙' if market == 'crypto' else '💱'} "
                    f"{market.title()} alerts {action}. "
                    f"Active markets: {', '.join(markets)}\n\nUse /config to see full settings."
                )

            elif data and data.startswith("conf_"):
                conf = int(data.replace("conf_", ""))
                config.min_confidence = conf
                await session.commit()
                await query.edit_message_text(
                    f"Minimum confidence set to {conf}%.\nUse /config to see full settings."
                )


async def send_telegram_message(chat_id: int, text: str) -> None:
    """Send a message to a Telegram chat. Used by the dispatcher."""

    settings = get_settings()
    bot = _get_bot_instance(settings.telegram_bot_token)
    await bot.send_message(chat_id=chat_id, text=text)


# Module-level bot singleton for connection reuse
_bot_instance: object | None = None
_bot_token: str | None = None


def _get_bot_instance(token: str) -> object:
    """Get or create a module-level Bot instance for connection reuse."""
    from telegram import Bot

    global _bot_instance, _bot_token
    if _bot_instance is None or _bot_token != token:
        _bot_instance = Bot(token=token)
        _bot_token = token
    return _bot_instance
