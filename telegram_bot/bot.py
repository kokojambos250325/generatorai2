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
        await update.effective_message.reply_text(
            "❌ An error occurred. Please try again or use /start to return to the main menu."
        )


def main():
    """Start the bot"""
    logger.info("Starting Telegram Bot...")
    logger.info(f"Backend URL: {settings.backend_api_url}")
    
    # Create application
    application = (
        Application.builder()
        .token(settings.telegram_bot_token)
        .build()
    )
    
    # Register handlers
    application.add_handler(CommandHandler("start", start.start_command))
    application.add_handler(CallbackQueryHandler(start.button_handler))
    
    # Free generation handlers
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.User(user_id=free.get_active_users()),
        free.handle_prompt
    ))
    
    # Clothes removal handlers
    application.add_handler(MessageHandler(
        filters.PHOTO & filters.User(user_id=clothes.get_active_users()),
        clothes.handle_photo
    ))
    
    # Error handler
    application.add_error_handler(error_handler)
    
    # Start bot
    logger.info("Bot started successfully. Press Ctrl+C to stop.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
