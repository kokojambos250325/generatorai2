"""
Inference Worker
Background worker that processes generation tasks from queue
"""
import os
import logging
import time
import traceback
from typing import Optional

from gpu_server.server.utils.queue import TaskQueue
from gpu_server.server.models_loader import ModelLoader
from gpu_server.schema import GPUGenerationRequest
from gpu_server.comfyui_service import ComfyUIService
import asyncio

logger = logging.getLogger(__name__)


class GPUWorker:
    """
    Background worker for processing inference tasks
    """
    
    def __init__(self, task_queue: TaskQueue):
        self.task_queue = task_queue
        self.model_loader = ModelLoader()
        self.is_running = False
        self.task_timeout = int(os.getenv("WORKER_TIMEOUT", "300"))  # 5 minutes default
        
        # Initialize ComfyUI service
        comfyui_url = os.getenv("COMFYUI_URL", "http://localhost:8188")
        self.comfyui_service = ComfyUIService(
            comfyui_url=comfyui_url,
            workflow_dir="/workspace/workflows",
            timeout=self.task_timeout
        )
        logger.info(f"ComfyUI service initialized with URL: {comfyui_url}")
    
    def run(self):
        """
        Main worker loop
        Continuously polls queue and processes tasks
        """
        self.is_running = True
        logger.info("Worker started, polling for tasks...")
        
        while self.is_running:
            try:
                # Poll for next task
                task = self.task_queue.dequeue_task()
                
                if task:
                    self._process_task(task)
                else:
                    # No tasks, sleep briefly
                    time.sleep(1)
            
            except Exception as e:
                logger.error(f"Worker error: {str(e)}\n{traceback.format_exc()}")
                time.sleep(5)  # Back off on error
    
    def stop(self):
        """
        Stop the worker gracefully
        """
        logger.info("Stopping worker...")
        self.is_running = False
    
    def _process_task(self, task: dict):
        """
        Process a single task
        
        Args:
            task: Task dictionary from queue
        """
        task_id = task["task_id"]
        request: GPUGenerationRequest = task["request"]
        
        logger.info(f"Processing task {task_id} with mode {request.mode}")
        
        try:
            # Update status to processing
            self.task_queue.update_status(task_id, "processing", progress=0.1)
            
            # Route to appropriate pipeline
            result_image = self._execute_pipeline(request)
            
            # Save result
            from gpu_server.server.utils.storage import save_image
            save_image(task_id, result_image)
            
            # Update status to completed
            self.task_queue.set_result(task_id, f"{task_id}.png")
            
            logger.info(f"Task {task_id} completed successfully")
        
        except Exception as e:
            error_msg = f"Task failed: {str(e)}"
            logger.error(f"Task {task_id} failed: {str(e)}\n{traceback.format_exc()}")
            self.task_queue.set_error(task_id, error_msg)
    
    def _execute_pipeline(self, request: GPUGenerationRequest):
        """
        Execute generation pipeline based on mode using ComfyUI
        
        Args:
            request: Generation request parameters
            
        Returns:
            PIL.Image: Generated image
        """
        mode = request.mode
        logger.info(f"Executing {mode} pipeline via ComfyUI")
        
        # Prepare parameters for ComfyUI
        params = {
            "prompt": getattr(request, "prompt", ""),
            "negative_prompt": getattr(request, "negative_prompt", "low quality, blurry"),
            "width": getattr(request, "width", 1024),
            "height": getattr(request, "height", 1024),
            "steps": getattr(request, "steps", 20),
            "seed": getattr(request, "seed", 42),
            "cfg_scale": getattr(request, "cfg_scale", 7.5),
        }
        
        # Add mode-specific parameters
        if hasattr(request, "source_image"):
            params["source_image"] = request.source_image
        if hasattr(request, "target_image"):
            params["target_image"] = request.target_image
        if hasattr(request, "face_image"):
            params["face_image"] = request.face_image
        
        # Execute via ComfyUI using asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            # Execute generation
            image_bytes = loop.run_until_complete(
                self.comfyui_service.execute_generation(mode, params)
            )
            
            # Convert bytes to PIL Image
            from PIL import Image
            import io
            image = Image.open(io.BytesIO(image_bytes))
            return image
            
        finally:
            loop.close()
