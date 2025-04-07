from telegram.ext import ApplicationBuilder
from config.settings import TELEGRAM_TOKEN
from bot.dispatcher import register_handlers


def run_bot():
    """ Start the bot. """
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    register_handlers(app)
    app.run_polling()
