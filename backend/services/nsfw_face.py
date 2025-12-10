"""
NSFW Face Service

Handles NSFW generation with multi-face consistency using IP-Adapter FaceID Plus.
"""

import logging
from typing import Dict, Any

from backend.schemas.request_free import NSFWFaceRequest
from backend.clients.gpu_client import GPUClient
from backend.services.param_resolver import ParameterResolver
from backend.config import STYLE_CONFIG

logger = logging.getLogger(__name__)


class NSFWFaceService:
    """Service for NSFW face-consistent generation"""
    
    def __init__(self, gpu_client: GPUClient, request_id: str = None):
        """
        Initialize service.
        
        Args:
            gpu_client: GPU service client
            request_id: Optional request ID for logging/tracing
        """
        self.gpu_client = gpu_client
        self.param_resolver = ParameterResolver()
        self.request_id = request_id
    
    async def generate(self, request: NSFWFaceRequest) -> str:
        """
        Generate NSFW image with face consistency.
        
        Args:
            request: NSFW generation request
        
        Returns:
            str: Base64 encoded image
        """
        logger.info(f"NSFW face generation: style={request.style}, faces={len(request.face_images)}")
        
        # Get style configuration
        if request.style not in STYLE_CONFIG:
            raise ValueError(f"Unknown style: {request.style}")
        
        style_config = STYLE_CONFIG[request.style]
        
        # Build generation parameters
        params = {
            "scene_prompt": request.scene_prompt,
            "negative_prompt": style_config["negative_prompt"],
            "face_images": request.face_images,
            "face_strength": request.face_strength,
            "enable_upscale": request.enable_upscale,
            "model": style_config["model"],
            "checkpoint": style_config["model"]
        }
        
        # Add extra params if provided
        if request.extra_params:
            extra = request.extra_params.model_dump()
            if extra.get("steps"):
                params["steps"] = extra["steps"]
            if extra.get("cfg_scale"):
                params["cfg"] = extra["cfg_scale"]
            if extra.get("seed"):
                params["seed"] = extra["seed"]
            if extra.get("width"):
                params["width"] = extra["width"]
            if extra.get("height"):
                params["height"] = extra["height"]
        
        # Set defaults if not provided
        params.setdefault("steps", 30)
        params.setdefault("cfg", 7.5)
        params.setdefault("seed", -1)
        params.setdefault("width", 1024)
        params.setdefault("height", 1024)
        
        logger.debug(f"NSFW generation params: faces={len(params['face_images'])}, upscale={params['enable_upscale']}")
        
        # Call GPU service
        result = await self.gpu_client.generate(
            workflow="nsfw_face",
            params=params
        )
        
        # Extract and return base64 image
        if "image" not in result:
            raise Exception("GPU service did not return image data")
        
        return result["image"]
