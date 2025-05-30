import os
from datetime import datetime, date

from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from bot.utils.auth import requires_registration
from bot.utils.date_parser import (
    parse_flexible_date,
    DateParseError,
    validate_date_range,
    format_date_range_display,
    get_user_transaction_date_bounds,
    get_date_range_suggestions,
    calculate_preset_dates,
    get_preset_transaction_count
)
from core.chart.report_generator import generate_all_charts, combine_charts
from core.database import Session
from core.repository.BankAccountRepository import BankAccountRepository
from core.repository.TransactionRepository import TransactionRepository

# Updated conversation states
CHOOSE_PRESET, CHOOSE_START_DATE, CHOOSE_END_DATE = range(3)


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
        await update.message.reply_text(
            "Recap synchronized and updated, use /recap_all_time to view the updated chart.")
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
        "📊 <b>Recap Summary</b>\n\n"
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
async def handle_custom_time_start_with_presets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show preset buttons for quick date range selection."""
    user_id = update.effective_user.id
    min_date, max_date = get_user_transaction_date_bounds(user_id)

    # Create preset buttons with transaction counts
    preset_buttons = []

    # Row 1: Last 7 days, Last 30 days
    count_7d = get_preset_transaction_count("preset_7d", user_id)
    count_30d = get_preset_transaction_count("preset_30d", user_id)

    btn_7d_text = "📅 Last 7 Days"
    btn_30d_text = "📅 Last 30 Days"

    if count_7d is not None:
        btn_7d_text += f" ({count_7d} txns)"
    if count_30d is not None:
        btn_30d_text += f" ({count_30d} txns)"

    preset_buttons.append([
        InlineKeyboardButton(btn_7d_text, callback_data="preset_7d"),
        InlineKeyboardButton(btn_30d_text, callback_data="preset_30d")
    ])

    # Row 2: This month, Last month
    count_this_month = get_preset_transaction_count("preset_this_month", user_id)
    count_last_month = get_preset_transaction_count("preset_last_month", user_id)

    btn_this_month_text = "📅 This Month"
    btn_last_month_text = "📅 Last Month"

    if count_this_month is not None:
        btn_this_month_text += f" ({count_this_month} txns)"
    if count_last_month is not None:
        btn_last_month_text += f" ({count_last_month} txns)"

    preset_buttons.append([
        InlineKeyboardButton(btn_this_month_text, callback_data="preset_this_month"),
        InlineKeyboardButton(btn_last_month_text, callback_data="preset_last_month")
    ])

    # Row 3: This year, Last year
    count_this_year = get_preset_transaction_count("preset_this_year", user_id)
    count_last_year = get_preset_transaction_count("preset_last_year", user_id)

    btn_this_year_text = "📅 This Year"
    btn_last_year_text = "📅 Last Year"

    if count_this_year is not None:
        btn_this_year_text += f" ({count_this_year} txns)"
    if count_last_year is not None:
        btn_last_year_text += f" ({count_last_year} txns)"

    preset_buttons.append([
        InlineKeyboardButton(btn_this_year_text, callback_data="preset_this_year"),
        InlineKeyboardButton(btn_last_year_text, callback_data="preset_last_year")
    ])

    # Row 4: Custom range, Cancel
    preset_buttons.append([
        InlineKeyboardButton("🎯 Custom Range", callback_data="custom_range"),
        InlineKeyboardButton("❌ Cancel", callback_data="cancel")
    ])

    reply_markup = InlineKeyboardMarkup(preset_buttons)

    # Prepare message with user's transaction context
    message_parts = ["📊 <b>Choose Your Recap Time Range</b>\n"]

    if min_date and max_date:
        message_parts.append(
            f"📅 Your data: <b>{min_date.strftime('%b %d, %Y')} → {max_date.strftime('%b %d, %Y')}</b>\n")
    else:
        message_parts.append("⚠️ No transaction history found. Upload your bank statement first.\n")

    message_parts.append("Select a quick preset or choose custom range:")

    message = "\n".join(message_parts)

    await update.message.reply_text(message, parse_mode="HTML", reply_markup=reply_markup)
    return CHOOSE_PRESET


async def handle_preset_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline keyboard button presses for date presets."""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    data = query.data

    if data == "cancel":
        await query.edit_message_text("❌ Cancelled. Use /recap to try again.")
        return ConversationHandler.END

    if data == "custom_range":
        # Switch to manual date input
        await query.edit_message_text("🎯 <b>Custom Date Range</b>\n\nSwitching to manual date input...",
                                      parse_mode="HTML")
        # Trigger the original manual input flow
        return await handle_custom_time_start(update, context)

    try:
        # Handle preset selections
        start_date, end_date, description = calculate_preset_dates(data)

        # Validate against user's data
        min_date, max_date = get_user_transaction_date_bounds(user_id)
        is_valid, validation_msg = validate_date_range(start_date, end_date, min_date, max_date)

        if not is_valid:
            await query.edit_message_text(
                f"❌ {validation_msg}\n\n💡 Try a different range or upload more transaction data.\nUse /recap to try again.",
                parse_mode="HTML"
            )
            return ConversationHandler.END

        # Show confirmation and generate recap
        date_display = format_date_range_display(start_date, end_date)
        await query.edit_message_text(
            f"📊 <b>Generating {description} Recap</b>\n\n{date_display}\n\n⏳ Please wait...",
            parse_mode="HTML"
        )

        # Generate recap statistics
        recap_stats = generate_recap(start_date, end_date)

        if recap_stats and recap_stats.get("total_transactions", 0) > 0:
            recap_text = generate_recap_text(recap_stats)
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=f"📊 <b>{description} Recap</b>\n{date_display}\n\n{recap_text}",
                parse_mode="HTML"
            )
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text="✅ Recap completed! Use /recap for another time range."
            )
        else:
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=f"📊 <b>{description} Recap</b>\n{date_display}\n\n❌ No transactions found in this date range.\n\n💡 Try a different period or check if you have uploaded your bank statements."
            )

        return ConversationHandler.END

    except Exception as e:
        await query.edit_message_text(
            f"❌ Error processing preset: {str(e)}\n\nUse /recap to try again.",
            parse_mode="HTML"
        )
        return ConversationHandler.END


