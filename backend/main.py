"""
Backend API - Main application entry point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from backend.config import get_settings
from backend.routers import health, generate
from backend.utils.json_logging import setup_json_logging

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle manager"""
    # Startup - Set up JSON logging
    logger = setup_json_logging(
        service_name="backend",
        log_file_path="/workspace/logs/backend.log",
        log_level=settings.log_level
    )
    logger.info(f"🚀 Starting {settings.api_title} v{settings.api_version}")
    logger.info(f"📡 GPU Service URL: {settings.gpu_service_url}")
    logger.info("⚙️  Mode: Three-mode generation with quality profiles")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Backend API")

app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # MVP: Allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health.router)
app.include_router(generate.router)

@app.get("/")
async def root():
    return {
        "service": "AI Image Generation Backend",
        "version": settings.api_version,
        "status": "running"
    }
