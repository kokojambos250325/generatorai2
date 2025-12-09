"""
Configuration management using environment variables
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment"""
    
    # Server configuration
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    
    # GPU Service
    gpu_service_url: str = "http://localhost:8002"
    request_timeout: int = 180
    
    # Logging
    log_level: str = "INFO"
    
    # API Metadata
    api_title: str = "AI Image Generation API"
    api_version: str = "1.0.0"
    
    # Validation limits (for future use)
    max_face_images: int = 5
    max_image_size_mb: int = 10
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
