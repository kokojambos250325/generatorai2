#!/bin/bash
# Скрипт запуска GPU сервера на RunPod с авто-обновлением из GitHub

set -e

echo "========================================"
echo "Запуск GPU сервера на RunPod"
echo "========================================"

# Переменные окружения
export MODEL_CACHE_DIR=/workspace/models
export RESULT_STORAGE_DIR=/tmp/gpu_results
export HF_HOME=/workspace/models
export DIFFUSERS_CACHE=/workspace/models/diffusers
export GPU_SERVER_PORT=3000
export LOG_LEVEL=INFO

# Проверка и обновление из GitHub
if [ -d "/workspace/.git" ]; then
    echo "Обновление из GitHub..."
    cd /workspace
    git pull origin main || git pull origin master || echo "Git pull failed, continuing with current version"
    echo "✓ Код обновлён"
else
    echo "⚠️ Git репозиторий не найден, используем текущие файлы"
fi

# Переход в директорию проекта
if [ -d "/workspace/gpu_server" ]; then
    cd /workspace
else if [ -d "/app/gpu_server" ]; then
    cd /app
else
    echo "❌ Проект не найден!"
    exit 1
fi

# Проверка GPU
echo "Проверка GPU..."
if command -v nvidia-smi &> /dev/null; then
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
    echo "✓ GPU доступен"
else
    echo "⚠️ GPU недоступен, сервер будет работать на CPU"
fi

# Установка зависимостей если нужно
if [ -f "gpu_server/deployment/requirements.txt" ]; then
    echo "Проверка зависимостей..."
    pip install -q --no-cache-dir -r gpu_server/deployment/requirements.txt || echo "⚠️ Не удалось обновить зависимости"
fi

# Создание директорий
mkdir -p /tmp/gpu_results /var/log

# Проверка Python модулей
echo "Проверка Python модулей..."
python3 - <<EOF
import torch
import sys

if torch.cuda.is_available():
    print(f"✓ GPU: {torch.cuda.get_device_name(0)}")
    print(f"✓ VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
else:
    print("⚠️ PyTorch CUDA недоступен")

try:
    import fastapi
    print("✓ FastAPI установлен")
except:
    print("❌ FastAPI не найден")
    sys.exit(1)
EOF

echo "========================================"
echo "Запуск сервера на порту $GPU_SERVER_PORT..."
echo "Логи: /var/log/gpu_server.log"
echo "========================================"

# Запуск сервера
exec uvicorn gpu_server.server.main:app \
    --host 0.0.0.0 \
    --port $GPU_SERVER_PORT \
    --workers 1 \
    --log-level info \
    2>&1 | tee /var/log/gpu_server.log
