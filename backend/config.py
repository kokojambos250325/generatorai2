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
        "negative_prompt": "score_6, score_5, score_4, worst quality, low quality, normal quality, lowres, bad anatomy, bad hands, signature, watermarks, ugly, imperfect eyes, skewed eyes, unnatural face, unnatural body, error, extra limb, missing limbs",
        "prompt_prefix": "score_9, score_8_up, score_7_up, noir style, high contrast black and white, cinematic lighting, film noir aesthetic, dramatic shadows, moody atmosphere, vintage photography, ",
        "default_quality_profile": "pony_balanced",
        "lora": None,
        "lora_strength": None
    },
    "super_realism": {
        "name": "Ultra realistic",
        "model": "cyberrealisticPony_v14.safetensors",
        "negative_prompt": "score_6, score_5, score_4, worst quality, low quality, normal quality, lowres, bad anatomy, bad hands, signature, watermarks, ugly, imperfect eyes, skewed eyes, unnatural face, unnatural body, error, extra limb, missing limbs",
        "prompt_prefix": "score_9, score_8_up, score_7_up, hyperrealistic, ultra detailed, high quality photography, natural lighting, professional photo, sharp focus, realistic skin texture, ",
        "default_quality_profile": "pony_high_quality",
        "lora": None,
        "lora_strength": None
    },
    "realism": {
        "name": "Photorealism",
        "model": "cyberrealisticPony_v14.safetensors",
        "negative_prompt": "score_6, score_5, score_4, worst quality, low quality, normal quality, lowres, bad anatomy, bad hands, signature, watermarks, ugly, imperfect eyes, skewed eyes, unnatural face, unnatural body, error, extra limb, missing limbs",
        "prompt_prefix": "score_9, score_8_up, score_7_up, ",
        "default_quality_profile": "pony_balanced",
        "lora": None,
        "lora_strength": None
    },
    "lux": {
        "name": "Luxury aesthetic",
        "model": "cyberrealisticPony_v14.safetensors",
        "negative_prompt": "score_6, score_5, score_4, worst quality, low quality, normal quality, lowres, bad anatomy, bad hands, signature, watermarks, ugly, imperfect eyes, skewed eyes, unnatural face, unnatural body, error, extra limb, missing limbs",
        "prompt_prefix": "score_9, score_8_up, score_7_up, luxury, elegant, professional photography, high-end aesthetic, sophisticated, glamorous, premium quality, ",
        "default_quality_profile": "pony_high_quality",
        "lora": None,
        "lora_strength": None
    },
    "anime": {
        "name": "Anime style",
        "model": "cyberrealisticPony_v14.safetensors",
        "negative_prompt": "score_6, score_5, score_4, worst quality, low quality, normal quality, lowres, bad anatomy, bad hands, signature, watermarks, ugly, imperfect eyes, skewed eyes, unnatural face, unnatural body, error, extra limb, missing limbs, realistic, photo",
        "prompt_prefix": "score_9, score_8_up, score_7_up, anime style, highly detailed anime art, vibrant colors, cel shaded, anime aesthetic, manga style, detailed illustration, ",
        "default_quality_profile": "pony_balanced",
        "lora": None,
        "lora_strength": None
    },
    "chatgpt": {
        "name": "General purpose",
        "model": "cyberrealisticPony_v14.safetensors",
        "negative_prompt": "score_6, score_5, score_4, worst quality, low quality, normal quality, lowres, bad anatomy, bad hands, signature, watermarks, ugly, imperfect eyes, skewed eyes, unnatural face, unnatural body, error, extra limb, missing limbs",
        "prompt_prefix": "score_9, score_8_up, score_7_up, ",
        "default_quality_profile": "pony_balanced",
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
