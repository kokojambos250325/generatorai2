"""
Start Command and Main Menu Handler

Displays welcome message and main menu with 2 buttons for MVP modes.
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /start command.
    
    First checks if user has selected language, if not shows language selection.
    Otherwise displays welcome message and main menu.
    """
    user = update.effective_user
    user_id = user.id
    logger.info(f"User {user_id} ({user.username}) started bot")
    
    # Get locale manager from bot_data
    locale = context.bot_data.get('locale_manager')
    if not locale:
        await update.message.reply_text("Bot initialization error. Please contact administrator.")
        return
    
    # Check if user has language preference
    user_lang = locale.get_user_language(user_id)
    
    if not user_lang:
        # First time user - show language selection
        await show_language_selection(update, context)
    else:
        # Show main menu
        await show_main_menu_message(update, context, user_lang)


async def show_language_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Show language selection menu.
    """
    locale = context.bot_data.get('locale_manager')
    from telegram_bot.utils.keyboards import get_language_keyboard
    
    # Use English for initial language selection
    reply_markup = get_language_keyboard(locale, "en")
    
    await update.message.reply_text(
        locale.get_text("language_selection.title", "en"),
        reply_markup=reply_markup
    )


async def show_main_menu_message(update: Update, context: ContextTypes.DEFAULT_TYPE, lang: str = None):
    """
    Show main menu with welcome message.
    """
    locale = context.bot_data.get('locale_manager')
    user = update.effective_user
    user_id = user.id
    
    if not lang:
        lang = locale.get_user_language(user_id)
    
    # Welcome message
    welcome_text = locale.get_text("main_menu.welcome", lang, name=user.first_name)
    
    # Use keyboard utility
    from telegram_bot.utils.keyboards import get_main_menu_keyboard
    reply_markup = get_main_menu_keyboard(locale, lang)
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle button callbacks from main menu and language selection.
    """
    locale = context.bot_data.get('locale_manager')
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    callback_data = query.data
    
    logger.info(f"User {user_id} selected: {callback_data}")
    
    # Language selection
    if callback_data.startswith("lang_"):
        lang_code = callback_data.replace("lang_", "")
        locale.set_user_language(user_id, lang_code)
        
        # Confirm language change
        await query.edit_message_text(
            locale.get_text("language_selection.selected", lang_code)
        )
        
        # Show main menu
        await show_main_menu_message_after_callback(update, context, lang_code)
        return
    
    # Show language selection
    elif callback_data == "show_language":
        from telegram_bot.utils.keyboards import get_language_keyboard
        user_lang = locale.get_user_language(user_id)
        reply_markup = get_language_keyboard(locale, user_lang)
        
        await query.edit_message_text(
            locale.get_text("language_selection.title", user_lang),
            reply_markup=reply_markup
        )
        return
    
    # Mode selection
    elif callback_data == "mode_free":
        # Import here to avoid circular imports
        from telegram_bot.handlers import free
        await free.start_free_generation(update, context)
    
    elif callback_data == "mode_nsfw_face":
        # Import here to avoid circular imports
        from telegram_bot.handlers import nsfw_face
        await nsfw_face.start_nsfw_face(update, context)
    
    elif callback_data == "mode_clothes":
        # Import here to avoid circular imports
        from telegram_bot.handlers import clothes
        await clothes.start_clothes_removal(update, context)
    
    elif callback_data == "show_help":
        from telegram_bot.handlers import help
        await help.show_help_menu(update, context)
    
    elif callback_data == "show_profile":
        from telegram_bot.handlers import profile
        await profile.show_profile(update, context)
    
    elif callback_data == "show_balance":
        from telegram_bot.handlers import balance
        await balance.show_balance(update, context)
    
    elif callback_data == "show_topup":
        from telegram_bot.handlers import balance
        await balance.show_topup(update, context)
    
    elif callback_data == "mode_video":
        from telegram_bot.handlers import video
        await video.start_video_animation(update, context)
    
    elif callback_data == "mode_free_face_menu":
        from telegram_bot.utils.keyboards import get_free_face_menu_keyboard
        user_lang = locale.get_user_language(user_id)
        menu_text = (
            f"✨ **Здесь вы можете:**\n\n"
            f"👥 Заменить лицо на любом фото\n"
            f"✨ Создать любую картинку по своему запросу (без встройки лица)\n\n"
            f"Что творим?"
        )
        keyboard = get_free_face_menu_keyboard(locale, user_lang)
        await query.edit_message_text(menu_text, reply_markup=keyboard, parse_mode="Markdown")
    
    elif callback_data == "mode_face_swap":
        from telegram_bot.handlers import face_swap
        await face_swap.handle_face_swap(update, context)
    
    elif callback_data == "show_create_bot":
        from telegram_bot.handlers import create_bot
        await create_bot.show_create_bot(update, context)
    
    elif callback_data.startswith("topup_"):
        from telegram_bot.handlers import balance
        amount = int(callback_data.replace("topup_", ""))
        await balance.handle_topup_amount(update, context, amount)
    
    elif callback_data == "back_to_menu":
        await show_main_menu_message_after_callback(update, context, locale.get_user_language(user_id))
    
    else:
        user_lang = locale.get_user_language(user_id)
        await query.edit_message_text(
            locale.get_text("errors.unknown_option", user_lang)
        )


async def show_main_menu_message_after_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, lang: str):
    """
    Show main menu after language selection (uses query.message instead of update.message).
    """
    locale = context.bot_data.get('locale_manager')
    user = update.effective_user
    
    # Welcome message
    welcome_text = locale.get_text("main_menu.welcome", lang, name=user.first_name)
    
    # Use keyboard utility
    from telegram_bot.utils.keyboards import get_main_menu_keyboard
    reply_markup = get_main_menu_keyboard(locale, lang)
    
    query = update.callback_query
    await query.message.reply_text(
        welcome_text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )


async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Show main menu (called from other handlers to return to menu).
    """
    locale = context.bot_data.get('locale_manager')
    user_id = update.effective_user.id
    lang = locale.get_user_language(user_id)
    
    from telegram_bot.utils.keyboards import get_main_menu_keyboard
    reply_markup = get_main_menu_keyboard(locale, lang)
    
    await update.effective_message.reply_text(
        locale.get_text("common.choose_mode", lang),
        reply_markup=reply_markup
    )
