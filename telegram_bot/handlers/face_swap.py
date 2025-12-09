"""
Face Swap Handler
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from telegram_bot.api_client import BackendAPIClient
from telegram_bot.utils.validators import validate_image_size
from telegram_bot.utils.image_handler import download_image, encode_image_to_base64, decode_base64_to_image, create_image_bytesio
from telegram_bot.config import get_bot_settings
import asyncio

logger = logging.getLogger(__name__)
settings = get_bot_settings()

# Conversation states
WAITING_FACE_SWAP_SOURCE, WAITING_FACE_SWAP_TARGET = range(2)


async def handle_face_swap(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Start face swap flow
    """
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        text="🔄 *Замена лица*\n\n"
             "Отправьте *исходное фото* (откуда взять лицо).\n\n"
             "Для отмены используйте /cancel",
        parse_mode='Markdown'
    )
    
    return WAITING_FACE_SWAP_SOURCE


async def process_face_swap_source(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Process source face image
    """
    if not update.message.photo:
        await update.message.reply_text("❌ Please send a photo")
        return WAITING_FACE_SWAP_SOURCE
    
    photo = update.message.photo[-1]  # Get highest resolution
    
    # Validate image size
    is_valid, error = validate_image_size(photo.file_size)
    if not is_valid:
        await update.message.reply_text(error)
        return WAITING_FACE_SWAP_SOURCE
    
    # Download image
    image_bytes = await download_image(photo)
    if not image_bytes:
        await update.message.reply_text("❌ Failed to download image")
        return WAITING_FACE_SWAP_SOURCE
    
    # Store in context
    context.user_data['face_swap_source'] = encode_image_to_base64(image_bytes)
    
    await update.message.reply_text(
        "✅ Исходное фото получено!\n\n"
        "Теперь отправьте *целевое фото* (куда вставить лицо).",
        parse_mode='Markdown'
    )
    
    return WAITING_FACE_SWAP_TARGET


async def process_face_swap_target(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Process target image and submit task
    """
    if not update.message.photo:
        await update.message.reply_text("❌ Please send a photo")
        return WAITING_FACE_SWAP_TARGET
    
    photo = update.message.photo[-1]
    
    # Validate image size
    is_valid, error = validate_image_size(photo.file_size)
    if not is_valid:
        await update.message.reply_text(error)
        return WAITING_FACE_SWAP_TARGET
    
    # Download image
    image_bytes = await download_image(photo)
    if not image_bytes:
        await update.message.reply_text("❌ Failed to download image")
        return WAITING_FACE_SWAP_TARGET
    
    target_image = encode_image_to_base64(image_bytes)
    source_image = context.user_data.get('face_swap_source')
    
    if not source_image:
        await update.message.reply_text("❌ Source image not found. Please start over with /start")
        return ConversationHandler.END
    
    # Send processing message
    processing_msg = await update.message.reply_text(
        "⏳ Submitting face swap task...\n"
        "This may take several minutes."
    )
    
    try:
        # Submit task to backend
        api_client = BackendAPIClient()
        task_id = await api_client.submit_task(
            mode="face_swap",
            face_image=source_image,
            image=target_image
        )
        
        logger.info(f"Face swap task submitted: {task_id}")
        
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
                        caption=f"✅ *Face Swap Complete!*\n\n"
                                f"Task ID: `{task_id}`",
                        parse_mode='Markdown'
                    )
                    
                    await processing_msg.delete()
                    logger.info(f"Face swap task {task_id} completed")
                else:
                    await processing_msg.edit_text("❌ Error: No result image received")
                
                break
            
            elif status == "failed":
                error_msg = status_data.get("error", "Unknown error")
                await processing_msg.edit_text(
                    f"❌ Face swap failed!\n"
                    f"Error: {error_msg}\n"
                    f"Task ID: `{task_id}`",
                    parse_mode='Markdown'
                )
                logger.error(f"Face swap task {task_id} failed: {error_msg}")
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
        logger.error(f"Error in face swap: {str(e)}")
        await processing_msg.edit_text(f"❌ Error: {str(e)}")
    
    finally:
        # Clean up context
        context.user_data.pop('face_swap_source', None)
    
    return ConversationHandler.END
