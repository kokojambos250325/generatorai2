from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # GPU Server Configuration
    GPU_SERVER_URL: str = "http://localhost:3000"
    GPU_SERVER_API_KEY: str = ""
    GPU_TIMEOUT_GENERATION: int = 600
    GPU_RETRY_ATTEMPTS: int = 3
    GPU_RETRY_INITIAL_BACKOFF: int = 1
    GPU_RETRY_MAX_BACKOFF: int = 30
    GPU_HEALTH_CHECK_INTERVAL: int = 60
    GPU_POLL_INTERVAL_MIN: int = 2
    GPU_POLL_INTERVAL_MAX: int = 10
    GPU_CIRCUIT_BREAKER_THRESHOLD: int = 5
    GPU_CIRCUIT_BREAKER_TIMEOUT: int = 60
    
    # Legacy GPU Configuration (for backwards compatibility)
    TIMEOUT_GENERATION: int = 300
    RETRY_ATTEMPTS: int = 3
    RETRY_DELAY: int = 5
    
    # Redis Configuration
    USE_REDIS_QUEUE: bool = False  # Enable Redis queue (set to True for production)
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    REDIS_DB: int = 0
    REDIS_MAX_CONNECTIONS: int = 50
    REDIS_SOCKET_TIMEOUT: int = 5
    REDIS_RETRY_ON_TIMEOUT: bool = True
    REDIS_TASK_TTL: int = 86400  # Task expiration time (24 hours)
    REDIS_KEY_PREFIX: str = "taskqueue"  # Prefix for Redis keys
    
    # ComfyUI Configuration
    COMFYUI_URL: str = "http://localhost:8188"
    WORKFLOW_DIR: str = "/workspace/workflows"
    MODEL_DIR: str = "/workspace/ComfyUI/models"
    
    # SDXL Model Configuration
    SDXL_MODEL_PATH: str = "stabilityai/stable-diffusion-xl-base-1.0"
    SDXL_VAE_PATH: str = "madebyollin/sdxl-vae-fp16-fix"
    
    # Post-processing Configuration
    ENABLE_UPSCALE: bool = False
    ENABLE_FACE_ENHANCE: bool = False
    
    # Generation Parameters
    DEFAULT_INFERENCE_STEPS: int = 50
    DEFAULT_GUIDANCE_SCALE: float = 7.5
    MAX_IMAGE_DIMENSION: int = 2048
    
    # Rate Limiting
    ENABLE_RATE_LIMITING: bool = True
    MAX_TASKS_PER_USER: int = 5
    
    # Telegram Bot Configuration
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_ADMIN_IDS: str = ""  # Comma-separated list
    
    # Backend API Configuration
    BACKEND_API_URL: str = "http://localhost:8000"
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
