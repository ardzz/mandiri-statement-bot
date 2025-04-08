import asyncio
import os

from core.chart.report_generator import generate_all_charts, combine_charts
from core.database import Session
from core.parser import parse_excel_data, open_excel
from core.repository.BankAccountRepository import BankAccountRepository
from core.repository.TransactionRepository import TransactionRepository


async def process_excel_async(file_path, user_id, context):
    """Process the Excel file asynchronously and generate charts."""
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, process_excel, file_path, user_id)

    if not result and context:  # if decryption failed and we can access Telegram context
        await context.bot.send_message(
            chat_id=user_id,
            text="❌ Failed to open your Excel file. Make sure the file password matches your birth date (DDMMYYYY)."
        )
    else:
        chart_path = f"cache/chart_cache/{user_id}_report.png"
        if os.path.exists(chart_path):
            with open(chart_path, "rb") as file:
                chart_data = file.read()
                await context.bot.send_photo(chat_id=user_id, photo=chart_data)
            await context.bot.send_message(chat_id=user_id, text="✅ Chart generated successfully!")
        else:
            await context.bot.send_message(chat_id=user_id, text="⚠️ Chart could not be found.")

def process_excel(file_path, user_id):
    """Process the Excel file and generate charts."""
    bank_account_repository = BankAccountRepository(Session())
    bank_account = bank_account_repository.get_by_telegram_id(user_id)
    birthdate = bank_account.birth_date.strftime("%d%m%Y")
    decrypt_excel = open_excel(file_path, birthdate)
    if decrypt_excel:
        transactions = parse_excel_data(decrypt_excel)
        bank_trx_repo = TransactionRepository(Session())
        bank_trx_repo.insert_transaction(transactions["transactions"], bank_account)
        generate_all_charts(transactions["transactions"], user_id)
        combine_charts(user_id, period=transactions["period"])
        return True
    return False
