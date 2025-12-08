"""
Generation Router

Main endpoint for image generation requests.
Supports MVP modes: free generation and clothes removal.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Union
import logging
import uuid

from schemas.request_free import FreeGenerationRequest
from schemas.request_clothes import ClothesRemovalRequest
from schemas.response_generate import GenerationResponse
from services.generation_router import GenerationRouter
from config import get_settings, Settings

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/generate", response_model=GenerationResponse)
async def generate_image(
    request: Union[FreeGenerationRequest, ClothesRemovalRequest],
    settings: Settings = Depends(get_settings)
):
    """
    Generate images based on mode and parameters.
    
    MVP supports two modes:
    - free: Text-to-image generation with style selection
    - clothes_removal: Remove clothing from images
    
    Args:
        request: Generation request (mode-specific schema)
        settings: Application settings
    
    Returns:
        GenerationResponse: Task ID, status, image (if done), or error
    
    Raises:
        HTTPException: If generation fails
    """
    task_id = str(uuid.uuid4())
    
    try:
        logger.info(f"[{task_id}] Received {request.mode} generation request")
        
        # Initialize generation router
        gen_router = GenerationRouter(
            gpu_service_url=settings.gpu_service_url,
            request_timeout=settings.request_timeout
        )
        
        # Route request to appropriate service
        if request.mode == "free":
            logger.info(f"[{task_id}] Processing free generation - style: {request.style}")
            result_image = await gen_router.process_free_generation(request)
        
        elif request.mode == "clothes_removal":
            logger.info(f"[{task_id}] Processing clothes removal - style: {request.style}")
            result_image = await gen_router.process_clothes_removal(request)
        
        else:
            # This shouldn't happen due to Pydantic validation, but just in case
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported mode: {request.mode}. MVP supports: free, clothes_removal"
            )
        
        logger.info(f"[{task_id}] Generation completed successfully")
        return GenerationResponse.success(image=result_image, task_id=task_id)
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"[{task_id}] Generation failed: {str(e)}", exc_info=True)
        return GenerationResponse.error(
            error_message=f"Generation failed: {str(e)}",
            task_id=task_id
        )
