"""
SDXL Pipeline - Free text-to-image generation
"""
import logging
import base64
from io import BytesIO
from PIL import Image
import torch

from gpu_server.schema import GPUGenerationRequest

logger = logging.getLogger(__name__)


def generate(request: GPUGenerationRequest, models: dict) -> Image.Image:
    """
    Generate image using SDXL base model
    
    Args:
        request: Generation request with prompt and parameters
        models: Dictionary of model loader functions
        
    Returns:
        Generated PIL Image
    """
    logger.info("Starting SDXL free generation")
    
    # Get SDXL pipeline
    pipeline = models["sdxl"]()
    
    # Extract parameters
    prompt = request.prompt or "a beautiful landscape"
    seed = request.seed or torch.randint(0, 2**32, (1,)).item()
    
    # Set generator for reproducibility
    generator = torch.Generator(device=pipeline.device).manual_seed(seed)
    
    # Generate image
    logger.info(f"Generating with prompt: {prompt[:50]}...")
    
    result = pipeline(
        prompt=prompt,
        num_inference_steps=30,
        guidance_scale=7.5,
        generator=generator,
        height=1024,
        width=1024
    )
    
    image = result.images[0]
    
    logger.info("SDXL generation completed")
    
    return image
