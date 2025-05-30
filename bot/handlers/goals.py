from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.utils.auth import requires_registration
from core.services.financial_analysis import FinancialAnalysisService
from core.repository.BudgetRepository import GoalRepository
from core.database import Session


@requires_registration()
async def handle_goals_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show financial goals management menu."""
    keyboard = [
        [
            InlineKeyboardButton("🎯 View Goals", callback_data="goals_view"),
            InlineKeyboardButton("➕ Create Goal", callback_data="goals_create")
        ],
        [
            InlineKeyboardButton("📊 Goal Progress", callback_data="goals_progress"),
            InlineKeyboardButton("✏️ Edit Goals", callback_data="goals_edit")
        ],
        [
            InlineKeyboardButton("🏆 Achievements", callback_data="goals_achievements"),
            InlineKeyboardButton("💡 Goal Suggestions", callback_data="goals_suggestions")
        ],
        [InlineKeyboardButton("❌ Close", callback_data="goals_close")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "🎯 <b>Financial Goals Management</b>\n\n"
        "Set, track, and achieve your financial objectives:\n\n"
        "• 💰 Savings targets\n"
        "• 📉 Spending reduction goals\n"
        "• 📈 Income increase targets\n"
        "• 🎯 Custom financial milestones\n\n"
        "Choose an option below:",
        parse_mode="HTML",
        reply_markup=reply_markup
    )


async def handle_goals_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle goals menu selections."""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    data = query.data

    if data == "goals_close":
        await query.edit_message_text("Goals management closed. Use /goals to open again.")
        return

    try:
        if data == "goals_view":
            await _show_user_goals(query, user_id)
        elif data == "goals_create":
            await _show_goal_creation_guide(query, user_id)
        elif data == "goals_progress":
            await _show_goal_progress(query, user_id)
        elif data == "goals_edit":
            await _show_goal_editing(query, user_id)
        elif data == "goals_achievements":
            await _show_achievements(query, user_id)
        elif data == "goals_suggestions":
            await _show_goal_suggestions(query, user_id)

    except Exception as e:
        await query.edit_message_text(f"❌ Error: {str(e)}")


