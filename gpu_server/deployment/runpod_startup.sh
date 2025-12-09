#!/bin/bash
# RunPod/Vast.ai startup script for GPU server
# Enhanced with automated model downloads and comprehensive logging

set -e

echo "=== GPU Server Startup Script ==="
echo "Start time: $(date '+%Y-%m-%d %H:%M:%S')"

# Update system packages
echo "Updating system packages..."
apt-get update || true

# Install system dependencies
echo "Installing system dependencies..."
apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgl1-mesa-glx \
    ffmpeg \
    git || true

# Verify CUDA availability and get GPU info
echo "Checking CUDA availability..."
if command -v nvidia-smi &> /dev/null; then
    echo "✓ nvidia-smi found"
    nvidia-smi --query-gpu=name,memory.total,driver_version,cuda_version --format=csv,noheader
    
    # Extract GPU info for logging
    GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader)
    GPU_MEMORY=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader)
    echo "GPU: $GPU_NAME"
    echo "VRAM: $GPU_MEMORY"
else
    echo "WARNING: nvidia-smi not found, GPU may not be available"
    echo "Server will run in CPU-only mode (significantly slower)"
fi

# Create necessary directories
echo "Creating directories..."
mkdir -p /workspace/models
mkdir -p /workspace/models/diffusers
mkdir -p /tmp/gpu_results
mkdir -p /var/log

echo "✓ Directories created"

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r /app/gpu_server/deployment/requirements.txt

echo "✓ Python dependencies installed"

# Set environment variables
export MODEL_CACHE_DIR=/workspace/models
export RESULT_STORAGE_DIR=/tmp/gpu_results
export LOG_LEVEL=INFO
export HF_HOME=/workspace/models
export DIFFUSERS_CACHE=/workspace/models/diffusers

echo "Environment variables set:"
echo "  MODEL_CACHE_DIR=$MODEL_CACHE_DIR"
echo "  RESULT_STORAGE_DIR=$RESULT_STORAGE_DIR"
echo "  HF_HOME=$HF_HOME"
echo "  DIFFUSERS_CACHE=$DIFFUSERS_CACHE"

# Download models automatically
echo "========================================"
echo "Starting automated model downloads..."
echo "========================================"

if [ -f "/app/scripts/download_models.py" ]; then
    # Run download script with all models
    python /app/scripts/download_models.py --all --skip-existing 2>&1 | tee -a /var/log/model_download.log
    
    DOWNLOAD_EXIT_CODE=${PIPESTATUS[0]}
    
    if [ $DOWNLOAD_EXIT_CODE -eq 0 ]; then
        echo "✓ Model downloads completed successfully"
    else
        echo "WARNING: Model downloads failed with exit code $DOWNLOAD_EXIT_CODE"
        echo "Server will start anyway and attempt lazy loading on first request"
    fi
else
    echo "WARNING: download_models.py not found, skipping model downloads"
    echo "Models will be downloaded on first use (lazy loading)"
fi

echo "========================================"
echo "Model download phase complete"
echo "========================================"

# Start the server
echo "Starting GPU server..."
echo "Server start time: $(date '+%Y-%m-%d %H:%M:%S')"

cd /app

# Start server with logging to both console and file
uvicorn gpu_server.server.main:app --host 0.0.0.0 --port 3000 --workers 1 2>&1 | tee /var/log/gpu_server.log
