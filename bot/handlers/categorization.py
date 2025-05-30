from telegram import Update
from telegram.ext import ContextTypes
from bot.utils.auth import requires_registration
from core.services.categorization_service import CategorizationService


@requires_registration()
async def handle_auto_categorize(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Run auto-categorization on user's transactions."""
    user_id = update.effective_user.id

    await update.message.reply_text(
        "🔄 <b>Starting Auto-Categorization</b>\n\n"
        "Analyzing your transactions and assigning categories...\n"
        "This may take a moment ⏳",
        parse_mode="HTML"
    )

    try:
        cat_service = CategorizationService()

        # Get current statistics
        stats_before = cat_service.get_categorization_statistics(user_id)

        # Run auto-categorization
        result = cat_service.auto_categorize_transactions(user_id)

        # Get updated statistics
        stats_after = cat_service.get_categorization_statistics(user_id)

        if 'error' in result:
            await update.message.reply_text(f"❌ Error: {result['error']}")
            return

        # Format results
        result_text = (
            "✅ <b>Auto-Categorization Complete!</b>\n\n"
            f"📊 <b>Processing Results:</b>\n"
            f"• Total processed: {result['total_processed']}\n"
            f"• Successfully categorized: {result['successfully_categorized']}\n"
            f"• Failed: {result['failed_categorization']}\n\n"
            f"📈 <b>Overall Statistics:</b>\n"
            f"• Total transactions: {stats_after['total_transactions']}\n"
            f"• Categorized: {stats_after['categorized_transactions']}\n"
            f"• Uncategorized: {stats_after['uncategorized_transactions']}\n"
            f"• Categorization rate: {stats_after['categorization_rate']:.1f}%\n\n"
        )

        if result['categories_assigned']:
            result_text += "🏷️ <b>Categories Assigned:</b>\n"
            for category, count in result['categories_assigned'].items():
                result_text += f"• {category}: {count} transactions\n"

        result_text += (
            "\n💡 <b>Tips:</b>\n"
            "• Run /categorize again to improve accuracy\n"
            "• Use /trends to see updated category analysis\n"
            "• Categories are learned from your transaction descriptions"
        )

        await update.message.reply_text(result_text, parse_mode="HTML")

    except Exception as e:
        await update.message.reply_text(
            f"❌ <b>Auto-Categorization Failed</b>\n\n"
            f"Error: {str(e)}\n\n"
            "Please try again or contact support if the problem persists.",
            parse_mode="HTML"
        )


@requires_registration()
async def handle_categorization_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show categorization statistics for the user."""
    user_id = update.effective_user.id

    try:
        cat_service = CategorizationService()
        stats = cat_service.get_categorization_statistics(user_id)

        if 'error' in stats:
            await update.message.reply_text(f"❌ Error: {stats['error']}")
            return

        # Create progress bar
        rate = stats['categorization_rate']
        progress_bar = "🟩" * int(rate // 10) + "⬜" * (10 - int(rate // 10))

        stats_text = (
            "📊 <b>Transaction Categorization Status</b>\n\n"
            f"📈 <b>Overall Progress:</b>\n"
            f"{progress_bar} {rate:.1f}%\n\n"
            f"📋 <b>Details:</b>\n"
            f"• Total transactions: {stats['total_transactions']}\n"
            f"• ✅ Categorized: {stats['categorized_transactions']}\n"
            f"• ❓ Uncategorized: {stats['uncategorized_transactions']}\n\n"
        )

        if stats['uncategorized_transactions'] > 0:
            stats_text += (
                "💡 <b>Recommendation:</b>\n"
                f"You have {stats['uncategorized_transactions']} uncategorized transactions. "
                "Use /categorize to automatically assign categories and improve your spending analysis."
            )
        else:
            stats_text += "🎉 <b>Great!</b> All your transactions are categorized!"

        await update.message.reply_text(stats_text, parse_mode="HTML")

    except Exception as e:
        await update.message.reply_text(f"❌ Error getting statistics: {str(e)}")