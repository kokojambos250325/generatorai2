"""
Clothes Pipeline - Generate person wearing specific clothing
"""
import logging
import base64
from io import BytesIO
from PIL import Image
import torch
import numpy as np
import cv2

from gpu_server.schema import GPUGenerationRequest

logger = logging.getLogger(__name__)


def _decode_base64_image(base64_str: str) -> Image.Image:
    """Decode base64 string to PIL Image"""
    img_bytes = base64.b64decode(base64_str)
    image = Image.open(BytesIO(img_bytes)).convert("RGB")
    return image


def _segment_clothing(image: Image.Image) -> Image.Image:
    """
    Segment clothing from image (placeholder)
    In production, use proper cloth segmentation model
    """
    # Placeholder: return the image as-is
    # TODO: Implement cloth segmentation
    return image


def generate(request: GPUGenerationRequest, models: dict) -> Image.Image:
    """
    Generate person wearing specific clothing
    
    Args:
        request: Generation request with clothes_image and optional face_image
        models: Dictionary of model loader functions
        
    Returns:
        Generated PIL Image
    """
    logger.info("Starting clothes generation")
    
    # Get models
    sdxl_pipeline = models["sdxl"]()
    controlnet = models["controlnet"]("canny")
    
    # Decode clothing image
    if not request.clothes_image:
        raise ValueError("Clothes mode requires clothes_image")
    
    clothes_image = _decode_base64_image(request.clothes_image)
    
    # Segment clothing
    clothing_mask = _segment_clothing(clothes_image)
    
    # If face provided, extract face embedding
    face_embedding = None
    if request.face_image:
        insightface_app = models["insightface"]()
        face_image = _decode_base64_image(request.face_image)
        face_array = np.array(face_image)
        faces = insightface_app.get(face_array)
        
        if faces:
            face_embedding = faces[0].embedding
            logger.info("Extracted face embedding for clothes generation")
    
    # Extract parameters
    prompt = request.prompt or "person wearing stylish outfit, high quality photo"
    seed = request.seed or torch.randint(0, 2**32, (1,)).item()
    
    # Set generator
    generator = torch.Generator(device=sdxl_pipeline.device).manual_seed(seed)
    
    # Preprocess clothing image for ControlNet
    clothes_array = np.array(clothes_image)
    edges = cv2.Canny(clothes_array, 100, 200)
    edges = cv2.cvtColor(edges, cv2.COLOR_GRAY2RGB)
    control_image = Image.fromarray(edges)
    
    # Create ControlNet pipeline
    from diffusers import StableDiffusionXLControlNetPipeline
    
    pipeline = StableDiffusionXLControlNetPipeline(
        vae=sdxl_pipeline.vae,
        text_encoder=sdxl_pipeline.text_encoder,
        text_encoder_2=sdxl_pipeline.text_encoder_2,
        tokenizer=sdxl_pipeline.tokenizer,
        tokenizer_2=sdxl_pipeline.tokenizer_2,
        unet=sdxl_pipeline.unet,
        controlnet=controlnet,
        scheduler=sdxl_pipeline.scheduler,
    ).to(sdxl_pipeline.device)
    
    # Enable optimizations
    pipeline.enable_attention_slicing()
    pipeline.enable_vae_tiling()
    
    # Generate
    logger.info(f"Generating clothes with prompt: {prompt[:50]}...")
    
    # TODO: Integrate proper clothing transfer model
    # This is a simplified implementation using ControlNet
    
    result = pipeline(
        prompt=prompt,
        image=control_image,
        num_inference_steps=30,
        guidance_scale=7.5,
        controlnet_conditioning_scale=0.8,
        generator=generator,
    )
    
    image = result.images[0]
    
    logger.info("Clothes generation completed")
    
    return image
