"""Entry point to run the Telegram bot."""

import logging
from bot.main import run_bot

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO  # or DEBUG for more detailed output
)

if __name__ == "__main__":
    run_bot()
