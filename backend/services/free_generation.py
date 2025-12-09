"""
Free Generation Service

Handles free text-to-image generation with style selection.
Uses parameter resolver for unified quality profiles and style configuration.
"""

import logging
from typing import Dict, Any

from schemas.request_free import FreeGenerationRequest
from clients.gpu_client import GPUClient
from services.param_resolver import ParameterResolver

logger = logging.getLogger(__name__)


class FreeGenerationService:
    """Service for free text-to-image generation"""
    
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
        Generate image from text prompt.
        
        Args:
            request: Generation request
        
        Returns:
            str: Base64 encoded image
        """
        logger.info(f"Free generation: style={request.style}, prompt_len={len(request.prompt)}")
        
        # Resolve parameters using the unified resolution logic
        # This handles: style → quality profile → extra_params → cfg_scale→cfg mapping
        extra_params_dict = request.extra_params.model_dump() if request.extra_params else None
        params = self.param_resolver.resolve_params(
            style=request.style,
            prompt=request.prompt,
            extra_params=extra_params_dict
        )
        
        logger.debug(f"Generation params after resolution: {params}")
        
        # Call GPU service with resolved parameters
        result = await self.gpu_client.generate(
            workflow="free_generation",
            params=params
        )
        
        # Extract and return base64 image
        if "image" not in result:
            raise Exception("GPU service did not return image data")
        
        return result["image"]
