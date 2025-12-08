"""
Image Utilities

Handles image encoding, decoding, and validation.
"""

import base64
import io
from PIL import Image
from typing import Union


def encode_image_to_base64(image: Union[Image.Image, bytes]) -> str:
    """
    Encode PIL Image or bytes to base64 string.
    
    Args:
        image: PIL Image or bytes
    
    Returns:
        str: Base64 encoded image string
    """
    if isinstance(image, Image.Image):
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        image_bytes = buffer.getvalue()
    else:
        image_bytes = image
    
    return base64.b64encode(image_bytes).decode('utf-8')


def decode_base64_to_image(base64_string: str) -> Image.Image:
    """
    Decode base64 string to PIL Image.
    
    Args:
        base64_string: Base64 encoded image
    
    Returns:
        Image.Image: PIL Image object
    """
    # Remove data URI prefix if present
    if base64_string.startswith('data:image/'):
        base64_string = base64_string.split(',', 1)[1]
    
    image_bytes = base64.b64decode(base64_string)
    image = Image.open(io.BytesIO(image_bytes))
    
    return image


def validate_image_size(base64_string: str, max_size_mb: int = 10) -> bool:
    """
    Validate image size doesn't exceed limit.
    
    Args:
        base64_string: Base64 encoded image
        max_size_mb: Maximum size in megabytes
    
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        image_bytes = base64.b64decode(base64_string.split(',', 1)[-1])
        size_mb = len(image_bytes) / (1024 * 1024)
        return size_mb <= max_size_mb
    except:
        return False
