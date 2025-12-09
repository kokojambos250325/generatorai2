"""
ID Generation
Generate unique task identifiers
"""
import time
import secrets


def generate_task_id() -> str:
    """
    Generate unique task ID
    
    Format: gpu_{timestamp}_{random}
    Example: gpu_1701234567_a3f9c2
    
    Returns:
        Unique task identifier string
    """
    timestamp = int(time.time())
    random_part = secrets.token_hex(3)  # 6 character hex string
    
    return f"gpu_{timestamp}_{random_part}"
