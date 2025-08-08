from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.utils.auth import requires_registration
from core.services.spending_pattern_service import SpendingPatternService


@requires_registration()
async def handle_patterns_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show spending patterns analysis menu."""
    keyboard = [
        [
            InlineKeyboardButton("📅 Daily Patterns", callback_data="patterns_daily"),
            InlineKeyboardButton("📆 Weekly Patterns", callback_data="patterns_weekly")
        ],
        [
            InlineKeyboardButton("📊 Monthly Patterns", callback_data="patterns_monthly"),
            InlineKeyboardButton("🔄 Recurring Transactions", callback_data="patterns_recurring")
        ],
        [
            InlineKeyboardButton("📈 Pattern Insights", callback_data="patterns_insights"),
            InlineKeyboardButton("⚠️ Anomaly Detection", callback_data="patterns_anomalies")
        ],
        [InlineKeyboardButton("❌ Close", callback_data="patterns_close")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "📊 <b>Spending Pattern Analysis</b>\n\n"
        "Discover your spending habits and patterns:\n\n"
        "• 📅 Analyze daily spending behaviors\n"
        "• 📆 Track weekly spending trends\n"
        "• 📊 Monitor monthly patterns\n"
        "• 🔄 Detect recurring subscriptions\n"
        "• 📈 Get personalized insights\n"
        "• ⚠️ Identify unusual spending\n\n"
        "Choose an analysis type:",
        parse_mode="HTML",
        reply_markup=reply_markup
    )


async def handle_patterns_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle pattern analysis menu selections."""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    data = query.data

    if data == "patterns_close":
        await query.edit_message_text("Pattern analysis closed. Use /patterns to open again.")
        return

    try:
        if data == "patterns_daily":
            await _show_daily_patterns(query, user_id)
        elif data == "patterns_weekly":
            await _show_weekly_patterns(query, user_id)
        elif data == "patterns_monthly":
            await _show_monthly_patterns(query, user_id)
        elif data == "patterns_recurring":
            await _show_recurring_transactions(query, user_id)
        elif data == "patterns_insights":
            await _show_pattern_insights(query, user_id)
        elif data == "patterns_anomalies":
            await _show_anomaly_detection(query, user_id)

    except Exception as e:
        await query.edit_message_text(f"❌ Error: {str(e)}")