# Keep the original manual input functions for custom range fallback
@requires_registration()
async def handle_custom_time_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the custom time range selection with enhanced date input."""
    user_id = update.effective_user.id

    # Get user's transaction date bounds
    min_date, max_date = get_user_transaction_date_bounds(user_id)

    # Prepare message with context
    message_parts = ["📅 <b>Custom Time Range Recap</b>\n"]

    if min_date and max_date:
        message_parts.append(
            f"📊 Your transaction history: <b>{min_date.strftime('%b %d, %Y')} → {max_date.strftime('%b %d, %Y')}</b>\n")
    else:
        message_parts.append("⚠️ No transaction history found. Upload your bank statement first.\n")

    message_parts.extend([
        "📅 <b>Please enter the START date:</b>\n",
        "<b>Supported formats:</b>",
        "• <code>2025-05-30</code> (YYYY-MM-DD)",
        "• <code>30/05/2025</code> (DD/MM/YYYY)",
        "• <code>May 30, 2025</code> (natural language)",
        "• <code>yesterday</code>, <code>last week</code>, <code>last month</code> (relative)",
        "",
        "<b>💡 Quick examples:</b>"
    ])

    # Add suggestions based on user's data
    suggestions = get_date_range_suggestions(min_date, max_date)
    for suggestion in suggestions[:3]:  # Show top 3 suggestions
        message_parts.append(f"• {suggestion}")

    message = "\n".join(message_parts)

    await update.effective_message.reply_text(message, parse_mode="HTML")
    return CHOOSE_START_DATE


@requires_registration()
async def handle_custom_time_input_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle start date input with flexible parsing."""
    user_id = update.effective_user.id
    user_input = update.message.text.strip()

    try:
        start_date = parse_flexible_date(user_input)

        # Get user's transaction bounds for validation
        min_date, max_date = get_user_transaction_date_bounds(user_id)

        # Store the parsed start date
        context.user_data["start_date"] = start_date
        context.user_data["user_min_date"] = min_date
        context.user_data["user_max_date"] = max_date

        # Show what we understood and ask for end date
        message_parts = [
            f"✅ Start date: <b>{start_date.strftime('%B %d, %Y')}</b>",
            "",
            "📅 <b>Now enter the END date:</b>",
            "",
            "<b>💡 Examples:</b>",
            f"• <code>today</code> (for up to today)",
            f"• <code>{date.today().strftime('%Y-%m-%d')}</code> (today in YYYY-MM-DD)",
            f"• <code>{date.today().strftime('%d/%m/%Y')}</code> (today in DD/MM/YYYY)",
        ]

        if max_date:
            message_parts.append(f"• <code>{max_date.strftime('%b %d, %Y')}</code> (your latest transaction)")

        message = "\n".join(message_parts)
        await update.message.reply_text(message, parse_mode="HTML")
        return CHOOSE_END_DATE

    except DateParseError as e:
        # Enhanced error message with suggestions
        error_parts = [
            f"❌ {e.message}",
            "",
            "💡 <b>Try one of these formats:</b>"
        ]

        for suggestion in e.suggestions:
            error_parts.append(f"• <code>{suggestion}</code>")

        # Add user-specific context if available
        min_date, max_date = get_user_transaction_date_bounds(user_id)
        if min_date and max_date:
            error_parts.extend([
                "",
                f"📅 Your data is available from <b>{min_date.strftime('%b %d, %Y')}</b> to <b>{max_date.strftime('%b %d, %Y')}</b>"
            ])

        error_message = "\n".join(error_parts)
        await update.message.reply_text(error_message, parse_mode="HTML")
        return CHOOSE_START_DATE


