"""
Structured Logging System for Telegram Bot

Logs user actions, errors, generation history, and debug information.
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from logging.handlers import RotatingFileHandler


class BotLogger:
    """Structured logger for bot operations"""
    
    def __init__(self, logs_dir: str = "/workspace/logs/bot"):
        """
        Initialize bot logger
        
        Args:
            logs_dir: Directory for log files
        """
        self.logs_dir = Path(logs_dir)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup loggers
        self.actions_logger = self._setup_logger(
            "bot_actions",
            self.logs_dir / "bot_actions.log",
            level=logging.INFO
        )
        
        self.errors_logger = self._setup_logger(
            "bot_errors",
            self.logs_dir / "bot_errors.log",
            level=logging.ERROR
        )
        
        self.debug_logger = self._setup_logger(
            "bot_debug",
            self.logs_dir / "debug.log",
            level=logging.DEBUG
        )
        
        # History file path
        self.history_file = self.logs_dir / "generation_history.json"
        self._init_history_file()
    
    def _setup_logger(self, name: str, log_file: Path, level: int) -> logging.Logger:
        """Setup a logger with file rotation"""
        logger = logging.getLogger(name)
        logger.setLevel(level)
        
        # Remove existing handlers
        logger.handlers.clear()
        
        # File handler with rotation (10MB, keep 5 backups)
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        
        # Also log to console for development
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        return logger
    
    def _init_history_file(self):
        """Initialize history file if it doesn't exist"""
        if not self.history_file.exists():
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump([], f)
    
    def log_action(
        self,
        user_id: int,
        action: str,
        mode: Optional[str] = None,
        **kwargs
    ):
        """
        Log user action
        
        Args:
            user_id: Telegram user ID
            action: Action name (e.g., "start", "free_generation", "style_selected")
            mode: Generation mode (free, nsfw_face, clothes_removal)
            **kwargs: Additional context
        """
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        
        log_entry = f"[{timestamp}] USER {user_id} | {action}"
        if mode:
            log_entry += f" | MODE={mode}"
        
        for key, value in kwargs.items():
            if isinstance(value, str) and len(value) > 100:
                value = value[:100] + "..."
            log_entry += f" | {key}={value}"
        
        self.actions_logger.info(log_entry)
    
    def log_generation(
        self,
        user_id: int,
        mode: str,
        prompt: Optional[str] = None,
        style: Optional[str] = None,
        status: str = "success",
        time_seconds: Optional[float] = None,
        error: Optional[str] = None,
        **kwargs
    ):
        """
        Log generation request and result
        
        Args:
            user_id: Telegram user ID
            mode: Generation mode
            prompt: User prompt (truncated if too long)
            style: Selected style
            status: success, failed, timeout
            time_seconds: Generation time
            error: Error message if failed
            **kwargs: Additional context
        """
        timestamp = datetime.utcnow().isoformat()
        
        # Log to actions log
        log_entry = f"[{timestamp}] USER {user_id} | {mode.upper()} |"
        if prompt:
            prompt_short = prompt[:50] + "..." if len(prompt) > 50 else prompt
            log_entry += f' prompt="{prompt_short}"'
        if style:
            log_entry += f" | style={style}"
        log_entry += f" | status={status}"
        if time_seconds:
            log_entry += f" | time={time_seconds:.1f}s"
        if error:
            log_entry += f" | error={error[:100]}"
        
        self.actions_logger.info(log_entry)
        
        # Add to history JSON
        history_entry = {
            "timestamp": timestamp,
            "user_id": user_id,
            "mode": mode,
            "prompt": prompt[:200] if prompt else None,  # Truncate long prompts
            "style": style,
            "status": status,
            "time_seconds": time_seconds,
            "error": error[:500] if error else None,
            **kwargs
        }
        
        self._append_to_history(history_entry)
    
    def log_error(
        self,
        user_id: Optional[int],
        error_type: str,
        error_message: str,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Log error
        
        Args:
            user_id: Telegram user ID (if available)
            error_type: Type of error (backend_error, validation_error, etc.)
            error_message: Error message
            context: Additional context
        """
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        
        log_entry = f"[{timestamp}]"
        if user_id:
            log_entry += f" USER {user_id}"
        log_entry += f" | ERROR={error_type} | {error_message}"
        
        if context:
            for key, value in context.items():
                log_entry += f" | {key}={value}"
        
        self.errors_logger.error(log_entry)
    
    def log_debug(self, message: str, **kwargs):
        """
        Log debug information
        
        Args:
            message: Debug message
            **kwargs: Additional context
        """
        log_entry = message
        if kwargs:
            for key, value in kwargs.items():
                log_entry += f" | {key}={value}"
        
        self.debug_logger.debug(log_entry)
    
    def _append_to_history(self, entry: Dict[str, Any]):
        """Append entry to history JSON file"""
        try:
            # Read existing history
            if self.history_file.exists():
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            else:
                history = []
            
            # Append new entry
            history.append(entry)
            
            # Keep only last 1000 entries
            if len(history) > 1000:
                history = history[-1000:]
            
            # Write back
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
        
        except Exception as e:
            self.errors_logger.error(f"Failed to write to history: {e}")


# Global logger instance
_bot_logger: Optional[BotLogger] = None


def get_bot_logger(logs_dir: str = "/workspace/logs/bot") -> BotLogger:
    """Get or create global bot logger instance"""
    global _bot_logger
    if _bot_logger is None:
        _bot_logger = BotLogger(logs_dir)
    return _bot_logger

