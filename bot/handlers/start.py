from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from core.database import Session
from core.repository.BankAccountRepository import BankAccountRepository
from .main import send_main_menu
from .register import ask_birth_date

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = Session()
    repo = BankAccountRepository(db)
    telegram_id = str(update.message.from_user.id)
    bank_account = repo.get_by_telegram_id(telegram_id)

    if not bank_account:
        return await ask_birth_date(update, context)

    return await send_main_menu(update, context)
