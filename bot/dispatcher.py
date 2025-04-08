from telegram.ext import CommandHandler, MessageHandler, filters, ConversationHandler

from bot.handlers.recap import send_recap, send_recap_all_time, sync_recap
from bot.handlers.register import BIRTHDATE, save_birth_date
from bot.handlers.start import start
from bot.handlers.upload import guide_upload, upload_excel


def register_handlers(app):
    """ Register all handlers for the bot. """
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            BIRTHDATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_birth_date)]
        },
        fallbacks=[],
    )

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("recap", send_recap))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^📤 Upload Excel$"), guide_upload))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^📊 Recap$"), send_recap))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^📊 Recap All Time$"), send_recap_all_time))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^🔄 Sync Recap$"), sync_recap))

    app.add_handler(CommandHandler("guide_upload", guide_upload))
    app.add_handler(CommandHandler("recap", send_recap))
    app.add_handler(CommandHandler("recap_all_time", send_recap_all_time))
    app.add_handler(CommandHandler("sync_recap", sync_recap))
    app.add_handler(MessageHandler(filters.Document.ALL, upload_excel))
