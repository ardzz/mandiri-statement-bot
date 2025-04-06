import asyncio
import os

from core.chart.report_generator import generate_all_charts, combine_charts
from core.database import Session
from core.parser import parse_excel_data, open_excel
from core.repository.BankAccountRepository import BankAccountRepository


async def process_excel_async(file_path, user_id, context):
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
            await context.bot.send_photo(chat_id=user_id, photo=open(chart_path, "rb"))
            await context.bot.send_message(chat_id=user_id, text="✅ Chart generated successfully!")
        else:
            await context.bot.send_message(chat_id=user_id, text="⚠️ Chart could not be found.")

def process_excel(file_path, user_id):
    bank_account_repository = BankAccountRepository(Session())
    bank_account = bank_account_repository.get_by_telegram_id(user_id)
    birthdate = bank_account.birth_date.strftime("%d%m%Y")
    decrypt_excel = open_excel(file_path, birthdate)
    if decrypt_excel:
        transactions = parse_excel_data(decrypt_excel)
        generate_all_charts(transactions["transactions"], user_id)
        combine_charts(user_id, period=transactions["period"])
        return True
    else:
        return False