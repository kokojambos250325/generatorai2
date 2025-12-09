#!/bin/bash
# Full System Diagnostic and Fix

echo "========================================="
echo "🔍 FULL SYSTEM DIAGNOSTIC"
echo "========================================="

# 1. Check running processes
echo ""
echo "1️⃣ Checking running processes..."
echo "---"
ps aux | grep -E "ComfyUI|gpu_server|telegram_bot" | grep -v grep
echo "---"

# 2. Check ComfyUI
echo ""
echo "2️⃣ Checking ComfyUI..."
if curl -s http://localhost:8188 > /dev/null 2>&1; then
    echo "✅ ComfyUI is running on port 8188"
else
    echo "❌ ComfyUI is NOT running"
    echo "   Starting ComfyUI..."
    cd /workspace/ComfyUI
    nohup python main.py --listen 0.0.0.0 --port 8188 > /workspace/.runpod/logs/comfyui.log 2>&1 &
    sleep 5
fi

# 3. Check GPU Server
echo ""
echo "3️⃣ Checking GPU Server..."
if curl -s http://localhost:3000/health > /dev/null 2>&1; then
    echo "✅ GPU Server is running on port 3000"
    echo "   Health check response:"
    curl -s http://localhost:3000/health | head -10
else
    echo "❌ GPU Server is NOT running"
    echo "   Starting GPU Server..."
    cd /workspace/ai-generator
    nohup python -m uvicorn gpu_server.server.main:app --host 0.0.0.0 --port 3000 > /workspace/.runpod/logs/gpu_server.log 2>&1 &
    sleep 5
fi

# 4. Check Telegram Bot
echo ""
echo "4️⃣ Checking Telegram Bot..."
BOT_PID=$(ps aux | grep -E "python.*run_telegram_bot" | grep -v grep | awk '{print $2}')
if [ -n "$BOT_PID" ]; then
    echo "✅ Telegram Bot is running (PID: $BOT_PID)"
else
    echo "❌ Telegram Bot is NOT running"
    echo "   Starting Telegram Bot..."
    cd /workspace/ai-generator
    nohup python run_telegram_bot.py > /workspace/.runpod/logs/telegram_bot.log 2>&1 &
    sleep 3
fi

# 5. Check models
echo ""
echo "5️⃣ Checking models..."
echo "Checkpoints:"
ls -lh /workspace/ComfyUI/models/checkpoints/*.safetensors 2>/dev/null | head -3 || echo "  No checkpoints found"
echo ""
echo "VAEs:"
ls -lh /workspace/ComfyUI/models/vae/*.safetensors 2>/dev/null | head -3 || echo "  No VAEs found"
echo ""
echo "LoRAs:"
ls -lh /workspace/ComfyUI/models/loras/*.safetensors 2>/dev/null | head -3 || echo "  No LoRAs found"
echo ""
echo "Upscale models:"
ls -lh /workspace/ComfyUI/models/upscale_models/*.pth 2>/dev/null | head -3 || echo "  No upscale models found"

# 6. Check workflows
echo ""
echo "6️⃣ Checking workflows..."
if [ -d "/workspace/ai-generator/gpu_server/workflows" ]; then
    echo "✅ Workflows directory exists"
    ls -lh /workspace/ai-generator/gpu_server/workflows/*.json | head -5
else
    echo "❌ Workflows directory missing"
fi

# 7. Test API endpoint
echo ""
echo "7️⃣ Testing API endpoint..."
echo "Testing POST /generate with free mode:"
RESPONSE=$(curl -s -X POST http://localhost:3000/generate \
  -H "Content-Type: application/json" \
  -d '{"mode":"free","prompt":"test prompt"}')
echo "$RESPONSE"

if echo "$RESPONSE" | grep -q "task_id"; then
    TASK_ID=$(echo "$RESPONSE" | grep -o '"task_id":"[^"]*"' | cut -d'"' -f4)
    echo "✅ Task created: $TASK_ID"
    
    echo ""
    echo "8️⃣ Checking task status..."
    sleep 2
    curl -s http://localhost:3000/task/$TASK_ID | head -20
else
    echo "❌ Failed to create task"
fi

# 9. Check logs for errors
echo ""
echo "9️⃣ Recent errors in logs..."
echo "---"
echo "GPU Server errors:"
grep -i "error\|exception\|failed" /workspace/.runpod/logs/gpu_server.log | tail -5 || echo "  No errors"
echo ""
echo "ComfyUI errors:"
grep -i "error\|exception\|failed" /workspace/.runpod/logs/comfyui.log | tail -5 || echo "  No errors"
echo ""
echo "Telegram Bot errors:"
grep -i "error\|exception\|failed" /workspace/.runpod/logs/telegram_bot.log | tail -5 || echo "  No errors"
echo "---"

# 10. Summary
echo ""
echo "========================================="
echo "📊 SUMMARY"
echo "========================================="
echo "ComfyUI:      http://localhost:8188"
echo "GPU Server:   http://localhost:3000"
echo "Telegram Bot: $(if [ -n "$BOT_PID" ]; then echo 'Running'; else echo 'Stopped'; fi)"
echo ""
echo "📋 Monitor logs:"
echo "  tail -f /workspace/.runpod/logs/comfyui.log"
echo "  tail -f /workspace/.runpod/logs/gpu_server.log"
echo "  tail -f /workspace/.runpod/logs/telegram_bot.log"
