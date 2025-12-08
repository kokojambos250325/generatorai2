"""
Telegram Bot Configuration

Loads settings from environment variables.
"""

import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Bot settings"""
    
    # Telegram Configuration
    telegram_bot_token: str
    
    # Backend Configuration
    backend_api_url: str
    
    # Limits
    max_image_size_mb: int = 10
    conversation_timeout: int = 300  # 5 minutes
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
