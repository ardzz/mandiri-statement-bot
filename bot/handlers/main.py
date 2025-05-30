from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes


async def handle_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send the main menu to the user with all available features."""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            ["📤 Upload E-statement Excel"],
            ["📊 Recap", "📈 Trends & Analysis"],
            ["💰 Budget Management", "🎯 Financial Goals"],
            ["🔔 Smart Insights", "🏷️ Auto Categorize"],
            ["📅 Update Birthdate", "❓ Help"],
            ["⚙️ Settings"]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    await update.message.reply_text(
        "🏦 <b>Mandiri Finance Bot</b> 💸\n\n"
        "Welcome to your personal finance management assistant!\n\n"
        "📊 <b>Available Features:</b>\n"
        "• 📤 Upload bank statements for analysis\n"
        "• 📊 View spending recaps and summaries\n"
        "• 📈 Advanced trend analysis & patterns\n"
        "• 💰 Set and track budget limits\n"
        "• 🎯 Create and monitor financial goals\n"
        "• 🔔 Get smart spending insights & alerts\n"
        "• 🏷️ Auto-categorize transactions\n\n"
        "💡 <b>Quick Commands:</b>\n"
        "• /categorize - Auto-assign categories\n"
        "• /categorization_stats - Check categorization status\n"
        "• /trends - View category analysis\n\n"
        "Choose an option below to get started 👇",
        reply_markup=keyboard,
        parse_mode="HTML"
    )