"""
Free Generation Request Schema

Defines the structure for free text-to-image generation requests.
"""

from typing import Optional, Literal, List
from pydantic import BaseModel, Field, field_validator


class ExtraParams(BaseModel):
    """Optional advanced parameters for fine-tuning generation"""
    
    quality_profile: Optional[Literal["fast", "balanced", "high_quality"]] = Field(default=None, description="Quality preset (overrides style default)")
    steps: Optional[int] = Field(default=None, ge=10, le=50, description="Sampling steps")
    cfg_scale: Optional[float] = Field(default=None, ge=5.0, le=15.0, description="Classifier-free guidance scale")
    seed: Optional[int] = Field(default=-1, description="Random seed (-1 for random)")
    sampler: Optional[str] = Field(default=None, description="Sampler algorithm")
    width: Optional[int] = Field(default=None, description="Output width")
    height: Optional[int] = Field(default=None, description="Output height")
    
    @field_validator('width', 'height')
    @classmethod
    def validate_dimensions(cls, v: int) -> int:
        """Validate output dimensions are within reasonable bounds"""
        if v < 512:
            raise ValueError("Dimension must be at least 512")
        if v > 2048:
            raise ValueError("Dimension must not exceed 2048")
        if v % 64 != 0:
            raise ValueError("Dimension must be divisible by 64")
        return v


class FreeGenerationRequest(BaseModel):
    """Request schema for free generation mode"""
    
    mode: Literal["free"] = Field(description="Generation mode (must be 'free')")
    prompt: str = Field(min_length=1, max_length=2000, description="Text description in Russian or English")
    style: Literal["noir", "super_realism", "anime", "realism", "lux", "chatgpt"] = Field(description="Visual style preset")
    add_face: Optional[bool] = Field(default=False, description="Add face embedding to generation")
    face_images: Optional[List[str]] = Field(default=None, description="Base64 encoded face images (1-5 images)")
    face_strength: Optional[float] = Field(default=0.75, ge=0.0, le=1.0, description="Face influence strength")
    extra_params: Optional[ExtraParams] = Field(default=None, description="Advanced parameters")
    
    @field_validator('prompt')
    @classmethod
    def validate_prompt(cls, v: str) -> str:
        """Validate and sanitize prompt"""
        v = v.strip()
        if not v:
            raise ValueError("Prompt cannot be empty")
        return v
    
    @field_validator('face_images')
    @classmethod
    def validate_face_images(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate face images array"""
        if v is not None:
            if len(v) > 5:
                raise ValueError("Maximum 5 face images allowed")
            if len(v) == 0:
                raise ValueError("If face_images provided, must have at least 1 image")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "mode": "free",
                "prompt": "a beautiful mountain landscape at sunset, photorealistic",
                "style": "super_realism",
                "add_face": False,
                "extra_params": {
                    "quality_profile": "balanced",
                    "steps": 30,
                    "cfg_scale": 7.5,
                    "seed": -1,
                    "width": 832,
                    "height": 1216
                }
            }
        }


class NSFWFaceRequest(BaseModel):
    """Request schema for NSFW face-consistent generation"""
    
    mode: Literal["nsfw_face"] = Field(description="Generation mode (must be 'nsfw_face')")
    face_images: List[str] = Field(min_length=1, max_length=5, description="Base64 encoded face reference images (1-5)")
    scene_prompt: str = Field(min_length=5, max_length=2000, description="Scene/pose description")
    style: Literal["realism", "lux", "anime"] = Field(description="Visual style preset")
    face_strength: Optional[float] = Field(default=0.8, ge=0.6, le=1.0, description="Face consistency strength")
    enable_upscale: Optional[bool] = Field(default=False, description="Enable 2x upscaling")
    extra_params: Optional[ExtraParams] = Field(default=None, description="Advanced parameters")
    
    @field_validator('scene_prompt')
    @classmethod
    def validate_scene_prompt(cls, v: str) -> str:
        """Validate scene prompt"""
        v = v.strip()
        if not v:
            raise ValueError("Scene prompt cannot be empty")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "mode": "nsfw_face",
                "face_images": ["base64_face_1", "base64_face_2"],
                "scene_prompt": "beautiful woman in intimate pose, artistic photography",
                "style": "lux",
                "face_strength": 0.8,
                "enable_upscale": False
            }
        }