def generate_recap(start_date, end_date):
    """Generate recap statistics for the given date range."""
    bank_trx_repo = TransactionRepository(Session())
    return bank_trx_repo.get_transaction_statistics_by_date_range(start_date, end_date)


@requires_registration()
async def handle_custom_time_input_end(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle end date input with validation and generate recap."""
    user_input = update.message.text.strip()

    try:
        end_date = parse_flexible_date(user_input)
        start_date = context.user_data["start_date"]
        min_date = context.user_data.get("user_min_date")
        max_date = context.user_data.get("user_max_date")

        # Validate the date range
        is_valid, validation_message = validate_date_range(start_date, end_date, min_date, max_date)

        if not is_valid:
            await update.message.reply_text(validation_message)
            return CHOOSE_END_DATE

        # Show validation warnings if any
        if "⚠️" in validation_message:
            await update.message.reply_text(validation_message, parse_mode="HTML")

        # Format and confirm the date range
        date_range_display = format_date_range_display(start_date, end_date)
        await update.message.reply_text(f"📊 Generating custom recap for:\n{date_range_display}\n\n⏳ Please wait...")

        # Generate the recap
        recap_stats = generate_recap(start_date, end_date)

        if recap_stats and recap_stats.get("total_transactions", 0) > 0:
            recap_text = generate_recap_text(recap_stats)
            await update.message.reply_text(f"📊 <b>Custom Range Recap</b>\n{date_range_display}\n\n{recap_text}",
                                            parse_mode="HTML")
            await update.message.reply_text("✅ Custom time range recap completed!")
        else:
            await update.message.reply_text(
                f"📊 No transactions found in the date range:\n{date_range_display}\n\n"
                "💡 Try a different date range or check if you have uploaded your bank statements."
            )

        return ConversationHandler.END

    except DateParseError as e:
        # Enhanced error message for end date
        error_parts = [
            f"❌ {e.message}",
            "",
            "💡 <b>Try one of these formats:</b>"
        ]

        for suggestion in e.suggestions:
            error_parts.append(f"• <code>{suggestion}</code>")

        # Remind about start date context
        start_date = context.user_data["start_date"]
        error_parts.extend([
            "",
            f"📅 Remember: Start date is <b>{start_date.strftime('%B %d, %Y')}</b>",
            "End date should be the same or later."
        ])

        error_message = "\n".join(error_parts)
        await update.message.reply_text(error_message, parse_mode="HTML")
        return CHOOSE_END_DATE


async def handle_back_to_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle cancellation and return to main menu."""
    await update.message.reply_text("↩️ Cancelled. Back to main menu.")
    return ConversationHandler.END