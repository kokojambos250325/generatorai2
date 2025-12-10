#!/bin/bash
# Restart Backend and ComfyUI services

cd /workspace
source venv/bin/activate

echo "=== Stopping old services ==="
pkill -f "uvicorn.*backend" 2>/dev/null || true
pkill -f "python.*ComfyUI.*main.py" 2>/dev/null || true
sleep 2

echo "=== Starting ComfyUI ==="
cd /workspace/ComfyUI
nohup python main.py --listen 0.0.0.0 --port 8188 > /workspace/logs/comfyui.log 2>&1 &
COMFY_PID=$!
echo "ComfyUI started (PID: $COMFY_PID)"
sleep 5

echo "=== Starting Backend ==="
cd /workspace/backend
nohup uvicorn main:app --host 0.0.0.0 --port 8000 > /workspace/logs/backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend started (PID: $BACKEND_PID)"
sleep 3

echo "=== Checking services ==="
# Check ComfyUI
if curl -s http://127.0.0.1:8188/system_stats > /dev/null 2>&1; then
    echo "✓ ComfyUI is responding"
else
    echo "✗ ComfyUI is not responding"
fi

# Check Backend
if curl -s http://127.0.0.1:8000/health > /dev/null 2>&1; then
    echo "✓ Backend is responding"
else
    echo "✗ Backend is not responding"
fi

echo "=== Service PIDs ==="
ps aux | grep -E '[u]vicorn.*backend|[p]ython.*main.py.*8188' | head -5
