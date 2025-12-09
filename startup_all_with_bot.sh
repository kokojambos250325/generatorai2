#!/bin/bash
# AI Generator - Complete System Startup with Telegram Bot

export COMFYUI_URL="http://localhost:8188"
export WORKER_TIMEOUT=900

echo "🚀 Starting AI Generator services..."

# Stop old processes
pkill -f "main.py" 2>/dev/null || true
pkill -f "uvicorn" 2>/dev/null || true
pkill -f "run_telegram_bot" 2>/dev/null || true
sleep 3

# Start ComfyUI
cd /workspace/ComfyUI
source venv/bin/activate
nohup python main.py --listen 0.0.0.0 --port 8188 > /workspace/.runpod/logs/comfyui.log 2>&1 &
echo "  ✓ ComfyUI started (port 8188)"
sleep 10

# Start FastAPI
cd /workspace/ai-generator
source /workspace/ComfyUI/venv/bin/activate
nohup python -m uvicorn gpu_server.server.main:app --host 0.0.0.0 --port 3000 > /workspace/.runpod/logs/fastapi.log 2>&1 &
echo "  ✓ FastAPI started (port 3000)"
sleep 10

# Start Telegram Bot
nohup python run_telegram_bot.py > /workspace/.runpod/logs/telegram_bot.log 2>&1 &
echo "  ✓ Telegram Bot started"
sleep 5

# Check status
echo ""
echo "📊 Service Status:"
curl -s http://localhost:8188/system_stats | python3 -c "import sys,json; print('  ComfyUI:', json.load(sys.stdin)['system']['comfyui_version'])" 2>/dev/null || echo "  ComfyUI: NOT RUNNING"
curl -s http://localhost:3000/health | python3 -c "import sys,json; print('  FastAPI:', json.load(sys.stdin)['status'])" 2>/dev/null || echo "  FastAPI: NOT RUNNING"
ps aux | grep "run_telegram_bot" | grep -v grep > /dev/null && echo "  Telegram Bot: RUNNING" || echo "  Telegram Bot: NOT RUNNING"

echo ""
echo "✅ Startup complete!"
echo "   Models: 23GB installed"
echo "   Workflows: 4 pipelines ready"
echo "   Logs: /workspace/.runpod/logs/"
echo ""
echo "📱 Telegram Bot Token: 8420116928:AAEg1qPoL5ow6OaKzubFMXEQAuoTIEOpzXE"
