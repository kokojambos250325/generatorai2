#!/bin/bash
# Quick test script - deploy and start everything

echo "========================================="
echo "🚀 Quick Deploy & Test"
echo "========================================="

cd /workspace/ai-generator
git pull

echo ""
echo "📥 Downloading missing models..."

# Check and download models if needed
if [ ! -f "/workspace/ComfyUI/models/checkpoints/cyberrealisticPony_v14.safetensors" ]; then
    echo "  Downloading CyberRealistic Pony v14..."
    bash download_model.sh &
fi

if [ ! -f "/workspace/ComfyUI/models/loras/add_detail.safetensors" ]; then
    echo "  Downloading LoRAs..."
    bash download_loras_public.sh
fi

if [ ! -f "/workspace/ComfyUI/models/embeddings/bad_dream.pt" ]; then
    echo "  Downloading embeddings..."
    bash download_embeddings_public.sh
fi

if [ ! -f "/workspace/ComfyUI/models/upscale_models/4x-UltraSharp.pth" ]; then
    echo "  Downloading 4x-UltraSharp..."
    bash download_ultrasharp.sh
fi

if [ ! -f "/workspace/ComfyUI/models/vae/sdxl_vae.safetensors" ]; then
    echo "  Downloading SDXL VAE..."
    bash download_vae.sh
fi

echo ""
echo "📋 Copying workflows..."
mkdir -p /workspace/workflows
cp gpu_server/workflows/hires_fix_workflow_template.json /workspace/workflows/hires_fix.json
cp gpu_server/workflows/cyberrealistic_pony_workflow_template.json /workspace/workflows/cyberrealistic_pony.json
cp gpu_server/workflows/free_workflow_template.json /workspace/workflows/free.json
cp gpu_server/workflows/clothes_removal_workflow_template.json /workspace/workflows/clothes_removal.json
cp gpu_server/workflows/face_swap_workflow_template.json /workspace/workflows/face_swap.json
cp gpu_server/workflows/face_consistent_workflow_template.json /workspace/workflows/face_consistent.json

echo ""
echo "🔄 Restarting services..."

# Stop existing services
pkill -9 -f "python.*main.py" || true
pkill -9 -f "uvicorn.*gpu_server" || true
pkill -9 -f "python.*run_telegram_bot" || true
sleep 2

# Start ComfyUI
echo "  Starting ComfyUI on port 8188..."
cd /workspace/ComfyUI
nohup python main.py --listen 0.0.0.0 --port 8188 > /workspace/.runpod/logs/comfyui.log 2>&1 &
sleep 5

# Start GPU Server
echo "  Starting GPU Server on port 3000..."
cd /workspace/ai-generator
nohup python -m uvicorn gpu_server.server.main:app --host 0.0.0.0 --port 3000 > /workspace/.runpod/logs/gpu_server.log 2>&1 &
sleep 3

# Start Telegram Bot
echo "  Starting Telegram Bot..."
nohup python run_telegram_bot.py > /workspace/.runpod/logs/telegram_bot.log 2>&1 &
sleep 2

echo ""
echo "========================================="
echo "✅ All services started!"
echo "========================================="
echo ""

echo "🔍 Service status:"
ps aux | grep -E "python.*main.py|uvicorn.*gpu_server|python.*run_telegram_bot" | grep -v grep

echo ""
echo "📊 Check logs:"
echo "  ComfyUI:      tail -f /workspace/.runpod/logs/comfyui.log"
echo "  GPU Server:   tail -f /workspace/.runpod/logs/gpu_server.log"
echo "  Telegram Bot: tail -f /workspace/.runpod/logs/telegram_bot.log"

echo ""
echo "🌐 Endpoints:"
echo "  ComfyUI:    http://localhost:8188"
echo "  GPU Server: http://localhost:3000"
echo "  Docs:       http://localhost:3000/docs"

echo ""
echo "🤖 Telegram Bot готов! Открой бот и попробуй:"
echo "  /start - главное меню"
echo "  ✨ Hires Fix (Ultra HD) - новый режим"
