"""
Free Generation with Face Service

Handles free text-to-image generation with face embedding using IP-Adapter FaceID.
"""

import logging
from typing import Dict, Any, List

from backend.schemas.request_free import FreeGenerationRequest
from backend.clients.gpu_client import GPUClient
from backend.services.param_resolver import ParameterResolver

logger = logging.getLogger(__name__)


class FreeGenerationFaceService:
    """Service for free generation with face consistency"""
    
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
    
    async def generate(self, request: FreeGenerationRequest) -> str:
        """
        Generate image from text prompt with face embedding.
        
        Args:
            request: Generation request with face images
        
        Returns:
            str: Base64 encoded image
        """
        logger.info(f"Free generation with face: style={request.style}, faces={len(request.face_images or [])}")
        
        # Resolve basic parameters
        extra_params_dict = request.extra_params.model_dump() if request.extra_params else None
        params = self.param_resolver.resolve_params(
            style=request.style,
            prompt=request.prompt,
            extra_params=extra_params_dict
        )
        
        # Add face-specific parameters
        if request.face_images:
            params["face_images"] = request.face_images
            params["face_strength"] = request.face_strength
        
        logger.debug(f"Generation params: {params}")
        
        # Call GPU service with face-aware workflow
        result = await self.gpu_client.generate(
            workflow="free_generation_face",
            params=params
        )
        
        # Extract and return base64 image
        if "image" not in result:
            raise Exception("GPU service did not return image data")
        
        return result["image"]
