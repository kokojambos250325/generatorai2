"""
ComfyUI Integration Service
High-level service for executing generation tasks through ComfyUI
"""
import base64
import logging
import asyncio
from typing import Dict, Any, Optional
from pathlib import Path
import uuid

from gpu_server.comfyui_client import ComfyUIClient
from gpu_server.workflow_adapter import get_adapter

logger = logging.getLogger(__name__)


class ComfyUIService:
    """Service for managing ComfyUI workflow execution"""
    
    def __init__(
        self,
        comfyui_url: str = "http://127.0.0.1:8188",
        workflow_dir: str = "/workspace/workflows",
        timeout: int = 600
    ):
        """
        Initialize ComfyUI service
        
        Args:
            comfyui_url: ComfyUI server URL
            workflow_dir: Directory containing workflow JSON files
            timeout: Execution timeout in seconds
        """
        self.client = ComfyUIClient(base_url=comfyui_url, timeout=timeout)
        self.workflow_dir = workflow_dir
        self.timeout = timeout
    
    async def execute_generation(
        self,
        mode: str,
        params: Dict[str, Any]
    ) -> bytes:
        """
        Execute generation task through ComfyUI
        
        Args:
            mode: Generation mode (free, face_swap, etc.)
            params: Generation parameters
        
        Returns:
            Generated image bytes
        """
        logger.info(f"Executing ComfyUI generation: mode={mode}")
        
        try:
            # Get appropriate adapter
            adapter = get_adapter(mode, workflow_dir=self.workflow_dir)
            
            # Prepare parameters (upload images if needed)
            prepared_params = await self._prepare_parameters(params)
            
            # Load and configure workflow
            adapter.load_workflow()
            workflow = adapter.inject_parameters(prepared_params)
            
            # Submit to ComfyUI
            prompt_id = await self.client.queue_prompt(workflow)
            
            # Poll until complete
            history = await self.client.poll_until_complete(
                prompt_id=prompt_id,
                poll_interval=2.0,
                max_attempts=self.timeout // 2
            )
            
            # Extract and download result image
            image_bytes = await self._extract_result_image(history)
            
            logger.info(f"ComfyUI generation completed: mode={mode}, image_size={len(image_bytes)}")
            return image_bytes
        
        except Exception as e:
            logger.error(f"ComfyUI generation failed: {str(e)}")
            raise
    
    async def _prepare_parameters(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare parameters by uploading images to ComfyUI
        
        Args:
            params: Raw parameters
        
        Returns:
            Prepared parameters with image filenames
        """
        prepared = params.copy()
        
        # Handle base64 images - upload to ComfyUI input folder
        image_fields = [
            "image",
            "face_image", 
            "source_image",
            "target_image",
            "control_image",
            "clothes_image"
        ]
        
        for field in image_fields:
            if field in params and params[field]:
                # Check if it's base64 encoded
                if isinstance(params[field], str) and len(params[field]) > 100:
                    try:
                        # Decode base64
                        image_data = base64.b64decode(params[field])
                        
                        # Generate unique filename
                        filename = f"{field}_{uuid.uuid4().hex[:8]}.png"
                        
                        # Upload to ComfyUI
                        await self.client.upload_image(image_data, filename)
                        
                        # Replace with filename
                        prepared[field] = filename
                        logger.debug(f"Uploaded {field} to ComfyUI: {filename}")
                    
                    except Exception as e:
                        logger.error(f"Failed to upload {field}: {str(e)}")
                        raise
        
        # Handle face_images array (for multi-face workflows)
        if "face_images" in params and params["face_images"]:
            face_images_list = params["face_images"]
            if isinstance(face_images_list, list):
                uploaded_filenames = []
                
                for i, face_image_data in enumerate(face_images_list[:5]):  # Max 5 faces
                    try:
                        # Decode base64
                        if isinstance(face_image_data, str) and len(face_image_data) > 100:
                            image_data = base64.b64decode(face_image_data)
                            
                            # Generate unique filename
                            filename = f"face_{i+1}_{uuid.uuid4().hex[:8]}.png"
                            
                            # Upload to ComfyUI
                            await self.client.upload_image(image_data, filename)
                            
                            uploaded_filenames.append(filename)
                            logger.debug(f"Uploaded face image {i+1} to ComfyUI: {filename}")
                    
                    except Exception as e:
                        logger.error(f"Failed to upload face image {i+1}: {str(e)}")
                        raise
                
                # Replace with filenames array
                prepared["face_images"] = uploaded_filenames
                logger.info(f"Uploaded {len(uploaded_filenames)} face images")
        
        return prepared
    
    async def _extract_result_image(self, history: Dict[str, Any]) -> bytes:
        """
        Extract result image from ComfyUI execution history
        
        Args:
            history: Execution history
        
        Returns:
            Image bytes
        """
        # Extract image information
        images = self.client.extract_output_images(history)
        
        if not images:
            raise ValueError("No output images found in execution history")
        
        # Get first image (assuming single output)
        image_info = images[0]
        
        # Download image
        image_bytes = await self.client.get_image(
            filename=image_info["filename"],
            subfolder=image_info.get("subfolder", ""),
            folder_type=image_info.get("type", "output")
        )
        
        return image_bytes
    
    async def health_check(self) -> bool:
        """
        Check if ComfyUI service is healthy
        
        Returns:
            True if healthy
        """
        return await self.client.health_check()
    
    async def get_queue_status(self) -> Dict[str, Any]:
        """
        Get current queue status
        
        Returns:
            Queue information
        """
        return await self.client.get_queue()
    
    async def interrupt_execution(self) -> bool:
        """
        Interrupt current execution
        
        Returns:
            True if interrupted
        """
        return await self.client.interrupt()


# Singleton instance
_comfyui_service: Optional[ComfyUIService] = None


def get_comfyui_service(
    comfyui_url: str = "http://127.0.0.1:8188",
    workflow_dir: str = "/workspace/workflows",
    timeout: int = 600
) -> ComfyUIService:
    """
    Get or create ComfyUI service singleton
    
    Args:
        comfyui_url: ComfyUI server URL
        workflow_dir: Workflow directory
        timeout: Execution timeout
    
    Returns:
        ComfyUIService instance
    """
    global _comfyui_service
    
    if _comfyui_service is None:
        _comfyui_service = ComfyUIService(
            comfyui_url=comfyui_url,
            workflow_dir=workflow_dir,
            timeout=timeout
        )
        logger.info(f"Initialized ComfyUI service: url={comfyui_url}")
    
    return _comfyui_service
