"""
Backend API Client for Telegram Bot
"""
import httpx
import logging
from typing import Optional, Dict, Any
from telegram_bot.config import get_bot_settings


logger = logging.getLogger(__name__)


class BackendAPIClient:
    """Client for communicating with backend API"""
    
    def __init__(self):
        self.settings = get_bot_settings()
        self.base_url = self.settings.BACKEND_API_URL
        self.timeout = self.settings.BACKEND_API_TIMEOUT
    
    async def submit_task(
        self,
        mode: str,
        prompt: Optional[str] = None,
        image: Optional[bytes] = None,
        face_image: Optional[bytes] = None,
        clothes_image: Optional[bytes] = None,
        style: Optional[str] = None,
        seed: Optional[int] = None
    ) -> str:
        """
        Submit generation task to backend
        
        Args:
            mode: Generation mode (free, face_swap, clothes_removal, face_consistent)
            prompt: Text prompt for generation
            image: Base64 encoded image
            face_image: Base64 encoded face image
            clothes_image: Base64 encoded clothes image
            style: Generation style (realistic, anime)
            seed: Random seed for reproducibility
        
        Returns:
            task_id: Task identifier for status checking
        """
        url = f"{self.base_url}/generate"
        
        # Prepare request payload
        payload: Dict[str, Any] = {"mode": mode}
        
        if prompt:
            payload["prompt"] = prompt
        if image:
            payload["image"] = image.decode('utf-8') if isinstance(image, bytes) else image
        if face_image:
            payload["face_image"] = face_image.decode('utf-8') if isinstance(face_image, bytes) else face_image
        if clothes_image:
            payload["clothes_image"] = clothes_image.decode('utf-8') if isinstance(clothes_image, bytes) else clothes_image
        if style:
            payload["style"] = style
        if seed is not None:
            payload["seed"] = seed
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                
                result = response.json()
                task_id = result.get("task_id")
                
                if not task_id:
                    raise ValueError("No task_id in response")
                
                logger.info(f"Task submitted successfully: {task_id}")
                return task_id
        
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error submitting task: {e.response.status_code} - {e.response.text}")
            raise Exception(f"Backend API error: {e.response.status_code}")
        except httpx.RequestError as e:
            logger.error(f"Request error submitting task: {str(e)}")
            raise Exception(f"Failed to connect to backend: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error submitting task: {str(e)}")
            raise
    
    async def check_status(self, task_id: str) -> Dict[str, Any]:
        """
        Check task status
        
        Args:
            task_id: Task identifier
        
        Returns:
            Status information including status, progress, result
        """
        url = f"{self.base_url}/task/{task_id}"
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(url)
                response.raise_for_status()
                
                return response.json()
        
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error checking status: {e.response.status_code} - {e.response.text}")
            raise Exception(f"Backend API error: {e.response.status_code}")
        except httpx.RequestError as e:
            logger.error(f"Request error checking status: {str(e)}")
            raise Exception(f"Failed to connect to backend: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error checking status: {str(e)}")
            raise
    
    async def health_check(self) -> bool:
        """
        Check if backend API is healthy
        
        Returns:
            True if healthy, False otherwise
        """
        url = f"{self.base_url}/health"
        
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(url)
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return False
