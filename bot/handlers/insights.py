from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.utils.auth import requires_registration
from core.services.spending_pattern import FinancialAnalysisService


@requires_registration()
async def handle_insights_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show smart insights menu."""
    keyboard = [
        [
            InlineKeyboardButton("🏆 Financial Health Score", callback_data="insights_health"),
            InlineKeyboardButton("⚠️ Spending Anomalies", callback_data="insights_anomalies")
        ],
        [
            InlineKeyboardButton("💡 Smart Recommendations", callback_data="insights_recommendations"),
            InlineKeyboardButton("🔔 Recent Alerts", callback_data="insights_alerts")
        ],
        [
            InlineKeyboardButton("📊 Category Analysis", callback_data="insights_categories"),
            InlineKeyboardButton("🎯 Goal Insights", callback_data="insights_goals")
        ],
        [
            InlineKeyboardButton("📈 Predictive Analysis", callback_data="insights_predictions"),
            InlineKeyboardButton("💰 Savings Opportunities", callback_data="insights_savings")
        ],
        [InlineKeyboardButton("❌ Close", callback_data="insights_close")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "🔔 <b>Smart Financial Insights</b>\n\n"
        "Get AI-powered insights about your financial behavior:\n\n"
        "• 🏆 Overall financial health assessment\n"
        "• ⚠️ Unusual spending pattern detection\n"
        "• 💡 Personalized money-saving tips\n"
        "• 📊 Deep category analysis\n"
        "• 📈 Future spending predictions\n\n"
        "Choose an insight type:",
        parse_mode="HTML",
        reply_markup=reply_markup
    )


async def handle_insights_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle insights menu selections."""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    data = query.data

    if data == "insights_close":
        await query.edit_message_text("Insights closed. Use /insights to open again.")
        return

    # Show loading message
    await query.edit_message_text("🔔 Analyzing your financial data... ⏳")

    try:
        analysis_service = FinancialAnalysisService()

        if data == "insights_health":
            await _show_financial_health(query, user_id, analysis_service)
        elif data == "insights_anomalies":
            await _show_spending_anomalies(query, user_id, analysis_service)
        elif data == "insights_recommendations":
            await _show_smart_recommendations(query, user_id, analysis_service)
        elif data == "insights_alerts":
            await _show_recent_alerts(query, user_id)
        elif data == "insights_categories":
            await _show_category_insights(query, user_id, analysis_service)
        elif data == "insights_goals":
            await _show_goal_insights(query, user_id)
        elif data == "insights_predictions":
            await _show_predictive_analysis(query, user_id, analysis_service)
        elif data == "insights_savings":
            await _show_savings_opportunities(query, user_id, analysis_service)

    except Exception as e:
        await query.edit_message_text(f"❌ Error generating insights: {str(e)}")


async def _show_financial_health(query, user_id, analysis_service):
    """Show comprehensive financial health score."""
    health_data = analysis_service.calculate_financial_health_score(user_id)

    if not health_data:
        await query.edit_message_text("❌ Insufficient data for health analysis. Upload more transactions.")
        return

    score = health_data['total_score']
    grade = health_data['grade']
    components = health_data['components']

    # Create grade emoji
    grade_emoji = {"A": "🏆", "B": "🥈", "C": "🥉", "D": "⚠️", "F": "🚨"}.get(grade, "❓")

    # Create progress bars for components
    def create_progress_bar(value, max_value):
        filled = int((value / max_value) * 10)
        return "🟩" * filled + "⬜" * (10 - filled)

    health_text = (
        f"🏆 <b>Financial Health Report</b>\n\n"
        f"{grade_emoji} <b>Overall Grade: {grade}</b>\n"
        f"📊 <b>Score: {score:.0f}/100</b>\n\n"
        f"📋 <b>Component Breakdown:</b>\n\n"
        f"💰 <b>Budget Adherence:</b> {components['budget_adherence']:.0f}/30\n"
        f"{create_progress_bar(components['budget_adherence'], 30)}\n\n"
        f"📊 <b>Spending Consistency:</b> {components['spending_consistency']:.0f}/25\n"
        f"{create_progress_bar(components['spending_consistency'], 25)}\n\n"
        f"💎 <b>Savings Rate:</b> {components['savings_rate']:.0f}/25\n"
        f"{create_progress_bar(components['savings_rate'], 25)}\n\n"
        f"📈 <b>Transaction Regularity:</b> {components['transaction_regularity']:.0f}/20\n"
        f"{create_progress_bar(components['transaction_regularity'], 20)}\n"
    )

    if health_data['recommendations']:
        health_text += "\n💡 <b>Improvement Recommendations:</b>\n"
        for i, rec in enumerate(health_data['recommendations'], 1):
            health_text += f"{i}. {rec}\n"

    await query.edit_message_text(health_text, parse_mode="HTML")


