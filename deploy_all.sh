#!/bin/bash
set -e

echo "========================================="
echo "🚀 Deploying CyberRealistic Pony Setup"
echo "========================================="

cd /workspace/ai-generator
git pull

echo ""
echo "📥 Step 1/6: Downloading CyberRealistic Pony model (12.92 GB)..."
bash download_model.sh > /workspace/.runpod/logs/model_download.log 2>&1 &
MODEL_PID=$!

echo "📥 Step 2/6: Downloading SDXL VAE (335 MB)..."
bash download_vae.sh

echo "📥 Step 3/6: Downloading Upscale models (808 MB)..."
bash download_upscale_models.sh

echo "📥 Step 4/6: Downloading LoRA (Crazy GF Mix)..."
bash download_lora_crazy_gf.sh

echo "📥 Step 5/6: Downloading Embeddings..."
bash download_embeddings.sh

echo ""
echo "⏳ Waiting for main model download..."
wait $MODEL_PID

echo ""
echo "📋 Step 6/6: Copying workflows..."
mkdir -p /workspace/workflows
cp gpu_server/workflows/free_workflow_template.json /workspace/workflows/free.json
cp gpu_server/workflows/clothes_removal_workflow_template.json /workspace/workflows/clothes_removal.json
cp gpu_server/workflows/face_swap_workflow_template.json /workspace/workflows/face_swap.json
cp gpu_server/workflows/face_consistent_workflow_template.json /workspace/workflows/face_consistent.json
cp gpu_server/workflows/cyberrealistic_pony_workflow_template.json /workspace/workflows/cyberrealistic_pony.json

echo ""
echo "🔄 Restarting services..."

echo "  - Stopping ComfyUI..."
pkill -9 -f "python.*main.py" || true
sleep 2

echo "  - Starting ComfyUI..."
cd /workspace/ComfyUI
nohup python main.py --listen 0.0.0.0 --port 8188 > /workspace/.runpod/logs/comfyui.log 2>&1 &
sleep 5

echo "  - Stopping GPU Server..."
pkill -9 -f "uvicorn.*gpu_server" || true
sleep 2

echo "  - Starting GPU Server..."
cd /workspace/ai-generator
nohup python -m uvicorn gpu_server.server.main:app --host 0.0.0.0 --port 3000 > /workspace/.runpod/logs/gpu_server.log 2>&1 &

echo ""
echo "========================================="
echo "✅ Deployment Complete!"
echo "========================================="
echo ""

sleep 3

echo "📊 Model inventory:"
echo "Checkpoints:"
ls -lh /workspace/ComfyUI/models/checkpoints/ 2>/dev/null || echo "  (none)"
echo ""
echo "VAE:"
ls -lh /workspace/ComfyUI/models/vae/ 2>/dev/null || echo "  (none)"
echo ""
echo "LoRAs:"
ls -lh /workspace/ComfyUI/models/loras/ 2>/dev/null || echo "  (none)"
echo ""
echo "Embeddings:"
ls -lh /workspace/ComfyUI/models/embeddings/ 2>/dev/null || echo "  (none)"
echo ""
echo "Upscale:"
ls -lh /workspace/ComfyUI/models/upscale_models/ 2>/dev/null || echo "  (none)"
echo ""

echo "🔍 Service status:"
ps aux | grep -E "python.*main.py|uvicorn.*gpu_server" | grep -v grep

echo ""
echo "✨ Ready for image generation!"
echo "   ComfyUI: http://localhost:8188"
echo "   GPU Server: http://localhost:3000"
