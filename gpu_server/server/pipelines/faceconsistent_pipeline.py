"""
Face Consistent Pipeline - Generate new images maintaining face identity
"""
import logging
import base64
from io import BytesIO
from PIL import Image
import torch
import numpy as np

from gpu_server.schema import GPUGenerationRequest

logger = logging.getLogger(__name__)


def _decode_base64_image(base64_str: str) -> Image.Image:
    """Decode base64 string to PIL Image"""
    img_bytes = base64.b64decode(base64_str)
    image = Image.open(BytesIO(img_bytes)).convert("RGB")
    return image


def generate(request: GPUGenerationRequest, models: dict) -> Image.Image:
    """
    Generate image with face consistency using InsightFace + SDXL
    
    Args:
        request: Generation request with face_image, prompt, and parameters
        models: Dictionary of model loader functions
        
    Returns:
        Generated PIL Image with consistent face
    """
    logger.info("Starting face consistent generation")
    
    # Get models
    sdxl_pipeline = models["sdxl"]()
    insightface_app = models["insightface"]()
    
    # Decode face reference
    if not request.face_image:
        raise ValueError("Face consistent mode requires face_image")
    
    face_image = _decode_base64_image(request.face_image)
    face_array = np.array(face_image)
    
    # Extract face embedding
    faces = insightface_app.get(face_array)
    
    if not faces:
        raise ValueError("No face detected in reference image")
    
    face_embedding = faces[0].embedding
    logger.info(f"Extracted face embedding from reference image")
    
    # Extract parameters
    prompt = request.prompt or "portrait photo, high quality"
    seed = request.seed or torch.randint(0, 2**32, (1,)).item()
    
    # Set generator
    generator = torch.Generator(device=sdxl_pipeline.device).manual_seed(seed)
    
    # Generate image
    # NOTE: This is a simplified implementation
    # In production, use IP-Adapter or face LoRA to inject face embedding
    # For now, just generate with prompt
    
    logger.info(f"Generating with prompt: {prompt[:50]}...")
    
    # TODO: Integrate IP-Adapter for face embedding injection
    # from ip_adapter import IPAdapter
    # ip_adapter = IPAdapter(sdxl_pipeline, image_encoder_path, ip_ckpt_path)
    # image = ip_adapter.generate(pil_image=face_image, prompt=prompt, ...)
    
    result = sdxl_pipeline(
        prompt=prompt,
        num_inference_steps=30,
        guidance_scale=7.5,
        generator=generator,
        height=1024,
        width=1024
    )
    
    image = result.images[0]
    
    logger.info("Face consistent generation completed (simplified implementation)")
    
    return image
