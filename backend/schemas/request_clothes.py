"""
Clothes Removal Request Schema

Defines the structure for clothes removal requests.
"""

from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator


class ClothesRemovalRequest(BaseModel):
    """Request schema for clothes removal mode"""
    
    mode: Literal["clothes_removal"] = Field(description="Generation mode (must be 'clothes_removal')")
    target_image: str = Field(description="Base64 encoded source image")
    style: Literal["realism", "lux", "anime"] = Field(description="Output style")
    controlnet_strength: Optional[float] = Field(default=0.8, ge=0.0, le=1.5, description="ControlNet strength")
    inpaint_denoise: Optional[float] = Field(default=0.75, ge=0.5, le=1.0, description="Inpaint denoise strength")
    segmentation_threshold: Optional[float] = Field(default=0.7, ge=0.5, le=0.9, description="Person segmentation threshold")
    seed: Optional[int] = Field(default=-1, description="Random seed")
    steps: Optional[int] = Field(default=30, ge=15, le=50, description="Sampling steps")
    
    @field_validator('target_image')
    @classmethod
    def validate_image(cls, v: str) -> str:
        """Validate base64 image"""
        v = v.strip()
        if not v:
            raise ValueError("Target image cannot be empty")
        
        # Check if it's base64 format (basic validation)
        if not v.startswith('data:image/') and not v.startswith('/9j/') and not v.startswith('iVBORw0KGgo'):
            raise ValueError("Invalid image format. Must be base64 encoded")
        
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "mode": "clothes_removal",
                "target_image": "base64_encoded_image_data_here",
                "style": "realism",
                "controlnet_strength": 0.8,
                "inpaint_denoise": 0.75,
                "segmentation_threshold": 0.7
            }
        }
