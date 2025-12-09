#!/bin/bash
set -e

echo "=== Fixing workflows on server ==="

# Create workflows directory if not exists
mkdir -p /workspace/workflows

# Copy workflow templates as production workflows
cd /workspace/ai-generator/gpu_server/workflows

cp free_workflow_template.json /workspace/workflows/free.json
cp clothes_removal_workflow_template.json /workspace/workflows/clothes_removal.json  
cp face_swap_workflow_template.json /workspace/workflows/face_swap.json
cp face_consistent_workflow_template.json /workspace/workflows/face_consistent.json

echo "Workflows copied!"
ls -la /workspace/workflows/

# Restart ComfyUI
echo "=== Restarting ComfyUI ==="
pkill -9 -f "python.*main.py" || true
sleep 2
cd /workspace/ComfyUI
nohup python main.py --listen 0.0.0.0 --port 8188 > /workspace/.runpod/logs/comfyui.log 2>&1 &
echo "ComfyUI restarting..."
sleep 5

# Restart GPU Server
echo "=== Restarting GPU Server ==="
pkill -9 -f "uvicorn.*gpu_server" || true
sleep 2
cd /workspace/ai-generator
nohup python -m uvicorn gpu_server.server.main:app --host 0.0.0.0 --port 3000 > /workspace/.runpod/logs/gpu_server.log 2>&1 &
echo "GPU Server restarting..."
sleep 3

# Check status
echo "=== Checking services ==="
ps aux | grep -E "python|uvicorn" | grep -v grep

echo ""
echo "=== Done! ==="
