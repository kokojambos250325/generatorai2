"""
Generation Response Schema

Defines unified response structure for all generation endpoints.
"""

from typing import Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime
import uuid


class GenerationResponse(BaseModel):
    """Unified response schema for generation requests"""
    
    task_id: str = Field(description="Unique task identifier")
    status: Literal["done", "queued", "processing", "failed"] = Field(description="Task status")
    image: Optional[str] = Field(default=None, description="Base64 encoded result image (when status=done)")
    error: Optional[str] = Field(default=None, description="Error message (when status=failed)")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    
    @classmethod
    def success(cls, image: str, task_id: Optional[str] = None) -> "GenerationResponse":
        """Create success response"""
        return cls(
            task_id=task_id or str(uuid.uuid4()),
            status="done",
            image=image,
            error=None
        )
    
    @classmethod
    def create_error(cls, error_message: str, task_id: Optional[str] = None) -> "GenerationResponse":
        """Create error response"""
        return cls(
            task_id=task_id or str(uuid.uuid4()),
            status="failed",
            image=None,
            error=error_message
        )
    
    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "done",
                "image": "base64_encoded_result_image_data",
                "error": None,
                "timestamp": "2025-12-08T20:00:00Z"
            }
        }


class HealthResponse(BaseModel):
    """Health check response schema"""
    
    status: str = Field(description="Service health status")
    gpu_available: bool = Field(description="GPU service connectivity status")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Check timestamp")
    version: str = Field(default="1.0.0", description="API version")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "gpu_available": True,
                "timestamp": "2025-12-08T20:00:00Z",
                "version": "1.0.0"
            }
        }
