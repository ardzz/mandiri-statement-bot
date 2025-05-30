import os
from datetime import datetime

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from bot.utils.auth import requires_registration
from core.chart.report_generator import generate_all_charts, combine_charts
from core.database import Session
from core.repository.BankAccountRepository import BankAccountRepository
from core.repository.TransactionRepository import TransactionRepository

CHOOSE_START_DATE, CHOOSE_END_DATE = range(2)

@requires_registration()
async def handle_recap_all_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a recap of the user's financial data for all time."""
    user_id = update.effective_user.id
    chart_path = f"cache/chart_cache/{user_id}_report_all_time.png"

    async def send_photo():
        with open(chart_path, "rb") as chart:
            await update.message.reply_text(
                "This is your all-time recap, if you want to sync it with the latest transactions, use /sync_recap.")
            await update.message.reply_photo(photo=chart)

    if os.path.exists(chart_path):
        await send_photo()
    else:
        bank_account_repo = BankAccountRepository(Session())
        bank_account = bank_account_repo.get_by_telegram_id(str(user_id))
        bank_trx_repo = TransactionRepository(Session())
        transactions = bank_trx_repo.get_all_transactions(bank_account.id)
        generate_all_charts(transactions, user_id, is_all_trx=True)
        combine_charts(user_id, period="All time", is_all_trx=True)
        await send_photo()


@requires_registration()
async def handle_sync_recap(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Synchronizes the user's financial data and generates a recap."""
    user_id = update.effective_user.id
    bank_account_repo = BankAccountRepository(Session())
    bank_trx_repo = TransactionRepository(Session())
    bank_account = bank_account_repo.get_by_telegram_id(str(user_id))
    transactions = bank_trx_repo.get_all_transactions(bank_account.id)

    if transactions:
        generate_all_charts(transactions, user_id, is_all_trx=True)
        combine_charts(user_id, period="All time", is_all_trx=True)
        await update.message.reply_text("Recap synchronized and updated, use /recap_all_time to view the updated chart.")
    else:
        await update.message.reply_text("No transactions found to sync.")


def generate_recap_text(statistics):
    total_transactions = statistics["total_transactions"]
    total_outcome = statistics["total_outcome"] or 0
    total_income = statistics["total_income"] or 0
    highest_outcome = statistics["highest_outcome"] or 0
    highest_income = statistics["highest_income"] or 0
    lowest_outcome = statistics["lowest_outcome"] or 0
    lowest_income = statistics["lowest_income"] or 0
    avg_outcome = statistics["avg_outcome"] or 0
    avg_income = statistics["avg_income"] or 0

    recap_message = (
        "📊 <b>All-Time Recap</b>\n"
        "If you want to sync with the latest transactions, use /sync_recap.\n\n"
        f"💳 Total transactions: <b>{total_transactions}</b>\n"
        f"💸 Total outcome: <b>Rp {abs(total_outcome):,.2f}</b>\n"
        f"💰 Total income: <b>Rp {total_income:,.2f}</b>\n"
        f"📉 Highest outcome: <b>Rp {abs(highest_outcome):,.2f}</b>\n"
        f"📈 Highest income: <b>Rp {highest_income:,.2f}</b>\n"
        f"📊 Average outcome: <b>Rp {abs(avg_outcome):,.2f}</b>\n"
        f"📊 Average income: <b>Rp {avg_income:,.2f}</b>\n"
        f"🔻 Lowest outcome: <b>Rp {abs(lowest_outcome):,.2f}</b>\n"
        f"🔺 Lowest income: <b>Rp {lowest_income:,.2f}</b>"
    )

    return recap_message


@requires_registration()
async def handle_recap_all_time_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a recap of the user's financial data for all time in text format."""
    user_id = update.effective_user.id
    bank_account_repo = BankAccountRepository(Session())
    bank_account = bank_account_repo.get_by_telegram_id(str(user_id))
    bank_trx_repo = TransactionRepository(Session())
    statistics = bank_trx_repo.get_transaction_statistics(bank_account.id)

    if statistics:
        recap_message = generate_recap_text(statistics)

        await update.message.reply_text(recap_message, parse_mode="HTML")
    else:
        await update.message.reply_text("No transactions found to display.")

@requires_registration()
async def handle_recap_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends the recap menu to the user."""
    keyboard = [
        ["📊 Recap All Time"],
        ["📊 Recap All Time Text Mode"],
        ["📅 Recap Custom Time"],
        ["🔄 Sync Recap"],
        ["↩️ Back to Main Menu"],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
    await update.message.reply_text(
        "Choose an option below 👇",
        reply_markup=reply_markup
    )

@requires_registration()
async def handle_custom_time_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📅 Please enter the start date (YYYY-MM-DD):")
    return CHOOSE_START_DATE

@requires_registration()
async def handle_custom_time_input_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        start_date = datetime.strptime(update.message.text.strip(), "%Y-%m-%d").date()
        context.user_data["start_date"] = start_date
        await update.message.reply_text("📅 Now enter the end date (YYYY-MM-DD):")
        return CHOOSE_END_DATE
    except ValueError:
        await update.message.reply_text("❌ Invalid date format. Please use YYYY-MM-DD.")
        return CHOOSE_START_DATE

def generate_recap(start_date, end_date):
    bank_trx_repo = TransactionRepository(Session())
    return bank_trx_repo.get_transaction_statistics_by_date_range(start_date, end_date)

@requires_registration()
async def handle_custom_time_input_end(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        end_date = datetime.strptime(update.message.text.strip(), "%Y-%m-%d").date()
        start_date = context.user_data["start_date"]

        if end_date < start_date:
            await update.message.reply_text("❌ End date cannot be earlier than start date. Try again.")
            return CHOOSE_END_DATE

        # Call your recap function here
        await update.message.reply_text(f"📊 Generating recap from {start_date} to {end_date}...")

        recap_text = generate_recap(start_date, end_date)
        recap_text = generate_recap_text(recap_text)
        await update.message.reply_text(recap_text, parse_mode="HTML")

        await update.message.reply_text("✅ Recap done!")  # placeholder
        return ConversationHandler.END

    except ValueError:
        await update.message.reply_text("❌ Invalid date format. Please use YYYY-MM-DD.")
        return CHOOSE_END_DATE

async def handle_back_to_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("↩️ Back to main menu.")
    return ConversationHandler.END
