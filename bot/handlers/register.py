from datetime import datetime
from telegram import Update
from telegram.ext import ConversationHandler, ContextTypes
from core.database import Session
from core.repository.BankAccountRepository import BankAccountRepository

BIRTHDATE = range(1)


async def ask_birth_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Asks the user for their birthdate."""
    await update.message.reply_text("Please enter your birth date (YYYY-MM-DD):")
    return BIRTHDATE


async def save_birth_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Saves the user's birthdate and registers them."""
    text = update.message.text
    try:
        birth_date = datetime.strptime(text, "%Y-%m-%d")
    except ValueError:
        await update.message.reply_text("❌ Invalid format. Please use YYYY-MM-DD.")
        return BIRTHDATE

    db = Session()
    repo = BankAccountRepository(db)
    telegram_id = str(update.message.from_user.id)

    if repo.get_by_telegram_id(telegram_id):
        await update.message.reply_text("You're already registered.")
        return ConversationHandler.END

    repo.create({"telegram_id": telegram_id, "birth_date": birth_date})
    await update.message.reply_text("✅ Registered successfully! You can now upload your bank statement.")
