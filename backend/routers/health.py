"""
Health check router
"""
from fastapi import APIRouter
import logging

from backend.clients.gpu_client import GPUClient
from backend.config import get_settings

router = APIRouter(prefix="/health", tags=["Health"])
settings = get_settings()
logger = logging.getLogger(__name__)


@router.get("")
async def health_check():
    """
    Health check endpoint
    
    Returns:
        status: healthy | degraded | unhealthy
        gpu_available: GPU service connectivity
        version: API version
    """
    gpu_client = GPUClient(settings.gpu_service_url)
    gpu_available = await gpu_client.check_health()
    
    if gpu_available:
        status = "healthy"
    else:
        status = "degraded"
        logger.warning("GPU service not available")
    
    return {
        "status": status,
        "gpu_available": gpu_available,
        "version": settings.api_version
    }
