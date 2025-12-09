"""
GPU Server - ComfyUI Integration Service

Wraps ComfyUI API and provides simplified HTTP interface for backend.
Supports free_generation and clothes_removal workflows.

This server runs on the RunPod POD and communicates with:
- ComfyUI API (localhost:8188)
- Backend API (receives requests)
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional
import logging
import uvicorn
import uuid

from comfy_client import ComfyUIClient
from config import get_settings
from json_logging import setup_json_logging, log_event

# Initialize settings
settings = get_settings()

# Setup JSON logging
logger = setup_json_logging(
    service_name="gpu_server",
    log_file_path="/workspace/logs/gpu_server.log",
    log_level=settings.log_level
)

# Initialize FastAPI app
app = FastAPI(
    title="GPU Generation Service",
    version="1.0.0",
    description="ComfyUI wrapper for AI image generation"
)

# Initialize ComfyUI client
comfy_client = ComfyUIClient(
    comfyui_url=settings.comfyui_api_url,
    workflows_path=settings.workflows_path,
    models_path=settings.models_path
)


class GenerationRequest(BaseModel):
    """Request schema for generation"""
    workflow: str  # free_generation or clothes_removal
    params: Dict[str, Any]
    request_id: Optional[str] = None  # Optional request_id from backend for tracing


class GenerationResponse(BaseModel):
    """Response schema for generation"""
    status: str
    image: Optional[str] = None
    error: Optional[str] = None


@app.get("/health")
async def health_check():
    """
    Check service health and ComfyUI availability.
    
    Returns:
        dict: Service status
    """
    try:
        comfy_available = await comfy_client.check_health()
        
        return {
            "status": "healthy" if comfy_available else "degraded",
            "comfyui_available": comfy_available,
            "service": "gpu_server",
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "comfyui_available": False,
                "error": str(e)
            }
        )


@app.post("/generate", response_model=GenerationResponse)
async def generate(request: GenerationRequest):
    """
    Generate image using specified workflow.
    
    Supports:
    - free_generation: Text-to-image with style
    - clothes_removal: Remove clothes with ControlNet
    
    Args:
        request: Generation request with workflow and params
    
    Returns:
        GenerationResponse: Result with base64 image or error
    """
    # Generate generation_id for GPU-level tracking
    generation_id = str(uuid.uuid4())
    request_id = request.request_id
    
    try:
        # Log incoming request
        log_event(
            logger=logger,
            level="INFO",
            event="execute_request",
            message=f"Execute request: workflow={request.workflow}",
            request_id=request_id,
            generation_id=generation_id,
            workflow=request.workflow,
            params_summary={
                "steps": request.params.get("steps"),
                "cfg": request.params.get("cfg"),
                "width": request.params.get("width"),
                "height": request.params.get("height")
            }
        )
        
        # Validate workflow
        if request.workflow not in ["free_generation", "clothes_removal"]:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported workflow: {request.workflow}"
            )
        
        # Execute workflow
        result_image = await comfy_client.execute_workflow(
            workflow_name=request.workflow,
            params=request.params,
            generation_id=generation_id,
            request_id=request_id
        )
        
        # Log success
        log_event(
            logger=logger,
            level="INFO",
            event="generation_complete",
            message=f"Generation completed successfully",
            request_id=request_id,
            generation_id=generation_id,
            workflow=request.workflow
        )
        
        return GenerationResponse(
            status="done",
            image=result_image,
            error=None
        )
    
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
            generation_id=generation_id,
            error_type=type(e).__name__,
            error_message=str(e)
        )
        return GenerationResponse(
            status="failed",
            image=None,
            error=str(e)
        )


@app.on_event("startup")
async def startup_event():
    """Application startup"""
    logger.info("Starting GPU Generation Service")
    logger.info(f"ComfyUI URL: {settings.comfyui_api_url}")
    logger.info(f"Workflows path: {settings.workflows_path}")
    logger.info(f"Models path: {settings.models_path}")
    
    # Check ComfyUI availability
    comfy_available = await comfy_client.check_health()
    if not comfy_available:
        logger.warning("ComfyUI is not available on startup!")
    else:
        logger.info("ComfyUI is available")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown"""
    logger.info("Shutting down GPU Generation Service")


if __name__ == "__main__":
    uvicorn.run(
        "server:app",
        host=settings.gpu_server_host,
        port=settings.gpu_server_port,
        reload=False,
        log_level=settings.log_level.lower()
    )
