"""
JSON Structured Logging Utility

Provides structured logging with JSON-formatted events.
"""

import logging
from typing import Any, Dict, Optional


def log_event(
    logger: logging.Logger,
    level: str,
    event: str,
    message: str,
    **extra_fields: Any
) -> None:
    """
    Log structured event with extra fields.
    
    Args:
        logger: Logger instance
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        event: Event type/name
        message: Log message
        **extra_fields: Additional fields to include in log
    """
    # Build log message with event type
    log_msg = f"{message}"
    
    # Add extra fields if any
    if extra_fields:
        fields_str = ", ".join(f"{k}={v}" for k, v in extra_fields.items() if v is not None)
        if fields_str:
            log_msg += f" [{fields_str}]"
    
    # Log at appropriate level
    log_level = getattr(logging, level.upper(), logging.INFO)
    logger.log(log_level, log_msg)
