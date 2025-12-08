"""
Free Generation Request Schema

Defines the structure for free text-to-image generation requests.
"""

from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator


class ExtraParams(BaseModel):
    """Optional advanced parameters for fine-tuning generation"""
    
    steps: Optional[int] = Field(default=30, ge=20, le=50, description="Sampling steps")
    cfg_scale: Optional[float] = Field(default=7.5, ge=5.0, le=15.0, description="Classifier-free guidance scale")
    seed: Optional[int] = Field(default=-1, description="Random seed (-1 for random)")
    sampler: Optional[str] = Field(default="euler_a", description="Sampler algorithm")
    width: Optional[int] = Field(default=1024, description="Output width")
    height: Optional[int] = Field(default=1024, description="Output height")
    
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
    style: Literal["realism", "lux", "anime", "chatgpt"] = Field(description="Visual style preset")
    extra_params: Optional[ExtraParams] = Field(default=None, description="Advanced parameters")
    
    @field_validator('prompt')
    @classmethod
    def validate_prompt(cls, v: str) -> str:
        """Validate and sanitize prompt"""
        v = v.strip()
        if not v:
            raise ValueError("Prompt cannot be empty")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "mode": "free",
                "prompt": "a beautiful mountain landscape at sunset, photorealistic",
                "style": "realism",
                "extra_params": {
                    "steps": 30,
                    "cfg_scale": 7.5,
                    "seed": -1,
                    "width": 1024,
                    "height": 1024
                }
            }
        }
