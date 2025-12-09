"""
Face-Consistent Generation Handler
"""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from telegram_bot.api_client import BackendAPIClient
from telegram_bot.utils.validators import validate_image_size, validate_prompt, is_valid_style
from telegram_bot.utils.image_handler import download_image, encode_image_to_base64, decode_base64_to_image, create_image_bytesio
from telegram_bot.config import get_bot_settings
import asyncio

logger = logging.getLogger(__name__)
settings = get_bot_settings()

# Conversation states
WAITING_FACE_CONSISTENT_PHOTO, WAITING_FACE_CONSISTENT_STYLE, WAITING_FACE_CONSISTENT_PROMPT = range(3)


async def handle_face_consistent(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Start face-consistent generation flow
    """
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        text="👤 *Генерация по лицу*\n\n"
             "Отправьте фото лица для создания изображения с сохранением черт лица.\n\n"
             "Для отмены используйте /cancel",
        parse_mode='Markdown'
    )
    
    return WAITING_FACE_CONSISTENT_PHOTO


async def process_face_consistent_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Process face photo
    """
    if not update.message.photo:
        await update.message.reply_text("❌ Please send a photo")
        return WAITING_FACE_CONSISTENT_PHOTO
    
    photo = update.message.photo[-1]
    
    # Validate image size
    is_valid, error = validate_image_size(photo.file_size)
    if not is_valid:
        await update.message.reply_text(error)
        return WAITING_FACE_CONSISTENT_PHOTO
    
    # Download image
    image_bytes = await download_image(photo)
    if not image_bytes:
        await update.message.reply_text("❌ Failed to download image")
        return WAITING_FACE_CONSISTENT_PHOTO
    
    # Store in context
    context.user_data['face_consistent_photo'] = encode_image_to_base64(image_bytes)
    
    # Ask for style
    keyboard = [
        [InlineKeyboardButton("📸 Реалистичный", callback_data="style_realistic")],
        [InlineKeyboardButton("🎨 Аниме", callback_data="style_anime")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "✅ Фото получено!\n\n"
        "Выберите стиль генерации:",
        reply_markup=reply_markup
    )
    
    return WAITING_FACE_CONSISTENT_STYLE


async def process_face_consistent_style(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Process style selection
    """
    query = update.callback_query
    await query.answer()
    
    style = query.data.replace("style_", "")
    context.user_data['face_consistent_style'] = style
    
    style_name = "Реалистичный" if style == "realistic" else "Аниме"
    
    await query.edit_message_text(
        f"✅ Стиль выбран: *{style_name}*\n\n"
        f"Теперь отправьте текстовое описание желаемого изображения на английском.\n\n"
        f"Пример: *beautiful woman in elegant dress, outdoor, sunset*",
        parse_mode='Markdown'
    )
    
    return WAITING_FACE_CONSISTENT_PROMPT


async def process_face_consistent_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Process prompt and submit task
    """
    prompt = update.message.text
    
    # Validate prompt
    is_valid, error = validate_prompt(prompt)
    if not is_valid:
        await update.message.reply_text(error)
        return WAITING_FACE_CONSISTENT_PROMPT
    
    face_image = context.user_data.get('face_consistent_photo')
    style = context.user_data.get('face_consistent_style')
    
    if not face_image or not style:
        await update.message.reply_text("❌ Missing data. Please start over with /start")
        return ConversationHandler.END
    
    # Send processing message
    processing_msg = await update.message.reply_text(
        "⏳ Submitting face-consistent generation task...\n"
        "This may take several minutes."
    )
    
    try:
        # Submit task to backend
        api_client = BackendAPIClient()
        task_id = await api_client.submit_task(
            mode="face_consistent",
            face_image=face_image,
            prompt=prompt,
            style=style
        )
        
        logger.info(f"Face-consistent task submitted: {task_id} (style={style})")
        
        await processing_msg.edit_text(
            f"✅ Task submitted!\n"
            f"Task ID: `{task_id}`\n"
            f"Style: {style}\n\n"
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
                        caption=f"✅ *Face-Consistent Generation Complete!*\n\n"
                                f"Style: {style}\n"
                                f"Prompt: _{prompt}_\n"
                                f"Task ID: `{task_id}`",
                        parse_mode='Markdown'
                    )
                    
                    await processing_msg.delete()
                    logger.info(f"Face-consistent task {task_id} completed")
                else:
                    await processing_msg.edit_text("❌ Error: No result image received")
                
                break
            
            elif status == "failed":
                error_msg = status_data.get("error", "Unknown error")
                await processing_msg.edit_text(
                    f"❌ Generation failed!\n"
                    f"Error: {error_msg}\n"
                    f"Task ID: `{task_id}`",
                    parse_mode='Markdown'
                )
                logger.error(f"Face-consistent task {task_id} failed: {error_msg}")
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
        logger.error(f"Error in face-consistent generation: {str(e)}")
        await processing_msg.edit_text(f"❌ Error: {str(e)}")
    
    finally:
        # Clean up context
        context.user_data.pop('face_consistent_photo', None)
        context.user_data.pop('face_consistent_style', None)
    
    return ConversationHandler.END
