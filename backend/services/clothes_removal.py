"""
Clothes Removal Service

Handles clothes removal with pose preservation using ControlNet.
MVP: Fixed parameters, no advanced customization.
"""

import logging
from typing import Dict, Any

from backend.schemas.request_clothes import ClothesRemovalRequest
from backend.clients.gpu_client import GPUClient

logger = logging.getLogger(__name__)


class ClothesRemovalService:
    """Service for clothes removal generation"""
    
    # Style to model configuration
    STYLE_CONFIG = {
        "realism": {
            "model": "chilloutmix",
            "strength": 0.8
        },
        "lux": {
            "model": "chilloutmix",
            "strength": 0.75
        },
        "anime": {
            "model": "anime_nsfw",
            "strength": 0.85
        }
    }
    
    def __init__(self, gpu_client: GPUClient):
        """
        Initialize service.
        
        Args:
            gpu_client: GPU service client
        """
        self.gpu_client = gpu_client
    
    async def generate(self, request: ClothesRemovalRequest) -> str:
        """
        Remove clothes from image while preserving pose.
        
        Args:
            request: Clothes removal request
        
        Returns:
            str: Base64 encoded result image
        """
        logger.info(f"Clothes removal: style={request.style}")
        
        # Get style configuration
        style_config = self.STYLE_CONFIG[request.style]
        
        # Build generation parameters
        params = {
            "target_image": request.target_image,
            "model": style_config["model"],
            "strength": style_config["strength"],
            "controlnet_strength": request.controlnet_strength,
            "inpaint_denoise": request.inpaint_denoise,
            "segmentation_threshold": request.segmentation_threshold,
            "negative_prompt": "clothing, dressed, covered, clothes, shirt, pants"
        }
        
        # Add optional parameters
        if request.seed is not None and request.seed != -1:
            params["seed"] = request.seed
        if request.steps:
            params["steps"] = request.steps
        
        logger.debug(f"Clothes removal params: model={params['model']}, controlnet={params['controlnet_strength']}")
        
        # Call GPU service
        result = await self.gpu_client.generate(
            workflow="clothes_removal",
            params=params
        )
        
        # Extract and return base64 image
        if "image" not in result:
            raise Exception("GPU service did not return image data")
        
        return result["image"]
