"""
Result Storage Management
Handles saving and retrieving generated images
"""
import os
import logging
import base64
from io import BytesIO
from typing import Optional
from PIL import Image

logger = logging.getLogger(__name__)

# Storage directory
STORAGE_DIR = os.getenv("RESULT_STORAGE_DIR", "/tmp/gpu_results")


def _ensure_storage_dir():
    """
    Create storage directory if it doesn't exist
    """
    if not os.path.exists(STORAGE_DIR):
        os.makedirs(STORAGE_DIR, exist_ok=True)
        logger.info(f"Created storage directory: {STORAGE_DIR}")


def save_image(task_id: str, image: Image.Image) -> str:
    """
    Save generated image to storage
    
    Args:
        task_id: Task identifier
        image: PIL Image to save
        
    Returns:
        Path to saved image
    """
    _ensure_storage_dir()
    
    file_path = os.path.join(STORAGE_DIR, f"{task_id}.png")
    
    image.save(file_path, format="PNG")
    logger.info(f"Saved result image: {file_path}")
    
    return file_path


def load_image(task_id: str) -> Optional[Image.Image]:
    """
    Load image from storage
    
    Args:
        task_id: Task identifier
        
    Returns:
        PIL Image or None if not found
    """
    file_path = os.path.join(STORAGE_DIR, f"{task_id}.png")
    
    if not os.path.exists(file_path):
        logger.warning(f"Image not found: {file_path}")
        return None
    
    image = Image.open(file_path)
    return image


def encode_base64(task_id: str) -> Optional[str]:
    """
    Load image and encode as base64
    
    Args:
        task_id: Task identifier
        
    Returns:
        Base64 encoded image string or None if not found
    """
    image = load_image(task_id)
    
    if not image:
        return None
    
    # Convert to base64
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    img_bytes = buffered.getvalue()
    img_base64 = base64.b64encode(img_bytes).decode("utf-8")
    
    return img_base64


def delete_image(task_id: str) -> bool:
    """
    Delete image from storage
    
    Args:
        task_id: Task identifier
        
    Returns:
        True if deleted, False if not found
    """
    file_path = os.path.join(STORAGE_DIR, f"{task_id}.png")
    
    if not os.path.exists(file_path):
        return False
    
    os.remove(file_path)
    logger.info(f"Deleted result image: {file_path}")
    
    return True


def cleanup_old_files(max_age_hours: int = 24) -> int:
    """
    Delete files older than max_age
    
    Args:
        max_age_hours: Maximum age in hours
        
    Returns:
        Number of files deleted
    """
    import time
    
    _ensure_storage_dir()
    
    now = time.time()
    deleted_count = 0
    
    for filename in os.listdir(STORAGE_DIR):
        file_path = os.path.join(STORAGE_DIR, filename)
        
        if not os.path.isfile(file_path):
            continue
        
        file_age = now - os.path.getmtime(file_path)
        file_age_hours = file_age / 3600
        
        if file_age_hours > max_age_hours:
            os.remove(file_path)
            deleted_count += 1
            logger.info(f"Deleted old file: {filename}")
    
    return deleted_count
