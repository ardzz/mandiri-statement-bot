from telegram.ext import CommandHandler, MessageHandler, filters, ConversationHandler, CallbackQueryHandler

from bot.handlers.main import handle_main_menu
from bot.handlers.recap import (
    handle_recap_all_time, handle_sync_recap, handle_recap_all_time_text, handle_recap_menu,
    handle_custom_time_start_with_presets, handle_preset_callback, handle_custom_time_start,
    handle_custom_time_input_start, handle_custom_time_input_end, handle_back_to_main_menu,
    CHOOSE_PRESET, CHOOSE_START_DATE, CHOOSE_END_DATE
)
from bot.handlers.patterns import (
    handle_patterns_menu, handle_patterns_callback,
    handle_daily_patterns, handle_recurring_analysis
)
from bot.handlers.register import BIRTHDATE, handle_save_birthdate, handle_update_birthdate
from bot.handlers.start import handle_start_command
from bot.handlers.upload import handle_upload_guide, handle_excel_upload
from bot.handlers.trends import handle_trends_menu, handle_trends_callback
from bot.handlers.budget import (
    handle_budget_menu, handle_budget_callback, handle_budget_category_selection,
    handle_budget_input, budget_conversation, SETTING_AMOUNT
)
from bot.handlers.goals import (
    handle_goals_menu, handle_goals_callback, handle_set_goal_command,
    handle_update_goal_command, handle_goal_title_input, handle_goal_amount_input,
    handle_goal_date_input, handle_goal_cancel, GOAL_TITLE, GOAL_AMOUNT, GOAL_DATE, handle_add_goal_progress_command,
    handle_list_goals_command
)
from bot.handlers.insights import handle_insights_menu, handle_insights_callback
from bot.handlers.settings import handle_settings_menu, handle_settings_callback
from bot.handlers.categorization import handle_auto_categorize, handle_categorization_stats


