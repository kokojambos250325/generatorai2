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
            "image": request.target_image,
            "style": request.style,
            "seed": request.seed if request.seed is not None and request.seed != -1 else None,
            # Extra params used by GPU worker logic if needed, 
            # but schema only strictly defines some fields. 
            # We might need to check if GPU server accepts extra fields.
            # Based on schema it doesn't allow extra.
            # But let's assume Pydantic extra="ignore" might be needed there too if we send extras.
        }
        
        # Call GPU service
        result = await self.gpu_client.generate(
            workflow="clothes",
            params=params
        )
        
        # Extract and return base64 image
        if "image" not in result:
            raise Exception("GPU service did not return image data")
        
        return result["image"]
