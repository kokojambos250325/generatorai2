"""
RunPod Serverless Handler
Wraps GPU inference for RunPod serverless deployment
"""
import runpod
import os
import sys
import asyncio
import logging
from typing import Dict, Any

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gpu_server.server.pipelines.sdxl_pipeline import SDXLPipeline
from gpu_server.server.pipelines.controlnet_pipeline import ControlNetPipeline
from gpu_server.server.pipelines.faceswap_pipeline import FaceSwapPipeline
from gpu_server.server.pipelines.faceconsistent_pipeline import FaceConsistentPipeline
from gpu_server.server.pipelines.clothes_pipeline import ClothesRemovalPipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global pipeline instances (loaded once on cold start)
pipelines = {}


def initialize_pipelines():
    """Initialize all pipelines on cold start"""
    global pipelines
    
    try:
        logger.info("Initializing pipelines...")
        
        # Initialize SDXL pipeline (most common)
        pipelines['sdxl'] = SDXLPipeline()
        logger.info("✓ SDXL pipeline ready")
        
        # Initialize ControlNet pipeline
        pipelines['controlnet'] = ControlNetPipeline()
        logger.info("✓ ControlNet pipeline ready")
        
        # Initialize FaceSwap pipeline
        pipelines['faceswap'] = FaceSwapPipeline()
        logger.info("✓ FaceSwap pipeline ready")
        
        # Initialize FaceConsistent pipeline
        pipelines['face_consistent'] = FaceConsistentPipeline()
        logger.info("✓ FaceConsistent pipeline ready")
        
        # Initialize Clothes Removal pipeline
        pipelines['clothes'] = ClothesRemovalPipeline()
        logger.info("✓ Clothes Removal pipeline ready")
        
        logger.info(f"All {len(pipelines)} pipelines initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize pipelines: {e}")
        raise


def handler(job: Dict[str, Any]) -> Dict[str, Any]:
    """
    RunPod serverless handler function
    
    Args:
        job: RunPod job containing input parameters
        
    Returns:
        Result dictionary with generated images or error
    """
    job_input = job.get('input', {})
    
    try:
        # Extract pipeline type
        pipeline_type = job_input.get('pipeline', 'sdxl')
        
        logger.info(f"Processing job with pipeline: {pipeline_type}")
        
        # Get appropriate pipeline
        if pipeline_type not in pipelines:
            return {
                "error": f"Unknown pipeline type: {pipeline_type}. Available: {list(pipelines.keys())}"
            }
        
        pipeline = pipelines[pipeline_type]
        
        # Run generation (synchronously)
        result = pipeline.generate(job_input)
        
        logger.info(f"Generation completed successfully")
        
        return {
            "status": "success",
            "output": result
        }
        
    except Exception as e:
        logger.error(f"Handler error: {e}", exc_info=True)
        return {
            "error": str(e),
            "status": "failed"
        }


# Initialize pipelines on cold start
logger.info("Cold start: initializing pipelines...")
initialize_pipelines()

# Start RunPod serverless worker
runpod.serverless.start({"handler": handler})
