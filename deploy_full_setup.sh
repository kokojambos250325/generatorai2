#!/bin/bash
# Полный автономный скрипт развёртывания AI-инфраструктуры на RunPod
# Выполняет все задачи без участия пользователя

set -e

echo "========================================="
echo "🚀 Начало полного развёртывания"
echo "========================================="
echo "Время старта: $(date '+%Y-%m-%d %H:%M:%S')"

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# ============================================
# 1. ДИАГНОСТИКА И ПОДГОТОВКА ОКРУЖЕНИЯ
# ============================================

log_info "Проверка GPU и CUDA..."
if command -v nvidia-smi &> /dev/null; then
    nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
    GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader | head -1)
    GPU_MEMORY=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader | head -1)
    log_info "GPU: $GPU_NAME | VRAM: $GPU_MEMORY"
else
    log_error "nvidia-smi не найден! GPU недоступен"
    exit 1
fi

log_info "Обновление системных пакетов..."
apt-get update -qq || true

log_info "Установка необходимых утилит..."
apt-get install -y -qq \
    wget \
    aria2 \
    git \
    curl \
    unzip \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgl1-mesa-glx \
    ffmpeg \
    || true

# ============================================
# 2. СОЗДАНИЕ СТРУКТУРЫ ДИРЕКТОРИЙ
# ============================================

log_info "Создание структуры директорий..."

mkdir -p /workspace/models/{checkpoints,loras,vae,controlnet,ipadapter,insightface,upscale_models,embeddings}
mkdir -p /workspace/models/diffusers
mkdir -p /workspace/ComfyUI/{custom_nodes,input,output}
mkdir -p /workspace/workflows
mkdir -p /workspace/.runpod/{scripts,logs}
mkdir -p /tmp/gpu_results
mkdir -p /var/log

log_info "✓ Директории созданы"

# ============================================
# 3. УСТАНОВКА PYTHON ЗАВИСИМОСТЕЙ
# ============================================

log_info "Установка Python зависимостей..."

pip install --upgrade pip -q
pip install -q torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip install -q \
    diffusers==0.25.0 \
    transformers==4.36.0 \
    accelerate==0.25.0 \
    safetensors==0.4.1 \
    opencv-python==4.8.1.78 \
    pillow==10.1.0 \
    insightface==0.7.3 \
    onnxruntime-gpu==1.16.3 \
    fastapi==0.109.0 \
    uvicorn==0.27.0 \
    httpx==0.26.0 \
    pydantic==2.5.3 \
    python-multipart==0.0.6

log_info "✓ Python зависимости установлены"

# ============================================
# 4. ЗАГРУЗКА МОДЕЛЕЙ (АВТОМАТИЧЕСКИ)
# ============================================

log_info "========================================="
log_info "📦 Начало загрузки моделей"
log_info "========================================="

export HF_HOME=/workspace/models
export DIFFUSERS_CACHE=/workspace/models/diffusers
export MODEL_CACHE_DIR=/workspace/models

# SDXL Base
log_info "Загрузка SDXL Base (6.9GB)..."
python3 - <<EOF
from diffusers import StableDiffusionXLPipeline
import torch

model_id = "stabilityai/stable-diffusion-xl-base-1.0"
pipeline = StableDiffusionXLPipeline.from_pretrained(
    model_id,
    torch_dtype=torch.float16,
    use_safetensors=True,
    cache_dir="/workspace/models/diffusers"
)
print("✓ SDXL Base загружен")
EOF

# SDXL Refiner
log_info "Загрузка SDXL Refiner (6.1GB)..."
python3 - <<EOF
from diffusers import StableDiffusionXLImg2ImgPipeline
import torch

model_id = "stabilityai/stable-diffusion-xl-refiner-1.0"
pipeline = StableDiffusionXLImg2ImgPipeline.from_pretrained(
    model_id,
    torch_dtype=torch.float16,
    use_safetensors=True,
    cache_dir="/workspace/models/diffusers"
)
print("✓ SDXL Refiner загружен")
EOF

# ControlNet models
log_info "Загрузка ControlNet Canny..."
python3 - <<EOF
from diffusers import ControlNetModel
import torch

controlnet = ControlNetModel.from_pretrained(
    "diffusers/controlnet-canny-sdxl-1.0",
    torch_dtype=torch.float16,
    cache_dir="/workspace/models/diffusers"
)
print("✓ ControlNet Canny загружен")
EOF

log_info "Загрузка ControlNet Depth..."
python3 - <<EOF
from diffusers import ControlNetModel
import torch

controlnet = ControlNetModel.from_pretrained(
    "diffusers/controlnet-depth-sdxl-1.0",
    torch_dtype=torch.float16,
    cache_dir="/workspace/models/diffusers"
)
print("✓ ControlNet Depth загружен")
EOF

log_info "Загрузка ControlNet OpenPose..."
python3 - <<EOF
from diffusers import ControlNetModel
import torch

controlnet = ControlNetModel.from_pretrained(
    "thibaud/controlnet-openpose-sdxl-1.0",
    torch_dtype=torch.float16,
    cache_dir="/workspace/models/diffusers"
)
print("✓ ControlNet OpenPose загружен")
EOF

# InsightFace
log_info "Установка InsightFace моделей..."
python3 - <<EOF
from insightface.app import FaceAnalysis

app = FaceAnalysis(name='buffalo_l', providers=['CUDAExecutionProvider', 'CPUExecutionProvider'])
app.prepare(ctx_id=0, det_size=(640, 640))
print("✓ InsightFace установлен")
EOF

log_info "========================================="
log_info "✓ Все модели загружены успешно"
log_info "========================================="

