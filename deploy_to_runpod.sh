#!/bin/bash

# Скрипт автоматического деплоя на RunPod
# Запустите в RunPod Terminal: bash deploy_to_runpod.sh

set -e

echo "🚀 Начинаем деплой AI Generator на RunPod..."

# Переход в workspace
cd /workspace

# Клонирование или обновление репозитория
if [ -d "ai-generator" ]; then
    echo "📦 Обновляем существующий репозиторий..."
    cd ai-generator
    git pull origin main
else
    echo "📦 Клонируем репозиторий..."
    git clone https://github.com/kokojambos250325/ai-generator.git ai-generator
    cd ai-generator
fi

# Установка зависимостей
echo "📚 Устанавливаем зависимости..."
pip install -r requirements.txt --quiet

# Запуск GPU сервера
echo "🔥 Запускаем GPU сервер..."
cd gpu_server/server

# Проверка GPU
if command -v nvidia-smi &> /dev/null; then
    echo "✅ GPU доступен:"
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
else
    echo "⚠️  GPU не обнаружен, продолжаем без него"
fi

# Запуск сервера
echo "🌐 Сервер запускается на порту 3000..."
python -m uvicorn main:app --host 0.0.0.0 --port 3000 --reload

echo "✅ Деплой завершён!"
