#!/bin/bash
# RunPod Quick Deploy Script
# Запуск: bash runpod_deploy.sh

set -e

echo "========================================="
echo "🚀 AI Generator RunPod Deployment"
echo "========================================="
echo ""

# Цвета для вывода
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Проверка окружения
echo -e "${BLUE}[1/8] Проверка окружения...${NC}"
cd /workspace

# GPU проверка
if command -v nvidia-smi &> /dev/null; then
    echo -e "${GREEN}✓ GPU доступен:${NC}"
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
else
    echo -e "${YELLOW}⚠ GPU не обнаружен${NC}"
fi

# Клонирование или обновление репозитория
echo ""
echo -e "${BLUE}[2/8] Обновление кода...${NC}"
if [ -d "ai-generator" ]; then
    echo "Обновление существующего репозитория..."
    cd ai-generator
    git fetch origin
    git reset --hard origin/main
    git pull origin main
else
    echo "Клонирование репозитория..."
    git clone https://github.com/kokojambos250325/ai-generator.git
    cd ai-generator
fi
echo -e "${GREEN}✓ Код обновлён${NC}"
git log -1 --oneline

# Активация виртуального окружения
echo ""
echo -e "${BLUE}[3/8] Активация виртуального окружения...${NC}"
if [ -d "/workspace/ComfyUI/venv" ]; then
    source /workspace/ComfyUI/venv/bin/activate
    echo -e "${GREEN}✓ venv активирован${NC}"
else
    echo -e "${YELLOW}⚠ venv не найден, создаём новый...${NC}"
    python -m venv /workspace/ComfyUI/venv
    source /workspace/ComfyUI/venv/bin/activate
fi

# Установка зависимостей
echo ""
echo -e "${BLUE}[4/8] Установка зависимостей...${NC}"
pip install -r requirements.txt --quiet
echo -e "${GREEN}✓ Зависимости установлены${NC}"

# Создание необходимых директорий
echo ""
echo -e "${BLUE}[5/8] Создание директорий...${NC}"
mkdir -p /workspace/.runpod/logs
mkdir -p /workspace/.runpod/scripts
mkdir -p /workspace/models
echo -e "${GREEN}✓ Директории созданы${NC}"

# Остановка старых процессов
echo ""
echo -e "${BLUE}[6/8] Остановка старых процессов...${NC}"
pkill -f "uvicorn.*main:app" || echo "Нет активных uvicorn процессов"
pkill -f "python.*run_telegram_bot" || echo "Нет активных telegram bot процессов"
sleep 3
echo -e "${GREEN}✓ Старые процессы остановлены${NC}"

# Запуск ComfyUI (если не запущен)
echo ""
echo -e "${BLUE}[7/8] Проверка ComfyUI...${NC}"
if pgrep -f "python.*main.py.*ComfyUI" > /dev/null; then
    echo -e "${GREEN}✓ ComfyUI уже запущен${NC}"
else
    echo "Запуск ComfyUI..."
    cd /workspace/ComfyUI
    source venv/bin/activate
    nohup python main.py --listen 0.0.0.0 --port 8188 > /workspace/.runpod/logs/comfyui.log 2>&1 &
    sleep 5
    echo -e "${GREEN}✓ ComfyUI запущен${NC}"
fi

# Запуск FastAPI сервера
echo ""
echo -e "${BLUE}[8/8] Запуск FastAPI сервера...${NC}"
cd /workspace/ai-generator/gpu_server/server
source /workspace/ComfyUI/venv/bin/activate
nohup python -m uvicorn main:app --host 0.0.0.0 --port 3000 --reload > /workspace/.runpod/logs/fastapi.log 2>&1 &
sleep 5
echo -e "${GREEN}✓ FastAPI сервер запущен${NC}"

# Проверка запущенных процессов
echo ""
echo "========================================="
echo -e "${GREEN}✅ Deployment завершён!${NC}"
echo "========================================="
echo ""
echo "📊 Активные процессы:"
ps aux | grep -E "(uvicorn|ComfyUI)" | grep -v grep

echo ""
echo "🔗 URL эндпоинтов:"
echo "  - ComfyUI:     https://p8q2agahufxw4a-8188.proxy.runpod.net"
echo "  - FastAPI:     https://p8q2agahufxw4a-8888.proxy.runpod.net:3000/docs"
echo "  - Health:      https://p8q2agahufxw4a-8888.proxy.runpod.net:3000/health"

echo ""
echo "📝 Просмотр логов:"
echo "  - FastAPI:     tail -f /workspace/.runpod/logs/fastapi.log"
echo "  - ComfyUI:     tail -f /workspace/.runpod/logs/comfyui.log"

echo ""
echo "🔄 Следующие шаги:"
echo "  1. Проверьте логи на ошибки"
echo "  2. Установите модели (см. gpu_server/deployment/MODEL_INSTALLATION.md)"
echo "  3. Настройте Telegram бота"
echo "  4. Протестируйте API эндпоинты"

echo ""
echo "========================================="
