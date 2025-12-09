#!/bin/bash
# Скрипт для установки зависимостей ComfyUI

echo "🔧 Installing ComfyUI dependencies..."

cd /workspace/ComfyUI
source venv/bin/activate

echo "📦 Installing packages from requirements.txt..."
pip install -r requirements.txt

echo "✅ Installation complete!"
deactivate

echo "🔄 Restarting services..."
bash /workspace/startup_all_services.sh

echo "✅ Done! Checking logs..."
sleep 5
tail -50 /workspace/.runpod/logs/comfyui.log
