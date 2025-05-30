from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters
from datetime import datetime
from bot.utils.auth import requires_registration
from core.services.spending_pattern import FinancialAnalysisService
from core.repository.BudgetRepository import GoalRepository
from core.database import Session

# Conversation states for goal creation
GOAL_TYPE, GOAL_TITLE, GOAL_AMOUNT, GOAL_DATE = range(4)


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
        return ConversationHandler.END

    try:
        if data == "goals_view":
            await _show_user_goals(query, user_id)
            return ConversationHandler.END
        elif data == "goals_create":
            await _start_goal_creation(query, user_id, context)
            return ConversationHandler.END
        elif data == "goals_progress":
            await _show_goal_progress(query, user_id)
            return ConversationHandler.END
        elif data == "goals_edit":
            await _show_goal_editing(query, user_id)
            return ConversationHandler.END
        elif data == "goals_achievements":
            await _show_achievements(query, user_id)
            return ConversationHandler.END
        elif data == "goals_suggestions":
            await _show_goal_suggestions(query, user_id)
            return ConversationHandler.END
        elif data.startswith("create_goal_"):
            return await _handle_goal_type_selection(query, data, context)
        return None

    except Exception as e:
        await query.edit_message_text(f"❌ Error: {str(e)}")
        return ConversationHandler.END

