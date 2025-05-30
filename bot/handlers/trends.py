from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from bot.utils.auth import requires_registration
from core.services.spending_pattern import FinancialAnalysisService
from core.chart.advanced_visuals import (
    plot_spending_trends,
    plot_category_trends,
    plot_spending_heatmap,
    plot_day_of_week_analysis,
    plot_spending_velocity
)
import os


@requires_registration()
async def handle_trends_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show trends analysis menu."""
    keyboard = [
        [
            InlineKeyboardButton("📈 Spending Trends", callback_data="trends_spending"),
            InlineKeyboardButton("📊 Category Analysis", callback_data="trends_category")
        ],
        [
            InlineKeyboardButton("🗓️ Day of Week Analysis", callback_data="trends_weekday"),
            InlineKeyboardButton("🔥 Spending Heatmap", callback_data="trends_heatmap")
        ],
        [
            InlineKeyboardButton("⚡ Spending Velocity", callback_data="trends_velocity"),
            InlineKeyboardButton("💡 Smart Insights", callback_data="trends_insights")
        ],
        [InlineKeyboardButton("❌ Close", callback_data="trends_close")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "📊 <b>Financial Trends & Analysis</b>\n\n"
        "Choose an analysis type to explore your spending patterns:",
        parse_mode="HTML",
        reply_markup=reply_markup
    )


async def handle_trends_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle trends menu selections."""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    data = query.data

    if data == "trends_close":
        await query.edit_message_text("Analysis closed. Use /trends to open again.")
        return

    # Show loading message
    await query.edit_message_text("📊 Generating analysis... ⏳")

    try:
        if data == "trends_spending":
            await _generate_spending_trends(query, user_id)
        elif data == "trends_category":
            await _generate_category_trends(query, user_id)
        elif data == "trends_weekday":
            await _generate_weekday_analysis(query, user_id)
        elif data == "trends_heatmap":
            await _generate_spending_heatmap(query, user_id)
        elif data == "trends_velocity":
            await _generate_spending_velocity(query, user_id)
        elif data == "trends_insights":
            await _generate_smart_insights(query, user_id)

    except Exception as e:
        await query.edit_message_text(f"❌ Error generating analysis: {str(e)}")


async def _generate_spending_trends(query, user_id):
    """Generate spending trends analysis."""
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

    if not transactions:
        await query.edit_message_text("❌ No transactions found for analysis.")
        return

    # Generate charts
    os.makedirs("cache/chart_cache", exist_ok=True)

    # Monthly trends
    monthly_path = f"cache/chart_cache/{user_id}_monthly_trends.png"
    plot_spending_trends(transactions, monthly_path, 'monthly')

    # Daily trends
    daily_path = f"cache/chart_cache/{user_id}_daily_trends.png"
    plot_spending_trends(transactions, daily_path, 'daily')

    # Send charts
    with open(monthly_path, 'rb') as chart:
        await query.message.reply_photo(
            photo=chart,
            caption="📈 <b>Monthly Spending Trends</b>\n\nShows your spending patterns over months with income comparison.",
            parse_mode="HTML"
        )

    with open(daily_path, 'rb') as chart:
        await query.message.reply_photo(
            photo=chart,
            caption="📊 <b>Daily Spending Trends</b>\n\nDaily spending with 7-day moving average and cumulative spending.",
            parse_mode="HTML"
        )

    await query.edit_message_text("✅ Spending trends analysis completed!")


async def _generate_category_trends(query, user_id):
    """Generate category trends analysis."""
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

    if not transactions:
        await query.edit_message_text("❌ No transactions found for analysis.")
        return

    # Generate category trends chart
    os.makedirs("cache/chart_cache", exist_ok=True)
    chart_path = f"cache/chart_cache/{user_id}_category_trends.png"
    plot_category_trends(transactions, chart_path)

    # Get text insights
    analysis_service = FinancialAnalysisService()
    insights = analysis_service.get_category_insights(user_id)

    insight_text = "📊 <b>Category Insights (Last 30 days vs Previous 30 days)</b>\n\n"

    for category, data in insights.items():
        trend_emoji = "📈" if data['trend'] == 'increasing' else "📉" if data['trend'] == 'decreasing' else "➡️"
        insight_text += f"{trend_emoji} <b>{category}</b>: {data['change_percentage']:+.1f}% change\n"
        insight_text += f"   Current: {data['recent_spending']:,.0f} IDR\n\n"

    # Send chart
    with open(chart_path, 'rb') as chart:
        await query.message.reply_photo(
            photo=chart,
            caption="📊 <b>Category Spending Trends</b>\n\nTop 5 categories spending over time.",
            parse_mode="HTML"
        )

    await query.message.reply_text(insight_text, parse_mode="HTML")
    await query.edit_message_text("✅ Category trends analysis completed!")


