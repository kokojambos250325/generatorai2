"""
Image handling utilities for Telegram Bot
"""
import base64
import logging
from io import BytesIO
from typing import Optional
from telegram import PhotoSize, File
from telegram_bot.config import get_bot_settings

logger = logging.getLogger(__name__)
settings = get_bot_settings()


async def download_image(photo: PhotoSize) -> Optional[bytes]:
    """
    Download image from Telegram
    
    Args:
        photo: Telegram PhotoSize object
    
    Returns:
        Image bytes or None if download fails
    """
    try:
        # Get file object
        file: File = await photo.get_file()
        
        # Check file size
        if file.file_size and file.file_size > settings.MAX_IMAGE_SIZE:
            logger.warning(f"Image too large: {file.file_size} bytes")
            return None
        
        # Download file
        image_bytes = await file.download_as_bytearray()
        
        logger.info(f"Downloaded image: {len(image_bytes)} bytes")
        return bytes(image_bytes)
    
    except Exception as e:
        logger.error(f"Failed to download image: {str(e)}")
        return None


def encode_image_to_base64(image_bytes: bytes) -> str:
    """
    Encode image bytes to base64 string
    
    Args:
        image_bytes: Raw image bytes
    
    Returns:
        Base64 encoded string
    """
    try:
        base64_string = base64.b64encode(image_bytes).decode('utf-8')
        logger.debug(f"Encoded image to base64: {len(base64_string)} chars")
        return base64_string
    
    except Exception as e:
        logger.error(f"Failed to encode image: {str(e)}")
        raise


def decode_base64_to_image(base64_string: str) -> bytes:
    """
    Decode base64 string to image bytes
    
    Args:
        base64_string: Base64 encoded string
    
    Returns:
        Raw image bytes
    """
    try:
        image_bytes = base64.b64decode(base64_string)
        logger.debug(f"Decoded base64 to image: {len(image_bytes)} bytes")
        return image_bytes
    
    except Exception as e:
        logger.error(f"Failed to decode image: {str(e)}")
        raise


def create_image_bytesio(image_bytes: bytes) -> BytesIO:
    """
    Create BytesIO object from image bytes for sending
    
    Args:
        image_bytes: Raw image bytes
    
    Returns:
        BytesIO object
    """
    return BytesIO(image_bytes)
