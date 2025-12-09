#!/bin/bash
# Start Telegram Bot on RunPod

cd /workspace/ai-generator
source /workspace/ComfyUI/venv/bin/activate

# Kill existing bot if running
pkill -f "run_telegram_bot.py" 2>/dev/null || true

# Start bot in background
nohup python run_telegram_bot.py > /workspace/.runpod/logs/telegram_bot.log 2>&1 &

echo "Telegram bot started!"
echo "Check logs: tail -f /workspace/.runpod/logs/telegram_bot.log"

# Wait a bit and check if it's running
sleep 3
ps aux | grep "run_telegram_bot" | grep -v grep
