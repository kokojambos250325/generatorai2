"""
Centralized Error Handling for Telegram Bot

Provides user-friendly error messages in multiple languages.
"""

import logging
from typing import Optional
from telegram import Update
from telegram.ext import ContextTypes

from telegram_bot.utils.locale import LocaleManager
from telegram_bot.utils.logger import get_bot_logger

logger = logging.getLogger(__name__)
bot_logger = get_bot_logger()


class BotError(Exception):
    """Base exception for bot errors"""
    def __init__(self, message: str, error_key: str = "generic", user_id: Optional[int] = None):
        self.message = message
        self.error_key = error_key
        self.user_id = user_id
        super().__init__(message)


async def handle_error(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    error: Exception,
    user_lang: Optional[str] = None
) -> str:
    """
    Handle error and return user-friendly message
    
    Args:
        update: Telegram update
        context: Bot context
        error: Exception that occurred
        user_lang: User language code
    
    Returns:
        Error message in user's language
    """
    user_id = update.effective_user.id if update.effective_user else None
    
    # Get locale manager
    locale_manager = context.bot_data.get('locale_manager')
    if not locale_manager:
        return "❌ An error occurred. Please try again or use /start to return to the main menu."
    
    # Get user language
    if not user_lang and user_id:
        user_lang = locale_manager.get_user_language(user_id)
    if not user_lang:
        user_lang = "en"
    
    # Determine error type and get message
    error_message = _get_error_message(error, locale_manager, user_lang)
    
    # Log error
    bot_logger.log_error(
        user_id=user_id,
        error_type=type(error).__name__,
        error_message=str(error),
        context={"error_key": getattr(error, 'error_key', 'unknown')}
    )
    
    return error_message


def _get_error_message(
    error: Exception,
    locale_manager: LocaleManager,
    lang: str
) -> str:
    """Get localized error message"""
    
    # Check if it's a known BotError
    if isinstance(error, BotError):
        error_key = error.error_key
    else:
        # Map exception types to error keys
        error_type = type(error).__name__
        error_str = str(error).lower()
        
        if "timeout" in error_str or "TimeoutException" in error_type:
            error_key = "timeout"
        elif "connection" in error_str or "connect" in error_str:
            error_key = "backend_unavailable"
        elif "photo" in error_str or "image" in error_str:
            if "too large" in error_str or "size" in error_str:
                error_key = "photo_too_large"
            elif "too small" in error_str or "resolution" in error_str:
                error_key = "photo_too_small"
            elif "invalid" in error_str or "format" in error_str:
                error_key = "invalid_photo"
            else:
                error_key = "invalid_photo"
        elif "prompt" in error_str:
            error_key = "no_prompt"
        elif "style" in error_str:
            error_key = "invalid_style"
        elif "face" in error_str and "not" in error_str:
            error_key = "no_face_detected"
        else:
            error_key = "generic"
    
    # Get localized message
    try:
        message = locale_manager.get_text(f"errors.{error_key}", lang)
        
        # Format message with error details if needed
        if error_key == "photo_too_large":
            max_mb = 10  # Default max size
            message = message.format(max_mb=max_mb)
        elif error_key == "processing_failed":
            error_detail = str(error)[:200]  # Truncate long errors
            message = message.format(error=error_detail)
        
        return message
    
    except Exception as e:
        logger.error(f"Failed to get error message: {e}")
        return locale_manager.get_text("errors.generic", lang)


async def send_error_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    error: Exception,
    user_lang: Optional[str] = None
):
    """
    Handle error and send message to user
    
    Args:
        update: Telegram update
        context: Bot context
        error: Exception that occurred
        user_lang: User language code
    """
    error_message = await handle_error(update, context, error, user_lang)
    
    try:
        if update.message:
            await update.message.reply_text(error_message)
        elif update.callback_query:
            await update.callback_query.answer(error_message, show_alert=True)
    except Exception as e:
        logger.error(f"Failed to send error message: {e}")


# Specific error classes
class BackendError(BotError):
    """Backend API error"""
    def __init__(self, message: str, user_id: Optional[int] = None):
        super().__init__(message, "backend_unavailable", user_id)


class TimeoutError(BotError):
    """Generation timeout error"""
    def __init__(self, message: str = "Generation timeout", user_id: Optional[int] = None):
        super().__init__(message, "timeout", user_id)


class ValidationError(BotError):
    """Validation error"""
    def __init__(self, message: str, error_key: str = "generic", user_id: Optional[int] = None):
        super().__init__(message, error_key, user_id)


class PhotoValidationError(ValidationError):
    """Photo validation error"""
    def __init__(self, message: str, error_key: str = "invalid_photo", user_id: Optional[int] = None):
        super().__init__(message, error_key, user_id)

