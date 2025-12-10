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

from telegram_bot.config import get_settings
from telegram_bot.handlers import start, free, clothes, nsfw_face, help, profile, balance, video, create_bot
from telegram_bot.utils.locale import init_locale_manager
from telegram_bot.utils.logger import get_bot_logger
from telegram_bot.utils.error_handler import send_error_message

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize bot logger
bot_logger = get_bot_logger()

# Load settings
settings = get_settings()


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors in the bot"""
    error = context.error
    user_id = update.effective_user.id if update.effective_user else None
    
    logger.error(f"Update {update} caused error {error}", exc_info=error)
    
    # Log error
    bot_logger.log_error(
        user_id=user_id,
        error_type=type(error).__name__,
        error_message=str(error)
    )
    
    if update and update.effective_message:
        # Use centralized error handler
        await send_error_message(update, context, error)


async def terms_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /terms command"""
    locale = context.bot_data.get('locale_manager')
    user_id = update.effective_user.id
    lang = locale.get_user_language(user_id) if locale else "en"
    
    await update.message.reply_text(
        "📄 **Условия оферты**\n\n"
        "1. Используя бота, вы соглашаетесь с правилами обработки данных.\n"
        "2. Бот предоставляет услуги генерации изображений \"как есть\".\n"
        "3. Пользователь несет ответственность за загружаемый контент.\n\n"
        "Полный текст оферты доступен на сайте (ссылка).",
        parse_mode="Markdown"
    )

async def post_init(application: Application):
    """Post initialization hook to set bot commands"""
    commands = [
        ("start", "Главное меню/Перезапуск ♻️"),
        ("balance", "Баланс 💰"),
        ("buy", "Купить обработки 🛒"),
        ("help", "Помощь ❓"),
        ("terms", "Условия оферты 📄")
    ]
    await application.bot.set_my_commands(commands)

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
        .post_init(post_init)
        .build()
    )
    
    # Store locale_manager in bot_data for access in handlers
    application.bot_data['locale_manager'] = locale_manager
    
    # Register handlers
    
    # Start command
    application.add_handler(CommandHandler("start", start.start_command))
    application.add_handler(CommandHandler("balance", balance.show_balance))
    application.add_handler(CommandHandler("buy", balance.show_topup))
    application.add_handler(CommandHandler("help", help.show_help_menu))
    application.add_handler(CommandHandler("terms", terms_command))
    
    # Help callbacks
    application.add_handler(CallbackQueryHandler(
        help.handle_help_callback,
        pattern=r"^help_|^show_help$"
    ))
    
    # Profile callback
    application.add_handler(CallbackQueryHandler(
        profile.show_profile,
        pattern=r"^show_profile$"
    ))
    
    # Combined Photo Handler
    async def global_photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        mode = context.user_data.get('mode')
        logger.info(f"Global photo handler: mode={mode}")
        
        if mode == 'nsfw_face':
            from telegram_bot.states import NSFWFaceState
            current_state = context.user_data.get('state')
            if current_state == NSFWFaceState.WAITING_FACES.value:
                await nsfw_face.handle_face_photo(update, context)
        
        elif mode == 'free_generation':
            from telegram_bot.states import FreeGenerationState
            current_state = context.user_data.get('state')
            if current_state == FreeGenerationState.WAITING_FACE.value:
                await free.handle_face_photo(update, context)
        
        elif mode == 'clothes_removal':
            from telegram_bot.states import ClothesRemovalState
            current_state = context.user_data.get('state')
            if current_state == ClothesRemovalState.WAITING_PHOTO.value:
                await clothes.handle_photo(update, context)
        
        elif mode == 'face_swap':
            from telegram_bot.handlers import face_swap
            current_state = context.user_data.get('state')
            if current_state == face_swap.WAITING_FACE_SWAP_SOURCE:
                await face_swap.process_face_swap_source(update, context)
            elif current_state == face_swap.WAITING_FACE_SWAP_TARGET:
                await face_swap.process_face_swap_target(update, context)

    # Combined Text Handler
    async def global_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        mode = context.user_data.get('mode')
        text = update.message.text.lower().strip()
        logger.info(f"Global text handler: mode={mode}, text={text}")
        
        if mode == 'nsfw_face':
            from telegram_bot.states import NSFWFaceState
            current_state = context.user_data.get('state')
            if current_state == NSFWFaceState.WAITING_FACES.value:
                if text == 'готово' or text == 'done':
                    await nsfw_face.handle_done_command(update, context)
            elif current_state == NSFWFaceState.WAITING_SCENE.value:
                await nsfw_face.handle_scene_prompt(update, context)
        
        elif mode == 'free_generation':
            from telegram_bot.states import FreeGenerationState
            current_state = context.user_data.get('state')
            if current_state == FreeGenerationState.WAITING_FACE.value:
                if text == 'готово' or text == 'done':
                    await free.handle_face_done(update, context)
            elif current_state == FreeGenerationState.WAITING_PROMPT.value:
                await free.handle_prompt(update, context)

    application.add_handler(MessageHandler(
        filters.PHOTO,
        global_photo_handler
    ))

    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        global_text_handler
    ))
    
    # NSFW templates and guide
    application.add_handler(CallbackQueryHandler(
        nsfw_face.show_templates,
        pattern=r"^nsfw_show_templates$"
    ))
    application.add_handler(CallbackQueryHandler(
        lambda u, c: nsfw_face.handle_template_selection(u, c, int(c.callback_query.data.replace("template_nsfw_", ""))),
        pattern=r"^template_nsfw_\d+$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        lambda u, c: nsfw_face.handle_style_selection(u, c, c.callback_query.data.replace("nsfw_style_", "")),
        pattern=r"^nsfw_style_(realism|lux|anime)$"
    ))
    
    # Free generation handlers - REMOVED (Merged into global handlers)
    # See global_text_handler and global_photo_handler above
    
    # Add callback handler for face choice (yes/no/done)
    application.add_handler(CallbackQueryHandler(
        free.handle_face_choice,
        pattern=r"^face_(yes|no)$"
    ))
    application.add_handler(CallbackQueryHandler(
        free.handle_face_done,
        pattern=r"^face_done$"
    ))
    
    # Examples handler
    application.add_handler(CallbackQueryHandler(
        free.show_examples,
        pattern=r"^show_examples$"
    ))
    application.add_handler(CallbackQueryHandler(
        lambda u, c: free.handle_example_selection(u, c, int(c.callback_query.data.replace("example_free_", ""))),
        pattern=r"^example_free_\d+$"
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
    
    # Clothes removal handlers - REMOVED (Merged into global handlers)
    # See global_photo_handler
    
    # Face swap handlers - REMOVED (Merged into global handlers)
    # See global_photo_handler

    # Add callback handler for confirmation in clothes mode
    application.add_handler(CallbackQueryHandler(
        clothes.handle_confirmation,
        pattern=r"^clothes_confirm$"
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