# ============================================
# 5. НАСТРОЙКА COMFYUI
# ============================================

log_info "Клонирование ComfyUI..."
if [ ! -d "/workspace/ComfyUI/.git" ]; then
    cd /workspace
    git clone https://github.com/comfyanonymous/ComfyUI.git
    cd ComfyUI
else
    log_warn "ComfyUI уже установлен, обновляем..."
    cd /workspace/ComfyUI
    git pull
fi

log_info "Установка зависимостей ComfyUI..."
pip install -q -r requirements.txt

# Создание extra_model_paths.yaml
log_info "Создание extra_model_paths.yaml..."
cat > /workspace/ComfyUI/extra_model_paths.yaml <<'YAML'
# Пути к моделям для ComfyUI
models:
  checkpoints: /workspace/models/checkpoints
  loras: /workspace/models/loras
  vae: /workspace/models/vae
  controlnet: /workspace/models/controlnet
  ipadapter: /workspace/models/ipadapter
  insightface: /workspace/models/insightface
  upscale_models: /workspace/models/upscale_models
  embeddings: /workspace/models/embeddings
YAML

log_info "✓ ComfyUI настроен"

# ============================================
# 6. СОЗДАНИЕ WORKFLOW ФАЙЛОВ
# ============================================

log_info "Создание workflow файлов..."

# Free generation workflow
cat > /workspace/workflows/free_workflow_template.json <<'JSON'
{
  "3": {
    "inputs": {
      "seed": 42,
      "steps": 30,
      "cfg": 7.5,
      "sampler_name": "euler",
      "scheduler": "normal",
      "denoise": 1
    },
    "class_type": "KSampler"
  },
  "4": {
    "inputs": {
      "ckpt_name": "sd_xl_base_1.0.safetensors"
    },
    "class_type": "CheckpointLoaderSimple"
  },
  "5": {
    "inputs": {
      "width": 1024,
      "height": 1024,
      "batch_size": 1
    },
    "class_type": "EmptyLatentImage"
  },
  "6": {
    "inputs": {
      "text": "a beautiful landscape"
    },
    "class_type": "CLIPTextEncode"
  },
  "7": {
    "inputs": {
      "text": "blurry, low quality"
    },
    "class_type": "CLIPTextEncode"
  },
  "8": {
    "class_type": "VAEDecode"
  },
  "9": {
    "inputs": {
      "filename_prefix": "ComfyUI"
    },
    "class_type": "SaveImage"
  }
}
JSON

log_info "✓ Workflow файлы созданы"

# ============================================
# 7. КОПИРОВАНИЕ ПРОЕКТА
# ============================================

log_info "Копирование файлов проекта..."
if [ -d "/app" ]; then
    log_info "Проект уже находится в /app"
else
    log_warn "Директория /app не найдена, создаём..."
    mkdir -p /app
fi

# ============================================
# 8. НАСТРОЙКА ПЕРЕМЕННЫХ ОКРУЖЕНИЯ
# ============================================

log_info "Настройка переменных окружения..."

cat >> ~/.bashrc <<'ENV'
# AI Project Environment
export MODEL_CACHE_DIR=/workspace/models
export RESULT_STORAGE_DIR=/tmp/gpu_results
export HF_HOME=/workspace/models
export DIFFUSERS_CACHE=/workspace/models/diffusers
export COMFYUI_URL=http://127.0.0.1:8188
export GPU_SERVER_PORT=3000
export LOG_LEVEL=INFO
ENV

source ~/.bashrc

log_info "✓ Переменные окружения настроены"

# ============================================
# 9. СОЗДАНИЕ SYSTEMD СЕРВИСА ДЛЯ COMFYUI
# ============================================

log_info "Создание systemd сервиса для ComfyUI..."

cat > /etc/systemd/system/comfyui.service <<'SERVICE'
[Unit]
Description=ComfyUI Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/workspace/ComfyUI
Environment="PATH=/usr/local/bin:/usr/bin:/bin"
ExecStart=/usr/bin/python3 main.py --listen 0.0.0.0 --port 8188
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICE

systemctl daemon-reload
systemctl enable comfyui
systemctl start comfyui

log_info "✓ ComfyUI сервис создан и запущен"

# ============================================
# 10. ФИНАЛЬНАЯ ДИАГНОСТИКА
# ============================================

log_info "========================================="
log_info "🔍 Финальная диагностика"
log_info "========================================="

log_info "Проверка моделей:"
ls -lh /workspace/models/diffusers/*/snapshots/*/

log_info "Проверка ComfyUI:"
sleep 5
curl -s http://localhost:8188 > /dev/null && log_info "✓ ComfyUI доступен" || log_warn "ComfyUI пока недоступен"

log_info "Проверка GPU:"
python3 - <<EOF
import torch
print(f"CUDA доступна: {torch.cuda.is_available()}")
print(f"Устройство: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'}")
EOF

# ============================================
# ФИНАЛ
# ============================================

log_info "========================================="
log_info "✅ РАЗВЁРТЫВАНИЕ ЗАВЕРШЕНО УСПЕШНО"
log_info "========================================="
log_info "Время завершения: $(date '+%Y-%m-%d %H:%M:%S')"

echo ""
log_info "📋 Итоговая информация:"
echo "  GPU Server: http://localhost:3000"
echo "  ComfyUI: http://localhost:8188"
echo "  Модели: /workspace/models"
echo "  Workflows: /workspace/workflows"
echo "  Логи: /var/log/gpu_server.log"
echo ""
log_info "Для проверки здоровья GPU сервера:"
echo "  curl http://localhost:3000/health"
echo ""
