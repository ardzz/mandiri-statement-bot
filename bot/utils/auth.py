# bot/utils/auth.py

from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes

from core.database import Session
from core.repository.BankAccountRepository import BankAccountRepository


def requires_registration():
    def decorator(func):
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            telegram_id = str(update.effective_user.id)
            db = Session()
            repo = BankAccountRepository(db)
            user = repo.get_by_telegram_id(telegram_id)
            if not user:
                await update.message.reply_text("❌ You need to register first. Use /start to begin.")
                return
            return await func(update, context, *args, **kwargs)
        return wrapper
    return decorator