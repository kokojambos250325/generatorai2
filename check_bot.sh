#!/bin/bash
# Диагностика и запуск бота

echo "========================================="
echo "🔍 Telegram Bot Diagnostic"
echo "========================================="

echo ""
echo "1️⃣ Checking bot process..."
BOT_PID=$(ps aux | grep -E "python.*run_telegram_bot" | grep -v grep | awk '{print $2}')
if [ -n "$BOT_PID" ]; then
    echo "✅ Bot is running (PID: $BOT_PID)"
else
    echo "❌ Bot is NOT running"
fi

echo ""
echo "2️⃣ Checking dependencies..."
cd /workspace/ai-generator

if python -c "import telegram" 2>/dev/null; then
    echo "✅ python-telegram-bot installed"
else
    echo "❌ python-telegram-bot NOT installed"
    echo "   Installing..."
    pip install python-telegram-bot --quiet
fi

if python -c "import aiohttp" 2>/dev/null; then
    echo "✅ aiohttp installed"
else
    echo "❌ aiohttp NOT installed"
    echo "   Installing..."
    pip install aiohttp --quiet
fi

echo ""
echo "3️⃣ Checking configuration..."
if [ -f "/workspace/ai-generator/.env" ]; then
    echo "✅ .env file exists"
    
    if grep -q "TELEGRAM_BOT_TOKEN" /workspace/ai-generator/.env; then
        echo "✅ TELEGRAM_BOT_TOKEN configured"
    else
        echo "❌ TELEGRAM_BOT_TOKEN missing in .env"
    fi
    
    if grep -q "BACKEND_API_URL" /workspace/ai-generator/.env; then
        echo "✅ BACKEND_API_URL configured"
    else
        echo "❌ BACKEND_API_URL missing in .env"
    fi
else
    echo "❌ .env file NOT found"
    echo "   Creating from .env.example..."
    cp /workspace/ai-generator/.env.example /workspace/ai-generator/.env
    echo "   ⚠️  Please edit .env and add your tokens!"
fi

echo ""
echo "4️⃣ Checking logs..."
if [ -f "/workspace/.runpod/logs/telegram_bot.log" ]; then
    echo "📋 Last 20 lines of bot log:"
    echo "---"
    tail -20 /workspace/.runpod/logs/telegram_bot.log
    echo "---"
else
    echo "⚠️  No log file yet"
fi

echo ""
echo "5️⃣ Checking backend connectivity..."
if curl -s http://localhost:3000/api/health > /dev/null 2>&1; then
    echo "✅ GPU Server is responding on port 3000"
else
    echo "❌ GPU Server is NOT responding"
    echo "   Starting GPU Server..."
    cd /workspace/ai-generator
    nohup python -m uvicorn gpu_server.server.main:app --host 0.0.0.0 --port 3000 > /workspace/.runpod/logs/gpu_server.log 2>&1 &
    sleep 3
fi

echo ""
echo "========================================="
echo "🚀 Actions"
echo "========================================="

if [ -z "$BOT_PID" ]; then
    echo ""
    echo "Starting Telegram Bot..."
    cd /workspace/ai-generator
    nohup python run_telegram_bot.py > /workspace/.runpod/logs/telegram_bot.log 2>&1 &
    sleep 2
    
    NEW_PID=$(ps aux | grep -E "python.*run_telegram_bot" | grep -v grep | awk '{print $2}')
    if [ -n "$NEW_PID" ]; then
        echo "✅ Bot started successfully (PID: $NEW_PID)"
    else
        echo "❌ Failed to start bot. Check logs:"
        echo "   tail -f /workspace/.runpod/logs/telegram_bot.log"
    fi
else
    echo "Bot is already running. To restart:"
    echo "  kill $BOT_PID"
    echo "  nohup python run_telegram_bot.py > /workspace/.runpod/logs/telegram_bot.log 2>&1 &"
fi

echo ""
echo "📊 Monitor logs:"
echo "  tail -f /workspace/.runpod/logs/telegram_bot.log"
