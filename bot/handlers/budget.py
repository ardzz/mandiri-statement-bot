from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters
from bot.utils.auth import requires_registration
from core.services.financial_analysis import FinancialAnalysisService
from core.repository.BudgetRepository import BudgetRepository
from core.database import Session
from core.chart.advanced_visuals import plot_budget_progress
import os

# Conversation states
SETTING_CATEGORY, SETTING_AMOUNT = range(2)


@requires_registration()
async def handle_budget_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show budget management menu."""
    keyboard = [
        [
            InlineKeyboardButton("💰 View Budget Status", callback_data="budget_view"),
            InlineKeyboardButton("⚙️ Set Budget Limits", callback_data="budget_set")
        ],
        [
            InlineKeyboardButton("📊 Budget Progress Chart", callback_data="budget_chart"),
            InlineKeyboardButton("🔔 Budget Alerts", callback_data="budget_alerts")
        ],
        [InlineKeyboardButton("❌ Close", callback_data="budget_close")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "💰 <b>Budget Management</b>\n\n"
        "Manage your spending limits and track budget progress:",
        parse_mode="HTML",
        reply_markup=reply_markup
    )


async def handle_budget_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle budget menu selections."""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    data = query.data

    if data == "budget_close":
        await query.edit_message_text("Budget management closed. Use /budget to open again.")
        return

    try:
        if data == "budget_view":
            await _show_budget_status(query, user_id)
        elif data == "budget_set":
            await _start_budget_setting(query, user_id)
        elif data == "budget_chart":
            await _show_budget_chart(query, user_id)
        elif data == "budget_alerts":
            await _show_budget_alerts(query, user_id)

    except Exception as e:
        await query.edit_message_text(f"❌ Error: {str(e)}")


async def _show_budget_status(query, user_id):
    """Show current budget status."""
    analysis_service = FinancialAnalysisService()
    budget_status = analysis_service.check_budget_status(user_id)

    if not budget_status:
        await query.edit_message_text(
            "💰 <b>No Budget Limits Set</b>\n\n"
            "You haven't set any budget limits yet. Use the 'Set Budget Limits' option to get started!",
            parse_mode="HTML"
        )
        return

    message_parts = ["💰 <b>Current Budget Status</b>\n"]

    total_budget = 0
    total_spent = 0

    for category, status in budget_status.items():
        status_emoji = "🔴" if status['status'] == 'exceeded' else "🟡" if status['status'] == 'warning' else "🟢"

        message_parts.append(
            f"{status_emoji} <b>{category}</b>\n"
            f"   Spent: {status['spent']:,.0f} IDR\n"
            f"   Budget: {status['limit']:,.0f} IDR\n"
            f"   Usage: {status['usage_percentage']:.1f}%\n"
            f"   Remaining: {status['remaining']:,.0f} IDR\n"
        )

        total_budget += status['limit']
        total_spent += status['spent']

    overall_usage = (total_spent / total_budget * 100) if total_budget > 0 else 0

    message_parts.append(
        f"\n📊 <b>Overall Budget Summary</b>\n"
        f"Total Spent: {total_spent:,.0f} IDR\n"
        f"Total Budget: {total_budget:,.0f} IDR\n"
        f"Overall Usage: {overall_usage:.1f}%"
    )

    budget_text = "\n".join(message_parts)
    await query.edit_message_text(budget_text, parse_mode="HTML")


async def _start_budget_setting(query, user_id):
    """Start the budget setting conversation."""
    common_categories = [
        "Food & Dining", "Shopping", "Transportation", "Entertainment",
        "Bills & Utilities", "Health & Fitness", "Personal Care"
    ]

    keyboard = []
    for i in range(0, len(common_categories), 2):
        row = [InlineKeyboardButton(common_categories[i], callback_data=f"set_budget_{common_categories[i]}")]
        if i + 1 < len(common_categories):
            row.append(
                InlineKeyboardButton(common_categories[i + 1], callback_data=f"set_budget_{common_categories[i + 1]}"))
        keyboard.append(row)

    keyboard.append([InlineKeyboardButton("✏️ Custom Category", callback_data="set_budget_custom")])
    keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="budget_close")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        "⚙️ <b>Set Budget Limit</b>\n\n"
        "Choose a category to set or update budget limit:",
        parse_mode="HTML",
        reply_markup=reply_markup
    )


