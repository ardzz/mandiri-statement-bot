import os
from telegram import Update
from telegram.ext import ContextTypes

from bot.utils.auth import requires_registration
from core.tasks import process_excel_async

@requires_registration()
async def upload_excel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the upload of an Excel file."""
    user_id = update.effective_user.id
    file = await update.message.document.get_file()
    if not file.file_path.endswith('.xlsx'):
        return await update.message.reply_text("Please upload an Excel file (.xlsx)")

    os.makedirs("uploads", exist_ok=True)
    file_path = f"uploads/{user_id}_{file.file_unique_id}.xlsx"
    await file.download_to_drive(file_path)
    if os.path.getsize(file_path) > 1 * 1024 * 1024:
        os.remove(file_path)
        return await update.message.reply_text("File too large. Please upload a file smaller than 1MB.")
    await update.message.reply_text("File received. Processing...")
    await process_excel_async(file_path, user_id, context)
    os.remove(file_path)
    await update.message.reply_text("✅ Processing complete. Use /recap to view charts.")

@requires_registration()
async def guide_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Guide the user to upload their bank statement."""
    await update.message.reply_text("Please upload your bank statement Excel file 📄")
