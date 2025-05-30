import os
from telegram import Update
from telegram.ext import ContextTypes

from bot.utils.auth import requires_registration
from core.tasks import process_excel_async


@requires_registration()
async def handle_excel_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    # Auto-categorize new transactions
    await update.message.reply_text("🔄 Auto-categorizing transactions...")

    try:
        from core.services.categorization_service import CategorizationService
        cat_service = CategorizationService()
        result = cat_service.auto_categorize_transactions(user_id)

        if result['successfully_categorized'] > 0:
            await update.message.reply_text(
                f"✅ Processing complete!\n\n"
                f"📊 Auto-categorized {result['successfully_categorized']} transactions\n"
                f"📈 Use /trends to view category analysis\n"
                f"📊 Use /recap to see your spending summary"
            )
            return None
        else:
            await update.message.reply_text(
                "✅ Processing complete!\n\n"
                "📊 Use /categorize to assign categories to your transactions\n"
                "📈 Use /trends to view analysis once categorized"
            )
            return None
    except Exception as e:
        await update.message.reply_text(
            "✅ File processed successfully!\n\n"
            "💡 Use /categorize to assign categories to your transactions for better analysis."
        )
        return None


@requires_registration()
async def handle_upload_guide(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Guide the user to upload their bank statement."""
    guide_text = (
        "📄 <b>Upload Your Bank Statement</b>\n\n"
        "📋 <b>Instructions:</b>\n"
        "1. Download your Mandiri e-Statement in Excel format\n"
        "2. Make sure the file is encrypted with your birth date (DDMMYYYY)\n"
        "3. Upload the .xlsx file to this chat\n\n"
        "🔒 <b>Security:</b>\n"
        "• Your birth date is used as the decryption password\n"
        "• All data is processed locally and securely\n"
        "• Files are automatically deleted after processing\n\n"
        "✨ <b>After Upload:</b>\n"
        "• Transactions will be automatically categorized\n"
        "• Charts and analysis will be generated\n"
        "• Use /trends to explore spending patterns\n\n"
        "💡 <b>Tip:</b> Upload statements regularly for accurate financial tracking!"
    )

    await update.message.reply_text(guide_text, parse_mode="HTML")