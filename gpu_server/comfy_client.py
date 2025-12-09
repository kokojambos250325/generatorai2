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
import time
from pathlib import Path
from typing import Dict, Any, Optional
import uuid

from json_logging import log_event

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
    
    def load_workflow(self, workflow_name: str, generation_id: str = None, request_id: str = None) -> Dict[str, Any]:
        """
        Load workflow JSON from disk.
        
        Args:
            workflow_name: Workflow filename (without .json)
            generation_id: Optional generation ID for logging
            request_id: Optional request ID for tracing
        
        Returns:
            dict: Workflow definition
        
        Raises:
            FileNotFoundError: If workflow file doesn't exist
        """
        workflow_file = self.workflows_path / f"{workflow_name}.json"
        
        if not workflow_file.exists():
            log_event(
                logger=logger,
                level="ERROR",
                event="error_workflow",
                message=f"Workflow not found: {workflow_file}",
                generation_id=generation_id,
                request_id=request_id,
                workflow=workflow_name,
                error_type="FileNotFoundError"
            )
            raise FileNotFoundError(f"Workflow not found: {workflow_file}")
        
        with open(workflow_file, 'r', encoding='utf-8') as f:
            workflow = json.load(f)
        
        # Count nodes in workflow
        node_count = len(workflow) if isinstance(workflow, dict) else 0
        
        log_event(
            logger=logger,
            level="INFO",
            event="workflow_loaded",
            message=f"Loaded workflow: {workflow_name}",
            generation_id=generation_id,
            request_id=request_id,
            workflow=workflow_name,
            node_count=node_count
        )
        
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
            logger.info(f"Injected prompt: {params['prompt'][:100]}...")
        
        # Inject negative prompt if provided
        if "negative_prompt" in params and "7" in modified_workflow:
            modified_workflow["7"]["inputs"]["text"] = params["negative_prompt"]
        
        # Inject checkpoint/model into CheckpointLoader (node 4)
        if "checkpoint" in params and "4" in modified_workflow:
            modified_workflow["4"]["inputs"]["ckpt_name"] = params["checkpoint"]
            logger.info(f"Injected checkpoint: {params['checkpoint']}")
        
        # Inject sampling parameters into KSampler (node 3)
        if "3" in modified_workflow:
            if "seed" in params:
                modified_workflow["3"]["inputs"]["seed"] = params["seed"]
            if "steps" in params:
                modified_workflow["3"]["inputs"]["steps"] = params["steps"]
            if "cfg" in params:
                modified_workflow["3"]["inputs"]["cfg"] = params["cfg"]
            if "sampler" in params:
                modified_workflow["3"]["inputs"]["sampler_name"] = params["sampler"]
            if "scheduler" in params:
                modified_workflow["3"]["inputs"]["scheduler"] = params["scheduler"]
        
        # Inject image dimensions into EmptyLatentImage (node 5)
        if "5" in modified_workflow:
            if "width" in params:
                modified_workflow["5"]["inputs"]["width"] = params["width"]
            if "height" in params:
                modified_workflow["5"]["inputs"]["height"] = params["height"]
        
        return modified_workflow
    
    async def submit_workflow(self, workflow: Dict[str, Any], generation_id: str = None, request_id: str = None) -> str:
        """
        Submit workflow to ComfyUI for execution.
        
        Args:
            workflow: Complete workflow with parameters
            generation_id: Optional generation ID for logging
            request_id: Optional request ID for tracing
        
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
                
                log_event(
                    logger=logger,
                    level="INFO",
                    event="comfyui_prompt_sent",
                    message=f"Workflow submitted to ComfyUI: prompt_id={prompt_id}",
                    generation_id=generation_id,
                    request_id=request_id,
                    prompt_id=prompt_id,
                    endpoint="/prompt"
                )
                
                return prompt_id
        
        except Exception as e:
            log_event(
                logger=logger,
                level="ERROR",
                event="error_comfyui",
                message=f"Failed to submit workflow: {e}",
                generation_id=generation_id,
                request_id=request_id,
                error_type=type(e).__name__,
                endpoint="/prompt"
            )
            raise Exception(f"Workflow submission failed: {str(e)}")
    
    async def wait_for_completion(self, prompt_id: str, generation_id: str = None, request_id: str = None) -> Dict[str, Any]:
        """
        Poll ComfyUI until workflow completes.
        
        Args:
            prompt_id: Prompt ID to track
            generation_id: Optional generation ID for logging
            request_id: Optional request ID for tracing
        
        Returns:
            dict: Execution result
        
        Raises:
            Exception: If execution fails or times out
        """
        max_attempts = 60  # 5 minutes with 5-second intervals
        attempt = 0
        start_time = time.time()
        
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
                                duration_ms = int((time.time() - start_time) * 1000)
                                
                                log_event(
                                    logger=logger,
                                    level="INFO",
                                    event="comfyui_complete",
                                    message=f"Workflow completed: prompt_id={prompt_id}",
                                    generation_id=generation_id,
                                    request_id=request_id,
                                    prompt_id=prompt_id,
                                    duration_ms=duration_ms
                                )
                                
                                return result
                            
                            # Check for errors
                            if "error" in result.get("status", {}):
                                error_msg = result["status"]["error"]
                                
                                log_event(
                                    logger=logger,
                                    level="ERROR",
                                    event="error_comfyui",
                                    message=f"Workflow failed: {error_msg}",
                                    generation_id=generation_id,
                                    request_id=request_id,
                                    prompt_id=prompt_id,
                                    error_type="workflow_execution_error"
                                )
                                
                                raise Exception(f"Workflow failed: {error_msg}")
                    
                    # Log polling progress every 10 attempts
                    if attempt > 0 and attempt % 10 == 0:
                        log_event(
                            logger=logger,
                            level="INFO",
                            event="comfyui_polling",
                            message=f"Polling ComfyUI: attempt {attempt}/{max_attempts}",
                            generation_id=generation_id,
                            request_id=request_id,
                            prompt_id=prompt_id,
                            attempt=attempt,
                            max_attempts=max_attempts
                        )
                    
                    # Wait before next poll
                    await asyncio.sleep(5.0)
                    attempt += 1
                
                except httpx.HTTPError as e:
                    logger.warning(f"Polling error (attempt {attempt}): {e}")
                    await asyncio.sleep(5.0)
                    attempt += 1
        
        # Timeout error
        log_event(
            logger=logger,
            level="ERROR",
            event="error_comfyui",
            message=f"Workflow timeout after {max_attempts * 5} seconds",
            generation_id=generation_id,
            request_id=request_id,
            prompt_id=prompt_id,
            error_type="timeout",
            timeout_seconds=max_attempts * 5
        )
        
        raise Exception(f"Workflow timeout after {max_attempts * 5} seconds")
    
    async def get_output_image(self, result: Dict[str, Any], generation_id: str = None, request_id: str = None) -> str:
        """
        Extract output image from workflow result and encode to base64.
        
        Args:
            result: Workflow execution result
            generation_id: Optional generation ID for logging
            request_id: Optional request ID for tracing
        
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
                            file_size_bytes = len(image_bytes)
                            
                            # Encode to base64
                            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
                            
                            log_event(
                                logger=logger,
                                level="INFO",
                                event="image_retrieved",
                                message=f"Retrieved output image: {filename}",
                                generation_id=generation_id,
                                request_id=request_id,
                                filename=filename,
                                file_size_bytes=file_size_bytes
                            )
                            
                            return image_base64
            
            raise Exception("No output images found in result")
        
        except Exception as e:
            log_event(
                logger=logger,
                level="ERROR",
                event="error_comfyui",
                message=f"Failed to get output image: {e}",
                generation_id=generation_id,
                request_id=request_id,
                error_type=type(e).__name__,
                endpoint="/view"
            )
            raise Exception(f"Image retrieval failed: {str(e)}")
    
    async def execute_workflow(self, workflow_name: str, params: Dict[str, Any], 
                              generation_id: str = None, request_id: str = None) -> str:
        """
        Complete workflow execution pipeline.
        
        Args:
            workflow_name: Name of workflow to execute
            params: Generation parameters
            generation_id: Optional generation ID for logging
            request_id: Optional request ID for tracing
        
        Returns:
            str: Base64 encoded result image
        
        Raises:
            Exception: If any step fails
        """
        logger.info(f"Executing workflow: {workflow_name} (gen_id={generation_id}, req_id={request_id})")
        
        # Load workflow
        workflow = self.load_workflow(workflow_name, generation_id=generation_id, request_id=request_id)
        
        # Inject parameters
        workflow = self.inject_parameters(workflow, params)
        
        # Submit to ComfyUI
        prompt_id = await self.submit_workflow(workflow, generation_id=generation_id, request_id=request_id)
        
        # Wait for completion
        result = await self.wait_for_completion(prompt_id, generation_id=generation_id, request_id=request_id)
        
        # Get output image
        image_base64 = await self.get_output_image(result, generation_id=generation_id, request_id=request_id)
        
        logger.info(f"Workflow execution complete: {workflow_name}")
        return image_base64
