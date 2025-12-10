"""
Backend API Client for Telegram Bot
"""
import httpx
import logging
from typing import Optional, Dict, Any, List
from telegram_bot.config import get_settings


logger = logging.getLogger(__name__)


class BackendAPIClient:
    """Client for communicating with backend API"""
    
    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.backend_api_url
        self.timeout = 120  # 2 minutes default timeout
    
    async def generate_free(
        self,
        prompt: str,
        style: str,
        face_images: Optional[List[str]] = None,
        add_face: bool = False,
        extra_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate free text-to-image
        
        Args:
            prompt: Text prompt
            style: Style (noir, super_realism, anime, realism, lux, chatgpt)
            face_images: Optional list of base64 face images
            add_face: Whether to add face
            extra_params: Optional extra parameters
        
        Returns:
            Dict with status, image (base64), task_id, error
        """
        url = f"{self.base_url}/generate"
        
        payload: Dict[str, Any] = {
            "mode": "free",
            "prompt": prompt,
            "style": style,
            "add_face": add_face
        }
        
        if face_images:
            payload["face_images"] = face_images
        if extra_params:
            payload["extra_params"] = extra_params
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                return response.json()
        
        except httpx.TimeoutException:
            logger.error(f"Timeout generating free image")
            raise Exception("Generation timeout - backend took too long to respond")
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
            error_detail = e.response.json().get("detail", str(e)) if e.response.content else str(e)
            raise Exception(f"Backend API error: {error_detail}")
        except httpx.RequestError as e:
            logger.error(f"Request error: {str(e)}")
            raise Exception(f"Failed to connect to backend: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise
    
    async def generate_nsfw_face(
        self,
        face_images: List[str],
        scene_prompt: str,
        style: str,
        face_strength: float = 0.8,
        enable_upscale: bool = False,
        extra_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate NSFW face-consistent image
        
        Args:
            face_images: List of base64 face images (1-5)
            scene_prompt: Scene description
            style: Style (realism, lux, anime)
            face_strength: Face consistency strength (0.6-1.0)
            enable_upscale: Enable 2x upscaling
            extra_params: Optional extra parameters
        
        Returns:
            Dict with status, image (base64), task_id, error
        """
        url = f"{self.base_url}/generate/nsfw_face"
        
        payload: Dict[str, Any] = {
            "mode": "nsfw_face",
            "face_images": face_images,
            "scene_prompt": scene_prompt,
            "style": style,
            "face_strength": face_strength,
            "enable_upscale": enable_upscale
        }
        
        if extra_params:
            payload["extra_params"] = extra_params
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                return response.json()
        
        except httpx.TimeoutException:
            logger.error(f"Timeout generating NSFW face image")
            raise Exception("Generation timeout - backend took too long to respond")
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
            error_detail = e.response.json().get("detail", str(e)) if e.response.content else str(e)
            raise Exception(f"Backend API error: {error_detail}")
        except httpx.RequestError as e:
            logger.error(f"Request error: {str(e)}")
            raise Exception(f"Failed to connect to backend: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise
    
    async def generate_clothes_removal(
        self,
        target_image: str,
        style: str,
        controlnet_strength: float = 0.8,
        inpaint_denoise: float = 0.75,
        segmentation_threshold: float = 0.7,
        seed: int = -1,
        steps: int = 30
    ) -> Dict[str, Any]:
        """
        Remove clothes from image
        
        Args:
            target_image: Base64 encoded source image
            style: Style (realism, lux, anime)
            controlnet_strength: ControlNet strength (0.0-1.5)
            inpaint_denoise: Inpaint denoise strength (0.5-1.0)
            segmentation_threshold: Person segmentation threshold (0.5-0.9)
            seed: Random seed (-1 for random)
            steps: Sampling steps (15-50)
        
        Returns:
            Dict with status, image (base64), task_id, error
        """
        url = f"{self.base_url}/generate/clothes_removal"
        
        payload: Dict[str, Any] = {
            "mode": "clothes_removal",
            "target_image": target_image,
            "style": style,
            "controlnet_strength": controlnet_strength,
            "inpaint_denoise": inpaint_denoise,
            "segmentation_threshold": segmentation_threshold,
            "seed": seed,
            "steps": steps
        }
        
        try:
            # Clothes removal takes longer, use extended timeout
            async with httpx.AsyncClient(timeout=180) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                return response.json()
        
        except httpx.TimeoutException:
            logger.error(f"Timeout removing clothes")
            raise Exception("Generation timeout - clothes removal takes 60-120 seconds")
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
            error_detail = e.response.json().get("detail", str(e)) if e.response.content else str(e)
            raise Exception(f"Backend API error: {error_detail}")
        except httpx.RequestError as e:
            logger.error(f"Request error: {str(e)}")
            raise Exception(f"Failed to connect to backend: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
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
