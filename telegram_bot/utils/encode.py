"""
Image Encoding Utilities

Converts Telegram photos to base64 for API transmission.
"""

import base64
import io
from PIL import Image


async def photo_to_base64(photo_bytes: bytes) -> str:
    """
    Convert photo bytes to base64 string.
    
    Args:
        photo_bytes: Raw photo bytes from Telegram
    
    Returns:
        str: Base64 encoded image
    """
    # Open image with Pillow
    image = Image.open(io.BytesIO(photo_bytes))
    
    # Convert to RGB if needed (remove alpha channel)
    if image.mode in ('RGBA', 'LA', 'P'):
        background = Image.new('RGB', image.size, (255, 255, 255))
        if image.mode == 'P':
            image = image.convert('RGBA')
        background.paste(image, mask=image.split()[-1] if image.mode in ('RGBA', 'LA') else None)
        image = background
    
    # Save to bytes buffer
    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    image_bytes = buffer.getvalue()
    
    # Encode to base64
    base64_str = base64.b64encode(image_bytes).decode('utf-8')
    
    return base64_str
