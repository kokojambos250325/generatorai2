"""
Input validators for Telegram Bot
"""
import logging
import io
from typing import Optional, Tuple
from PIL import Image
from telegram_bot.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def validate_prompt(prompt: str, min_length: int = 3, max_length: int = 2000) -> Tuple[bool, Optional[str]]:
    """
    Validate text prompt
    
    Args:
        prompt: User text prompt
        min_length: Minimum prompt length
        max_length: Maximum prompt length
    
    Returns:
        (is_valid, error_message)
    """
    if not prompt or not prompt.strip():
        return False, "❌ Prompt cannot be empty"
    
    if len(prompt) > max_length:
        return False, f"❌ Prompt too long (max {max_length} characters)"
    
    if len(prompt) < min_length:
        return False, f"❌ Prompt too short (min {min_length} characters)"
    
    return True, None


def validate_image_size(file_size: int, max_mb: int = 10) -> Tuple[bool, Optional[str]]:
    """
    Validate image file size
    
    Args:
        file_size: File size in bytes
        max_mb: Maximum size in MB
    
    Returns:
        (is_valid, error_message)
    """
    max_bytes = max_mb * 1024 * 1024
    if file_size > max_bytes:
        return False, f"❌ Image too large (max {max_mb} MB)"
    
    if file_size < 1024:  # Less than 1 KB
        return False, "❌ Image too small (min 1 KB)"
    
    return True, None


def validate_image_format(image_bytes: bytes) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Validate image format
    
    Args:
        image_bytes: Image file bytes
    
    Returns:
        (is_valid, error_message, format)
    """
    try:
        image = Image.open(io.BytesIO(image_bytes))
        format_name = image.format
        
        # Check if format is supported
        if format_name not in ['JPEG', 'PNG', 'JPG']:
            return False, "❌ Unsupported image format. Please use JPG or PNG", None
        
        return True, None, format_name
    
    except Exception as e:
        logger.error(f"Image format validation error: {e}")
        return False, "❌ Invalid image file. Please send a valid JPG or PNG image", None


def validate_image_resolution(
    image_bytes: bytes,
    min_width: int = 512,
    min_height: int = 512
) -> Tuple[bool, Optional[str], Optional[Tuple[int, int]]]:
    """
    Validate image resolution
    
    Args:
        image_bytes: Image file bytes
        min_width: Minimum width in pixels
        min_height: Minimum height in pixels
    
    Returns:
        (is_valid, error_message, (width, height))
    """
    try:
        image = Image.open(io.BytesIO(image_bytes))
        width, height = image.size
        
        if width < min_width or height < min_height:
            return False, f"❌ Image resolution too low. Minimum: {min_width}x{min_height} pixels", (width, height)
        
        return True, None, (width, height)
    
    except Exception as e:
        logger.error(f"Image resolution validation error: {e}")
        return False, "❌ Failed to read image dimensions", None


def validate_photo(
    photo_file: bytes,
    max_mb: int = 10,
    min_width: int = 512,
    min_height: int = 512,
    require_face: bool = False,
    require_person: bool = False
) -> Tuple[bool, Optional[str], Optional[dict]]:
    """
    Comprehensive photo validation
    
    Args:
        photo_file: Photo file bytes
        max_mb: Maximum file size in MB
        min_width: Minimum width
        min_height: Minimum height
        require_face: Whether face detection is required
        require_person: Whether person detection is required
    
    Returns:
        (is_valid, error_message, metadata)
    """
    # Validate size
    file_size = len(photo_file)
    is_valid_size, size_error = validate_image_size(file_size, max_mb)
    if not is_valid_size:
        return False, size_error, None
    
    # Validate format
    is_valid_format, format_error, image_format = validate_image_format(photo_file)
    if not is_valid_format:
        return False, format_error, None
    
    # Validate resolution
    is_valid_res, res_error, dimensions = validate_image_resolution(
        photo_file, min_width, min_height
    )
    if not is_valid_res:
        return False, res_error, None
    
    metadata = {
        "size_bytes": file_size,
        "format": image_format,
        "width": dimensions[0],
        "height": dimensions[1]
    }
    
    # Note: Face and person detection would require additional libraries
    # (e.g., face_recognition, opencv). For now, we just validate basic properties.
    # These checks can be added later if needed.
    
    if require_face:
        # TODO: Add face detection using face_recognition or similar
        logger.warning("Face detection not implemented yet")
    
    if require_person:
        # TODO: Add person detection using opencv or similar
        logger.warning("Person detection not implemented yet")
    
    return True, None, metadata




def is_valid_style(style: str, mode: str = "free") -> bool:
    """
    Check if style is valid for given mode
    
    Args:
        style: Style name
        mode: Generation mode (free, nsfw_face, clothes_removal)
    
    Returns:
        True if valid
    """
    if mode == "free":
        valid_styles = ["noir", "super_realism", "anime", "realism", "lux", "chatgpt"]
    elif mode == "nsfw_face":
        valid_styles = ["realism", "lux", "anime"]
    elif mode == "clothes_removal":
        valid_styles = ["realism", "lux", "anime"]
    else:
        return False
    
    return style.lower() in valid_styles
