"""
Validation Utilities

Common validation functions for request data.
"""

import re
from typing import Optional


def validate_prompt(prompt: str, min_length: int = 1, max_length: int = 2000) -> tuple[bool, Optional[str]]:
    """
    Validate text prompt.
    
    Args:
        prompt: Text prompt to validate
        min_length: Minimum length
        max_length: Maximum length
    
    Returns:
        tuple: (is_valid, error_message)
    """
    prompt = prompt.strip()
    
    if len(prompt) < min_length:
        return False, f"Prompt must be at least {min_length} characters"
    
    if len(prompt) > max_length:
        return False, f"Prompt must not exceed {max_length} characters"
    
    return True, None


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing invalid characters.
    
    Args:
        filename: Original filename
    
    Returns:
        str: Sanitized filename
    """
    # Remove invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '', filename)
    
    # Limit length
    if len(sanitized) > 255:
        name, ext = sanitized.rsplit('.', 1) if '.' in sanitized else (sanitized, '')
        sanitized = name[:250] + ('.' + ext if ext else '')
    
    return sanitized or 'unnamed'
