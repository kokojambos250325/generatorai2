"""
Hires Fix Generation Handler
High-resolution image generation with detail enhancement
"""

import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
import io

from telegram_bot.api_client import BackendAPIClient
from telegram_bot.config import get_bot_settings

logger = logging.getLogger(__name__)

# Conversation states
WAITING_HIRES_PROMPT = 1

async def handle_hires_fix(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle Hires Fix generation mode selection"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    logger.info(f"User {user_id} selected Hires Fix mode")
    
    message = (
        "🎨 **Hires Fix - Ultra Quality Generation**\n\n"
        "Создает изображение с улучшенной детализацией:\n"
        "• Базовое разрешение: 832x1216\n"
        "• Финальное: 1248x1824 (после upscale)\n"
        "• 4x-UltraSharp upscaler\n"
        "• Двойной проход для деталей\n\n"
        "📝 Отправь промпт для генерации.\n\n"
        "💡 **Примеры промптов:**\n"
        "```\n"
        "score_9, score_8_up, rating_explicit,\n"
        "1girl, solo, beautiful woman, 23 years old,\n"
        "long blonde hair, blue eyes, perfect face,\n"
        "athletic body, large breasts,\n"
        "standing, looking at viewer,\n"
        "wearing white dress,\n"
        "bedroom, natural lighting,\n"
        "photorealistic, 8k, detailed\n"
        "```\n\n"
        "Используй /cancel для отмены."
    )
    
    await query.message.reply_text(message, parse_mode='Markdown')
    
    return WAITING_HIRES_PROMPT


async def process_hires_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process prompt and generate with Hires Fix"""
    user_id = update.effective_user.id
    prompt = update.message.text.strip()
    
    if not prompt:
        await update.message.reply_text("❌ Промпт не может быть пустым. Попробуй еще раз или используй /cancel")
        return WAITING_HIRES_PROMPT
    
    logger.info(f"User {user_id} requested Hires Fix generation with prompt: {prompt[:50]}...")
    
    # Send status message
    status_msg = await update.message.reply_text(
        "⏳ Генерирую изображение с Hires Fix...\n\n"
        "Этот процесс займет ~2-3 минуты:\n"
        "1️⃣ Базовая генерация (832x1216)\n"
        "2️⃣ Upscale 4x (UltraSharp)\n"
        "3️⃣ Детализация (Hires Fix)\n"
        "4️⃣ Финальная обработка\n\n"
        "Пожалуйста, подожди..."
    )
    
    try:
        settings = get_bot_settings()
        client = BackendAPIClient()
        
        # Build negative prompt
        negative_prompt = (
            "embedding:bad_dream, embedding:easynegative, "
            "score_4, score_5, score_6, "
            "low quality, worst quality, bad anatomy, bad hands, "
            "missing fingers, extra fingers, blurry, cropped, "
            "jpeg artifacts, watermark, signature, text"
        )
        
        # Submit generation task using free mode (Hires Fix is done via workflow)
        task_id = await client.submit_task(
            mode="free",
            prompt=prompt
        )
        logger.info(f"Hires Fix task submitted: {task_id}")
        
        # Update status
        await status_msg.edit_text(
            f"✅ Задача создана: `{task_id}`\n\n"
            "⏳ Генерация началась...\n"
            "Это может занять 2-3 минуты.\n\n"
            "Используй /status для проверки прогресса.",
            parse_mode='Markdown'
        )
        
        # Poll for result
        max_attempts = 60  # 5 minutes (5 sec intervals)
        for attempt in range(max_attempts):
            await asyncio.sleep(5)
            
            result = await client.check_status(task_id)
            
            if result.get("status") == "completed":
                image_data = result.get("result", {}).get("image")
                
                if image_data:
                    # Decode base64 image
                    import base64
                    image_bytes = base64.b64decode(image_data)
                    
                    # Send image
                    await update.message.reply_photo(
                        photo=io.BytesIO(image_bytes),
                        caption=(
                            f"✨ **Hires Fix Generation Complete!**\n\n"
                            f"**Resolution:** 1248x1824\n"
                            f"**Prompt:** {prompt[:100]}...\n"
                            f"**Task ID:** `{task_id}`"
                        ),
                        parse_mode='Markdown'
                    )
                    
                    await status_msg.delete()
                    logger.info(f"Hires Fix generation completed for user {user_id}")
                    break
                else:
                    await status_msg.edit_text("❌ Ошибка: изображение не получено")
                    break
                    
            elif result.get("status") == "failed":
                error_msg = result.get("error", "Unknown error")
                await status_msg.edit_text(f"❌ Generation failed: {error_msg}")
                logger.error(f"Hires Fix generation failed: {error_msg}")
                break
                
            elif attempt % 6 == 0:  # Update every 30 seconds
                progress = min(100, int((attempt / max_attempts) * 100))
                await status_msg.edit_text(
                    f"⏳ Генерация в процессе... {progress}%\n\n"
                    f"Task ID: `{task_id}`",
                    parse_mode='Markdown'
                )
        else:
            await status_msg.edit_text(
                f"⏱ Timeout! Task ID: `{task_id}`\n\n"
                "Используй /status <task_id> для проверки.",
                parse_mode='Markdown'
            )
            logger.warning(f"Timeout waiting for task {task_id}")
            
    except Exception as e:
        error_msg = f"❌ Error: {str(e)}"
        await update.message.reply_text(error_msg)
        logger.error(f"Hires Fix generation error for user {user_id}: {e}", exc_info=True)
    
    return ConversationHandler.END


# Export conversation states
__all__ = ['handle_hires_fix', 'process_hires_prompt', 'WAITING_HIRES_PROMPT']
