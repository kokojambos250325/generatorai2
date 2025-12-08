"""
Free Generation Service

Handles free text-to-image generation with style selection.
MVP: Basic implementation with default LoRAs per style.
"""

import logging
from typing import Dict, Any

from schemas.request_free import FreeGenerationRequest
from clients.gpu_client import GPUClient

logger = logging.getLogger(__name__)


class FreeGenerationService:
    """Service for free text-to-image generation"""
    
    # Style to model/LoRA mapping (MVP: simplified)
    STYLE_CONFIG = {
        "realism": {
            "model": "sd_xl_base_1.0",
            "lora": "realistic_vision",
            "negative_prompt": "cartoon, anime, 3d, illustration, painting"
        },
        "lux": {
            "model": "sd_xl_base_1.0",
            "lora": "glossy_lux",
            "negative_prompt": "low quality, blurry, bad anatomy"
        },
        "anime": {
            "model": "anything_v5",
            "lora": "anime_style",
            "negative_prompt": "realistic, photo, 3d"
        },
        "chatgpt": {
            "model": "sd_xl_base_1.0",
            "lora": None,
            "negative_prompt": "nsfw, explicit, nude"
        }
    }
    
    def __init__(self, gpu_client: GPUClient):
        """
        Initialize service.
        
        Args:
            gpu_client: GPU service client
        """
        self.gpu_client = gpu_client
    
    async def generate(self, request: FreeGenerationRequest) -> str:
        """
        Generate image from text prompt.
        
        Args:
            request: Generation request
        
        Returns:
            str: Base64 encoded image
        """
        logger.info(f"Free generation: style={request.style}, prompt_len={len(request.prompt)}")
        
        # Get style configuration
        style_config = self.STYLE_CONFIG[request.style]
        
        # Build generation parameters
        params = {
            "prompt": request.prompt,
            "negative_prompt": style_config["negative_prompt"],
            "model": style_config["model"],
            "lora": style_config["lora"],
            "steps": request.extra_params.steps if request.extra_params else 30,
            "cfg_scale": request.extra_params.cfg_scale if request.extra_params else 7.5,
            "seed": request.extra_params.seed if request.extra_params else -1,
            "sampler": request.extra_params.sampler if request.extra_params else "euler_a",
            "width": request.extra_params.width if request.extra_params else 1024,
            "height": request.extra_params.height if request.extra_params else 1024,
        }
        
        logger.debug(f"Generation params: {params}")
        
        # Call GPU service
        result = await self.gpu_client.generate(
            workflow="free_generation",
            params=params
        )
        
        # Extract and return base64 image
        if "image" not in result:
            raise Exception("GPU service did not return image data")
        
        return result["image"]
