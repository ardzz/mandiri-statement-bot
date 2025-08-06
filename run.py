"""Entry point to run the Telegram bot."""

import logging
import sys
import os

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

def check_dependencies():
    """Check if all required dependencies are available."""
    missing_deps = []
    
    try:
        import telegram
    except ImportError:
        missing_deps.append("python-telegram-bot")
    
    try:
        import sqlalchemy
    except ImportError:
        missing_deps.append("sqlalchemy")
    
    try:
        import pandas
    except ImportError:
        missing_deps.append("pandas")
    
    try:
        import matplotlib
    except ImportError:
        missing_deps.append("matplotlib")
    
    if missing_deps:
        logger.error(f"Missing required dependencies: {', '.join(missing_deps)}")
        logger.error("Please install them with: pip install -r requirements.txt")
        return False
    
    return True

def check_configuration():
    """Check if the bot is properly configured."""
    try:
        from config.settings import TELEGRAM_TOKEN, DATABASE_URL
        
        if not TELEGRAM_TOKEN:
            logger.error("TELEGRAM_TOKEN not set in environment variables!")
            logger.error("Please set TELEGRAM_TOKEN in your .env file")
            return False
        
        if not DATABASE_URL:
            logger.warning("DATABASE_URL not set, using default SQLite database")
        
        logger.info(f"Using database: {DATABASE_URL}")
        return True
        
    except ImportError as e:
        logger.error(f"Configuration import error: {e}")
        return False

def run_bot():
    """Start the bot with proper error handling."""
    try:
        # Check dependencies first
        if not check_dependencies():
            sys.exit(1)
        
        # Check configuration
        if not check_configuration():
            sys.exit(1)
        
        # Import bot modules after dependency check
        from bot.main import run_bot as start_bot
        
        logger.info("🚀 Starting Mandiri Statement Bot...")
        start_bot()
        
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        logger.error("Check your configuration and try again")
        sys.exit(1)

if __name__ == "__main__":
    run_bot()
