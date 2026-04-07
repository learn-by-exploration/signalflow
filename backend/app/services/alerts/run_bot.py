"""Entry point for running the Telegram bot in polling mode.

Launched by supervisord as a standalone process. Gracefully skips
if TELEGRAM_BOT_TOKEN is not configured.
"""

import logging
import sys

from app.config import get_settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    settings = get_settings()
    if not settings.telegram_bot_token:
        logger.warning("TELEGRAM_BOT_TOKEN not set — Telegram bot disabled")
        # Exit cleanly so supervisord doesn't restart endlessly
        sys.exit(0)

    from app.services.alerts.telegram_bot import SignalFlowBot

    logger.info("Starting Telegram bot in polling mode...")
    bot = SignalFlowBot()
    app = bot.build()
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
