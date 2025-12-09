#!/bin/bash
# Full system deployment and diagnostics

echo "=== STOPPING ALL SERVICES ==="
pkill -9 python
sleep 3

echo "=== CHECKING FILE VERSIONS ==="
echo "Backend files:"
ls -lh /workspace/backend/clients/gpu_client.py
ls -lh /workspace/backend/services/generation_router.py
ls -lh /workspace/backend/schemas/response_generate.py

echo ""
echo "=== STARTING GPU SERVER ==="
cd /workspace
nohup /workspace/venv/bin/python gpu_server/server.py > /workspace/logs/gpu_server.log 2>&1 &
GPU_PID=$!
echo "GPU Server PID: $GPU_PID"
sleep 3

echo ""
echo "=== STARTING BACKEND API ==="
cd /workspace/backend
nohup /workspace/venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000 > /workspace/logs/backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend API PID: $BACKEND_PID"
sleep 3

echo ""
echo "=== STARTING TELEGRAM BOT ==="
cd /workspace/telegram_bot
nohup python bot.py > /workspace/logs/telegram_bot.log 2>&1 &
BOT_PID=$!
echo "Telegram Bot PID: $BOT_PID"
sleep 3

echo ""
echo "=== PROCESS STATUS ==="
ps aux | grep python | grep -E "server.py|uvicorn|bot.py" | grep -v grep

echo ""
echo "=== LOG TAIL (Backend) ==="
tail -20 /workspace/logs/backend.log

echo ""
echo "=== LOG TAIL (GPU Server) ==="
tail -20 /workspace/logs/gpu_server.log

echo ""
echo "=== DEPLOYMENT COMPLETE ==="
