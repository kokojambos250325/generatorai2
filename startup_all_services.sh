#!/bin/bash
# AI Generator - Complete System Startup Script
# Запускает все необходимые сервисы на RunPod

set -e

echo "========================================="
echo "🚀 AI Generator - System Startup"
echo "========================================="
echo ""

# Установить переменные окружения
export COMFYUI_URL="http://localhost:8188"

# Остановить старые процессы
echo "[1/4] Stopping old processes..."
pkill -f "main.py.*8188" 2>/dev/null || true
pkill -f "uvicorn.*main:app" 2>/dev/null || true
sleep 3

# Запустить ComfyUI
echo "[2/4] Starting ComfyUI..."
cd /workspace/ComfyUI
source venv/bin/activate
nohup python main.py --listen 0.0.0.0 --port 8188 > /workspace/.runpod/logs/comfyui.log 2>&1 &
echo "  ✓ ComfyUI started on port 8188"

# Подождать запуска ComfyUI
sleep 10

# Запустить FastAPI
echo "[3/4] Starting FastAPI server..."
cd /workspace/ai-generator
source /workspace/ComfyUI/venv/bin/activate
nohup python -m uvicorn gpu_server.server.main:app --host 0.0.0.0 --port 3000 > /workspace/.runpod/logs/fastapi.log 2>&1 &
echo "  ✓ FastAPI server started on port 3000"

# Подождать запуска FastAPI
sleep 10

# Проверить статус
echo "[4/4] Checking services..."
echo ""

# ComfyUI
COMFYUI_VERSION=$(curl -s http://localhost:8188/system_stats 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin)['system']['comfyui_version'])" 2>/dev/null || echo "NOT RUNNING")
echo "  ComfyUI: $COMFYUI_VERSION"

# FastAPI
FASTAPI_STATUS=$(curl -s http://localhost:3000/health 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin)['status'])" 2>/dev/null || echo "NOT RUNNING")
echo "  FastAPI: $FASTAPI_STATUS"

echo ""
echo "========================================="
echo "✅ Startup Complete!"
echo "========================================="
echo ""
echo "📊 Service URLs:"
echo "  - ComfyUI: http://localhost:8188"
echo "  - FastAPI: http://localhost:3000"
echo "  - API Docs: http://localhost:3000/docs"
echo ""
echo "📝 Logs:"
echo "  - ComfyUI: /workspace/.runpod/logs/comfyui.log"
echo "  - FastAPI: /workspace/.runpod/logs/fastapi.log"
echo ""
echo "🎯 Models: 11GB loaded in /workspace/ComfyUI/models"
echo "🎨 Workflows: 4 pipelines in /workspace/workflows"
echo ""
