"""
AI Image Generation Backend - Main Application

FastAPI application entry point for MVP with 2 generation modes:
- Free generation (text-to-image)
- Clothes removal

Architecture:
- Backend: Orchestration, validation, routing (NO ML models)
- GPU Service: Heavy processing on RunPod

MVP: Synchronous processing only
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from config import get_settings
from routers import health, generate
from utils.logging import setup_logging

# Initialize settings
settings = get_settings()

# Setup logging
setup_logging(settings.log_level, settings.log_format)

# Create FastAPI application
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description=settings.api_description,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Configuration (adjust for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(generate.router, tags=["Generation"])


@app.on_event("startup")
async def startup_event():
    """Application startup tasks"""
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Starting {settings.api_title} v{settings.api_version}")
    logger.info(f"GPU Service URL: {settings.gpu_service_url}")
    logger.info("MVP Mode: 2 generation modes (free, clothes_removal)")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown tasks"""
    import logging
    logger = logging.getLogger(__name__)
    logger.info("Shutting down application")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=False,
        log_level=settings.log_level.lower()
    )
