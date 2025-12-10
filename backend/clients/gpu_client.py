"""
GPU Service Client

HTTP client for communicating with GPU server.
Handles all requests to the ComfyUI-based GPU service.
"""

import httpx
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class GPUClient:
    """HTTP client for GPU service communication"""
    
    def __init__(self, base_url: str, timeout: int = 180, request_id: str = None):
        """
        Initialize GPU client.
        
        Args:
            base_url: GPU service base URL
            timeout: Request timeout in seconds
            request_id: Optional request ID for tracing
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.request_id = request_id
    
    async def check_health(self) -> bool:
        """
        Check if GPU service is available.
        
        Returns:
            bool: True if service is healthy
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except Exception as e:
            logger.warning(f"GPU service health check failed: {e}")
            return False
    
    async def generate(self, workflow: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Submit generation request to GPU service.
        
        Args:
            workflow: Workflow name (free_generation, clothes_removal)
            params: Generation parameters
        
        Returns:
            dict: Generation result with image data
        
        Raises:
            Exception: If generation fails
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/generate",
                    json={
                        "workflow": workflow,
                        "params": params,
                        "request_id": self.request_id  # Include request_id for tracing
                    }
                )
                
                response.raise_for_status()
                result = response.json()
                
                # Check if GPU server returned an error status
                if result.get("status") == "failed":
                    error_msg = result.get("error", "Unknown GPU service error")
                    logger.error(f"GPU service returned failed status: {error_msg} (request_id={self.request_id})")
                    raise Exception(f"GPU generation failed: {error_msg}")
                
                return result
        
        except httpx.TimeoutException:
            logger.error(f"GPU service timeout after {self.timeout}s (request_id={self.request_id})")
            raise Exception(f"Generation timeout after {self.timeout} seconds")
        
        except httpx.HTTPStatusError as e:
            logger.error(f"GPU service HTTP error: {e.response.status_code} (request_id={self.request_id})")
            error_detail = e.response.json().get("detail", str(e)) if e.response.content else str(e)
            raise Exception(f"GPU service error: {error_detail}")
        
        except Exception as e:
            logger.error(f"GPU service communication error: {e} (request_id={self.request_id})")
            raise Exception(f"Failed to communicate with GPU service: {str(e)}")
