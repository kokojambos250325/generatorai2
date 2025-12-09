"""
Generation router
"""
from fastapi import APIRouter, HTTPException
import logging
import uuid

from schemas.request_free import FreeGenerationRequest
from schemas.response_generate import GenerationResponse
from services.generation_router import GenerationRouter
from config import get_settings

router = APIRouter(prefix="/generate", tags=["Generation"])
logger = logging.getLogger(__name__)
settings = get_settings()


@router.post("")
async def generate_image(request: FreeGenerationRequest):
    """
    Generate image endpoint
    
    Accepts request, processes through GPU service, returns image
    """
    task_id = str(uuid.uuid4())
    
    logger.info(f"Generation request received: mode={request.mode}, task_id={task_id}")
    logger.debug(f"Request params: {request.model_dump()}")
    
    try:
        # Initialize generation router
        gen_router = GenerationRouter(
            gpu_service_url=settings.gpu_service_url,
            request_timeout=settings.request_timeout
        )
        
        # Process request
        if request.mode == "free":
            result_image = await gen_router.process_free_generation(request)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported mode: {request.mode}")
        
        logger.info(f"Generation completed: task_id={task_id}")
        
        return GenerationResponse.success(image=result_image, task_id=task_id)
    
    except Exception as e:
        logger.error(f"Generation failed: task_id={task_id}, error={str(e)}")
        return GenerationResponse.error(error_message=str(e), task_id=task_id)