@requires_registration()
async def handle_daily_patterns(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Direct command for daily pattern analysis."""
    user_id = update.effective_user.id

    await update.message.reply_text("📅 Analyzing your daily spending patterns... ⏳")

    try:
        pattern_service = SpendingPatternService()
        daily_analysis = pattern_service.analyze_daily_patterns(user_id)

        if 'error' in daily_analysis:
            await update.message.reply_text(f"❌ {daily_analysis['error']}")
            return

        # Format and send daily patterns
        await _format_daily_patterns_response(update, daily_analysis)

    except Exception as e:
        await update.message.reply_text(f"❌ Error analyzing daily patterns: {str(e)}")


@requires_registration()
async def handle_recurring_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Direct command for recurring transaction detection."""
    user_id = update.effective_user.id

    await update.message.reply_text("🔄 Detecting recurring transactions... ⏳")

    try:
        pattern_service = SpendingPatternService()
        recurring_transactions = pattern_service.detect_recurring_transactions(user_id)

        if not recurring_transactions:
            await update.message.reply_text(
                "🔄 <b>No Recurring Transactions Detected</b>\n\n"
                "We couldn't find any recurring payment patterns in your transactions.\n\n"
                "💡 <b>Tips:</b>\n"
                "• Upload more transaction history for better detection\n"
                "• Check back after a few months of data\n"
                "• Recurring patterns need at least 3 similar transactions",
                parse_mode="HTML"
            )
            return

        # Format and send recurring transactions
        await _format_recurring_transactions_response(update, recurring_transactions)

    except Exception as e:
        await update.message.reply_text(f"❌ Error detecting recurring transactions: {str(e)}")


# Helper functions for formatting responses
async def _show_daily_patterns(query, user_id):
    """Show daily spending patterns analysis."""
    await query.edit_message_text("📅 Analyzing daily patterns... ⏳")

    pattern_service = SpendingPatternService()
    daily_analysis = pattern_service.analyze_daily_patterns(user_id)

    if 'error' in daily_analysis:
        await query.edit_message_text(f"❌ {daily_analysis['error']}")
        return

    # Format daily patterns
    message_parts = ["📅 <b>Daily Spending Patterns</b>\n"]

    daily_patterns = daily_analysis.get('daily_patterns', {})
    if daily_patterns:
        message_parts.append("📊 <b>Average Spending by Day:</b>")

        # Sort days by weekday order
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        for day in day_order:
            if day in daily_patterns:
                stats = daily_patterns[day]
                message_parts.append(
                    f"• <b>{day}:</b> {stats['average_amount']:,.0f} IDR "
                    f"({stats['transaction_count']} txns)"
                )

    # Show top spending hours
    hourly_patterns = daily_analysis.get('hourly_patterns', {})
    if hourly_patterns:
        # Get top 3 spending hours
        top_hours = sorted(
            hourly_patterns.items(),
            key=lambda x: x[1]['total_amount'],
            reverse=True
        )[:3]

        message_parts.append("\n⏰ <b>Peak Spending Hours:</b>")
        for hour, stats in top_hours:
            message_parts.append(
                f"• <b>{hour:02d}:00:</b> {stats['total_amount']:,.0f} IDR "
                f"({stats['transaction_count']} txns)"
            )

    # Show top individual transactions
    top_transactions = daily_analysis.get('top_transactions', [])
    if top_transactions:
        message_parts.append("\n🧾 <b>Top Transactions:</b>")
        for txn in top_transactions:
            message_parts.append(
                f"• {txn['amount']:,.0f} IDR - {txn['merchant']} "
                f"({txn['category']}) at {txn['time']}"
            )

    message_parts.append(f"\n📊 Analysis period: {daily_analysis.get('analysis_period', 'Last 90 days')}")

    await query.edit_message_text("\n".join(message_parts), parse_mode="HTML")


async def _format_daily_patterns_response(update, daily_analysis):
    """Format daily patterns response for direct command."""
    message_parts = ["📅 <b>Daily Spending Patterns Analysis</b>\n"]

    daily_patterns = daily_analysis.get('daily_patterns', {})
    if daily_patterns:
        # Find highest and lowest spending days
        highest_day = max(daily_patterns.items(), key=lambda x: x[1]['average_amount'])
        lowest_day = min(daily_patterns.items(), key=lambda x: x[1]['average_amount'])

        message_parts.extend([
            f"📈 <b>Highest Spending:</b> {highest_day[0]} ({highest_day[1]['average_amount']:,.0f} IDR avg)",
            f"📉 <b>Lowest Spending:</b> {lowest_day[0]} ({lowest_day[1]['average_amount']:,.0f} IDR avg)\n",
            "📊 <b>Daily Breakdown:</b>"
        ])

        # Sort and display all days
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        for day in day_order:
            if day in daily_patterns:
                stats = daily_patterns[day]
                emoji = "💸" if day == highest_day[0] else "💰" if day == lowest_day[0] else "💳"
                message_parts.append(
                    f"{emoji} <b>{day}:</b> {stats['average_amount']:,.0f} IDR "
                    f"({stats['transaction_count']} transactions)"
                )

    # Add top transactions detail
    top_transactions = daily_analysis.get('top_transactions', [])
    if top_transactions:
        message_parts.append("\n🧾 <b>Top Transactions:</b>")
        for txn in top_transactions:
            message_parts.append(
                f"• {txn['amount']:,.0f} IDR - {txn['merchant']} "
                f"({txn['category']}) at {txn['time']}"
            )

    message_parts.append(
        f"\n📊 Based on {daily_analysis.get('total_transactions', 0)} transactions")
    message_parts.append("💡 Use /patterns for more detailed analysis options")

    await update.message.reply_text("\n".join(message_parts), parse_mode="HTML")


async def _format_recurring_transactions_response(update, recurring_transactions):
    """Format recurring transactions response."""
    message_parts = ["🔄 <b>Recurring Transactions Detected</b>\n"]

    # Group by frequency
    frequency_groups = {}
    for transaction in recurring_transactions:
        freq = transaction['frequency']
        if freq not in frequency_groups:
            frequency_groups[freq] = []
        frequency_groups[freq].append(transaction)

    for frequency, transactions in frequency_groups.items():
        frequency_emoji = {
            'weekly': '📅',
            'monthly': '📆',
            'quarterly': '📊',
            'irregular': '❓'
        }.get(frequency, '🔄')

        message_parts.append(f"\n{frequency_emoji} <b>{frequency.title()} Payments:</b>")

        for transaction in transactions[:5]:  # Limit to 5 per frequency
            confidence_indicator = "🟢" if transaction['confidence'] > 0.8 else "🟡" if transaction[
                                                                                          'confidence'] > 0.6 else "🔴"

            message_parts.append(
                f"{confidence_indicator} <b>{transaction['merchant'][:30]}...</b>\n"
                f"   Amount: {transaction['average_amount']:,.0f} IDR\n"
                f"   Confidence: {transaction['confidence'] * 100:.0f}%\n"
                f"   Last seen: {transaction['last_transaction']}"
            )

            if transaction['next_expected']:
                message_parts.append(f"   Next expected: {transaction['next_expected']}")

    message_parts.extend([
        "\n💡 <b>Tips:</b>",
        "• Review these for subscription optimization",
        "• Cancel unused recurring services",
        "• Set budget alerts for recurring expenses",
        "• Use /budget to set limits for these categories"
    ])

    await update.message.reply_text("\n".join(message_parts), parse_mode="HTML")


async def _show_weekly_patterns(query, user_id):
    """Show weekly spending patterns analysis."""
    await query.edit_message_text("📆 Analyzing weekly patterns... ⏳")

    try:
        pattern_service = SpendingPatternService()
        weekly_analysis = pattern_service.analyze_weekly_patterns(user_id)

        if 'error' in weekly_analysis:
            await query.edit_message_text(f"❌ {weekly_analysis['error']}")
            return

        # Format weekly patterns
        message_parts = ["📆 <b>Weekly Spending Patterns</b>\n"]

        weekly_patterns = weekly_analysis.get('weekly_patterns', {})
        if weekly_patterns:
            # Get recent weeks data
            recent_weeks = sorted(weekly_patterns.items())[-8:]  # Last 8 weeks

            message_parts.append("📊 <b>Recent Weekly Spending:</b>")
            for week, stats in recent_weeks:
                week_display = week.replace('W', ' Week ')
                message_parts.append(
                    f"• <b>{week_display}:</b> {stats['total_spending']:,.0f} IDR "
                    f"({stats['transaction_count']} txns)"
                )

            # Show trend
            trend = weekly_analysis.get('trend', 'stable')
            trend_emoji = {
                'increasing': '📈',
                'decreasing': '📉',
                'stable': '➡️',
                'insufficient_data': '❓'
            }.get(trend, '❓')

            message_parts.append(f"\n{trend_emoji} <b>Trend:</b> {trend.replace('_', ' ').title()}")

            avg_weekly = weekly_analysis.get('average_weekly_spending', 0)
            message_parts.append(f"📊 <b>Average Weekly:</b> {avg_weekly:,.0f} IDR")

        message_parts.append(f"\n📊 Analysis period: {weekly_analysis.get('analysis_period', 'Last 12 weeks')}")

        await query.edit_message_text("\n".join(message_parts), parse_mode="HTML")

    except Exception as e:
        await query.edit_message_text(f"❌ Error analyzing weekly patterns: {str(e)}")


async def _show_monthly_patterns(query, user_id):
    """Show monthly spending patterns analysis."""
    await query.edit_message_text("📊 Analyzing monthly patterns... ⏳")

    try:
        pattern_service = SpendingPatternService()
        monthly_analysis = pattern_service.analyze_monthly_patterns(user_id)

        if 'error' in monthly_analysis:
            await query.edit_message_text(f"❌ {monthly_analysis['error']}")
            return

        # Format monthly patterns
        message_parts = ["📊 <b>Monthly Spending Patterns</b>\n"]

        monthly_patterns = monthly_analysis.get('monthly_patterns', {})
        if monthly_patterns:
            # Get recent months
            recent_months = sorted(monthly_patterns.items())[-6:]  # Last 6 months

            message_parts.append("📊 <b>Recent Monthly Spending:</b>")
            for month, stats in recent_months:
                month_display = month.replace('-', '/')
                message_parts.append(
                    f"• <b>{month_display}:</b> {stats['total_spending']:,.0f} IDR "
                    f"({stats['transaction_count']} txns)"
                )

                # Show top category for this month
                top_categories = stats.get('top_categories', {})
                if top_categories:
                    top_category = list(top_categories.items())[0]
                    message_parts.append(
                        f"   Top: {top_category[0]} ({top_category[1]:,.0f} IDR)"
                    )

            # Show seasonal analysis
            seasonal_analysis = monthly_analysis.get('seasonal_analysis', {})
            if seasonal_analysis:
                message_parts.append("\n🌟 <b>Seasonal Insights:</b>")

                # Find highest and lowest spending months
                seasonal_spending = [(month, data['average_spending'])
                                     for month, data in seasonal_analysis.items()
                                     if data['data_points'] >= 1]

                if seasonal_spending:
                    highest_month = max(seasonal_spending, key=lambda x: x[1])
                    lowest_month = min(seasonal_spending, key=lambda x: x[1])

                    month_names = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

                    message_parts.append(
                        f"📈 Highest: {month_names[highest_month[0]]} ({highest_month[1]:,.0f} IDR avg)"
                    )
                    message_parts.append(
                        f"📉 Lowest: {month_names[lowest_month[0]]} ({lowest_month[1]:,.0f} IDR avg)"
                    )

        message_parts.append(f"\n📊 Analysis period: {monthly_analysis.get('analysis_period', 'Last 12 months')}")

        await query.edit_message_text("\n".join(message_parts), parse_mode="HTML")

    except Exception as e:
        await query.edit_message_text(f"❌ Error analyzing monthly patterns: {str(e)}")


async def _show_recurring_transactions(query, user_id):
    """Show recurring transactions analysis."""
    await query.edit_message_text("🔄 Detecting recurring transactions... ⏳")

    try:
        pattern_service = SpendingPatternService()
        recurring_transactions = pattern_service.detect_recurring_transactions(user_id)

        if not recurring_transactions:
            await query.edit_message_text(
                "🔄 <b>No Recurring Transactions Detected</b>\n\n"
                "We couldn't find any recurring payment patterns in your transactions.\n\n"
                "💡 <b>Tips:</b>\n"
                "• Upload more transaction history for better detection\n"
                "• Check back after a few months of data\n"
                "• Recurring patterns need at least 3 similar transactions",
                parse_mode="HTML"
            )
            return

        # Format recurring transactions (reuse existing function)
        message_parts = ["🔄 <b>Recurring Transactions Detected</b>\n"]

        # Group by frequency
        frequency_groups = {}
        for transaction in recurring_transactions:
            freq = transaction['frequency']
            if freq not in frequency_groups:
                frequency_groups[freq] = []
            frequency_groups[freq].append(transaction)

        for frequency, transactions in frequency_groups.items():
            frequency_emoji = {
                'weekly': '📅',
                'monthly': '📆',
                'quarterly': '📊',
                'irregular': '❓'
            }.get(frequency, '🔄')

            message_parts.append(f"\n{frequency_emoji} <b>{frequency.title()} Payments:</b>")

            for transaction in transactions[:3]:  # Limit to 3 per frequency in callback
                confidence_indicator = "🟢" if transaction['confidence'] > 0.8 else "🟡" if transaction[
                                                                                              'confidence'] > 0.6 else "🔴"

                message_parts.append(
                    f"{confidence_indicator} <b>{transaction['merchant'][:25]}...</b>\n"
                    f"   {transaction['average_amount']:,.0f} IDR ({transaction['confidence'] * 100:.0f}%)"
                )

                if transaction['next_expected']:
                    message_parts.append(f"   Next: {transaction['next_expected']}")

        message_parts.extend([
            f"\n📊 <b>Total Found:</b> {len(recurring_transactions)} recurring patterns",
            "\n💡 Use /recurring for detailed analysis"
        ])

        await query.edit_message_text("\n".join(message_parts), parse_mode="HTML")

    except Exception as e:
        await query.edit_message_text(f"❌ Error detecting recurring transactions: {str(e)}")


async def _show_pattern_insights(query, user_id):
    """Show comprehensive pattern insights."""
    await query.edit_message_text("📈 Generating pattern insights... ⏳")

    try:
        pattern_service = SpendingPatternService()

        # Get all pattern analyses
        daily_analysis = pattern_service.analyze_daily_patterns(user_id)
        weekly_analysis = pattern_service.analyze_weekly_patterns(user_id)
        recurring_transactions = pattern_service.detect_recurring_transactions(user_id)

        message_parts = ["📈 <b>Pattern Insights & Recommendations</b>\n"]

        # Daily insights
        if 'daily_patterns' in daily_analysis:
            daily_patterns = daily_analysis['daily_patterns']
            if daily_patterns:
                # Find spending habits
                highest_day = max(daily_patterns.items(), key=lambda x: x[1]['average_amount'])
                lowest_day = min(daily_patterns.items(), key=lambda x: x[1]['average_amount'])

                message_parts.extend([
                    "🗓️ <b>Daily Habits:</b>",
                    f"• You spend most on {highest_day[0]}s ({highest_day[1]['average_amount']:,.0f} IDR avg)",
                    f"• You spend least on {lowest_day[0]}s ({lowest_day[1]['average_amount']:,.0f} IDR avg)"
                ])

                # Weekend vs weekday analysis
                weekend_days = ['Saturday', 'Sunday']
                weekday_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']

                weekend_avg = sum(daily_patterns[day]['average_amount']
                                  for day in weekend_days if day in daily_patterns) / 2
                weekday_avg = sum(daily_patterns[day]['average_amount']
                                  for day in weekday_days if day in daily_patterns) / 5

                if weekend_avg > weekday_avg * 1.2:
                    message_parts.append("• 🎉 Weekend spender - you spend 20%+ more on weekends")
                elif weekday_avg > weekend_avg * 1.2:
                    message_parts.append("• 💼 Weekday spender - you spend more during work days")

        # Weekly trends
        if 'trend' in weekly_analysis:
            trend = weekly_analysis['trend']
            trend_insights = {
                'increasing': "📈 Your weekly spending is trending upward",
                'decreasing': "📉 Your weekly spending is trending downward - great job!",
                'stable': "➡️ Your weekly spending is consistent"
            }
            if trend in trend_insights:
                message_parts.append(f"\n🔄 <b>Weekly Trend:</b>\n• {trend_insights[trend]}")

        # Recurring transaction insights
        if recurring_transactions:
            total_recurring = sum(t['average_amount'] for t in recurring_transactions)
            message_parts.extend([
                f"\n💳 <b>Recurring Payments:</b>",
                f"• {len(recurring_transactions)} recurring transactions detected",
                f"• Estimated monthly recurring: {total_recurring:,.0f} IDR"
            ])

            # High confidence recurring transactions
            high_confidence = [t for t in recurring_transactions if t['confidence'] > 0.8]
            if high_confidence:
                message_parts.append(f"• {len(high_confidence)} with high confidence (80%+)")

        # Recommendations
        message_parts.extend([
            "\n💡 <b>Recommendations:</b>",
            "• Set budget alerts for your high-spending days",
            "• Review recurring payments for optimization",
            "• Track weekly trends to maintain spending control",
            "• Use /budget to set category-specific limits"
        ])

        await query.edit_message_text("\n".join(message_parts), parse_mode="HTML")

    except Exception as e:
        await query.edit_message_text(f"❌ Error generating insights: {str(e)}")


async def _show_anomaly_detection(query, user_id):
    """Show spending anomaly detection."""
    await query.edit_message_text("⚠️ Detecting spending anomalies... ⏳")

    try:
        # This is a placeholder implementation since anomaly detection
        # logic is not fully implemented in the service
        from core.database import Session
        from core.repository.BankAccountRepository import BankAccountRepository
        from core.repository.TransactionRepository import TransactionRepository
        from datetime import datetime, timedelta
        import numpy as np

        session = Session()
        account_repo = BankAccountRepository(session)
        account = account_repo.get_by_telegram_id(str(user_id))

        if not account:
            await query.edit_message_text("❌ Account not found.")
            return

        # Get recent transactions for anomaly detection
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)

        transaction_repo = TransactionRepository(session)
        transactions = transaction_repo.get_transactions_by_date_range(
            account.id, start_date, end_date
        )

        if not transactions:
            await query.edit_message_text(
                "⚠️ <b>Insufficient Data</b>\n\n"
                "Not enough recent transactions for anomaly detection.\n"
                "Upload more transaction data to enable this feature.",
                parse_mode="HTML"
            )
            return

        # Simple anomaly detection based on spending amounts
        outgoing_amounts = [t.outgoing for t in transactions if t.outgoing and t.outgoing > 0]

        if len(outgoing_amounts) < 10:
            await query.edit_message_text(
                "⚠️ <b>Insufficient Transaction Data</b>\n\n"
                "Need at least 10 spending transactions for anomaly detection.",
                parse_mode="HTML"
            )
            return

        # Calculate statistical measures
        mean_amount = np.mean(outgoing_amounts)
        std_amount = np.std(outgoing_amounts)
        threshold = mean_amount + (2 * std_amount)  # 2 standard deviations

        # Find anomalies
        anomalies = []
        for t in transactions:
            if t.outgoing and t.outgoing > threshold:
                anomalies.append(t)

        message_parts = ["⚠️ <b>Spending Anomaly Detection</b>\n"]

        if anomalies:
            message_parts.extend([
                f"🚨 <b>Found {len(anomalies)} unusual spending patterns:</b>\n",
                f"📊 Normal spending range: 0 - {threshold:,.0f} IDR\n"
            ])

            for anomaly in anomalies[-5:]:  # Show last 5 anomalies
                message_parts.append(
                    f"🔴 <b>{anomaly.date.strftime('%Y-%m-%d')}:</b> {anomaly.outgoing:,.0f} IDR\n"
                    f"   {anomaly.description[:50]}..."
                )
        else:
            message_parts.extend([
                "✅ <b>No Unusual Spending Detected</b>\n",
                f"📊 All recent transactions within normal range (< {threshold:,.0f} IDR)",
                f"📈 Average spending: {mean_amount:,.0f} IDR"
            ])

        message_parts.extend([
            f"\n📅 Analysis period: {start_date} to {end_date}",
            f"📊 Transactions analyzed: {len(outgoing_amounts)}",
            "\n💡 Anomalies are transactions 2+ standard deviations above average"
        ])

        await query.edit_message_text("\n".join(message_parts), parse_mode="HTML")
        session.close()

    except Exception as e:
        await query.edit_message_text(f"❌ Error detecting anomalies: {str(e)}")