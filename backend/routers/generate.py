"""
Generation router
"""
from fastapi import APIRouter, HTTPException
import logging
import uuid

from backend.schemas.request_free import FreeGenerationRequest, NSFWFaceRequest
from backend.schemas.request_clothes import ClothesRemovalRequest
from backend.schemas.response_generate import GenerationResponse
from backend.services.generation_router import GenerationRouter
from backend.config import get_settings
from backend.utils.json_logging import log_event

router = APIRouter(prefix="/generate", tags=["Generation"])
logger = logging.getLogger(__name__)
settings = get_settings()


@router.post("")
async def generate_image(request: FreeGenerationRequest):
    """
    Generate image endpoint
    
    Accepts request, processes through GPU service, returns image
    """
    # Generate request_id for tracing
    request_id = str(uuid.uuid4())
    
    # Log incoming request
    log_event(
        logger=logger,
        level="INFO",
        event="generate_request",
        message=f"Generate request received: mode={request.mode}, style={request.style}",
        request_id=request_id,
        mode=request.mode,
        style=request.style,
        prompt_length=len(request.prompt),
        has_extra_params=request.extra_params is not None,
        add_face=request.add_face
    )
    
    try:
        # Initialize generation router
        gen_router = GenerationRouter(
            gpu_service_url=settings.gpu_service_url,
            request_timeout=settings.request_timeout,
            request_id=request_id  # Pass request_id for logging
        )
        
        # Process request
        if request.mode == "free":
            result_image = await gen_router.process_free_generation(request)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported mode: {request.mode}")
        
        # Log successful completion
        log_event(
            logger=logger,
            level="INFO",
            event="response_sent",
            message=f"Generation completed successfully",
            request_id=request_id,
            status_code=200,
            result_status="done"
        )
        
        return GenerationResponse.success(image=result_image, task_id=request_id)
    
    except HTTPException:
        raise
    
    except Exception as e:
        # Log error
        log_event(
            logger=logger,
            level="ERROR",
            event="generation_error",
            message=f"Generation failed: {str(e)}",
            request_id=request_id,
            error_type=type(e).__name__,
            error_message=str(e)
        )
        return GenerationResponse.create_error(error_message=str(e), task_id=request_id)


@router.post("/nsfw_face")
async def generate_nsfw_face(request: NSFWFaceRequest):
    """
    Generate NSFW face-consistent image endpoint
    
    Accepts face images and scene prompt, returns adult content with face consistency
    """
    # Generate request_id for tracing
    request_id = str(uuid.uuid4())
    
    # Log incoming request
    log_event(
        logger=logger,
        level="INFO",
        event="generate_request",
        message=f"NSFW face request received: mode={request.mode}, style={request.style}",
        request_id=request_id,
        mode=request.mode,
        style=request.style,
        face_count=len(request.face_images),
        scene_prompt_length=len(request.scene_prompt)
    )
    
    try:
        # Initialize generation router
        gen_router = GenerationRouter(
            gpu_service_url=settings.gpu_service_url,
            request_timeout=settings.request_timeout,
            request_id=request_id
        )
        
        # Process NSFW face request
        result_image = await gen_router.process_nsfw_face(request)
        
        # Log successful completion
        log_event(
            logger=logger,
            level="INFO",
            event="response_sent",
            message=f"NSFW generation completed successfully",
            request_id=request_id,
            status_code=200,
            result_status="done"
        )
        
        return GenerationResponse.success(image=result_image, task_id=request_id)
    
    except HTTPException:
        raise
    
    except Exception as e:
        # Log error
        log_event(
            logger=logger,
            level="ERROR",
            event="generation_error",
            message=f"NSFW generation failed: {str(e)}",
            request_id=request_id,
            error_type=type(e).__name__,
            error_message=str(e)
        )
        return GenerationResponse.create_error(error_message=str(e), task_id=request_id)


@router.post("/clothes_removal")
async def generate_clothes_removal(request: ClothesRemovalRequest):
    """
    Clothes removal endpoint
    
    Accepts image, removes clothes while preserving pose, returns result
    """
    # Generate request_id for tracing
    request_id = str(uuid.uuid4())
    
    # Log incoming request
    log_event(
        logger=logger,
        level="INFO",
        event="generate_request",
        message=f"Clothes removal request received: style={request.style}",
        request_id=request_id,
        mode=request.mode,
        style=request.style,
        has_image=True
    )
    
    try:
        # Initialize generation router
        gen_router = GenerationRouter(
            gpu_service_url=settings.gpu_service_url,
            request_timeout=settings.request_timeout,
            request_id=request_id
        )
        
        # Process clothes removal request
        result_image = await gen_router.process_clothes_removal(request)
        
        # Log successful completion
        log_event(
            logger=logger,
            level="INFO",
            event="response_sent",
            message=f"Clothes removal completed successfully",
            request_id=request_id,
            status_code=200,
            result_status="done"
        )
        
        return GenerationResponse.success(image=result_image, task_id=request_id)
    
    except HTTPException:
        raise
    
    except Exception as e:
        # Log error
        log_event(
            logger=logger,
            level="ERROR",
            event="generation_error",
            message=f"Clothes removal failed: {str(e)}",
            request_id=request_id,
            error_type=type(e).__name__,
            error_message=str(e)
        )
        return GenerationResponse.create_error(error_message=str(e), task_id=request_id)
