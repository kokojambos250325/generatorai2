"""
Status Check Handler
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram_bot.api_client import BackendAPIClient
from telegram_bot.utils.image_handler import decode_base64_to_image, create_image_bytesio

logger = logging.getLogger(__name__)


async def handle_status_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle status check button
    """
    query = update.callback_query
    await query.answer()
    
    # Check if user has active task
    user_id = update.effective_user.id
    active_task = context.user_data.get('active_task_id')
    
    if not active_task:
        await query.edit_message_text(
            "ℹ️ У вас нет активных задач.\n\n"
            "Используйте меню ниже для создания новой генерации.",
            reply_markup=query.message.reply_markup
        )
        return
    
    try:
        api_client = BackendAPIClient()
        status_data = await api_client.check_status(active_task)
        
        status = status_data.get("status")
        progress = status_data.get("progress", 0)
        message = status_data.get("message", "")
        
        if status == "pending":
            status_text = f"📋 *Task Status*\n\n" \
                         f"Task ID: `{active_task}`\n" \
                         f"Status: ⏳ Pending\n" \
                         f"Progress: {progress}%\n\n" \
                         f"Your task is in queue..."
        
        elif status == "processing":
            status_text = f"📋 *Task Status*\n\n" \
                         f"Task ID: `{active_task}`\n" \
                         f"Status: 🔄 Processing\n" \
                         f"Progress: {progress}%\n" \
                         f"Message: {message}"
        
        elif status == "completed":
            result_image_base64 = status_data.get("result")
            
            if result_image_base64:
                image_bytes = decode_base64_to_image(result_image_base64)
                image_file = create_image_bytesio(image_bytes)
                
                await query.message.reply_photo(
                    photo=image_file,
                    caption=f"✅ *Task Completed!*\n\nTask ID: `{active_task}`",
                    parse_mode='Markdown'
                )
                
                # Clear active task
                context.user_data.pop('active_task_id', None)
                
                status_text = "✅ Task completed! Image sent above."
            else:
                status_text = f"📋 *Task Status*\n\n" \
                             f"Task ID: `{active_task}`\n" \
                             f"Status: ✅ Completed\n" \
                             f"⚠️ No result image available"
        
        elif status == "failed":
            error_msg = status_data.get("error", "Unknown error")
            status_text = f"📋 *Task Status*\n\n" \
                         f"Task ID: `{active_task}`\n" \
                         f"Status: ❌ Failed\n" \
                         f"Error: {error_msg}"
            
            # Clear active task
            context.user_data.pop('active_task_id', None)
        
        else:
            status_text = f"📋 *Task Status*\n\n" \
                         f"Task ID: `{active_task}`\n" \
                         f"Status: {status}\n" \
                         f"Progress: {progress}%"
        
        await query.edit_message_text(
            status_text,
            parse_mode='Markdown',
            reply_markup=query.message.reply_markup
        )
    
    except Exception as e:
        logger.error(f"Error checking status: {str(e)}")
        await query.edit_message_text(
            f"❌ Error checking status:\n{str(e)}",
            reply_markup=query.message.reply_markup
        )


async def handle_status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /status command with task ID
    Usage: /status <task_id>
    """
    if not context.args:
        await update.message.reply_text(
            "❌ Usage: /status <task_id>\n\n"
            "Example: `/status task_12345678`",
            parse_mode='Markdown'
        )
        return
    
    task_id = context.args[0]
    
    try:
        api_client = BackendAPIClient()
        status_data = await api_client.check_status(task_id)
        
        status = status_data.get("status")
        progress = status_data.get("progress", 0)
        message = status_data.get("message", "")
        
        status_text = f"📋 *Task Status*\n\n" \
                     f"Task ID: `{task_id}`\n" \
                     f"Status: {status}\n" \
                     f"Progress: {progress}%"
        
        if message:
            status_text += f"\nMessage: {message}"
        
        if status == "completed":
            result_image_base64 = status_data.get("result")
            
            if result_image_base64:
                image_bytes = decode_base64_to_image(result_image_base64)
                image_file = create_image_bytesio(image_bytes)
                
                await update.message.reply_photo(
                    photo=image_file,
                    caption=status_text,
                    parse_mode='Markdown'
                )
                return
        
        elif status == "failed":
            error_msg = status_data.get("error", "Unknown error")
            status_text += f"\n❌ Error: {error_msg}"
        
        await update.message.reply_text(status_text, parse_mode='Markdown')
    
    except Exception as e:
        logger.error(f"Error checking status for task {task_id}: {str(e)}")
        await update.message.reply_text(f"❌ Error: {str(e)}")
