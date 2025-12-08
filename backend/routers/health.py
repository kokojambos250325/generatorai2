"""
Health Check Router

Provides service health status and GPU availability check.
"""

from fastapi import APIRouter, Depends
import logging

from schemas.response_generate import HealthResponse
from clients.gpu_client import GPUClient
from config import get_settings, Settings

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/health", response_model=HealthResponse)
async def health_check(settings: Settings = Depends(get_settings)):
    """
    Check service health and GPU availability.
    
    Returns:
        HealthResponse: Service status and GPU availability
    """
    try:
        # Check GPU service connectivity
        gpu_client = GPUClient(settings.gpu_service_url, settings.request_timeout)
        gpu_available = await gpu_client.check_health()
        
        logger.info(f"Health check: GPU available={gpu_available}")
        
        return HealthResponse(
            status="healthy" if gpu_available else "degraded",
            gpu_available=gpu_available,
            version=settings.api_version
        )
    
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            gpu_available=False,
            version=settings.api_version
        )
