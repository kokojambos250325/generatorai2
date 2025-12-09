"""
Clothes Removal Handler (NSFW - 18+)
"""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from telegram_bot.api_client import BackendAPIClient
from telegram_bot.utils.validators import validate_image_size, validate_age_confirmation
from telegram_bot.utils.image_handler import download_image, encode_image_to_base64, decode_base64_to_image, create_image_bytesio
from telegram_bot.config import get_bot_settings
import asyncio

logger = logging.getLogger(__name__)
settings = get_bot_settings()

# Conversation states
WAITING_UNDRESS_AGE, WAITING_UNDRESS_PHOTO = range(2)


async def handle_clothes_removal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Start clothes removal flow with age verification
    """
    query = update.callback_query
    await query.answer()
    
    if settings.REQUIRE_AGE_VERIFICATION:
        keyboard = [
            [InlineKeyboardButton("✅ Мне есть 18+", callback_data="age_confirmed")],
            [InlineKeyboardButton("❌ Отмена", callback_data="age_declined")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text="👗 *Удалить одежду* (18+)\n\n"
                 "⚠️ *ВНИМАНИЕ*: Этот режим создает контент для взрослых (NSFW).\n\n"
                 f"Подтвердите, что вам есть {settings.MIN_AGE_FOR_NSFW} лет.",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
        return WAITING_UNDRESS_AGE
    else:
        return await start_undress_flow(update, context)


async def process_age_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Process age confirmation
    """
    query = update.callback_query
    await query.answer()
    
    if query.data == "age_confirmed":
        context.user_data['age_verified'] = True
        return await start_undress_flow(update, context)
    else:
        await query.edit_message_text(
            "❌ Для использования этой функции необходимо быть старше 18 лет.\n\n"
            "Используйте /start для возврата в главное меню."
        )
        return ConversationHandler.END


async def start_undress_flow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Start undress photo collection
    """
    if update.callback_query:
        await update.callback_query.edit_message_text(
            text="👗 *Удалить одежду*\n\n"
                 "Отправьте фото человека.\n\n"
                 "⚠️ Лицо будет сохранено на результирующем изображении.\n\n"
                 "Для отмены используйте /cancel",
            parse_mode='Markdown'
        )
    
    return WAITING_UNDRESS_PHOTO


async def process_undress_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Process photo and submit undress task
    """
    # Verify age
    if settings.REQUIRE_AGE_VERIFICATION and not context.user_data.get('age_verified'):
        await update.message.reply_text("❌ Age verification required. Please start over with /start")
        return ConversationHandler.END
    
    if not update.message.photo:
        await update.message.reply_text("❌ Please send a photo")
        return WAITING_UNDRESS_PHOTO
    
    photo = update.message.photo[-1]
    
    # Validate image size
    is_valid, error = validate_image_size(photo.file_size)
    if not is_valid:
        await update.message.reply_text(error)
        return WAITING_UNDRESS_PHOTO
    
    # Download image
    image_bytes = await download_image(photo)
    if not image_bytes:
        await update.message.reply_text("❌ Failed to download image")
        return WAITING_UNDRESS_PHOTO
    
    image_base64 = encode_image_to_base64(image_bytes)
    
    # Send processing message
    processing_msg = await update.message.reply_text(
        "⏳ Submitting clothes removal task...\n"
        "⚠️ NSFW content generation in progress.\n"
        "This may take several minutes."
    )
    
    try:
        # Submit task to backend
        api_client = BackendAPIClient()
        task_id = await api_client.submit_task(
            mode="clothes_removal",
            image=image_base64
        )
        
        logger.info(f"Clothes removal task submitted: {task_id}")
        
        await processing_msg.edit_text(
            f"✅ Task submitted!\n"
            f"Task ID: `{task_id}`\n\n"
            f"⏳ Processing... Please wait.",
            parse_mode='Markdown'
        )
        
        # Poll for result
        poll_count = 0
        while poll_count < settings.MAX_POLL_ATTEMPTS:
            await asyncio.sleep(settings.STATUS_POLL_INTERVAL)
            poll_count += 1
            
            status_data = await api_client.check_status(task_id)
            status = status_data.get("status")
            
            if poll_count % 5 == 0:
                progress = status_data.get("progress", 0)
                await processing_msg.edit_text(
                    f"⏳ Processing... ({progress}%)\n"
                    f"Task ID: `{task_id}`",
                    parse_mode='Markdown'
                )
            
            if status == "completed":
                result_image_base64 = status_data.get("result")
                
                if result_image_base64:
                    image_bytes = decode_base64_to_image(result_image_base64)
                    image_file = create_image_bytesio(image_bytes)
                    
                    await update.message.reply_photo(
                        photo=image_file,
                        caption=f"✅ *Clothes Removal Complete!*\n\n"
                                f"⚠️ NSFW Content (18+)\n"
                                f"Task ID: `{task_id}`",
                        parse_mode='Markdown',
                        has_spoiler=True  # Blur image by default
                    )
                    
                    await processing_msg.delete()
                    logger.info(f"Clothes removal task {task_id} completed")
                else:
                    await processing_msg.edit_text("❌ Error: No result image received")
                
                break
            
            elif status == "failed":
                error_msg = status_data.get("error", "Unknown error")
                await processing_msg.edit_text(
                    f"❌ Clothes removal failed!\n"
                    f"Error: {error_msg}\n"
                    f"Task ID: `{task_id}`",
                    parse_mode='Markdown'
                )
                logger.error(f"Clothes removal task {task_id} failed: {error_msg}")
                break
        else:
            # Timeout
            await processing_msg.edit_text(
                f"⏰ Task timeout!\n"
                f"Task ID: `{task_id}`\n\n"
                f"Use /status {task_id} to check later.",
                parse_mode='Markdown'
            )
    
    except Exception as e:
        logger.error(f"Error in clothes removal: {str(e)}")
        await processing_msg.edit_text(f"❌ Error: {str(e)}")
    
    finally:
        # Clean up context
        context.user_data.pop('age_verified', None)
    
    return ConversationHandler.END
