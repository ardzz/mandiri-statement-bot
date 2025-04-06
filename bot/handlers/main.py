from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes


async def send_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[["📤 Upload E-statement Excel"], ["📊 Recap"]],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    await update.message.reply_text(
        "Hi! I can help you track your spending.\nChoose an option below 👇",
        reply_markup=keyboard
    )