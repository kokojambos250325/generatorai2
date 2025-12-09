"""
ComfyUI API Client

Handles communication with ComfyUI API for workflow execution.
Manages workflow loading, parameter injection, and result retrieval.
"""

import httpx
import json
import logging
import base64
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional
import uuid

logger = logging.getLogger(__name__)


class ComfyUIClient:
    """Client for ComfyUI API communication"""
    
    def __init__(self, comfyui_url: str, workflows_path: str, models_path: str):
        """
        Initialize ComfyUI client.
        
        Args:
            comfyui_url: ComfyUI API URL (e.g., http://localhost:8188)
            workflows_path: Path to workflow JSON files
            models_path: Path to models directory
        """
        self.comfyui_url = comfyui_url.rstrip('/')
        self.workflows_path = Path(workflows_path)
        self.models_path = Path(models_path)
        self.timeout = 300.0  # 5 minutes for generation
    
    async def check_health(self) -> bool:
        """
        Check if ComfyUI is available.
        
        Returns:
            bool: True if ComfyUI is responsive
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.comfyui_url}/system_stats")
                return response.status_code == 200
        except Exception as e:
            logger.warning(f"ComfyUI health check failed: {e}")
            return False
    
    def load_workflow(self, workflow_name: str) -> Dict[str, Any]:
        """
        Load workflow JSON from disk.
        
        Args:
            workflow_name: Workflow filename (without .json)
        
        Returns:
            dict: Workflow definition
        
        Raises:
            FileNotFoundError: If workflow file doesn't exist
        """
        workflow_file = self.workflows_path / f"{workflow_name}.json"
        
        if not workflow_file.exists():
            raise FileNotFoundError(f"Workflow not found: {workflow_file}")
        
        with open(workflow_file, 'r', encoding='utf-8') as f:
            workflow = json.load(f)
        
        logger.info(f"Loaded workflow: {workflow_name}")
        return workflow
    
    def inject_parameters(self, workflow: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Inject dynamic parameters into workflow.
        
        Args:
            workflow: Base workflow definition
            params: Parameters to inject (prompt, seed, steps, cfg, etc.)
        
        Returns:
            dict: Workflow with injected parameters
        """
        logger.info(f"Injecting parameters: {list(params.keys())}")
        
        # Deep copy to avoid modifying original
        import copy
        modified_workflow = copy.deepcopy(workflow)
        
        # Inject prompt into CLIPTextEncode node (node 6)
        if "prompt" in params and "6" in modified_workflow:
            modified_workflow["6"]["inputs"]["text"] = params["prompt"]
            logger.info(f"Injected prompt: {params['prompt']}")
        
        # Inject negative prompt if provided
        if "negative_prompt" in params and "7" in modified_workflow:
            modified_workflow["7"]["inputs"]["text"] = params["negative_prompt"]
        
        # Inject sampling parameters into KSampler (node 3)
        if "3" in modified_workflow:
            if "seed" in params:
                modified_workflow["3"]["inputs"]["seed"] = params["seed"]
            if "steps" in params:
                modified_workflow["3"]["inputs"]["steps"] = params["steps"]
            if "cfg" in params:
                modified_workflow["3"]["inputs"]["cfg"] = params["cfg"]
        
        # Inject image dimensions into EmptyLatentImage (node 5)
        if "5" in modified_workflow:
            if "width" in params:
                modified_workflow["5"]["inputs"]["width"] = params["width"]
            if "height" in params:
                modified_workflow["5"]["inputs"]["height"] = params["height"]
        
        return modified_workflow
    
    async def submit_workflow(self, workflow: Dict[str, Any]) -> str:
        """
        Submit workflow to ComfyUI for execution.
        
        Args:
            workflow: Complete workflow with parameters
        
        Returns:
            str: Prompt ID for tracking
        
        Raises:
            Exception: If submission fails
        """
        try:
            # Generate unique client ID
            client_id = str(uuid.uuid4())
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.comfyui_url}/prompt",
                    json={
                        "prompt": workflow,
                        "client_id": client_id
                    }
                )
                
                response.raise_for_status()
                result = response.json()
                
                prompt_id = result.get("prompt_id")
                if not prompt_id:
                    raise Exception("No prompt_id returned from ComfyUI")
                
                logger.info(f"Workflow submitted: prompt_id={prompt_id}")
                return prompt_id
        
        except Exception as e:
            logger.error(f"Failed to submit workflow: {e}")
            raise Exception(f"Workflow submission failed: {str(e)}")
    
    async def wait_for_completion(self, prompt_id: str) -> Dict[str, Any]:
        """
        Poll ComfyUI until workflow completes.
        
        Args:
            prompt_id: Prompt ID to track
        
        Returns:
            dict: Execution result
        
        Raises:
            Exception: If execution fails or times out
        """
        max_attempts = 60  # 5 minutes with 5-second intervals
        attempt = 0
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            while attempt < max_attempts:
                try:
                    response = await client.get(f"{self.comfyui_url}/history/{prompt_id}")
                    
                    if response.status_code == 200:
                        history = response.json()
                        
                        if prompt_id in history:
                            result = history[prompt_id]
                            
                            # Check if completed
                            if result.get("status", {}).get("completed", False):
                                logger.info(f"Workflow completed: prompt_id={prompt_id}")
                                return result
                            
                            # Check for errors
                            if "error" in result.get("status", {}):
                                error_msg = result["status"]["error"]
                                raise Exception(f"Workflow failed: {error_msg}")
                    
                    # Wait before next poll
                    await asyncio.sleep(5.0)
                    attempt += 1
                
                except httpx.HTTPError as e:
                    logger.warning(f"Polling error (attempt {attempt}): {e}")
                    await asyncio.sleep(5.0)
                    attempt += 1
        
        raise Exception(f"Workflow timeout after {max_attempts * 5} seconds")
    
    async def get_output_image(self, result: Dict[str, Any]) -> str:
        """
        Extract output image from workflow result and encode to base64.
        
        Args:
            result: Workflow execution result
        
        Returns:
            str: Base64 encoded image
        
        Raises:
            Exception: If image extraction fails
        """
        try:
            # Navigate result structure to find output images
            outputs = result.get("outputs", {})
            
            # Find first image output (this structure depends on workflow)
            for node_id, node_output in outputs.items():
                if "images" in node_output:
                    images = node_output["images"]
                    if images:
                        # Get first image
                        image_info = images[0]
                        filename = image_info["filename"]
                        subfolder = image_info.get("subfolder", "")
                        
                        # Download image from ComfyUI
                        async with httpx.AsyncClient(timeout=30.0) as client:
                            params = {"filename": filename}
                            if subfolder:
                                params["subfolder"] = subfolder
                            
                            response = await client.get(
                                f"{self.comfyui_url}/view",
                                params=params
                            )
                            
                            response.raise_for_status()
                            image_bytes = response.content
                            
                            # Encode to base64
                            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
                            
                            logger.info(f"Retrieved output image: {filename}")
                            return image_base64
            
            raise Exception("No output images found in result")
        
        except Exception as e:
            logger.error(f"Failed to get output image: {e}")
            raise Exception(f"Image retrieval failed: {str(e)}")
    
    async def execute_workflow(self, workflow_name: str, params: Dict[str, Any]) -> str:
        """
        Complete workflow execution pipeline.
        
        Args:
            workflow_name: Name of workflow to execute
            params: Generation parameters
        
        Returns:
            str: Base64 encoded result image
        
        Raises:
            Exception: If any step fails
        """
        logger.info(f"Executing workflow: {workflow_name}")
        
        # Load workflow
        workflow = self.load_workflow(workflow_name)
        
        # Inject parameters
        workflow = self.inject_parameters(workflow, params)
        
        # Submit to ComfyUI
        prompt_id = await self.submit_workflow(workflow)
        
        # Wait for completion
        result = await self.wait_for_completion(prompt_id)
        
        # Get output image
        image_base64 = await self.get_output_image(result)
        
        logger.info(f"Workflow execution complete: {workflow_name}")
        return image_base64
