# Dockerfile for GPU Server
# Base image: NVIDIA CUDA with Ubuntu
# Enhanced for RunPod deployment with optimal caching and dependencies

FROM nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV MODEL_CACHE_DIR=/workspace/models
ENV RESULT_STORAGE_DIR=/tmp/gpu_results
ENV HF_HOME=/workspace/models
ENV DIFFUSERS_CACHE=/workspace/models/diffusers

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    python3-dev \
    git \
    wget \
    curl \
    ffmpeg \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libvips-dev \
    && rm -rf /var/lib/apt/lists/*

# Create symbolic link for python
RUN ln -sf /usr/bin/python3.10 /usr/bin/python

# Set working directory
WORKDIR /app

# Copy requirements first (for better layer caching)
COPY gpu_server/deployment/requirements.txt /app/gpu_server/deployment/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/gpu_server/deployment/requirements.txt

# Copy application code
COPY . /app/

# Create necessary directories with proper permissions
RUN mkdir -p /workspace/models/diffusers && \
    mkdir -p /workspace/models/sdxl/base && \
    mkdir -p /workspace/models/sdxl/refiner && \
    mkdir -p /workspace/models/controlnet/pose && \
    mkdir -p /workspace/models/controlnet/depth && \
    mkdir -p /workspace/models/controlnet/canny && \
    mkdir -p /workspace/models/insightface && \
    mkdir -p /workspace/models/enhancement/gfpgan && \
    mkdir -p /workspace/models/enhancement/esrgan && \
    mkdir -p /workspace/models/lora && \
    mkdir -p /workspace/models/cache && \
    mkdir -p /tmp/gpu_results && \
    mkdir -p /var/log && \
    chmod -R 777 /workspace && \
    chmod -R 777 /tmp/gpu_results && \
    chmod -R 777 /var/log

# Expose port
EXPOSE 3000

# Set entrypoint
CMD ["uvicorn", "gpu_server.server.main:app", "--host", "0.0.0.0", "--port", "3000", "--workers", "1"]