async def _show_spending_anomalies(query, user_id, analysis_service):
    """Show detected spending anomalies."""
    anomalies = analysis_service.detect_spending_anomalies(user_id)

    if not anomalies:
        await query.edit_message_text(
            "✅ <b>No Spending Anomalies Detected</b>\n\n"
            "Your spending patterns look consistent and normal. "
            "Keep up the good financial habits!",
            parse_mode="HTML"
        )
        return

    anomaly_text = "⚠️ <b>Spending Anomalies Detected</b>\n\n"

    for i, anomaly in enumerate(anomalies[:5], 1):  # Show top 5
        severity_emoji = "🔴" if anomaly['severity'] == 'high' else "🟡"
        deviation = anomaly.get('deviation', 0)
        anomaly_text += (
            f"{severity_emoji} <b>Anomaly #{i}</b>\n"
            f"📅 Date: {anomaly['date']}\n"
            f"💰 Amount: {anomaly['amount']:,.0f} IDR\n"
            f"📊 Deviation: {deviation:+,.0f} IDR from average\n"
            f"⚠️ Severity: {anomaly['severity'].title()}\n\n"
        )

    anomaly_text += (
        "💡 <b>What this means:</b>\n"
        "These are days when your spending was significantly higher than usual. "
        "Review these transactions to identify patterns or one-time expenses."
    )

    await query.edit_message_text(anomaly_text, parse_mode="HTML")


async def _show_smart_recommendations(query, user_id, analysis_service):
    """Show personalized financial recommendations."""
    # Get various insights
    health_data = analysis_service.calculate_financial_health_score(user_id)
    category_insights = analysis_service.get_category_insights(user_id)
    budget_status = analysis_service.check_budget_status(user_id)

    recommendations = []

    # Health-based recommendations
    if health_data and health_data['recommendations']:
        recommendations.extend(health_data['recommendations'])

    # Category-based recommendations
    if category_insights:
        for category, data in category_insights.items():
            if data['trend'] == 'increasing' and data['change_percentage'] > 25:
                recommendations.append(
                    f"Consider reducing {category} spending - it increased by {data['change_percentage']:.1f}%")

    # Budget-based recommendations
    if budget_status:
        for category, status in budget_status.items():
            if status['status'] == 'exceeded':
                recommendations.append(
                    f"Review {category} budget - you've exceeded the limit by {status['usage_percentage'] - 100:.1f}%")

    # General recommendations
    general_tips = [
        "Track daily expenses to increase awareness",
        "Set up automatic savings transfers",
        "Review and cancel unused subscriptions",
        "Use the 50/30/20 budgeting rule",
        "Build an emergency fund covering 6 months of expenses",
        "Invest in financial education and skills"
    ]

    if len(recommendations) < 5:
        recommendations.extend(general_tips[:5 - len(recommendations)])

    rec_text = "💡 <b>Smart Financial Recommendations</b>\n\n"

    for i, rec in enumerate(recommendations[:8], 1):
        rec_text += f"{i}. {rec}\n\n"

    rec_text += (
        "🎯 <b>Pro Tip:</b>\n"
        "Implement one recommendation at a time for better success rates. "
        "Small, consistent changes lead to big financial improvements!"
    )

    await query.edit_message_text(rec_text, parse_mode="HTML")


async def _show_recent_alerts(query, user_id):
    """Show recent spending alerts."""
    from core.database import Session
    from core.repository.BudgetRepository import AlertRepository
    from core.repository.BankAccountRepository import BankAccountRepository

    session = Session()
    account_repo = BankAccountRepository(session)
    account = account_repo.get_by_telegram_id(str(user_id))

    if not account:
        await query.edit_message_text("❌ No account found.")
        return

    alert_repo = AlertRepository(session)
    alerts = alert_repo.get_user_alerts(account.id)

    if not alerts:
        await query.edit_message_text(
            "🔔 <b>No Recent Alerts</b>\n\n"
            "You have no spending alerts at the moment. "
            "This is a good sign - your spending is within normal patterns!",
            parse_mode="HTML"
        )
        return

    alert_text = "🔔 <b>Recent Spending Alerts</b>\n\n"

    for alert in alerts[:10]:  # Show last 10 alerts
        alert_emoji = {
            'budget_exceeded': '🔴',
            'budget_warning': '🟡',
            'unusual_spending': '⚠️',
            'goal_milestone': '🎯'
        }.get(alert.alert_type, '📢')

        read_status = "✅" if alert.is_read else "🔺"

        alert_text += (
            f"{alert_emoji} {read_status} <b>{alert.alert_type.replace('_', ' ').title()}</b>\n"
            f"📅 {alert.created_at.strftime('%Y-%m-%d %H:%M')}\n"
            f"💬 {alert.message}\n\n"
        )

    await query.edit_message_text(alert_text, parse_mode="HTML")


