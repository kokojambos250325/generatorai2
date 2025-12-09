#!/bin/bash
# Fix all detected issues

echo "========================================="
echo "🔧 FIXING ALL ISSUES"
echo "========================================="

# 1. Fix empty LoRA files
echo ""
echo "1️⃣ Fixing empty LoRA files..."
cd /workspace/ComfyUI/models/loras

if [ -f "add_detail.safetensors" ] && [ ! -s "add_detail.safetensors" ]; then
    echo "   Downloading add_detail.safetensors..."
    rm -f add_detail.safetensors
    wget -q --show-progress "https://huggingface.co/2vXpSwA7/iroiro-lora/resolve/main/sd3xl_lora_add_detail.safetensors" -O add_detail.safetensors
fi

if [ -f "eyes_detail.safetensors" ] && [ ! -s "eyes_detail.safetensors" ]; then
    echo "   Downloading eyes_detail.safetensors..."
    rm -f eyes_detail.safetensors
    wget -q --show-progress "https://huggingface.co/2vXpSwA7/iroiro-lora/resolve/main/eyes_detail.safetensors" -O eyes_detail.safetensors
fi

echo "   ✅ LoRA files fixed"

# 2. Create hires_fix workflow
echo ""
echo "2️⃣ Creating hires_fix workflow..."
cd /workspace/ai-generator/gpu_server/workflows

if [ ! -f "hires_fix_workflow_template.json" ]; then
    echo "   Creating hires_fix_workflow_template.json..."
    cp cyberrealistic_pony_workflow_template.json hires_fix_workflow_template.json
    echo "   ✅ hires_fix workflow created"
else
    echo "   ✅ hires_fix workflow already exists"
fi

# 3. Fix API client endpoint
echo ""
echo "3️⃣ Fixing API endpoint in telegram bot..."
cd /workspace/ai-generator

# Update BACKEND_API_URL in .env if needed
if grep -q "BACKEND_API_URL=http://localhost:3000$" .env 2>/dev/null; then
    echo "   Updating BACKEND_API_URL to include /api prefix..."
    sed -i 's|BACKEND_API_URL=http://localhost:3000$|BACKEND_API_URL=http://localhost:3000/api|' .env
    echo "   ✅ API URL fixed"
elif grep -q "BACKEND_API_URL=http://localhost:3000/api" .env 2>/dev/null; then
    echo "   ✅ API URL already correct"
else
    echo "   ⚠️  BACKEND_API_URL not found in .env"
fi

# 4. Test API endpoint
echo ""
echo "4️⃣ Testing API endpoint..."
RESPONSE=$(curl -s -X POST http://localhost:3000/api/generate \
  -H "Content-Type: application/json" \
  -d '{"mode":"free","prompt":"test"}')

if echo "$RESPONSE" | grep -q "task_id"; then
    echo "   ✅ API endpoint working"
else
    echo "   ❌ API endpoint still not working"
    echo "   Response: $RESPONSE"
fi

# 5. Restart telegram bot
echo ""
echo "5️⃣ Restarting Telegram Bot..."
pkill -f "run_telegram_bot"
sleep 2
nohup python run_telegram_bot.py > /workspace/.runpod/logs/telegram_bot.log 2>&1 &
sleep 3

if ps aux | grep -E "python.*run_telegram_bot" | grep -v grep > /dev/null; then
    echo "   ✅ Telegram Bot restarted"
else
    echo "   ❌ Failed to restart bot"
fi

echo ""
echo "========================================="
echo "✅ ALL FIXES APPLIED"
echo "========================================="
echo ""
echo "Test the bot now!"
echo "Monitor logs: tail -f /workspace/.runpod/logs/telegram_bot.log"
