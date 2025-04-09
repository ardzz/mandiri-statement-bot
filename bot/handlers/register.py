from datetime import datetime
from telegram import Update
from telegram.ext import ConversationHandler, ContextTypes

from bot.utils.auth import requires_registration
from core.database import Session
from core.repository.BankAccountRepository import BankAccountRepository

BIRTHDATE = range(1)


async def ask_birth_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Asks the user for their birthdate."""
    await update.message.reply_text("Please enter your birth date (YYYY-MM-DD):")
    return BIRTHDATE


async def handle_save_birthdate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Saves the user's birthdate and registers them."""
    text = update.message.text
    try:
        birth_date = datetime.strptime(text, "%Y-%m-%d")
    except ValueError:
        await update.message.reply_text("❌ Invalid format. Please use YYYY-MM-DD.")
        return ConversationHandler.END

    db = Session()
    repo = BankAccountRepository(db)
    telegram_id = str(update.message.from_user.id)

    acc = repo.get_by_telegram_id(telegram_id)

    if acc:
        acc = db.merge(acc)
        repo.update(acc, {"birth_date": birth_date})
        await update.message.reply_text("✅ Birthdate updated successfully!")
    else:
        repo.create({"telegram_id": telegram_id, "birth_date": birth_date})
        await update.message.reply_text("✅ Registered successfully! You can now upload your bank statement.")
    return ConversationHandler.END

@requires_registration()
async def handle_update_birthdate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Updates the user's birthdate."""
    await update.message.reply_text("Please enter your new birth date (YYYY-MM-DD):")
    return BIRTHDATE