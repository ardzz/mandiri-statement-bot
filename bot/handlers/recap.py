import os

from telegram import Update
from telegram.ext import ContextTypes

from bot.utils.auth import requires_registration
from core.chart.report_generator import generate_all_charts, combine_charts
from core.database import Session
from core.repository.BankAccountRepository import BankAccountRepository
from core.repository.TransactionRepository import TransactionRepository


@requires_registration()
async def send_recap(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a recap of the user's financial data."""
    user_id = update.effective_user.id
    chart_path = f"cache/chart_cache/{user_id}_report.png"

    if os.path.exists(chart_path):
        with open(chart_path, "rb") as chart:
            await update.message.reply_photo(photo=chart)
    else:
        await update.message.reply_text("No chart cached yet. Please upload a statement first.")


@requires_registration()
async def send_recap_all_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
async def sync_recap(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

@requires_registration()
async def recap_all_time_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a recap of the user's financial data for all time in text format."""
    user_id = update.effective_user.id
    bank_account_repo = BankAccountRepository(Session())
    bank_account = bank_account_repo.get_by_telegram_id(str(user_id))
    bank_trx_repo = TransactionRepository(Session())
    transactions = bank_trx_repo.get_all_transactions(bank_account.id)

    if transactions:
        total_transactions = len(transactions)
        total_outcome = sum(trx.outgoing for trx in transactions if trx.outgoing and trx.outgoing < 0)
        total_income = sum(trx.incoming for trx in transactions if trx.incoming and trx.incoming > 0)
        highest_outcome = max((trx.outgoing for trx in transactions if trx.outgoing and trx.outgoing < 0), default=0)
        highest_income = max((trx.incoming for trx in transactions if trx.incoming and trx.incoming > 0), default=0)
        lowest_outcome = min((trx.outgoing for trx in transactions if trx.outgoing and trx.outgoing < 0), default=0)
        lowest_income = min((trx.incoming for trx in transactions if trx.incoming and trx.incoming > 0), default=0)

        outcome_count = len([trx for trx in transactions if trx.outgoing and trx.outgoing < 0])
        income_count = len([trx for trx in transactions if trx.incoming and trx.incoming > 0])

        avg_outcome = total_outcome / outcome_count if outcome_count else 0
        avg_income = total_income / income_count if income_count else 0

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

        await update.message.reply_text(recap_message, parse_mode="HTML")
    else:
        await update.message.reply_text("No transactions found to display.")