"""
Configuration management using environment variables
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


# Style Configuration System
STYLE_CONFIG = {
    "noir": {
        "name": "Noir cinematic",
        "model": "cyberrealisticPony_v14.safetensors",
        "negative_prompt": "low quality, bad anatomy, jpeg artifacts, cartoon, anime, 3d, oversaturated, blurry, watermark, text, signature",
        "prompt_prefix": "noir style, high contrast black and white, cinematic lighting, film noir aesthetic, dramatic shadows, moody atmosphere, vintage photography, ",
        "default_quality_profile": "balanced",
        "lora": None,
        "lora_strength": None
    },
    "super_realism": {
        "name": "Ultra realistic",
        "model": "cyberrealisticPony_v14.safetensors",
        "negative_prompt": "low quality, bad anatomy, jpeg artifacts, cartoon, anime, 3d, painting, drawing, illustration, oversaturated, blurry",
        "prompt_prefix": "hyperrealistic, ultra detailed, 16k uhd, high quality photography, natural lighting, professional photo, dslr, sharp focus, realistic skin texture, ",
        "default_quality_profile": "high_quality",
        "lora": None,
        "lora_strength": None
    },
    "realism": {
        "name": "Photorealism",
        "model": "cyberrealisticPony_v14.safetensors",
        "negative_prompt": "low quality, bad anatomy, jpeg artifacts, cartoon, anime, 3d, blurry, watermark, text",
        "prompt_prefix": "photorealistic, detailed, 8k, professional photography, natural lighting, ",
        "default_quality_profile": "balanced",
        "lora": None,
        "lora_strength": None
    },
    "lux": {
        "name": "Luxury aesthetic",
        "model": "cyberrealisticPony_v14.safetensors",
        "negative_prompt": "low quality, bad anatomy, jpeg artifacts, cartoon, anime, cheap, low-end, blurry, watermark",
        "prompt_prefix": "luxury, elegant, professional photography, high-end aesthetic, sophisticated, glamorous, premium quality, ",
        "default_quality_profile": "high_quality",
        "lora": None,
        "lora_strength": None
    },
    "anime": {
        "name": "Anime style",
        "model": "cyberrealisticPony_v14.safetensors",
        "negative_prompt": "low quality, bad anatomy, jpeg artifacts, realistic, photo, 3d, blurry, watermark, text, signature, western cartoon",
        "prompt_prefix": "anime style, highly detailed anime art, vibrant colors, cel shaded, anime aesthetic, manga style, detailed illustration, ",
        "default_quality_profile": "balanced",
        "lora": None,
        "lora_strength": None
    },
    "chatgpt": {
        "name": "General purpose",
        "model": "cyberrealisticPony_v14.safetensors",
        "negative_prompt": "low quality, bad anatomy, blurry, watermark, text",
        "prompt_prefix": "",  # No enhancement for ChatGPT style
        "default_quality_profile": "balanced",
        "lora": None,
        "lora_strength": None
    }
}


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
