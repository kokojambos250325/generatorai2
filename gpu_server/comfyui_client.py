"""
ComfyUI HTTP API Client
Handles communication with ComfyUI instance for workflow execution
"""
import httpx
import json
import logging
import time
import asyncio
from typing import Dict, Any, Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)


class ComfyUIClient:
    """Client for interacting with ComfyUI HTTP API"""
    
    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8188",
        timeout: int = 600
    ):
        """
        Initialize ComfyUI client
        
        Args:
            base_url: ComfyUI server URL
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.client_id = f"gpu_server_{int(time.time())}"
    
    async def queue_prompt(self, workflow: Dict[str, Any]) -> str:
        """
        Submit workflow to ComfyUI queue
        
        Args:
            workflow: ComfyUI workflow JSON
        
        Returns:
            prompt_id: Unique execution ID
        """
        url = f"{self.base_url}/prompt"
        
        payload = {
            "prompt": workflow,
            "client_id": self.client_id
        }
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                
                result = response.json()
                prompt_id = result.get("prompt_id")
                
                if not prompt_id:
                    raise ValueError("No prompt_id in response")
                
                logger.info(f"Queued prompt to ComfyUI: {prompt_id}")
                return prompt_id
        
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error queuing prompt: {e.response.status_code} - {e.response.text}")
            raise Exception(f"ComfyUI API error: {e.response.status_code}")
        except httpx.RequestError as e:
            logger.error(f"Request error queuing prompt: {str(e)}")
            raise Exception(f"Failed to connect to ComfyUI: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error queuing prompt: {str(e)}")
            raise
    
    async def get_history(self, prompt_id: str) -> Optional[Dict[str, Any]]:
        """
        Get execution history for a prompt
        
        Args:
            prompt_id: Prompt execution ID
        
        Returns:
            History data or None if not found
        """
        url = f"{self.base_url}/history/{prompt_id}"
        
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(url)
                response.raise_for_status()
                
                history = response.json()
                return history.get(prompt_id)
        
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            logger.error(f"HTTP error getting history: {e.response.status_code}")
            raise
        except Exception as e:
            logger.error(f"Error getting history: {str(e)}")
            return None
    
    async def get_queue(self) -> Dict[str, Any]:
        """
        Get current queue status
        
        Returns:
            Queue information
        """
        url = f"{self.base_url}/queue"
        
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.json()
        
        except Exception as e:
            logger.error(f"Error getting queue: {str(e)}")
            return {"queue_running": [], "queue_pending": []}
    
    async def poll_until_complete(
        self,
        prompt_id: str,
        poll_interval: float = 2.0,
        max_attempts: int = 300
    ) -> Dict[str, Any]:
        """
        Poll ComfyUI until execution completes
        
        Args:
            prompt_id: Prompt execution ID
            poll_interval: Seconds between polls
            max_attempts: Maximum polling attempts
        
        Returns:
            Execution result
        
        Raises:
            TimeoutError: If execution exceeds max attempts
            Exception: If execution fails
        """
        logger.info(f"Polling ComfyUI for prompt {prompt_id}")
        
        for attempt in range(max_attempts):
            await asyncio.sleep(poll_interval)
            
            # Check history
            history = await self.get_history(prompt_id)
            
            if history is None:
                # Still executing or in queue
                if attempt % 10 == 0:
                    logger.debug(f"Still waiting for prompt {prompt_id} (attempt {attempt}/{max_attempts})")
                continue
            
            # Check status
            status = history.get("status", {})
            status_str = status.get("status_str")
            
            if status_str == "success":
                logger.info(f"ComfyUI execution completed: {prompt_id}")
                return history
            
            elif status_str == "error":
                error_messages = status.get("messages", [])
                error_str = "; ".join([str(msg) for msg in error_messages])
                logger.error(f"ComfyUI execution failed: {error_str}")
                raise Exception(f"ComfyUI execution failed: {error_str}")
            
            # Check if completed but with unknown status
            if "outputs" in history:
                logger.info(f"ComfyUI execution completed (legacy): {prompt_id}")
                return history
        
        # Timeout
        logger.error(f"ComfyUI execution timeout for prompt {prompt_id}")
        raise TimeoutError(f"Execution timeout after {max_attempts * poll_interval} seconds")
    
    async def get_image(self, filename: str, subfolder: str = "", folder_type: str = "output") -> bytes:
        """
        Download image from ComfyUI
        
        Args:
            filename: Image filename
            subfolder: Subfolder path
            folder_type: Folder type (output, input, temp)
        
        Returns:
            Image bytes
        """
        url = f"{self.base_url}/view"
        params = {
            "filename": filename,
            "type": folder_type
        }
        if subfolder:
            params["subfolder"] = subfolder
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                
                logger.info(f"Downloaded image from ComfyUI: {filename}")
                return response.content
        
        except Exception as e:
            logger.error(f"Error downloading image: {str(e)}")
            raise
    
    async def upload_image(self, image_bytes: bytes, filename: str, overwrite: bool = True) -> Dict[str, Any]:
        """
        Upload image to ComfyUI input folder
        
        Args:
            image_bytes: Image data
            filename: Target filename
            overwrite: Whether to overwrite existing file
        
        Returns:
            Upload result
        """
        url = f"{self.base_url}/upload/image"
        
        files = {
            "image": (filename, image_bytes, "image/png")
        }
        data = {
            "overwrite": "true" if overwrite else "false"
        }
        
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(url, files=files, data=data)
                response.raise_for_status()
                
                result = response.json()
                logger.info(f"Uploaded image to ComfyUI: {filename}")
                return result
        
        except Exception as e:
            logger.error(f"Error uploading image: {str(e)}")
            raise
    
    async def health_check(self) -> bool:
        """
        Check if ComfyUI is responding
        
        Returns:
            True if healthy
        """
        url = f"{self.base_url}/system_stats"
        
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(url)
                return response.status_code == 200
        except Exception as e:
            logger.error(f"ComfyUI health check failed: {str(e)}")
            return False
    
    async def get_embeddings(self) -> List[str]:
        """
        Get list of available embeddings
        
        Returns:
            List of embedding names
        """
        url = f"{self.base_url}/embeddings"
        
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error getting embeddings: {str(e)}")
            return []
    
    async def interrupt(self) -> bool:
        """
        Interrupt current execution
        
        Returns:
            True if interrupted successfully
        """
        url = f"{self.base_url}/interrupt"
        
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.post(url)
                response.raise_for_status()
                logger.info("Interrupted ComfyUI execution")
                return True
        except Exception as e:
            logger.error(f"Error interrupting: {str(e)}")
            return False
    
    def extract_output_images(self, history: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Extract output image information from history
        
        Args:
            history: Execution history
        
        Returns:
            List of image info dicts with 'filename', 'subfolder', 'type'
        """
        images = []
        
        outputs = history.get("outputs", {})
        for node_id, node_output in outputs.items():
            if "images" in node_output:
                for image in node_output["images"]:
                    images.append({
                        "filename": image.get("filename"),
                        "subfolder": image.get("subfolder", ""),
                        "type": image.get("type", "output")
                    })
        
        return images