async def _start_goal_creation(query, user_id, context):
    """Start the goal creation process."""
    keyboard = [
        [
            InlineKeyboardButton("💰 Savings Goal", callback_data="create_goal_savings"),
            InlineKeyboardButton("📉 Spending Limit", callback_data="create_goal_spending")
        ],
        [
            InlineKeyboardButton("📈 Income Target", callback_data="create_goal_income"),
            InlineKeyboardButton("🎯 Custom Goal", callback_data="create_goal_custom")
        ],
        [InlineKeyboardButton("❌ Cancel", callback_data="goals_close")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        "➕ <b>Create New Financial Goal</b>\n\n"
        "Choose the type of goal you want to create:\n\n"
        "💰 <b>Savings Goal:</b> Save a specific amount\n"
        "📉 <b>Spending Limit:</b> Reduce expenses in a category\n"
        "📈 <b>Income Target:</b> Increase your income\n"
        "🎯 <b>Custom Goal:</b> Any other financial objective\n\n"
        "Select a goal type:",
        parse_mode="HTML",
        reply_markup=reply_markup
    )


async def _handle_goal_type_selection(query, callback_data, context):
    """Handle goal type selection."""
    goal_type = callback_data.replace("create_goal_", "")
    context.user_data["goal_type"] = goal_type

    goal_type_names = {
        "savings": "Savings Goal",
        "spending": "Spending Limit",
        "income": "Income Target",
        "custom": "Custom Goal"
    }

    goal_name = goal_type_names.get(goal_type, "Goal")

    await query.edit_message_text(
        f"📝 <b>Create {goal_name}</b>\n\n"
        f"Please enter a title for your {goal_name.lower()}:\n\n"
        "Examples:\n"
        "• Emergency Fund\n"
        "• Vacation Savings\n"
        "• Reduce Food Expenses\n"
        "• Freelance Income\n\n"
        "💡 Type /cancel to cancel this operation.",
        parse_mode="HTML"
    )

    return GOAL_TITLE


async def handle_goal_title_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle goal title input."""
    title = update.message.text.strip()

    if len(title) < 3:
        await update.message.reply_text(
            "❌ Title must be at least 3 characters long. Please try again:"
        )
        return GOAL_TITLE

    context.user_data["goal_title"] = title
    goal_type = context.user_data.get("goal_type", "custom")

    amount_examples = {
        "savings": "• 10000000 (for 10 million IDR emergency fund)\n• 5000000 (for 5 million IDR vacation)",
        "spending": "• 2000000 (reduce monthly food expenses to 2 million)\n• 1500000 (limit shopping to 1.5 million)",
        "income": "• 15000000 (target monthly income of 15 million)\n• 3000000 (additional income from side hustle)",
        "custom": "• 50000000 (for house down payment)\n• 20000000 (for car purchase)"
    }

    await update.message.reply_text(
        f"💰 <b>Set Target Amount</b>\n\n"
        f"Goal: {title}\n\n"
        f"Please enter the target amount (in IDR):\n\n"
        f"Examples:\n{amount_examples.get(goal_type, amount_examples['custom'])}\n\n"
        "💡 Type /cancel to cancel this operation.",
        parse_mode="HTML"
    )

    return GOAL_AMOUNT


async def handle_goal_amount_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle goal amount input."""
    text = update.message.text.strip()

    try:
        # Remove common formatting characters
        cleaned_text = text.replace(",", "").replace(".", "").replace(" ", "")
        amount = float(cleaned_text)

        if amount <= 0:
            await update.message.reply_text(
                "❌ Please enter a positive amount.\n\n"
                "Example: 10000000 (for 10 million IDR)"
            )
            return GOAL_AMOUNT

        context.user_data["goal_amount"] = amount

        await update.message.reply_text(
            f"📅 <b>Set Target Date</b>\n\n"
            f"Goal: {context.user_data['goal_title']}\n"
            f"Amount: {amount:,.0f} IDR\n\n"
            f"Please enter the target date (YYYY-MM-DD):\n\n"
            "Examples:\n"
            "• 2024-12-31 (end of this year)\n"
            "• 2025-06-30 (mid next year)\n"
            "• 2025-12-31 (end of next year)\n\n"
            "💡 Type 'skip' to create goal without target date\n"
            "💡 Type /cancel to cancel this operation.",
            parse_mode="HTML"
        )

        return GOAL_DATE

    except ValueError:
        await update.message.reply_text(
            "❌ Please enter a valid number.\n\n"
            "Example: 10000000 (for 10 million IDR)\n\n"
            "💡 Type /cancel to cancel this operation."
        )
        return GOAL_AMOUNT


async def handle_goal_date_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle goal date input and save the goal."""
    text = update.message.text.strip().lower()
    user_id = update.effective_user.id

    target_date = None

    if text != "skip":
        try:
            target_date = datetime.strptime(text, "%Y-%m-%d")

            if target_date.date() <= datetime.now().date():
                await update.message.reply_text(
                    "❌ Target date must be in the future. Please enter a future date:"
                )
                return GOAL_DATE

        except ValueError:
            await update.message.reply_text(
                "❌ Invalid date format. Please use YYYY-MM-DD format:\n\n"
                "Example: 2024-12-31\n\n"
                "Or type 'skip' to create goal without target date."
            )
            return GOAL_DATE

    # Save the goal
    try:
        from core.repository.BankAccountRepository import BankAccountRepository

        session = Session()
        try:
            account_repo = BankAccountRepository(session)
            account = account_repo.get_by_telegram_id(str(user_id))

            if not account:
                await update.message.reply_text("❌ Account not found.")
                return ConversationHandler.END

            goal_repo = GoalRepository(session)
            goal = goal_repo.create({
                'user_id': account.id,
                'goal_type': context.user_data["goal_type"],
                'title': context.user_data["goal_title"],
                'target_amount': context.user_data["goal_amount"],
                'current_amount': 0.0,
                'target_date': target_date,
                'is_active': True
            })

            # Format success message
            date_text = target_date.strftime('%Y-%m-%d') if target_date else "No target date"

            await update.message.reply_text(
                f"✅ <b>Goal Created Successfully!</b>\n\n"
                f"🎯 <b>Title:</b> {goal.title}\n"
                f"💰 <b>Target Amount:</b> {goal.target_amount:,.0f} IDR\n"
                f"📅 <b>Target Date:</b> {date_text}\n"
                f"📊 <b>Progress:</b> 0% (0 / {goal.target_amount:,.0f} IDR)\n\n"
                "Use /goals to view and manage your goals.",
                parse_mode="HTML"
            )

        finally:
            session.close()

    except Exception as e:
        await update.message.reply_text(
            f"❌ Error saving goal: {str(e)}\n\n"
            "Please try again or contact support."
        )

    # Clear user data
    context.user_data.clear()
    return ConversationHandler.END


async def handle_goal_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel goal creation."""
    context.user_data.clear()
    await update.message.reply_text("❌ Goal creation cancelled.")
    return ConversationHandler.END


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

    goals = goal_repo.get_user_goals(account.id, active_only=False)

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

    session.close()
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


@requires_registration()
async def handle_set_goal_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /set_goal command with parameters."""
    if not context.args:
        await update.message.reply_text(
            "❌ <b>Missing parameters</b>\n\n"
            "<b>Usage:</b>\n"
            "<code>/set_goal [type] \"[title]\" [amount] [date]</code>\n\n"
            "<b>Examples:</b>\n"
            "• <code>/set_goal savings \"Emergency Fund\" 10000000 2025-12-31</code>\n"
            "• <code>/set_goal spending \"Reduce Food Costs\" 2000000 2025-06-30</code>\n"
            "• <code>/set_goal income \"Freelance Target\" 5000000 2025-08-31</code>\n\n"
            "<b>Goal Types:</b> savings, spending, income, custom\n"
            "<b>Date Format:</b> YYYY-MM-DD",
            parse_mode="HTML"
        )
        return

    try:
        # Parse the command arguments
        args_text = " ".join(context.args)

        # Extract quoted title using regex
        title_match = re.search(r'"([^"]*)"', args_text)
        if not title_match:
            await update.message.reply_text(
                "❌ <b>Invalid format</b>\n\n"
                "Title must be in quotes. Example:\n"
                "<code>/set_goal savings \"Emergency Fund\" 10000000 2025-12-31</code>",
                parse_mode="HTML"
            )
            return

        title = title_match.group(1)

        # Remove the quoted title and parse remaining args
        remaining_args = args_text.replace(f'"{title}"', '').split()

        if len(remaining_args) < 3:
            await update.message.reply_text(
                "❌ <b>Missing parameters</b>\n\n"
                "Required: goal_type, amount, and date\n\n"
                "Example:\n"
                "<code>/set_goal savings \"Emergency Fund\" 10000000 2025-12-31</code>",
                parse_mode="HTML"
            )
            return

        goal_type = remaining_args[0].lower()
        amount_str = remaining_args[1]
        date_str = remaining_args[2]

        # Validate goal type
        valid_types = ['savings', 'spending', 'income', 'custom']
        if goal_type not in valid_types:
            await update.message.reply_text(
                f"❌ <b>Invalid goal type</b>\n\n"
                f"Valid types: {', '.join(valid_types)}\n\n"
                "Example:\n"
                "<code>/set_goal savings \"Emergency Fund\" 10000000 2025-12-31</code>",
                parse_mode="HTML"
            )
            return

        # Validate and parse amount
        try:
            amount = float(amount_str.replace(",", "").replace(".", ""))
            if amount <= 0:
                raise ValueError("Amount must be positive")
        except ValueError:
            await update.message.reply_text(
                "❌ <b>Invalid amount</b>\n\n"
                "Amount must be a positive number\n\n"
                "Example: 10000000 (for 10 million IDR)",
                parse_mode="HTML"
            )
            return

        # Validate and parse date
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d")
            if target_date.date() <= datetime.now().date():
                await update.message.reply_text(
                    "❌ <b>Invalid date</b>\n\n"
                    "Target date must be in the future\n\n"
                    "Example: 2025-12-31",
                    parse_mode="HTML"
                )
                return
        except ValueError:
            await update.message.reply_text(
                "❌ <b>Invalid date format</b>\n\n"
                "Use YYYY-MM-DD format\n\n"
                "Example: 2025-12-31",
                parse_mode="HTML"
            )
            return

        # Save the goal
        user_id = update.effective_user.id

        from core.repository.BankAccountRepository import BankAccountRepository

        session = Session()
        try:
            account_repo = BankAccountRepository(session)
            account = account_repo.get_by_telegram_id(str(user_id))

            if not account:
                await update.message.reply_text("❌ Account not found. Please register first with /start.")
                return

            goal_repo = GoalRepository(session)
            goal = goal_repo.create({
                'user_id': account.id,
                'goal_type': goal_type,
                'title': title,
                'target_amount': amount,
                'current_amount': 0.0,
                'target_date': target_date,
                'is_active': True
            })

            # Format goal type display name
            goal_type_names = {
                "savings": "💰 Savings Goal",
                "spending": "📉 Spending Limit",
                "income": "📈 Income Target",
                "custom": "🎯 Custom Goal"
            }

            goal_display_name = goal_type_names.get(goal_type, "🎯 Goal")

            await update.message.reply_text(
                f"✅ <b>Goal Created Successfully!</b>\n\n"
                f"🏷️ <b>Type:</b> {goal_display_name}\n"
                f"🎯 <b>Title:</b> {goal.title}\n"
                f"💰 <b>Target Amount:</b> {goal.target_amount:,.0f} IDR\n"
                f"📅 <b>Target Date:</b> {goal.target_date.strftime('%Y-%m-%d')}\n"
                f"📊 <b>Progress:</b> 0% (0 / {goal.target_amount:,.0f} IDR)\n\n"
                "🎉 Your goal has been saved! Use /goals to view and manage all your goals.",
                parse_mode="HTML"
            )

        except Exception as e:
            await update.message.reply_text(
                f"❌ <b>Error saving goal:</b> {str(e)}\n\n"
                "Please try again or use the interactive menu with /goals",
                parse_mode="HTML"
            )
        finally:
            session.close()

    except Exception as e:
        await update.message.reply_text(
            f"❌ <b>Error processing command:</b> {str(e)}\n\n"
            "Please check your command format:\n"
            "<code>/set_goal savings \"Emergency Fund\" 10000000 2025-12-31</code>",
            parse_mode="HTML"
        )


# Add similar commands for updating and managing goals
@requires_registration()
async def handle_update_goal_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /update_goal command to update goal progress."""
    if len(context.args) < 2:
        await update.message.reply_text(
            "❌ <b>Missing parameters</b>\n\n"
            "<b>Usage:</b>\n"
            "<code>/update_goal [goal_id] [current_amount]</code>\n\n"
            "<b>Example:</b>\n"
            "<code>/update_goal 1 2500000</code>\n\n"
            "Use /goals to see your goal IDs.",
            parse_mode="HTML"
        )
        return

    try:
        goal_id = int(context.args[0])
        current_amount = float(context.args[1].replace(",", "").replace(".", ""))

        if current_amount < 0:
            await update.message.reply_text("❌ Amount cannot be negative.")
            return

        user_id = update.effective_user.id

        from core.repository.BankAccountRepository import BankAccountRepository

        session = Session()
        try:
            account_repo = BankAccountRepository(session)
            account = account_repo.get_by_telegram_id(str(user_id))

            if not account:
                await update.message.reply_text("❌ Account not found.")
                return

            goal_repo = GoalRepository(session)
            goal = goal_repo.get(goal_id)

            if not goal or goal.user_id != account.id:
                await update.message.reply_text("❌ Goal not found or you don't have permission to update it.")
                return

            # Update goal progress
            updated_goal = goal_repo.update_goal_progress(goal_id, current_amount)

            if updated_goal:
                progress_pct = (
                            current_amount / updated_goal.target_amount * 100) if updated_goal.target_amount > 0 else 0
                progress_bar = "🟩" * int(progress_pct // 10) + "⬜" * (10 - int(progress_pct // 10))

                status = "🎉 COMPLETED!" if progress_pct >= 100 else f"{progress_pct:.1f}%"

                await update.message.reply_text(
                    f"✅ <b>Goal Updated Successfully!</b>\n\n"
                    f"🎯 <b>Goal:</b> {updated_goal.title}\n"
                    f"💰 <b>Current Amount:</b> {current_amount:,.0f} IDR\n"
                    f"🎯 <b>Target Amount:</b> {updated_goal.target_amount:,.0f} IDR\n"
                    f"📊 <b>Progress:</b> {progress_bar} {status}\n\n"
                    f"💡 Use /goals to view all your goals.",
                    parse_mode="HTML"
                )
            else:
                await update.message.reply_text("❌ Failed to update goal.")

        finally:
            session.close()

    except ValueError:
        await update.message.reply_text(
            "❌ Invalid parameters. Goal ID must be a number and amount must be numeric.\n\n"
            "Example: <code>/update_goal 1 2500000</code>",
            parse_mode="HTML"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Error updating goal: {str(e)}")


async def _handle_goal_type_selection(query, callback_data, context):
    """Handle goal type selection."""
    goal_type = callback_data.replace("create_goal_", "")
    context.user_data["goal_type"] = goal_type

    goal_type_names = {
        "savings": "Savings Goal",
        "spending": "Spending Limit",
        "income": "Income Target",
        "custom": "Custom Goal"
    }

    goal_name = goal_type_names.get(goal_type, "Goal")

    await query.edit_message_text(
        f"📝 <b>Create {goal_name}</b>\n\n"
        f"Please enter a title for your {goal_name.lower()}:\n\n"
        "Examples:\n"
        "• Emergency Fund\n"
        "• Vacation Savings\n"
        "• Reduce Food Expenses\n"
        "• Freelance Income\n\n"
        "💡 Type /cancel to cancel this operation.",
        parse_mode="HTML"
    )

    # THIS IS THE KEY FIX - return the conversation state
    return GOAL_TITLE