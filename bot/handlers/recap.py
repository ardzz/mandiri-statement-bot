import os
from telegram import Update
from telegram.ext import ContextTypes
from bot.utils.auth import requires_registration


@requires_registration()
async def send_recap(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chart_path = f"cache/chart_cache/{user_id}_report.png"

    if os.path.exists(chart_path):
        await update.message.reply_photo(photo=open(chart_path, "rb"))
    else:
        await update.message.reply_text("No chart cached yet. Please upload a statement first.")
