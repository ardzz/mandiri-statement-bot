from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes


async def handle_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send the main menu to the user."""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            ["📤 Upload E-statement Excel"],
            ["📅 Update Birthdate"],
            ["📊 Recap", "❓ Help"]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    await update.message.reply_text(
        "Hi! I can help you track your spending.\nChoose an option below 👇",
        reply_markup=keyboard
    )
