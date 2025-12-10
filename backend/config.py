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
        "negative_prompt": (
            "low quality, bad anatomy, jpeg artifacts, cartoon, anime, 3d, "
            "overexposed, underexposed, extra limbs, bad hands, bad face"
        ),
        "prompt_prefix": (
            "noir style, high contrast black and white, cinematic lighting, film grain, "
            "moody atmosphere, dramatic shadows, "
        ),
        "default_quality_profile": "balanced",
        "default_sampler": "euler",
        "default_steps": 26,
        "default_cfg": 7.5,
        "default_resolution": {"width": 832, "height": 1216}
    },
    "super_realism": {
        "name": "Super Realism",
        "model": "cyberrealisticPony_v14.safetensors",
        "negative_prompt": (
            "cartoon, anime, 3d, illustration, painting, cgi, lowres, bad anatomy, "
            "bad hands, bad face, blurry, out of focus, plastic skin"
        ),
        "prompt_prefix": (
            "ultra realistic, 8k, detailed skin texture, realistic lighting, "
            "photorealistic, sharp focus, "
        ),
        "default_quality_profile": "high_quality",
        "default_sampler": "dpmpp_2m",
        "default_steps": 32,
        "default_cfg": 8.0,
        "default_resolution": {"width": 896, "height": 1344}
    },
    "realism": {
        "name": "Photorealism",
        "model": "cyberrealisticPony_v14.safetensors",
        "negative_prompt": "score_6, score_5, score_4, (worst quality:1.2), (low quality:1.2), (normal quality:1.2), lowres, bad anatomy, bad hands, signature, watermarks, ugly, imperfect eyes, skewed eyes, unnatural face, unnatural body, error, extra limb, missing limbs",
        "prompt_prefix": "score_9, score_8_up, score_7_up, ",
        "default_quality_profile": "balanced",
        "lora": None,
        "lora_strength": None
    },
    "lux": {
        "name": "Luxury aesthetic",
        "model": "cyberrealisticPony_v14.safetensors",
        "negative_prompt": "score_6, score_5, score_4, (worst quality:1.2), (low quality:1.2), (normal quality:1.2), lowres, bad anatomy, bad hands, signature, watermarks, ugly, imperfect eyes, skewed eyes, unnatural face, unnatural body, error, extra limb, missing limbs",
        "prompt_prefix": "score_9, score_8_up, score_7_up, luxury, elegant, professional photography, high-end aesthetic, sophisticated, glamorous, premium quality, ",
        "default_quality_profile": "high_quality",
        "lora": None,
        "lora_strength": None
    },
    "anime": {
        "name": "Anime",
        "model": "animeModelXL.safetensors",
        "negative_prompt": (
            "photo, realistic, 3d, lowres, bad anatomy, bad hands, blurry, "
            "distorted face, extra limbs"
        ),
        "prompt_prefix": (
            "anime illustration, highly detailed, clean lineart, vibrant colors, "
            "beautiful anime style, "
        ),
        "default_quality_profile": "balanced",
        "default_sampler": "euler",
        "default_steps": 24,
        "default_cfg": 7.0,
        "default_resolution": {"width": 768, "height": 1152}
    },
    "chatgpt": {
        "name": "General purpose",
        "model": "cyberrealisticPony_v14.safetensors",
        "negative_prompt": "score_6, score_5, score_4, (worst quality:1.2), (low quality:1.2), (normal quality:1.2), lowres, bad anatomy, bad hands, signature, watermarks, ugly, imperfect eyes, skewed eyes, unnatural face, unnatural body, error, extra limb, missing limbs",
        "prompt_prefix": "score_9, score_8_up, score_7_up, ",
        "default_quality_profile": "balanced",
        "lora": None,
        "lora_strength": None
    },
    "super_realism_nsfw": {
        "name": "Super Realism NSFW",
        "model": "cyberrealisticPony_v14.safetensors",
        "negative_prompt": "score_6, score_5, score_4, (worst quality:1.2), (low quality:1.2), (normal quality:1.2), lowres, bad anatomy, bad hands, signature, watermarks, ugly, imperfect eyes, skewed eyes, unnatural face, unnatural body, error, extra limb, missing limbs",
        "prompt_prefix": "score_9, score_8_up, score_7_up, ",
        "default_quality_profile": "high_quality",
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
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
