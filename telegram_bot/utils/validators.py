"""
Input validators for Telegram Bot
"""
import logging
from typing import Optional
from telegram_bot.config import get_bot_settings

logger = logging.getLogger(__name__)
settings = get_bot_settings()


def validate_prompt(prompt: str) -> tuple[bool, Optional[str]]:
    """
    Validate text prompt
    
    Args:
        prompt: User text prompt
    
    Returns:
        (is_valid, error_message)
    """
    if not prompt or not prompt.strip():
        return False, "❌ Prompt cannot be empty"
    
    if len(prompt) > 1000:
        return False, "❌ Prompt too long (max 1000 characters)"
    
    if len(prompt) < 3:
        return False, "❌ Prompt too short (min 3 characters)"
    
    return True, None


def validate_image_size(file_size: int) -> tuple[bool, Optional[str]]:
    """
    Validate image file size
    
    Args:
        file_size: File size in bytes
    
    Returns:
        (is_valid, error_message)
    """
    if file_size > settings.MAX_IMAGE_SIZE:
        max_mb = settings.MAX_IMAGE_SIZE / (1024 * 1024)
        return False, f"❌ Image too large (max {max_mb:.1f} MB)"
    
    if file_size < 1024:  # Less than 1 KB
        return False, "❌ Image too small (min 1 KB)"
    
    return True, None


def validate_age_confirmation(age: str) -> tuple[bool, Optional[str]]:
    """
    Validate age confirmation for NSFW content
    
    Args:
        age: User age input
    
    Returns:
        (is_valid, error_message)
    """
    try:
        age_int = int(age)
        if age_int < settings.MIN_AGE_FOR_NSFW:
            return False, f"❌ You must be at least {settings.MIN_AGE_FOR_NSFW} years old to use this feature"
        if age_int > 120:
            return False, "❌ Invalid age"
        return True, None
    except ValueError:
        return False, "❌ Please enter a valid age (number)"


def is_valid_style(style: str) -> bool:
    """
    Check if style is valid
    
    Args:
        style: Style name
    
    Returns:
        True if valid
    """
    valid_styles = ["realistic", "anime"]
    return style.lower() in valid_styles