async def _show_category_insights(query, user_id, analysis_service):
    """Show detailed category spending insights."""
    insights = analysis_service.get_category_insights(user_id)

    if not insights:
        await query.edit_message_text("❌ Insufficient transaction data for category analysis.")
        return

    insight_text = "📊 <b>Category Spending Analysis</b>\n<i>Last 30 days vs Previous 30 days</i>\n\n"

    # Sort by spending amount
    sorted_categories = sorted(
        insights.items(),
        key=lambda x: x[1]['recent_spending'],
        reverse=True
    )

    for category, data in sorted_categories[:8]:  # Top 8 categories
        trend_emoji = "📈" if data['trend'] == 'increasing' else "📉" if data['trend'] == 'decreasing' else "➡️"

        insight_text += (
            f"{trend_emoji} <b>{category}</b>\n"
            f"💰 Current: {data['recent_spending']:,.0f} IDR\n"
            f"📊 Previous: {data['previous_spending']:,.0f} IDR\n"
            f"📈 Change: {data['change_percentage']:+.1f}%\n"
            f"🔄 Trend: {data['trend'].title()}\n\n"
        )

    await query.edit_message_text(insight_text, parse_mode="HTML")


async def _show_goal_insights(query, user_id):
    """Show goal-related insights and progress predictions."""
    await query.edit_message_text(
        "🎯 <b>Goal Insights & Predictions</b>\n\n"
        "📊 <b>Goal Performance Analysis:</b>\n"
        "• Average progress rate: Calculating...\n"
        "• Predicted completion dates: Analyzing...\n"
        "• Success probability: Computing...\n\n"
        "🎯 <b>Goal Recommendations:</b>\n"
        "• Break large goals into smaller milestones\n"
        "• Set monthly progress targets\n"
        "• Review and adjust goals quarterly\n\n"
        "💡 This feature will be enhanced with more data!",
        parse_mode="HTML"
    )


async def _show_predictive_analysis(query, user_id, analysis_service):
    """Show predictive financial analysis."""
    trends = analysis_service.get_spending_trends(user_id, 'daily')

    if not trends or len(trends) < 7:
        await query.edit_message_text("❌ Need at least 7 days of data for predictions.")
        return

    # Simple prediction based on recent trends
    recent_days = list(trends.values())[-7:]  # Last 7 days
    avg_daily_spending = sum(day['spending'] for day in recent_days) / len(recent_days)
    avg_daily_income = sum(day['income'] for day in recent_days) / len(recent_days)

    # Monthly projections
    monthly_spending_projection = avg_daily_spending * 30
    monthly_income_projection = avg_daily_income * 30
    monthly_savings_projection = monthly_income_projection - monthly_spending_projection

    prediction_text = (
        "📈 <b>Predictive Financial Analysis</b>\n"
        "<i>Based on last 7 days of activity</i>\n\n"
        "📊 <b>Monthly Projections:</b>\n"
        f"💸 Spending: {monthly_spending_projection:,.0f} IDR\n"
        f"💰 Income: {monthly_income_projection:,.0f} IDR\n"
        f"💎 Net Savings: {monthly_savings_projection:,.0f} IDR\n\n"
        "📈 <b>Trends:</b>\n"
        f"📅 Daily avg spending: {avg_daily_spending:,.0f} IDR\n"
        f"💰 Daily avg income: {avg_daily_income:,.0f} IDR\n\n"
        "⚠️ <b>Accuracy Note:</b>\n"
        "Predictions improve with more data. Upload statements regularly for better forecasts."
    )

    await query.edit_message_text(prediction_text, parse_mode="HTML")


async def _show_savings_opportunities(query, user_id, analysis_service):
    """Show personalized savings opportunities."""
    category_insights = analysis_service.get_category_insights(user_id)

    savings_text = "💰 <b>Savings Opportunities</b>\n\n"

    if category_insights:
        # Find categories with high spending or increasing trends
        opportunities = []

        for category, data in category_insights.items():
            if data['recent_spending'] > 1000000:  # High spending categories (>1M IDR)
                potential_savings = data['recent_spending'] * 0.1  # 10% reduction potential
                opportunities.append((category, potential_savings, "High spending category"))

            elif data['trend'] == 'increasing' and data['change_percentage'] > 20:
                potential_savings = data['recent_spending'] * 0.15  # 15% reduction potential
                opportunities.append((category, potential_savings, "Rapidly increasing"))

        if opportunities:
            opportunities.sort(key=lambda x: x[1], reverse=True)  # Sort by savings potential

            savings_text += "🎯 <b>Top Savings Opportunities:</b>\n\n"

            total_potential = 0
            for i, (category, savings, reason) in enumerate(opportunities[:5], 1):
                savings_text += (
                    f"{i}. <b>{category}</b>\n"
                    f"💰 Potential monthly savings: {savings:,.0f} IDR\n"
                    f"📊 Reason: {reason}\n"
                    f"💡 Target: Reduce by 10-15%\n\n"
                )
                total_potential += savings

            savings_text += f"🏆 <b>Total Monthly Potential: {total_potential:,.0f} IDR</b>\n"
            savings_text += f"📅 <b>Annual Potential: {total_potential * 12:,.0f} IDR</b>\n\n"

    savings_text += (
        "💡 <b>General Savings Tips:</b>\n"
        "• Review subscriptions monthly\n"
        "• Use price comparison apps\n"
        "• Cook more meals at home\n"
        "• Set spending limits per category\n"
        "• Use cash for discretionary expenses\n"
        "• Automate savings transfers"
    )

    await query.edit_message_text(savings_text, parse_mode="HTML")