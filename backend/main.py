"""
Backend API - Main application entry point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from config import get_settings
from routers import health, generate
from utils.logging import setup_logging

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle manager"""
    # Startup
    setup_logging(settings.log_level)
    logger = logging.getLogger(__name__)
    logger.info(f"🚀 Starting {settings.api_title} v{settings.api_version}")
    logger.info(f"📡 GPU Service URL: {settings.gpu_service_url}")
    logger.info(f"⚙️  Mode: MVP (stub endpoints)")
    
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
