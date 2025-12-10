"""
Clothes Removal Handler

Complete conversation flow for clothes removal with validation, confirmation, and style selection.
"""

import logging
import base64
import time
from telegram import Update
from telegram.ext import ContextTypes

from telegram_bot.api_client import BackendAPIClient
from telegram_bot.utils.locale import LocaleManager
from telegram_bot.utils.keyboards import (
    get_style_keyboard, get_confirmation_keyboard, get_result_actions_keyboard,
    get_main_menu_keyboard
)
from telegram_bot.utils.validators import validate_photo
from telegram_bot.utils.logger import get_bot_logger
from telegram_bot.utils.error_handler import send_error_message
from telegram_bot.states import ClothesRemovalState, set_user_state, clear_user_state

logger = logging.getLogger(__name__)
bot_logger = get_bot_logger()
api_client = BackendAPIClient()


def get_locale(context: ContextTypes.DEFAULT_TYPE) -> LocaleManager:
    """Helper to get locale from bot_data"""
    return context.bot_data.get('locale_manager')


async def start_clothes_removal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start clothes removal conversation"""
    query = update.callback_query
    if query:
        await query.answer()
    
    user_id = update.effective_user.id
    locale = get_locale(context)
    lang = locale.get_user_language(user_id)
    
    # Set state
    set_user_state(context, ClothesRemovalState.WAITING_PHOTO.value)
    context.user_data['mode'] = 'clothes_removal'
    
    # Create start text similar to competitor
    if lang == "ru":
        start_text = (
            f"👗 **Помните о рекомендациях из [инструкции](https://t.me/example) для достижения наилучшего результата**\n\n"
            f"Отправьте фото девушки, и я его обработаю"
        )
    else:
        start_text = locale.get_text("clothes_removal.start", lang)
    
    if query:
        await query.edit_message_text(start_text, parse_mode="Markdown")
    else:
        await update.message.reply_text(start_text, parse_mode="Markdown")
    
    bot_logger.log_action(user_id, "clothes_removal_started", mode="clothes_removal")


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle photo from user"""
    user_id = update.effective_user.id
    locale = get_locale(context)
    lang = locale.get_user_language(user_id)
    
    # Check if user is in clothes removal mode
    if context.user_data.get('mode') != 'clothes_removal':
        return
    
    logger.info(f"User {user_id} sent photo for clothes removal")
    
    try:
        # Get photo file
        photo = update.message.photo[-1]  # Largest size
        photo_file = await photo.get_file()
        photo_bytes = await photo_file.download_as_bytearray()
        
        # Validate photo
        is_valid, error_msg, metadata = validate_photo(
            bytes(photo_bytes),
            max_mb=10,
            min_width=512,
            min_height=512,
            require_person=True
        )
        
        if not is_valid:
            await update.message.reply_text(error_msg)
            bot_logger.log_error(user_id, "photo_validation_failed", error_msg)
            return
        
        # Convert to base64
        photo_base64 = base64.b64encode(photo_bytes).decode('utf-8')
        
        # Store photo
        context.user_data['target_image'] = photo_base64
        context.user_data['photo_metadata'] = metadata
        
        # Move to confirmation state
        set_user_state(context, ClothesRemovalState.WAITING_CONFIRM.value)
        
        # Show confirmation
        confirmation_text = locale.get_text("clothes_removal.confirmation", lang)
        keyboard = get_confirmation_keyboard(
            locale, lang,
            confirm_callback="clothes_confirm",
            cancel_callback="back_to_menu"
        )
        
        await update.message.reply_text(
            confirmation_text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        
        bot_logger.log_action(user_id, "photo_received", mode="clothes_removal")
    
    except Exception as e:
        await send_error_message(update, context, e, lang)
        logger.error(f"Photo processing error for user {user_id}: {e}", exc_info=True)


async def handle_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle confirmation callback"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    locale = get_locale(context)
    lang = locale.get_user_language(user_id)
    
    if context.user_data.get('mode') != 'clothes_removal':
        return
    
    if not context.user_data.get('target_image'):
        await query.edit_message_text(
            locale.get_text("errors.generic", lang)
        )
        return
    
    # Move to style selection
    set_user_state(context, ClothesRemovalState.WAITING_STYLE.value)
    
    keyboard = get_style_keyboard(locale, lang, mode="clothes_removal")
    await query.edit_message_text(
        locale.get_text("clothes_removal.style_selection", lang),
        reply_markup=keyboard
    )


async def handle_style_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, style: str):
    """Handle style selection and start processing"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    locale = get_locale(context)
    lang = locale.get_user_language(user_id)
    
    if context.user_data.get('mode') != 'clothes_removal':
        return
    
    target_image = context.user_data.get('target_image')
    
    if not target_image:
        await query.edit_message_text(
            locale.get_text("errors.generic", lang)
        )
        return
    
    # Validate style
    from telegram_bot.utils.validators import is_valid_style
    if not is_valid_style(style, mode="clothes_removal"):
        await query.edit_message_text(
            locale.get_text("errors.invalid_style", lang)
        )
        return
    
    # Set generating state
    set_user_state(context, ClothesRemovalState.GENERATING.value)
    
    # Show processing message
    await query.edit_message_text(
        locale.get_text("clothes_removal.processing", lang, style=style),
        parse_mode="Markdown"
    )
    
    start_time = time.time()
    
    try:
        # Call API with extended timeout for clothes removal
        result = await api_client.generate_clothes_removal(
            target_image=target_image,
            style=style
        )
        
        generation_time = time.time() - start_time
        
        if result.get('status') == 'done' and result.get('image'):
            # Send result image
            image_data = base64.b64decode(result['image'])
            
            await query.message.reply_photo(
                photo=image_data,
                caption=locale.get_text("clothes_removal.success", lang, style=style),
                parse_mode="Markdown"
            )
            
            # Show result actions
            keyboard = get_result_actions_keyboard(locale, lang, mode="clothes_removal")
            await query.message.reply_text(
                locale.get_text("common.choose_mode", lang),
                reply_markup=keyboard
            )
            
            bot_logger.log_generation(
                user_id=user_id,
                mode="clothes_removal",
                prompt=None,
                style=style,
                status="success",
                time_seconds=generation_time
            )
        else:
            error_msg = result.get('error', 'Unknown error')
            await query.edit_message_text(
                locale.get_text("errors.processing_failed", lang, error=error_msg)
            )
            
            bot_logger.log_generation(
                user_id=user_id,
                mode="clothes_removal",
                prompt=None,
                style=style,
                status="failed",
                time_seconds=generation_time,
                error=error_msg
            )
    
    except Exception as e:
        generation_time = time.time() - start_time
        await send_error_message(update, context, e, lang)
        
        bot_logger.log_generation(
            user_id=user_id,
            mode="clothes_removal",
            prompt=None,
            style=style,
            status="failed",
            time_seconds=generation_time,
            error=str(e)
        )
    
    finally:
        clear_user_state(context)