async def _generate_weekday_analysis(query, user_id):
    """Generate day-of-week spending analysis."""
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

    if not transactions:
        await query.edit_message_text("❌ No transactions found for analysis.")
        return

    # Generate weekday analysis chart
    os.makedirs("cache/chart_cache", exist_ok=True)
    chart_path = f"cache/chart_cache/{user_id}_weekday_analysis.png"
    plot_day_of_week_analysis(transactions, chart_path)

    # Send chart
    with open(chart_path, 'rb') as chart:
        await query.message.reply_photo(
            photo=chart,
            caption="📅 <b>Day of Week Spending Analysis</b>\n\nDiscover your spending patterns by day of the week.",
            parse_mode="HTML"
        )

    await query.edit_message_text("✅ Day of week analysis completed!")


async def _generate_spending_heatmap(query, user_id):
    """Generate spending heatmap."""
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

    if not transactions:
        await query.edit_message_text("❌ No transactions found for analysis.")
        return

    # Generate heatmap
    os.makedirs("cache/chart_cache", exist_ok=True)
    chart_path = f"cache/chart_cache/{user_id}_spending_heatmap.png"
    plot_spending_heatmap(transactions, chart_path)

    # Send chart
    with open(chart_path, 'rb') as chart:
        await query.message.reply_photo(
            photo=chart,
            caption="🔥 <b>Spending Heatmap</b>\n\nVisual calendar showing spending intensity by day.",
            parse_mode="HTML"
        )

    await query.edit_message_text("✅ Spending heatmap generated!")


async def _generate_spending_velocity(query, user_id):
    """Generate spending velocity analysis."""
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

    if not transactions:
        await query.edit_message_text("❌ No transactions found for analysis.")
        return

    # Generate velocity chart
    os.makedirs("cache/chart_cache", exist_ok=True)
    chart_path = f"cache/chart_cache/{user_id}_spending_velocity.png"
    plot_spending_velocity(transactions, chart_path)

    # Send chart
    with open(chart_path, 'rb') as chart:
        await query.message.reply_photo(
            photo=chart,
            caption="⚡ <b>Spending Velocity Analysis</b>\n\nTrack how fast you're spending and balance changes over time.",
            parse_mode="HTML"
        )

    await query.edit_message_text("✅ Spending velocity analysis completed!")


async def _generate_smart_insights(query, user_id):
    """Generate smart financial insights."""
    analysis_service = FinancialAnalysisService()

    # Get financial health score
    health_score = analysis_service.calculate_financial_health_score(user_id)

    # Get spending anomalies
    anomalies = analysis_service.detect_spending_anomalies(user_id)

    # Get budget status
    budget_status = analysis_service.check_budget_status(user_id)

    # Build insights message
    message_parts = ["💡 <b>Smart Financial Insights</b>\n"]

    if health_score:
        message_parts.append(
            f"🏆 <b>Financial Health Score: {health_score['total_score']:.0f}/100 (Grade {health_score['grade']})</b>\n")

        if health_score['recommendations']:
            message_parts.append("📋 <b>Recommendations:</b>")
            for rec in health_score['recommendations']:
                message_parts.append(f"• {rec}")
            message_parts.append("")

    if anomalies:
        message_parts.append("⚠️ <b>Recent Spending Anomalies:</b>")
        for anomaly in anomalies[:3]:  # Show top 3
            message_parts.append(f"• {anomaly['date']}: {anomaly['amount']:,.0f} IDR ({anomaly['severity']} deviation)")
        message_parts.append("")

    if budget_status:
        message_parts.append("💰 <b>Budget Status:</b>")
        for category, status in budget_status.items():
            status_emoji = "🔴" if status['status'] == 'exceeded' else "🟡" if status['status'] == 'warning' else "🟢"
            message_parts.append(f"{status_emoji} {category}: {status['usage_percentage']:.1f}% used")
        message_parts.append("")

    if len(message_parts) == 1:
        message_parts.append("No specific insights available. Upload more transaction data for better analysis.")

    insights_text = "\n".join(message_parts)

    await query.edit_message_text(insights_text, parse_mode="HTML")