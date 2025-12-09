"""
FastAPI GPU Server Main Application
Entry point for autonomous GPU inference server
"""
import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import threading

from gpu_server.server.router import router
from gpu_server.server.inference_worker import GPUWorker
from gpu_server.server.utils.queue import task_queue

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global instances
# Use the global task_queue instance from utils.queue
worker = None
worker_thread = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager
    Starts worker on startup, stops on shutdown
    """
    global worker, worker_thread
    
    logger.info("Starting GPU server...")
    
    # Initialize and start worker thread
    worker = GPUWorker(task_queue)
    worker_thread = threading.Thread(target=worker.run, daemon=True)
    worker_thread.start()
    logger.info("Inference worker started")
    
    yield
    
    # Cleanup on shutdown
    logger.info("Shutting down GPU server...")
    if worker:
        worker.stop()
    if worker_thread:
        worker_thread.join(timeout=5)
    logger.info("GPU server stopped")


# Create FastAPI application
app = FastAPI(
    title="GPU Inference Server",
    description="Autonomous SDXL/ControlNet generation server",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API router
app.include_router(router, prefix="/api")

# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Enhanced health check endpoint with model readiness reporting
    
    Returns comprehensive server status including:
    - Overall status (ok/degraded/error)
    - GPU availability and information
    - Individual model loading status
    - Server runtime metrics
    """
    import torch
    import time
    
    try:
        # Get GPU information
        gpu_available = torch.cuda.is_available()
        
        gpu_info = {}
        if gpu_available:
            gpu_info = {
                "name": torch.cuda.get_device_name(0),
                "memory_total": f"{torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f}GB",
                "memory_used": f"{torch.cuda.memory_allocated(0) / 1024**3:.2f}GB",
                "memory_reserved": f"{torch.cuda.memory_reserved(0) / 1024**3:.2f}GB"
            }
        
        # Check model loading status
        # Note: ModelManager will be initialized on first use, so may not exist yet
        models_status = {
            "sdxl_base": False,
            "sdxl_refiner": False,
            "controlnet_pose": False,
            "controlnet_depth": False,
            "controlnet_canny": False,
            "insightface": False,
            "gfpgan": False,
            "esrgan": False
        }
        
        # Try to get model status from worker if available
        if worker and hasattr(worker, 'model_loader'):
            model_loader = worker.model_loader
            if model_loader:
                # Check which models are cached
                models_status["sdxl_base"] = "sdxl_base" in model_loader.cache
                models_status["controlnet_pose"] = "controlnet_pose" in model_loader.cache
                models_status["controlnet_depth"] = "controlnet_depth" in model_loader.cache
                models_status["controlnet_canny"] = "controlnet_canny" in model_loader.cache
        
        # Determine overall status
        critical_models_loaded = models_status["sdxl_base"]
        any_controlnet_loaded = (
            models_status["controlnet_pose"] or 
            models_status["controlnet_depth"] or 
            models_status["controlnet_canny"]
        )
        
        if gpu_available and critical_models_loaded and any_controlnet_loaded:
            overall_status = "ok"
        elif gpu_available or critical_models_loaded:
            overall_status = "degraded"
        else:
            overall_status = "error"
        
        # Server info
        server_info = {
            "queue_size": task_queue.get_queue_size(),
            "worker_status": "running" if worker and getattr(worker, 'is_running', False) else "stopped"
        }
        
        return {
            "status": overall_status,
            "gpu_available": gpu_available,
            "models": models_status,
            "gpu_info": gpu_info,
            "server_info": server_info
        }
        
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return {
            "status": "error",
            "gpu_available": False,
            "models": {},
            "gpu_info": {},
            "server_info": {"error": str(e)}
        }


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("GPU_SERVER_PORT", 3000))
    
    uvicorn.run(
        "gpu_server.server.main:app",
        host="0.0.0.0",
        port=port,
        workers=1,
        log_level=os.getenv("LOG_LEVEL", "info").lower()
    )
