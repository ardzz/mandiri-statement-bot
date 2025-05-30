from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.utils.auth import requires_registration


@requires_registration()
async def handle_settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show settings and configuration menu."""
    keyboard = [
        [
            InlineKeyboardButton("👤 Account Info", callback_data="settings_account"),
            InlineKeyboardButton("📅 Update Birthdate", callback_data="settings_birthdate")
        ],
        [
            InlineKeyboardButton("🔔 Notification Settings", callback_data="settings_notifications"),
            InlineKeyboardButton("📊 Display Preferences", callback_data="settings_display")
        ],
        [
            InlineKeyboardButton("🗑️ Data Management", callback_data="settings_data"),
            InlineKeyboardButton("❓ Help & Support", callback_data="settings_help")
        ],
        [
            InlineKeyboardButton("🔄 Reset All Settings", callback_data="settings_reset"),
            InlineKeyboardButton("❌ Close", callback_data="settings_close")
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "⚙️ <b>Settings & Configuration</b>\n\n"
        "Customize your bot experience:\n\n"
        "• 👤 Manage account information\n"
        "• 🔔 Configure notifications and alerts\n"
        "• 📊 Set display preferences\n"
        "• 🗑️ Manage your data and privacy\n"
        "• ❓ Get help and support\n\n"
        "Choose an option:",
        parse_mode="HTML",
        reply_markup=reply_markup
    )


async def handle_settings_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle settings menu selections."""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    data = query.data

    if data == "settings_close":
        await query.edit_message_text("Settings closed. Use /settings to open again.")
        return

    try:
        if data == "settings_account":
            await _show_account_info(query, user_id)
        elif data == "settings_birthdate":
            await _show_birthdate_update(query, user_id)
        elif data == "settings_notifications":
            await _show_notification_settings(query, user_id)
        elif data == "settings_display":
            await _show_display_preferences(query, user_id)
        elif data == "settings_data":
            await _show_data_management(query, user_id)
        elif data == "settings_help":
            await _show_help_support(query, user_id)
        elif data == "settings_reset":
            await _show_reset_confirmation(query, user_id)

    except Exception as e:
        await query.edit_message_text(f"❌ Error: {str(e)}")


async def _show_account_info(query, user_id):
    """Show user account information."""
    from core.database import Session
    from core.repository.BankAccountRepository import BankAccountRepository
    from core.repository.TransactionRepository import TransactionRepository

    session = Session()
    account_repo = BankAccountRepository(session)
    account = account_repo.get_by_telegram_id(str(user_id))

    if not account:
        await query.edit_message_text("❌ No account found.")
        return

    trx_repo = TransactionRepository(session)
    transactions = trx_repo.get_all_transactions(account.id)

    account_text = (
        "👤 <b>Account Information</b>\n\n"
        f"🆔 <b>Telegram ID:</b> {account.telegram_id}\n"
        f"🏦 <b>Bank Name:</b> {account.bank_name or 'Not set'}\n"
        f"💳 <b>Account Number:</b> {account.account_number or 'Not set'}\n"
        f"💰 <b>Current Balance:</b> {account.balance:,.0f} IDR\n" if account.balance else "💰 <b>Current Balance:</b> Not available\n"
                                                                                          f"📅 <b>Birth Date:</b> {account.birth_date.strftime('%Y-%m-%d') if account.birth_date else 'Not set'}\n"
                                                                                          f"📊 <b>Total Transactions:</b> {len(transactions)}\n\n"
                                                                                          "💡 <b>Account Status:</b> Active ✅\n"
                                                                                          "🔒 <b>Data Security:</b> All data is encrypted and secure"
    )

    await query.edit_message_text(account_text, parse_mode="HTML")


async def _show_birthdate_update(query, user_id):
    """Show birthdate update instructions."""
    update_text = (
        "📅 <b>Update Birth Date</b>\n\n"
        "Your birth date is used as the password for your encrypted bank statement files.\n\n"
        "To update your birth date:\n"
        "1. Use the '📅 Update Birthdate' button from the main menu\n"
        "2. Enter your new birth date in YYYY-MM-DD format\n"
        "3. Make sure it matches your bank statement password\n\n"
        "⚠️ <b>Important:</b>\n"
        "• Birth date must match your bank statement encryption password\n"
        "• Format must be exactly YYYY-MM-DD (e.g., 1990-05-15)\n"
        "• This is required for processing encrypted Excel files"
    )

    await query.edit_message_text(update_text, parse_mode="HTML")


