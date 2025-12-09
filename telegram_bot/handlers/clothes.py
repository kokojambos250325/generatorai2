"""
Clothes Removal Handler

Conversation flow for clothes removal.

Flow:
1. User selects Remove Clothes
2. Bot asks for photo
3. User sends photo
4. Bot asks for style
5. User selects style
6. Bot processes image
7. Bot shows result and returns to main menu
"""

import logging
import httpx
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import get_settings
from utils.encode import photo_to_base64
from handlers import start
from utils.locale import get_locale_manager

logger = logging.getLogger(__name__)
settings = get_settings()
locale = get_locale_manager()

# Track users in clothes removal flow
active_users = set()


def get_active_users():
    """Return set of users currently in clothes removal flow"""
    return active_users


async def start_clothes_removal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Start clothes removal conversation.
    """
    query = update.callback_query
    user_id = update.effective_user.id
    lang = get_locale(context).get_user_language(user_id)
    
    # Add user to active users
    active_users.add(user_id)
    
    # Store state
    context.user_data['mode'] = 'clothes_removal'
    context.user_data['step'] = 'waiting_photo'
    
    await query.edit_message_text(
        get_locale(context).get_text("clothes_removal.start", lang),
        parse_mode="Markdown"
    )


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle photo from user.
    """
    user_id = update.effective_user.id
    lang = get_locale(context).get_user_language(user_id)
    
    # Check if user is in clothes removal flow
    if user_id not in active_users:
        return
    
    # Check step
    if context.user_data.get('step') != 'waiting_photo':
        return
    
    logger.info(f"User {user_id} sent photo")
    
    try:
        # Get photo file
        photo = update.message.photo[-1]  # Largest size
        file = await photo.get_file()
        
        # Download photo bytes
        photo_bytes = await file.download_as_bytearray()
        
        # Convert to base64
        photo_base64 = await photo_to_base64(bytes(photo_bytes))
        
        # Store photo
        context.user_data['target_image'] = photo_base64
        context.user_data['step'] = 'waiting_style'
        
        # Ask for style
        keyboard = [
            [InlineKeyboardButton(
                get_locale(context).get_text("clothes_removal.style_realism", lang),
                callback_data="clothes_style_realism"
            )],
            [InlineKeyboardButton(
                get_locale(context).get_text("clothes_removal.style_lux", lang),
                callback_data="clothes_style_lux"
            )],
            [InlineKeyboardButton(
                get_locale(context).get_text("clothes_removal.style_anime", lang),
                callback_data="clothes_style_anime"
            )]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            get_locale(context).get_text("clothes_removal.choose_style", lang),
            reply_markup=reply_markup
        )
    
    except Exception as e:
        await update.message.reply_text(
            get_locale(context).get_text("errors.photo_processing", lang, error=str(e))
        )
        logger.error(f"Photo processing error for user {user_id}: {e}", exc_info=True)


async def handle_style_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, style: str):
    """
    Handle style selection and trigger processing.
    """
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    logger.info(f"User {user_id} selected style: {style}")
    
    # Show processing message
    await query.edit_message_text(
        get_locale(context).get_text("clothes_removal.processing", lang, style=style),
        parse_mode="Markdown"
    )
    
    # Call backend API
    try:
        target_image = context.user_data['target_image']
        
        async with httpx.AsyncClient(timeout=180.0) as client:
            response = await client.post(
                f"{settings.backend_api_url}/generate",
                json={
                    "mode": "clothes_removal",
                    "target_image": target_image,
                    "style": style
                }
            )
            
            response.raise_for_status()
            result = response.json()
            
            if result['status'] == 'done' and result['image']:
                # Send result image
                import base64
                import io
                
                image_data = base64.b64decode(result['image'])
                
                await query.message.reply_photo(
                    photo=io.BytesIO(image_data),
                    caption=get_locale(context).get_text("clothes_removal.success", lang, style=style),
                    parse_mode="Markdown"
                )
                
                logger.info(f"Successfully processed image for user {user_id}")
            
            else:
                # Error
                error_msg = result.get('error', 'Unknown error')
                await query.message.reply_text(
                    get_locale(context).get_text("errors.processing_failed", lang, error=error_msg)
                )
                logger.error(f"Processing failed for user {user_id}: {error_msg}")
    
    except httpx.TimeoutException:
        await query.message.reply_text(
            get_locale(context).get_text("errors.timeout_clothes", lang)
        )
        logger.error(f"Timeout for user {user_id}")
    
    except Exception as e:
        await query.message.reply_text(
            get_locale(context).get_text("errors.generic", lang, error=str(e))
        )
        logger.error(f"Error for user {user_id}: {e}", exc_info=True)
    
    finally:
        # Clean up
        active_users.discard(user_id)
        context.user_data.clear()
        
        # Show main menu
        await start.show_main_menu(update, context)