async def _show_user_goals(query, user_id):
    """Show user's current financial goals."""
    session = Session()
    goal_repo = GoalRepository(session)

    from core.repository.BankAccountRepository import BankAccountRepository
    account_repo = BankAccountRepository(session)
    account = account_repo.get_by_telegram_id(str(user_id))

    if not account:
        await query.edit_message_text("❌ No account found.")
        return

    goals = goal_repo.get_user_goals(account.id)

    if not goals:
        await query.edit_message_text(
            "🎯 <b>No Goals Set</b>\n\n"
            "You haven't set any financial goals yet. "
            "Use 'Create Goal' to get started!",
            parse_mode="HTML"
        )
        return

    message_parts = ["🎯 <b>Your Financial Goals</b>\n"]

    for goal in goals:
        progress_pct = (goal.current_amount / goal.target_amount * 100) if goal.target_amount > 0 else 0
        progress_bar = "🟩" * int(progress_pct // 10) + "⬜" * (10 - int(progress_pct // 10))

        status_emoji = "🟢" if goal.is_active else "⏸️"

        message_parts.append(f"\n{status_emoji} <b>{goal.title}</b>")
        message_parts.append(f"Target: {goal.target_amount:,.0f} IDR")
        message_parts.append(f"Current: {goal.current_amount:,.0f} IDR")
        message_parts.append(f"Progress: {progress_bar} {progress_pct:.1f}%")

        if goal.target_date:
            message_parts.append(f"Target Date: {goal.target_date.strftime('%Y-%m-%d')}")

    await query.edit_message_text("\n".join(message_parts), parse_mode="HTML")


async def _show_goal_creation_guide(query, user_id):
    """Show guide for creating new goals."""
    guide_text = (
        "➕ <b>Create Financial Goal</b>\n\n"
        "To create a new goal, use one of these commands:\n\n"
        "💰 <b>Savings Goal:</b>\n"
        "<code>/set_goal savings \"Emergency Fund\" 10000000 2025-12-31</code>\n\n"
        "📉 <b>Spending Limit:</b>\n"
        "<code>/set_goal spending \"Reduce Food Expenses\" 2000000 2025-06-30</code>\n\n"
        "📈 <b>Income Target:</b>\n"
        "<code>/set_goal income \"Freelance Income\" 5000000 2025-08-31</code>\n\n"
        "<b>Format:</b>\n"
        "<code>/set_goal [type] \"[title]\" [amount] [date]</code>\n\n"
        "💡 <b>Tips:</b>\n"
        "• Set realistic and achievable targets\n"
        "• Break large goals into smaller milestones\n"
        "• Review and adjust goals regularly"
    )

    await query.edit_message_text(guide_text, parse_mode="HTML")


async def _show_goal_progress(query, user_id):
    """Show detailed goal progress with charts."""
    # This would generate progress charts for each goal
    await query.edit_message_text(
        "📊 <b>Goal Progress Charts</b>\n\n"
        "Generating detailed progress visualization... ⏳\n\n"
        "This feature will show:\n"
        "• Progress over time\n"
        "• Trend analysis\n"
        "• Projected completion dates\n"
        "• Achievement probability",
        parse_mode="HTML"
    )


async def _show_goal_editing(query, user_id):
    """Show goal editing options."""
    edit_text = (
        "✏️ <b>Edit Goals</b>\n\n"
        "To modify existing goals, use:\n\n"
        "<b>Update Progress:</b>\n"
        "<code>/update_goal [goal_id] [new_amount]</code>\n\n"
        "<b>Change Target:</b>\n"
        "<code>/modify_goal [goal_id] target [new_target]</code>\n\n"
        "<b>Extend Deadline:</b>\n"
        "<code>/modify_goal [goal_id] date [new_date]</code>\n\n"
        "<b>Pause/Resume:</b>\n"
        "<code>/toggle_goal [goal_id]</code>\n\n"
        "Use /goals to see your goal IDs."
    )

    await query.edit_message_text(edit_text, parse_mode="HTML")


async def _show_achievements(query, user_id):
    """Show user's achievements and completed goals."""
    await query.edit_message_text(
        "🏆 <b>Achievements & Milestones</b>\n\n"
        "🎉 Completed Goals: 0\n"
        "⚡ Current Streak: 0 days\n"
        "📈 Best Month: -\n"
        "💰 Total Saved: 0 IDR\n\n"
        "Complete your first goal to unlock achievements!",
        parse_mode="HTML"
    )


async def _show_goal_suggestions(query, user_id):
    """Show personalized goal suggestions based on spending patterns."""
    analysis_service = FinancialAnalysisService()
    insights = analysis_service.get_category_insights(user_id)

    suggestions_text = (
        "💡 <b>Personalized Goal Suggestions</b>\n\n"
        "Based on your spending patterns:\n\n"
    )

    if insights:
        # Find categories with increasing spending
        increasing_categories = [
            cat for cat, data in insights.items()
            if data['trend'] == 'increasing' and data['change_percentage'] > 20
        ]

        if increasing_categories:
            suggestions_text += "📉 <b>Spending Reduction Goals:</b>\n"
            for category in increasing_categories[:3]:
                target_reduction = insights[category]['recent_spending'] * 0.8  # 20% reduction
                suggestions_text += f"• Reduce {category} spending to {target_reduction:,.0f} IDR/month\n"
            suggestions_text += "\n"

    suggestions_text += (
        "💰 <b>Recommended Savings Goals:</b>\n"
        "• Emergency Fund: 6 months of expenses\n"
        "• Vacation Fund: 5,000,000 IDR\n"
        "• Investment Fund: 10,000,000 IDR\n\n"
        "📈 <b>Income Goals:</b>\n"
        "• Increase monthly income by 20%\n"
        "• Develop side income stream\n"
        "• Skill development investment"
    )

    await query.edit_message_text(suggestions_text, parse_mode="HTML")