async def _show_notification_settings(query, user_id):
    """Show notification and alert settings."""
    notification_text = (
        "🔔 <b>Notification Settings</b>\n\n"
        "Configure when and how you receive alerts:\n\n"
        "📊 <b>Budget Alerts:</b> ✅ Enabled\n"
        "• Budget exceeded warnings\n"
        "• 80% budget usage alerts\n"
        "• Monthly budget summaries\n\n"
        "⚠️ <b>Spending Anomalies:</b> ✅ Enabled\n"
        "• Unusual spending pattern detection\n"
        "• Large transaction alerts\n"
        "• Weekly spending summaries\n\n"
        "🎯 <b>Goal Updates:</b> ✅ Enabled\n"
        "• Goal milestone notifications\n"
        "• Progress reminders\n"
        "• Achievement celebrations\n\n"
        "💡 <b>Smart Insights:</b> ✅ Enabled\n"
        "• Weekly financial health reports\n"
        "• Savings opportunity alerts\n"
        "• Personalized recommendations\n\n"
        "⚙️ Use /toggle_notifications to customize these settings"
    )

    await query.edit_message_text(notification_text, parse_mode="HTML")


async def _show_display_preferences(query, user_id):
    """Show display and format preferences."""
    display_text = (
        "📊 <b>Display Preferences</b>\n\n"
        "Customize how information is shown:\n\n"
        "💱 <b>Currency Format:</b> Indonesian Rupiah (IDR) ✅\n"
        "📅 <b>Date Format:</b> YYYY-MM-DD ✅\n"
        "📊 <b>Chart Style:</b> Modern with colors ✅\n"
        "📱 <b>Message Format:</b> Rich HTML ✅\n"
        "🔢 <b>Number Format:</b> Thousand separators ✅\n\n"
        "🌍 <b>Language:</b> English 🇺🇸\n"
        "• Indonesian 🇮🇩 (Coming soon)\n\n"
        "📊 <b>Chart Preferences:</b>\n"
        "• High-resolution charts ✅\n"
        "• Include trend lines ✅\n"
        "• Show moving averages ✅\n"
        "• Color-coded categories ✅\n\n"
        "⚙️ More customization options coming soon!"
    )

    await query.edit_message_text(display_text, parse_mode="HTML")


async def _show_data_management(query, user_id):
    """Show data management and privacy options."""
    data_text = (
        "🗑️ <b>Data Management & Privacy</b>\n\n"
        "Manage your financial data:\n\n"
        "📊 <b>Data Overview:</b>\n"
        "• Transaction records: Stored securely\n"
        "• Budget settings: Saved locally\n"
        "• Goals and preferences: Encrypted\n"
        "• Chart cache: Temporary files\n\n"
        "🔒 <b>Privacy & Security:</b>\n"
        "• All data is encrypted at rest\n"
        "• No data shared with third parties\n"
        "• Local processing only\n"
        "• Regular security updates\n\n"
        "🗑️ <b>Data Actions:</b>\n"
        "• <code>/export_data</code> - Download your data\n"
        "• <code>/clear_cache</code> - Clear temporary files\n"
        "• <code>/delete_account</code> - Permanently delete all data\n\n"
        "⚠️ <b>Warning:</b> Data deletion is permanent and cannot be undone!"
    )

    await query.edit_message_text(data_text, parse_mode="HTML")


async def _show_help_support(query, user_id):
    """Show help and support information."""
    help_text = (
        "❓ <b>Help & Support</b>\n\n"
        "Get help with using the bot:\n\n"
        "📚 <b>Quick Start Guide:</b>\n"
        "1. Upload your bank statement Excel file\n"
        "2. View your financial recap and trends\n"
        "3. Set budgets and financial goals\n"
        "4. Get smart insights and recommendations\n\n"
        "🔧 <b>Common Commands:</b>\n"
        "• <code>/start</code> - Restart the bot\n"
        "• <code>/menu</code> - Show main menu\n"
        "• <code>/recap</code> - Quick financial summary\n"
        "• <code>/trends</code> - Spending analysis\n"
        "• <code>/budget</code> - Budget management\n"
        "• <code>/goals</code> - Financial goals\n"
        "• <code>/insights</code> - Smart recommendations\n\n"
        "🐛 <b>Report Issues:</b>\n"
        "Found a bug or have a suggestion? Contact:\n"
        "• GitHub: github.com/ardzz/mandiri-statement-bot\n"
        "• Email: support@example.com\n\n"
        "📖 <b>Documentation:</b>\n"
        "• Full user guide: /guide\n"
        "• FAQ: /faq\n"
        "• Video tutorials: Coming soon!"
    )

    await query.edit_message_text(help_text, parse_mode="HTML")


async def _show_reset_confirmation(query, user_id):
    """Show reset confirmation dialog."""
    reset_text = (
        "🔄 <b>Reset All Settings</b>\n\n"
        "⚠️ <b>Warning:</b> This will reset:\n"
        "• All budget limits\n"
        "• Financial goals\n"
        "• Notification preferences\n"
        "• Display settings\n\n"
        "❗ <b>This will NOT delete:</b>\n"
        "• Your transaction history\n"
        "• Account information\n"
        "• Generated charts\n\n"
        "To confirm reset, type: <code>/confirm_reset</code>\n\n"
        "💡 Consider backing up your settings first with <code>/export_data</code>"
    )

    await query.edit_message_text(reset_text, parse_mode="HTML")