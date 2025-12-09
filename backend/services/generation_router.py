"""
Generation Router Service

Routes generation requests to appropriate service handlers based on mode.
MVP: Supports free generation and clothes removal only.
"""

import logging
from typing import Dict, Any

from schemas.request_free import FreeGenerationRequest, NSFWFaceRequest
from schemas.request_clothes import ClothesRemovalRequest
from clients.gpu_client import GPUClient
from services.free_generation import FreeGenerationService
from services.free_generation_face import FreeGenerationFaceService
from services.clothes_removal import ClothesRemovalService
from services.nsfw_face import NSFWFaceService

logger = logging.getLogger(__name__)


class GenerationRouter:
    """Routes generation requests to appropriate handlers"""
    
    def __init__(self, gpu_service_url: str, request_timeout: int, request_id: str = None):
        """
        Initialize generation router.
        
        Args:
            gpu_service_url: URL of GPU service
            request_timeout: Request timeout in seconds
            request_id: Optional request ID for logging/tracing
        """
        self.gpu_client = GPUClient(gpu_service_url, request_timeout, request_id=request_id)
        self.free_gen_service = FreeGenerationService(self.gpu_client, request_id)
        self.free_gen_face_service = FreeGenerationFaceService(self.gpu_client, request_id)
        self.clothes_removal_service = ClothesRemovalService(self.gpu_client)
        self.nsfw_face_service = NSFWFaceService(self.gpu_client, request_id)
        self.request_id = request_id
    
    async def process_free_generation(self, request: FreeGenerationRequest) -> str:
        """
        Process free generation request.
        Routes to face-aware service if add_face=True.
        
        Args:
            request: Free generation request
        
        Returns:
            str: Base64 encoded result image
        """
        if request.add_face and request.face_images:
            logger.info(f"Routing to free generation with face - style: {request.style}, faces: {len(request.face_images)}")
            return await self.free_gen_face_service.generate(request)
        else:
            logger.info(f"Routing to standard free generation - style: {request.style}")
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
    
    async def process_nsfw_face(self, request: NSFWFaceRequest) -> str:
        """
        Process NSFW face-consistent generation request.
        
        Args:
            request: NSFW face request
        
        Returns:
            str: Base64 encoded result image
        """
        logger.info(f"Routing to NSFW face service - style: {request.style}, faces: {len(request.face_images)}")
        return await self.nsfw_face_service.generate(request)
