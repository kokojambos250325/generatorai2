"""
GPU Service Client

HTTP client for communicating with GPU server.
Handles all requests to the ComfyUI-based GPU service.
"""

import httpx
import logging
import asyncio
import time
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
            workflow: Workflow name (maps to 'mode' in GPU request)
            params: Generation parameters (unpacked to request body)
        
        Returns:
            dict: Generation result with image data
        
        Raises:
            Exception: If generation fails
        """
        try:
            # Construct payload matching GPUGenerationRequest schema
            payload = {
                "mode": workflow,
                **{k: v for k, v in params.items() if v is not None}
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/generate",
                    json=payload
                )
                
                response.raise_for_status()
                submit_result = response.json()
                task_id = submit_result.get("task_id")
                
                if not task_id:
                    raise Exception("GPU service did not return task_id")
                
                logger.info(f"Task submitted to GPU service: {task_id} (request_id={self.request_id})")
                
                # Poll for completion
                start_time = time.time()
                while (time.time() - start_time) < self.timeout:
                    try:
                        status_response = await client.get(f"{self.base_url}/task/{task_id}")
                        status_response.raise_for_status()
                        status_data = status_response.json()
                        status = status_data.get("status")
                        
                        if status == "completed":
                            # Fetch result
                            result_response = await client.get(f"{self.base_url}/result/{task_id}")
                            result_response.raise_for_status()
                            result_data = result_response.json()
                            
                            # Normalize result for services
                            return {
                                "status": "done",
                                "image": result_data.get("result_image"),
                                "task_id": task_id
                            }
                            
                        elif status == "failed":
                            error = status_data.get("error", "Unknown error")
                            raise Exception(f"Task failed: {error}")
                            
                        # Wait before next poll
                        await asyncio.sleep(1)
                        
                    except httpx.RequestError as e:
                        logger.warning(f"Polling error for task {task_id}: {e}")
                        await asyncio.sleep(1)
                
                raise Exception(f"Generation timeout after {self.timeout} seconds")
        
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