async def handle_budget_category_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle budget category selection."""
    query = update.callback_query
    await query.answer()

    if query.data.startswith("set_budget_"):
        category = query.data.replace("set_budget_", "")

        if category == "custom":
            await query.edit_message_text(
                "✏️ <b>Custom Category</b>\n\n"
                "Please type the name of the category you want to set a budget for:",
                parse_mode="HTML"
            )
            context.user_data["budget_setting_step"] = "custom_category"
        else:
            context.user_data["budget_category"] = category
            await query.edit_message_text(
                f"💰 <b>Set Budget for {category}</b>\n\n"
                "Please enter the monthly budget limit amount (in IDR):\n"
                "Example: 1000000 (for 1 million IDR)",
                parse_mode="HTML"
            )
            context.user_data["budget_setting_step"] = "amount"

        return SETTING_AMOUNT


async def handle_budget_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle budget input during conversation."""
    text = update.message.text.strip()
    step = context.user_data.get("budget_setting_step")

    if step == "custom_category":
        # User entered custom category name
        context.user_data["budget_category"] = text
        await update.message.reply_text(
            f"💰 <b>Set Budget for {text}</b>\n\n"
            "Please enter the monthly budget limit amount (in IDR):\n"
            "Example: 1000000 (for 1 million IDR)",
            parse_mode="HTML"
        )
        context.user_data["budget_setting_step"] = "amount"
        return SETTING_AMOUNT

    elif step == "amount":
        # User entered budget amount
        try:
            amount = float(text.replace(",", "").replace(".", ""))
            if amount <= 0:
                await update.message.reply_text("❌ Please enter a positive amount.")
                return SETTING_AMOUNT

            # Save budget limit
            user_id = update.effective_user.id
            category = context.user_data["budget_category"]

            from core.database import Session
            from core.repository.BankAccountRepository import BankAccountRepository

            session = Session()
            account_repo = BankAccountRepository(session)
            account = account_repo.get_by_telegram_id(str(user_id))

            if account:
                budget_repo = BudgetRepository(session)
                budget_repo.set_budget_limit(account.id, category, amount)

                await update.message.reply_text(
                    f"✅ <b>Budget Set Successfully!</b>\n\n"
                    f"Category: {category}\n"
                    f"Monthly Limit: {amount:,.0f} IDR\n\n"
                    "Use /budget to view your budget status.",
                    parse_mode="HTML"
                )
            else:
                await update.message.reply_text("❌ Account not found.")

            # Clear user data
            context.user_data.clear()
            return ConversationHandler.END

        except ValueError:
            await update.message.reply_text(
                "❌ Please enter a valid number.\n"
                "Example: 1000000 (for 1 million IDR)"
            )
            return SETTING_AMOUNT


async def _show_budget_chart(query, user_id):
    """Show budget progress chart."""
    await query.edit_message_text("📊 Generating budget progress chart... ⏳")

    try:
        analysis_service = FinancialAnalysisService()
        budget_status = analysis_service.check_budget_status(user_id)

        if not budget_status:
            await query.edit_message_text(
                "📊 <b>No Budget Data</b>\n\n"
                "Set budget limits first to see progress charts.",
                parse_mode="HTML"
            )
            return

        # Get transactions for chart
        from core.database import Session
        from core.repository.BankAccountRepository import BankAccountRepository
        from core.repository.TransactionRepository import TransactionRepository

        session = Session()
        account_repo = BankAccountRepository(session)
        account = account_repo.get_by_telegram_id(str(user_id))

        if not account:
            await query.edit_message_text("❌ Account not found.")
            return

        trx_repo = TransactionRepository(session)
        transactions = trx_repo.get_all_transactions(account.id)

        # Create budget limits dict
        budget_limits = {category: status['limit'] for category, status in budget_status.items()}

        # Generate chart
        os.makedirs("cache/chart_cache", exist_ok=True)
        chart_path = f"cache/chart_cache/{user_id}_budget_progress.png"
        plot_budget_progress(transactions, budget_limits, chart_path)

        # Send chart
        with open(chart_path, 'rb') as chart:
            await query.message.reply_photo(
                photo=chart,
                caption="📊 <b>Budget Progress Chart</b>\n\nVisual representation of your spending vs budget limits.",
                parse_mode="HTML"
            )

        await query.edit_message_text("✅ Budget chart generated!")

    except Exception as e:
        await query.edit_message_text(f"❌ Error generating chart: {str(e)}")


async def _show_budget_alerts(query, user_id):
    """Show budget-related alerts."""
    from core.database import Session
    from core.repository.BankAccountRepository import BankAccountRepository
    from core.repository.BudgetRepository import AlertRepository

    session = Session()
    account_repo = BankAccountRepository(session)
    account = account_repo.get_by_telegram_id(str(user_id))

    if not account:
        await query.edit_message_text("❌ Account not found.")
        return

    alert_repo = AlertRepository(session)
    alerts = alert_repo.get_user_alerts(account.id, unread_only=False)

    # Filter budget-related alerts
    budget_alerts = [a for a in alerts if a.alert_type in ['budget_exceeded', 'budget_warning']]

    if not budget_alerts:
        await query.edit_message_text(
            "🔔 <b>No Budget Alerts</b>\n\n"
            "You don't have any budget-related alerts yet.",
            parse_mode="HTML"
        )
        return

    message_parts = ["🔔 <b>Budget Alerts</b>\n"]

    for alert in budget_alerts[:10]:  # Show last 10 alerts
        alert_emoji = "🔴" if alert.alert_type == 'budget_exceeded' else "🟡"
        read_status = "✅" if alert.is_read else "🔔"

        message_parts.append(
            f"{alert_emoji} {read_status} <b>{alert.category or 'General'}</b>\n"
            f"   {alert.message}\n"
            f"   {alert.created_at.strftime('%Y-%m-%d %H:%M')}\n"
        )

    alerts_text = "\n".join(message_parts)
    await query.edit_message_text(alerts_text, parse_mode="HTML")


# Budget setting conversation handler
budget_conversation = ConversationHandler(
    entry_points=[],  # Will be handled by callback query
    states={
        SETTING_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_budget_input)],
    },
    fallbacks=[],
)


async def handle_budget_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel budget setting."""
    context.user_data.clear()
    await update.message.reply_text("❌ Budget setting cancelled.")
    return ConversationHandler.END