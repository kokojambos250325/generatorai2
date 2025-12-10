"""
Face Swap Handler

Handles face swap functionality.
"""
import logging
import base64
import time
from telegram import Update
from telegram.ext import ContextTypes

from telegram_bot.api_client import BackendAPIClient
from telegram_bot.utils.locale import LocaleManager
from telegram_bot.utils.keyboards import get_main_menu_keyboard
from telegram_bot.utils.validators import validate_photo
from telegram_bot.utils.logger import get_bot_logger
from telegram_bot.utils.error_handler import send_error_message
from telegram_bot.states import set_user_state, clear_user_state

logger = logging.getLogger(__name__)
bot_logger = get_bot_logger()
api_client = BackendAPIClient()

# Conversation states
WAITING_FACE_SWAP_SOURCE = "face_swap_waiting_source"
WAITING_FACE_SWAP_TARGET = "face_swap_waiting_target"


def get_locale(context: ContextTypes.DEFAULT_TYPE) -> LocaleManager:
    """Helper to get locale from bot_data"""
    return context.bot_data.get('locale_manager')


async def handle_face_swap(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Start face swap flow
    """
    query = update.callback_query
    if query:
        await query.answer()
    
    user_id = update.effective_user.id
    locale = get_locale(context)
    lang = locale.get_user_language(user_id)
    
    # Set state
    set_user_state(context, WAITING_FACE_SWAP_SOURCE)
    context.user_data['mode'] = 'face_swap'
    
    start_text = locale.get_text("face_swap.start", lang)
    
    if query:
        await query.edit_message_text(start_text, parse_mode="Markdown")
    else:
        await update.message.reply_text(start_text, parse_mode="Markdown")
    
    bot_logger.log_action(user_id, "face_swap_started", mode="face_swap")


async def process_face_swap_source(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Process source face image
    """
    user_id = update.effective_user.id
    locale = get_locale(context)
    lang = locale.get_user_language(user_id)
    
    if not update.message.photo:
        await update.message.reply_text(locale.get_text("errors.photo_required", lang))
        return
    
    photo = update.message.photo[-1]  # Get highest resolution
    photo_file = await photo.get_file()
    photo_bytes = await photo_file.download_as_bytearray()
    
    # Validate photo
    is_valid, error_msg, metadata = validate_photo(
        bytes(photo_bytes),
        max_mb=10,
        min_width=512,
        min_height=512,
        require_face=True
    )
    
    if not is_valid:
        await update.message.reply_text(error_msg)
        return
    
    # Convert to base64
    face_base64 = base64.b64encode(photo_bytes).decode('utf-8')
    
    # Store in context
    context.user_data['face_swap_source'] = face_base64
    set_user_state(context, WAITING_FACE_SWAP_TARGET)
    
    await update.message.reply_text(
        locale.get_text("face_swap.source_received", lang),
        parse_mode='Markdown'
    )
    
    bot_logger.log_action(user_id, "face_swap_source_received", mode="face_swap")


async def process_face_swap_target(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Process target image and submit task
    """
    user_id = update.effective_user.id
    locale = get_locale(context)
    lang = locale.get_user_language(user_id)
    
    if not update.message.photo:
        await update.message.reply_text(locale.get_text("errors.photo_required", lang))
        return
    
    photo = update.message.photo[-1]
    photo_file = await photo.get_file()
    photo_bytes = await photo_file.download_as_bytearray()
    
    # Validate photo
    is_valid, error_msg, metadata = validate_photo(
        bytes(photo_bytes),
        max_mb=10,
        min_width=512,
        min_height=512
    )
    
    if not is_valid:
        await update.message.reply_text(error_msg)
        return
    
    # Convert to base64
    target_image = base64.b64encode(photo_bytes).decode('utf-8')
    source_image = context.user_data.get('face_swap_source')
    
    if not source_image:
        await update.message.reply_text(locale.get_text("errors.generic", lang))
        clear_user_state(context)
        return
    
    # Set generating state
    set_user_state(context, "face_swap_generating")
    
    # Show processing message
    processing_msg = await update.message.reply_text(
        locale.get_text("face_swap.processing", lang),
        parse_mode='Markdown'
    )
    
    start_time = time.time()
    
    try:
        # TODO: Integrate with face swap API endpoint when available
        # For now, show coming soon message
        await processing_msg.edit_text(
            locale.get_text("face_swap.coming_soon", lang),
            parse_mode='Markdown'
        )
        
        bot_logger.log_action(user_id, "face_swap_requested", mode="face_swap")
    
    except Exception as e:
        generation_time = time.time() - start_time
        await send_error_message(update, context, e, lang)
        
        bot_logger.log_generation(
            user_id=user_id,
            mode="face_swap",
            prompt=None,
            style=None,
            status="failed",
            time_seconds=generation_time,
            error=str(e)
        )
    
    finally:
        # Clean up context
        clear_user_state(context)
        context.user_data.pop('face_swap_source', None)
