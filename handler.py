"""
RunPod Serverless Handler for ComfyUI
Production-ready handler with local testing support
"""
import runpod
import os
import sys
import json
import time
import base64
import asyncio
import logging
import subprocess
from typing import Dict, Any
from pathlib import Path
from runpod.serverless.utils.rp_validator import validate

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add project to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import ComfyUI service
from gpu_server.comfyui_service import get_comfyui_service

# Configuration
COMFYUI_DIR = os.getenv("COMFYUI_DIR", "/workspace/ComfyUI")
COMFYUI_URL = os.getenv("COMFYUI_URL", "http://127.0.0.1:8188")  # Замените на ваш RunPod URL
WORKFLOW_DIR = os.getenv("WORKFLOW_DIR", str(PROJECT_ROOT / "gpu_server" / "workflows"))

# Для тестирования с удалённым ComfyUI:
# COMFYUI_URL = "http://your-runpod-host:8188"

# Global state
comfyui_process = None
comfyui_service = None


# Validation schemas for different modes
VALIDATION_SCHEMAS = {
    "free": {
        "mode": {"type": str, "required": True},
        "params": {
            "type": dict,
            "required": True,
            "default": {},
            "fields": {
                "prompt": {"type": str, "required": True},
                "negative_prompt": {"type": str, "required": False, "default": ""},
                "width": {"type": int, "required": False, "default": 1024, "constraints": lambda x: x > 0 and x <= 2048},
                "height": {"type": int, "required": False, "default": 1024, "constraints": lambda x: x > 0 and x <= 2048},
                "steps": {"type": int, "required": False, "default": 30, "constraints": lambda x: x > 0 and x <= 150},
                "cfg_scale": {"type": float, "required": False, "default": 7.5, "constraints": lambda x: x > 0 and x <= 30},
                "seed": {"type": int, "required": False, "default": -1}
            }
        }
    },
    "face_swap": {
        "mode": {"type": str, "required": True},
        "params": {
            "type": dict,
            "required": True,
            "fields": {
                "source_image": {"type": str, "required": True},
                "target_image": {"type": str, "required": True},
                "face_restore_strength": {"type": float, "required": False, "default": 0.8}
            }
        }
    },
    "face_consistent": {
        "mode": {"type": str, "required": True},
        "params": {
            "type": dict,
            "required": True,
            "fields": {
                "face_image": {"type": str, "required": True},
                "prompt": {"type": str, "required": True},
                "negative_prompt": {"type": str, "required": False, "default": ""},
                "ip_adapter_strength": {"type": float, "required": False, "default": 0.7, "constraints": lambda x: 0 <= x <= 1}
            }
        }
    },
    "clothes": {
        "mode": {"type": str, "required": True},
        "params": {
            "type": dict,
            "required": True,
            "fields": {
                "source_image": {"type": str, "required": True},
                "prompt": {"type": str, "required": False, "default": ""},
                "denoise_strength": {"type": float, "required": False, "default": 0.8}
            }
        }
    }
}


def start_comfyui():
    """Start ComfyUI server in background"""
    global comfyui_process
    
    if comfyui_process is not None:
        logger.info("ComfyUI already running")
        return True
    
    logger.info(f"Starting ComfyUI from: {COMFYUI_DIR}")
    
    try:
        # Start ComfyUI
        comfyui_process = subprocess.Popen(
            [sys.executable, "main.py", "--listen", "0.0.0.0", "--port", "8188"],
            cwd=COMFYUI_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for ComfyUI to be ready
        logger.info("Waiting for ComfyUI to start...")
        max_wait = 60
        for i in range(max_wait):
            try:
                import requests
                response = requests.get(f"{COMFYUI_URL}/system_stats", timeout=2)
                if response.status_code == 200:
                    logger.info(f"✅ ComfyUI started successfully in {i} seconds")
                    return True
            except:
                pass
            time.sleep(1)
        
        logger.error("ComfyUI failed to start within timeout")
        return False
        
    except Exception as e:
        logger.error(f"Failed to start ComfyUI: {e}")
        return False


def initialize_service():
    """Initialize ComfyUI service"""
    global comfyui_service
    
    if comfyui_service is None:
        logger.info("Initializing ComfyUI service...")
        comfyui_service = get_comfyui_service(
            comfyui_url=COMFYUI_URL,
            workflow_dir=WORKFLOW_DIR,
            timeout=600
        )
        logger.info("✅ ComfyUI service initialized")
    
    return comfyui_service


def handler(job: Dict[str, Any]) -> Dict[str, Any]:
    """
    RunPod serverless handler
    
    Input format:
    {
        "input": {
            "mode": "free" | "face_swap" | "face_consistent" | "clothes" | "hires_fix",
            "params": {
                "prompt": "...",
                "negative_prompt": "...",
                "width": 1024,
                "height": 1024,
                "steps": 30,
                "cfg_scale": 7.5,
                "seed": -1,
                ... (mode-specific params)
            }
        }
    }
    
    Returns:
    {
        "status": "success" | "error",
        "image": "base64_encoded_image",
        "info": { execution details }
    }
    """
    job_input = job.get('input', {})
    
    try:
        # Extract mode first
        mode = job_input.get('mode', 'free')
        
        # Get appropriate validation schema
        schema = VALIDATION_SCHEMAS.get(mode)
        if not schema:
            return {
                "status": "error",
                "error": f"Unknown mode: {mode}. Available modes: {list(VALIDATION_SCHEMAS.keys())}",
                "error_type": "ValidationError"
            }
        
        # Validate input
        validation_result = validate(job_input, schema)
        
        if "errors" in validation_result:
            logger.error(f"Validation errors: {validation_result['errors']}")
            return {
                "status": "error",
                "error": validation_result["errors"],
                "error_type": "ValidationError"
            }
        
        # Get validated input
        validated_input = validation_result["validated_input"]
        mode = validated_input["mode"]
        params = validated_input.get("params", {})
        
        logger.info(f"Processing job: mode={mode}")
        logger.debug(f"Validated parameters: {params}")
        
        # Ensure ComfyUI service is ready
        service = initialize_service()
        
        # Execute generation synchronously (wrap async)
        import nest_asyncio
        nest_asyncio.apply()
        
        loop = asyncio.get_event_loop()
        image_bytes = loop.run_until_complete(
            service.execute_generation(mode=mode, params=params)
        )
        
        # Encode image to base64
        image_b64 = base64.b64encode(image_bytes).decode('utf-8')
        
        logger.info(f"✅ Generation completed: mode={mode}, size={len(image_bytes)} bytes")
        
        return {
            "status": "success",
            "image": image_b64,
            "info": {
                "mode": mode,
                "size_bytes": len(image_bytes),
                "size_kb": round(len(image_bytes) / 1024, 2)
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Handler error: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "error_type": type(e).__name__
        }


# Cold start initialization
logger.info("="*60)
logger.info("RunPod ComfyUI Handler - Cold Start")
logger.info("="*60)

# Check if ComfyUI directory exists
if not Path(COMFYUI_DIR).exists():
    logger.warning(f"ComfyUI directory not found: {COMFYUI_DIR}")
    logger.info("This is OK for local testing without GPU")
else:
    # Start ComfyUI
    if start_comfyui():
        logger.info("✅ ComfyUI ready")
        # Initialize service
        initialize_service()
    else:
        logger.error("❌ Failed to start ComfyUI")

logger.info("="*60)
logger.info("Handler initialized - Ready for requests")
logger.info("="*60)

# Start RunPod serverless worker
runpod.serverless.start({"handler": handler})
