"""
Generation Router Service

Routes generation requests to appropriate service handlers based on mode.
MVP: Supports free generation and clothes removal only.
"""

import logging
from typing import Dict, Any

from schemas.request_free import FreeGenerationRequest
from schemas.request_clothes import ClothesRemovalRequest
from clients.gpu_client import GPUClient
from services.free_generation import FreeGenerationService
from services.clothes_removal import ClothesRemovalService

logger = logging.getLogger(__name__)


class GenerationRouter:
    """Routes generation requests to appropriate handlers"""
    
    def __init__(self, gpu_service_url: str, request_timeout: int):
        """
        Initialize generation router.
        
        Args:
            gpu_service_url: URL of GPU service
            request_timeout: Request timeout in seconds
        """
        self.gpu_client = GPUClient(gpu_service_url, request_timeout)
        self.free_gen_service = FreeGenerationService(self.gpu_client)
        self.clothes_removal_service = ClothesRemovalService(self.gpu_client)
    
    async def process_free_generation(self, request: FreeGenerationRequest) -> str:
        """
        Process free generation request.
        
        Args:
            request: Free generation request
        
        Returns:
            str: Base64 encoded result image
        """
        logger.info(f"Routing to free generation service - style: {request.style}")
        return await self.free_gen_service.generate(request)
    
    async def process_clothes_removal(self, request: ClothesRemovalRequest) -> str:
        """
        Process clothes removal request.
        
        Args:
            request: Clothes removal request
        
        Returns:
            str: Base64 encoded result image
        """
        logger.info(f"Routing to clothes removal service - style: {request.style}")
        return await self.clothes_removal_service.generate(request)
