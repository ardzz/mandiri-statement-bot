from telegram.ext import ApplicationBuilder
from config.settings import TELEGRAM_TOKEN
from bot.dispatcher import register_handlers
import logging

logger = logging.getLogger(__name__)

def run_bot():
    """ Start the bot with error handling."""
    try:
        if not TELEGRAM_TOKEN:
            raise ValueError("TELEGRAM_TOKEN not configured")
        
        logger.info("Building Telegram application...")
        app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
        
        logger.info("Registering handlers...")
        register_handlers(app)
        
        logger.info("Bot started successfully! Press Ctrl+C to stop.")
        app.run_polling()
        
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        raise
