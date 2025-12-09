#!/bin/bash
# RunPod Persistent Startup Script
# This script runs automatically when pod starts
# Place this in /workspace and configure in RunPod settings

set -e

echo "========================================="
echo "🚀 AI Generator - RunPod Startup"
echo "========================================="

# Wait for network
sleep 5

# Activate virtual environment
source /workspace/ComfyUI/venv/bin/activate

# Start ComfyUI in background
echo "[1/2] Starting ComfyUI on port 8188..."
cd /workspace/ComfyUI
nohup python main.py --listen 0.0.0.0 --port 8188 > /workspace/logs/comfyui.log 2>&1 &
echo "  ✓ ComfyUI started (PID: $!)"
sleep 5

# Start FastAPI GPU Server
echo "[2/2] Starting FastAPI GPU Server on port 3000..."
cd /workspace/ai-generator
export PYTHONPATH=/workspace/ai-generator
nohup python -m uvicorn gpu_server.server.main:app --host 0.0.0.0 --port 3000 > /workspace/logs/fastapi.log 2>&1 &
echo "  ✓ FastAPI started (PID: $!)"
sleep 3

# Check status
echo ""
echo "========================================="
echo "✅ Services Status:"
echo "========================================="
ps aux | grep -E "(ComfyUI|uvicorn)" | grep -v grep || echo "No services running"

echo ""
echo "📊 API Endpoints:"
echo "  - ComfyUI:  http://localhost:8188"
echo "  - FastAPI:  http://localhost:3000/api/health"
echo ""
echo "🌐 Public URLs:"
echo "  - ComfyUI:  https://p8q2agahufxw4a-8188.proxy.runpod.net"
echo "  - FastAPI:  https://p8q2agahufxw4a-3000.proxy.runpod.net"
echo ""
echo "✅ Startup complete!"
