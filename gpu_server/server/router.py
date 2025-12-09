"""
API Router for GPU Server
Defines all REST endpoints for task submission and retrieval
"""
import logging
from fastapi import APIRouter, HTTPException, Header
from typing import Optional
import os

from gpu_server.schema import GPUGenerationRequest, GPUGenerationStatus, GPUGenerationResult
from gpu_server.server.utils.queue import task_queue

logger = logging.getLogger(__name__)

router = APIRouter()

# API Key for authentication
API_KEY = os.getenv("GPU_SERVER_API_KEY", "")


def verify_api_key(authorization: Optional[str] = Header(None)):
    """
    Verify API key from Authorization header
    """
    if not API_KEY:
        # No API key configured, skip verification
        return True
    
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization format")
    
    token = authorization.replace("Bearer ", "")
    if token != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    return True


@router.post("/generate")
async def generate(
    request: GPUGenerationRequest,
    _: bool = Header(None, alias="Authorization", convert_underscores=False, include_in_schema=False)
):
    """
    Submit generation task to queue
    
    Returns:
        task_id: Unique identifier for tracking the task
    """
    # Note: API key verification moved to dependency for cleaner code
    # For now, simplified implementation
    
    try:
        # Validate request
        if not request.mode:
            raise HTTPException(status_code=400, detail="Mode is required")
        
        # Check queue capacity
        if task_queue.get_queue_size() >= 100:
            raise HTTPException(status_code=503, detail="Queue is full, try again later")
        
        # Enqueue task
        task_id = task_queue.enqueue_task(request)
        
        logger.info(f"Task {task_id} enqueued with mode {request.mode}")
        
        return {"task_id": task_id}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error enqueueing task: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/task/{task_id}", response_model=GPUGenerationStatus)
async def get_status(task_id: str):
    """
    Check status of a task
    
    Returns:
        GPUGenerationStatus with current task state
    """
    try:
        status = task_queue.get_status(task_id)
        
        if not status:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        
        return status
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting status for task {task_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/result/{task_id}", response_model=GPUGenerationResult)
async def get_result(task_id: str):
    """
    Retrieve result of completed task
    
    Returns:
        GPUGenerationResult with base64 encoded image
    """
    try:
        # Get task status
        status = task_queue.get_status(task_id)
        
        if not status:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        
        if status.status == "pending" or status.status == "processing":
            raise HTTPException(status_code=425, detail=f"Task {task_id} not yet completed")
        
        if status.status == "failed":
            return GPUGenerationResult(
                task_id=task_id,
                status="failed",
                error=status.error
            )
        
        # Get result from storage
        from gpu_server.server.utils.storage import encode_base64
        
        result_image = encode_base64(task_id)
        
        if not result_image:
            raise HTTPException(status_code=404, detail=f"Result image for task {task_id} not found")
        
        return GPUGenerationResult(
            task_id=task_id,
            status="completed",
            result_image=result_image
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting result for task {task_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
