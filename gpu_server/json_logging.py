"""
JSON Structured Logging Utility

Provides structured logging with JSON-formatted events.
"""

import logging
import sys
from typing import Any, Dict, Optional


def setup_json_logging(
    service_name: str,
    log_file_path: str = None,
    log_level: str = "INFO"
) -> logging.Logger:
    """
    Setup JSON structured logging for a service.
    
    Args:
        service_name: Name of the service
        log_file_path: Optional path to log file
        log_level: Logging level (default: INFO)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(service_name)
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file_path:
        try:
            file_handler = logging.FileHandler(log_file_path)
            file_handler.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s')
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            logger.warning(f"Could not setup file logging: {e}")
    
    return logger


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
