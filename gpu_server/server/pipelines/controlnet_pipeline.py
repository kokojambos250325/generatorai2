"""
ControlNet Pipeline - Image-to-image with structural guidance
"""
import logging
import base64
from io import BytesIO
from PIL import Image
import torch
import cv2
import numpy as np

from gpu_server.schema import GPUGenerationRequest

logger = logging.getLogger(__name__)


def _decode_base64_image(base64_str: str) -> Image.Image:
    """Decode base64 string to PIL Image"""
    img_bytes = base64.b64decode(base64_str)
    image = Image.open(BytesIO(img_bytes)).convert("RGB")
    return image


def _preprocess_canny(image: Image.Image) -> Image.Image:
    """Apply canny edge detection"""
    img_array = np.array(image)
    edges = cv2.Canny(img_array, 100, 200)
    edges = cv2.cvtColor(edges, cv2.COLOR_GRAY2RGB)
    return Image.fromarray(edges)


def generate(request: GPUGenerationRequest, models: dict) -> Image.Image:
    """
    Generate image using SDXL + ControlNet
    
    Args:
        request: Generation request with prompt, image, and parameters
        models: Dictionary of model loader functions
        
    Returns:
        Generated PIL Image
    """
    logger.info("Starting ControlNet generation")
    
    # Get models
    sdxl_pipeline = models["sdxl"]()
    controlnet = models["controlnet"]("canny")
    
    # Decode input image
    if not request.image:
        raise ValueError("ControlNet requires input image")
    
    input_image = _decode_base64_image(request.image)
    
    # Preprocess image (canny edge detection)
    control_image = _preprocess_canny(input_image)
    
    # Extract parameters
    prompt = request.prompt or "high quality image"
    seed = request.seed or torch.randint(0, 2**32, (1,)).item()
    
    # Set generator
    generator = torch.Generator(device=sdxl_pipeline.device).manual_seed(seed)
    
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
    logger.info(f"Generating with ControlNet and prompt: {prompt[:50]}...")
    
    result = pipeline(
        prompt=prompt,
        image=control_image,
        num_inference_steps=30,
        guidance_scale=7.5,
        controlnet_conditioning_scale=1.0,
        generator=generator,
    )
    
    image = result.images[0]
    
    logger.info("ControlNet generation completed")
    
    return image