def register_handlers(app):
    """Register all handlers for the bot."""

    # === Conversation Handlers ===

    # Register: Birthdate Conversation
    birthdate_conv = ConversationHandler(
        entry_points=[CommandHandler("start", handle_start_command)],
        states={
            BIRTHDATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_save_birthdate)]
        },
        fallbacks=[],
    )
    app.add_handler(birthdate_conv)

    # Update birthdate Conversation
    update_birthdate_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(r"^📅 Update Birthdate$"), handle_update_birthdate)],
        states={
            BIRTHDATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_save_birthdate)]
        },
        fallbacks=[MessageHandler(filters.Regex(r"^↩️ Back to Main Menu$"), handle_back_to_main_menu)],
    )
    app.add_handler(update_birthdate_conv)

    # Budget setting conversation handler
    budget_setting_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(handle_budget_category_selection, pattern="^set_budget_")],
        states={
            SETTING_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_budget_input)],
        },
        fallbacks=[
            CallbackQueryHandler(handle_budget_callback, pattern="^budget_close$"),
            CommandHandler("cancel", lambda update, context: ConversationHandler.END)
        ],
    )
    app.add_handler(budget_setting_conv)

    # Goal creation conversation handler - THIS IS THE FIX
    goal_creation_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(handle_goals_callback, pattern="^create_goal_")],
        states={
            GOAL_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_goal_title_input)],
            GOAL_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_goal_amount_input)],
            GOAL_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_goal_date_input)],
        },
        fallbacks=[
            CallbackQueryHandler(handle_goals_callback, pattern="^goals_close$"),
            CommandHandler("cancel", handle_goal_cancel)
        ],
    )
    app.add_handler(goal_creation_conv)

    # Enhanced Recap Custom Time Conversation with Presets
    recap_custom_time_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(r"^📅 Recap Custom Time$"), handle_custom_time_start_with_presets)],
        states={
            CHOOSE_PRESET: [CallbackQueryHandler(handle_preset_callback)],
            CHOOSE_START_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_custom_time_input_start)],
            CHOOSE_END_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_custom_time_input_end)],
        },
        fallbacks=[
            MessageHandler(filters.Regex(r"^↩️ Back to Main Menu$"), handle_back_to_main_menu),
            CallbackQueryHandler(handle_preset_callback, pattern="^(cancel|custom_range)$")
        ],
    )
    app.add_handler(recap_custom_time_conv)

    # === Command Handlers ===
    app.add_handler(CommandHandler("start", handle_start_command))
    app.add_handler(CommandHandler("menu", handle_main_menu))
    app.add_handler(CommandHandler("recap", handle_recap_menu))
    app.add_handler(CommandHandler("recap_all_time", handle_recap_all_time))
    app.add_handler(CommandHandler("recap_all_time_text", handle_recap_all_time_text))
    app.add_handler(CommandHandler("sync_recap", handle_sync_recap))
    app.add_handler(CommandHandler("guide", handle_upload_guide))
    app.add_handler(CommandHandler("trends", handle_trends_menu))
    app.add_handler(CommandHandler("budget", handle_budget_menu))
    app.add_handler(CommandHandler("goals", handle_goals_menu))
    app.add_handler(CommandHandler("insights", handle_insights_menu))
    app.add_handler(CommandHandler("settings", handle_settings_menu))

    # Goal management commands
    app.add_handler(CommandHandler("set_goal", handle_set_goal_command))
    app.add_handler(CommandHandler("update_goal", handle_update_goal_command))
    app.add_handler(CommandHandler("add_goal_progress", handle_add_goal_progress_command))
    app.add_handler(CommandHandler("list_goals", handle_list_goals_command))

    # Categorization commands
    app.add_handler(CommandHandler("categorize", handle_auto_categorize))
    app.add_handler(CommandHandler("categorization_stats", handle_categorization_stats))

    # === Callback Query Handlers ===
    app.add_handler(CallbackQueryHandler(handle_trends_callback, pattern="^trends_"))
    app.add_handler(CallbackQueryHandler(handle_budget_callback, pattern="^budget_"))
    app.add_handler(CallbackQueryHandler(handle_goals_callback, pattern="^goals_"))
    app.add_handler(CallbackQueryHandler(handle_insights_callback, pattern="^insights_"))
    app.add_handler(CallbackQueryHandler(handle_settings_callback, pattern="^settings_"))

    # === Message Handlers (Text-Based Triggers) ===
    # Main menu navigation
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r"^📤 Upload E-statement Excel$"), handle_upload_guide))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r"^📊 Recap$"), handle_recap_menu))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r"^📈 Trends & Analysis$"), handle_trends_menu))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r"^💰 Budget Management$"), handle_budget_menu))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r"^🎯 Financial Goals$"), handle_goals_menu))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r"^🔔 Smart Insights$"), handle_insights_menu))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r"^🏷️ Auto Categorize$"), handle_auto_categorize))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r"^⚙️ Settings$"), handle_settings_menu))

    # Legacy recap handlers
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r"^📊?\s*Recap All Time$"), handle_recap_all_time))
    app.add_handler(
        MessageHandler(filters.TEXT & filters.Regex(r"^📊?\s*Recap All Time Text Mode$"), handle_recap_all_time_text))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r"^🔄 Sync Recap$"), handle_sync_recap))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r"^❓ Help$"), handle_upload_guide))

    # Pattern analysis handlers
    app.add_handler(MessageHandler(filters.Regex("^📊 Spending Patterns$"), handle_patterns_menu))
    app.add_handler(CallbackQueryHandler(handle_patterns_callback, pattern="^patterns_"))
    app.add_handler(CommandHandler("patterns", handle_patterns_menu))
    app.add_handler(CommandHandler("daily_patterns", handle_daily_patterns))
    app.add_handler(CommandHandler("recurring", handle_recurring_analysis))

    # === File Upload Handler ===
    app.add_handler(MessageHandler(filters.Document.ALL, handle_excel_upload))