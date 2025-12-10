#!/bin/bash
# Скрипт для обновления кода на сервере и перезапуска сервисов

echo "=== ОБНОВЛЕНИЕ СЕРВЕРА ==="
cd /workspace/ai-generator

echo "1. Получение изменений из GitHub..."
git pull origin main

if [ $? -ne 0 ]; then
    echo "❌ Ошибка при обновлении кода!"
    exit 1
fi

echo "✓ Код обновлен"

echo "2. Установка зависимостей..."
source /workspace/ComfyUI/venv/bin/activate
pip install -r requirements.txt --quiet

echo "3. Перезапуск сервисов..."
# Убиваем старые процессы
pkill -f 'main.py.*8188' || true
pkill -f 'uvicorn.*gpu_server' || true
pkill -f 'uvicorn.*backend.main' || true
pkill -f 'python.*bot.py' || true
sleep 2

# Запускаем ComfyUI (должен быть первым)
echo "   - Запуск ComfyUI (Port 8188)..."
cd /workspace/ComfyUI
source venv/bin/activate
nohup python main.py --listen 0.0.0.0 --port 8188 > /workspace/logs/comfyui.log 2>&1 &
sleep 5

# Запускаем GPU Server (Port 3000)
echo "   - Запуск GPU Server (Port 3000)..."
cd /workspace/ai-generator
source /workspace/ComfyUI/venv/bin/activate
export PYTHONPATH=/workspace/ai-generator
nohup python -m uvicorn gpu_server.server.main:app --host 0.0.0.0 --port 3000 > /workspace/logs/gpu_server.log 2>&1 &

# Запускаем Backend API (Port 8000)
echo "   - Запуск Backend API (Port 8000)..."
nohup python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 > /workspace/logs/backend.log 2>&1 &

# Запускаем Telegram Bot
echo "   - Запуск Telegram Bot..."
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi
nohup python telegram_bot/bot.py > /workspace/logs/telegram_bot.log 2>&1 &

echo "=== ГОТОВО! СЕРВИСЫ ПЕРЕЗАПУЩЕНЫ ==="
echo "Логи: /workspace/logs/"

