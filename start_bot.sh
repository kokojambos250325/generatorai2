#!/bin/bash
# Start Telegram Bot on RunPod

cd /workspace
source venv/bin/activate
cd telegram_bot

# Kill existing bot process
pkill -f "bot.py" 2>/dev/null || true
sleep 2

# Start bot
nohup python bot.py > /workspace/logs/telegram_bot.log 2>&1 &
BOT_PID=$!

sleep 3

# Check if running
if ps -p $BOT_PID > /dev/null 2>&1; then
    echo "Bot started successfully (PID: $BOT_PID)"
    echo "Log: /workspace/logs/telegram_bot.log"
else
    echo "Bot failed to start"
    tail -20 /workspace/logs/telegram_bot.log
    exit 1
fi


