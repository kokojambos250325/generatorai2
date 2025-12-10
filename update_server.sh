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
pkill -f 'uvicorn.*main:app' || true
pkill -f 'python.*bot.py' || true
sleep 2

# Запускаем Backend
echo "   - Запуск Backend..."
nohup python -m uvicorn gpu_server.server.main:app --host 0.0.0.0 --port 3000 > /workspace/logs/backend.log 2>&1 &

# Запускаем Telegram Bot
echo "   - Запуск Telegram Bot..."
export PYTHONPATH=/workspace/ai-generator
# Подгружаем .env если есть
if [ -f .env ]; then export $(cat .env | xargs); fi
cd /workspace/ai-generator
nohup python telegram_bot/bot.py > /workspace/logs/telegram_bot.log 2>&1 &

echo "=== ГОТОВО! СЕРВИСЫ ПЕРЕЗАПУЩЕНЫ ==="
echo "Логи: /workspace/logs/"

