"""
GPU Server Configuration

Loads configuration from environment variables.
"""

import os
from functools import lru_cache
from pydantic_settings import BaseSettings


# Quality Profiles - Unified configuration for all workflows
QUALITY_PROFILES = {
    "fast": {
        "steps": 18,
        "cfg": 6.5,
        "width": 704,
        "height": 1024,
        "sampler": "euler",
        "scheduler": "normal"
    },
    "balanced": {
        "steps": 26,
        "cfg": 7.5,
        "width": 832,
        "height": 1216,
        "sampler": "euler",
        "scheduler": "normal"
    },
    "high_quality": {
        "steps": 32,
        "cfg": 8.0,
        "width": 896,
        "height": 1344,
        "sampler": "dpmpp_2m",
        "scheduler": "karras"
    }
}


class Settings(BaseSettings):
    """GPU server settings"""
    
    # Server Configuration
    gpu_server_host: str = "0.0.0.0"
    gpu_server_port: int = 8002
    
    # ComfyUI Configuration
    comfyui_api_url: str = "http://localhost:8188"
    
    # Paths (relative to /workspace on POD)
    models_path: str = "/workspace/models"
    workflows_path: str = "/workspace/gpu_server/workflows"
    
    # Logging
    log_level: str = "INFO"
    
    # Performance
    max_concurrent_tasks: int = 1  # MVP: synchronous only
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
