"""
Backend Configuration Management

Loads configuration from environment variables with sensible defaults.
"""

import os
from typing import Optional
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Server Configuration
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    
    # GPU Service Configuration
    gpu_service_url: str = "http://localhost:8001"
    request_timeout: int = 180  # seconds
    
    # Logging Configuration
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Generation Limits
    max_face_images: int = 5
    max_image_size_mb: int = 10
    
    # API Configuration
    api_title: str = "AI Image Generation API"
    api_version: str = "1.0.0"
    api_description: str = "Backend API for NSFW/realistic/anime image generation"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
