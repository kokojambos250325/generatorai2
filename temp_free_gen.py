"""
Free Generation Service
"""
import logging
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from schemas.request_free import FreeGenerationRequest
from clients.gpu_client import GPUClient
from config_styles import STYLE_CONFIG

# Configure JSON logger
logger = logging.getLogger(__name__)
json_handler = logging.FileHandler('/workspace/logs/backend.log')
json_handler.setFormatter(logging.Formatter('%(message)s'))
logger.addHandler(json_handler)
logger.setLevel(logging.INFO)

class FreeGenerationService:
    def __init__(self, gpu_client: GPUClient):
        self.gpu_client = gpu_client

    def _resolve_parameters(self, style: str, extra_params: Optional[Any]) -> Dict[str, Any]:
        style_cfg = STYLE_CONFIG[style]
        params = {
            "steps": style_cfg["default_steps"],
            "cfg": style_cfg["default_cfg"],
            "sampler": style_cfg["default_sampler"],
            "width": style_cfg["default_resolution"]["width"],
            "height": style_cfg["default_resolution"]["height"],
            "seed": -1
        }
        if extra_params:
            if hasattr(extra_params, "steps") and extra_params.steps is not None:
                params["steps"] = extra_params.steps
            if hasattr(extra_params, "cfg_scale") and extra_params.cfg_scale is not None:
                params["cfg"] = extra_params.cfg_scale
            if hasattr(extra_params, "sampler") and extra_params.sampler is not None:
                params["sampler"] = extra_params.sampler
            if hasattr(extra_params, "width") and extra_params.width is not None:
                params["width"] = extra_params.width
            if hasattr(extra_params, "height") and extra_params.height is not None:
                params["height"] = extra_params.height
            if hasattr(extra_params, "seed") and extra_params.seed is not None:
                params["seed"] = extra_params.seed
        return params

    async def generate(self, request: FreeGenerationRequest) -> str:
        # Generate unique request_id for tracing
        request_id = str(uuid.uuid4())
        
        # Event 1: generate_request
        log_entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": "INFO",
            "service": "backend",
            "event": "generate_request",
            "request_id": request_id,
            "client": "tg_bot",
            "mode": "free",
            "style": request.style,
            "prompt_length": len(request.prompt),
            "images_count": 0,
            "extra_params": request.extra_params.dict() if request.extra_params else {}
        }
        logger.info(json.dumps(log_entry))
        
        try:
            # Validate style
            if request.style not in STYLE_CONFIG:
                # Event 2: validation_error
                log_entry = {
                    "ts": datetime.now(timezone.utc).isoformat(),
                    "level": "ERROR",
                    "service": "backend",
                    "event": "validation_error",
                    "request_id": request_id,
                    "error_type": "invalid_style",
                    "details": {"style": request.style, "valid_styles": list(STYLE_CONFIG.keys())}
                }
                logger.error(json.dumps(log_entry))
                raise ValueError(f"Invalid style: {request.style}")
            
            style_cfg = STYLE_CONFIG[request.style]
            full_prompt = style_cfg["prompt_prefix"] + request.prompt
            negative_prompt = style_cfg["negative_prompt"]
            resolved_params = self._resolve_parameters(request.style, request.extra_params)
            
            gpu_params = {
                "mode": "free",
                "prompt": full_prompt,
                "negative_prompt": negative_prompt,
                "model": style_cfg["model"],
                **resolved_params
            }
            
            # Event 3: gpu_request
            log_entry = {
                "ts": datetime.now(timezone.utc).isoformat(),
                "level": "INFO",
                "service": "backend",
                "event": "gpu_request",
                "request_id": request_id,
                "gpu_endpoint": "execute",
                "workflow": "free_generation",
                "params": {
                    "steps": resolved_params["steps"],
                    "cfg": resolved_params["cfg"],
                    "width": resolved_params["width"],
                    "height": resolved_params["height"],
                    "sampler": resolved_params["sampler"]
                }
            }
            logger.info(json.dumps(log_entry))
            
            # Call GPU server
            result = await self.gpu_client.generate(gpu_params)
            
            # Event 4: gpu_response
            log_entry = {
                "ts": datetime.now(timezone.utc).isoformat(),
                "level": "INFO",
                "service": "backend",
                "event": "gpu_response",
                "request_id": request_id,
                "status": "done",
                "image_size_bytes": len(result) if isinstance(result, str) else 0
            }
            logger.info(json.dumps(log_entry))
            
            # Event 5: response_sent
            log_entry = {
                "ts": datetime.now(timezone.utc).isoformat(),
                "level": "INFO",
                "service": "backend",
                "event": "response_sent",
                "request_id": request_id,
                "to_client": "tg_bot"
            }
            logger.info(json.dumps(log_entry))
            
            return result
            
        except Exception as e:
            # Event 6: timeout_error (or general error)
            log_entry = {
                "ts": datetime.now(timezone.utc).isoformat(),
                "level": "ERROR",
                "service": "backend",
                "event": "timeout_error" if "timeout" in str(e).lower() else "error",
                "request_id": request_id,
                "error_message": str(e),
                "error_type": type(e).__name__
            }
            logger.error(json.dumps(log_entry))
            raise

