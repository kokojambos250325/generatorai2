"""
Telegram Bot - Main Entry Point

MVP Bot with 2 conversation flows:
- Free Generation: Text-to-image
- Clothes Removal: Remove clothes from photos

Bot Token: Store in .env file, never in code!
"""

import logging
import asyncio
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)

from config import get_settings
from handlers import start, free, clothes
from utils.locale import init_locale_manager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load settings
settings = get_settings()


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors in the bot"""
    logger.error(f"Update {update} caused error {context.error}")
    
    if update and update.effective_message:
        # Get locale from bot_data
        locale = context.bot_data.get('locale_manager')
        if locale:
            user_id = update.effective_user.id if update.effective_user else None
            lang = locale.get_user_language(user_id) if user_id else "en"
            error_text = locale.get_text("errors.generic_restart", lang)
        else:
            error_text = "❌ An error occurred. Please try again or use /start to return to the main menu."
        
        await update.effective_message.reply_text(error_text)


def main():
    """Start the bot"""
    logger.info("Starting Telegram Bot...")
    logger.info(f"Backend URL: {settings.backend_api_url}")
    
    # Initialize locale manager
    logger.info("Initializing locale manager...")
    locale_manager = init_locale_manager()
    logger.info(f"Loaded {len(locale_manager._locales)} languages: {', '.join(locale_manager._locales.keys())}")
    
    # Create application
    application = (
        Application.builder()
        .token(settings.telegram_bot_token)
        .build()
    )
    
    # Store locale_manager in bot_data for access in handlers
    application.bot_data['locale_manager'] = locale_manager
    
    # Register handlers
    application.add_handler(CommandHandler("start", start.start_command))
    
    # Free generation handlers - TEXT messages for prompts
    # Don't use filters.User() because active_users changes dynamically
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        free.handle_prompt
    ))
    
    # Add callback handler for face choice (yes/no) - BEFORE general button_handler
    application.add_handler(CallbackQueryHandler(
        free.handle_face_choice,
        pattern=r"^face_(yes|no|done)$"
    ))
    
    # Add callback handler for style selection in free mode
    async def free_style_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        style = query.data.replace("style_", "")
        await free.handle_style_selection(update, context, style)
    
    application.add_handler(CallbackQueryHandler(
        free_style_callback,
        pattern=r"^style_(realism|lux|anime|chatgpt|noir|super_realism)$"
    ))
    
    # Add callback handler for prompt guide
    application.add_handler(CallbackQueryHandler(
        free.show_prompt_guide,
        pattern=r"^show_prompt_guide$"
    ))
    
    # Clothes removal handlers - PHOTO messages
    # Don't use filters.User() because active_users changes dynamically
    application.add_handler(MessageHandler(
        filters.PHOTO,
        clothes.handle_photo
    ))
    
    # Add callback handler for style selection in clothes mode
    async def clothes_style_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        style = query.data.replace("clothes_style_", "")
        await clothes.handle_style_selection(update, context, style)
    
    application.add_handler(CallbackQueryHandler(
        clothes_style_callback,
        pattern=r"^clothes_style_(realism|lux|anime)$"
    ))
    
    # General button handler for main menu - MUST BE LAST
    application.add_handler(CallbackQueryHandler(start.button_handler))
    
    # Error handler
    application.add_error_handler(error_handler)
    
    # Start bot
    logger.info("Bot started successfully. Press Ctrl+C to stop.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
