#!/bin/bash
# QUICK SETUP - Скопируйте и вставьте этот скрипт в RunPod Web Terminal
# Выполняет полное развёртывание за один раз

set -e

echo "🚀 Быстрая установка AI-инфраструктуры на RunPod"
echo "================================================"

# Создание структуры
mkdir -p /workspace/models/{checkpoints,loras,vae,controlnet,ipadapter,insightface,upscale_models,embeddings,diffusers}
mkdir -p /workspace/ComfyUI
mkdir -p /workspace/workflows
mkdir -p /tmp/gpu_results
mkdir -p /app

# Установка зависимостей
pip install -q torch torchvision --index-url https://download.pytorch.org/whl/cu118
pip install -q diffusers transformers accelerate safetensors fastapi uvicorn httpx pydantic insightface onnxruntime-gpu opencv-python pillow

# Установка переменных окружения
export MODEL_CACHE_DIR=/workspace/models
export HF_HOME=/workspace/models
export DIFFUSERS_CACHE=/workspace/models/diffusers

# Загрузка SDXL Base
python3 <<'PY'
from diffusers import StableDiffusionXLPipeline
import torch
print("Загрузка SDXL Base...")
pipe = StableDiffusionXLPipeline.from_pretrained(
    "stabilityai/stable-diffusion-xl-base-1.0",
    torch_dtype=torch.float16,
    cache_dir="/workspace/models/diffusers"
)
print("✓ SDXL Base загружен")
PY

# Загрузка ControlNet Canny
python3 <<'PY'
from diffusers import ControlNetModel
import torch
print("Загрузка ControlNet Canny...")
cn = ControlNetModel.from_pretrained(
    "diffusers/controlnet-canny-sdxl-1.0",
    torch_dtype=torch.float16,
    cache_dir="/workspace/models/diffusers"
)
print("✓ ControlNet загружен")
PY

# Загрузка InsightFace
python3 <<'PY'
from insightface.app import FaceAnalysis
print("Установка InsightFace...")
app = FaceAnalysis(name='buffalo_l')
app.prepare(ctx_id=0, det_size=(640, 640))
print("✓ InsightFace установлен")
PY

echo ""
echo "✅ Базовые модели установлены"
echo "📁 Модели: /workspace/models/diffusers"
echo ""
echo "Теперь загрузите проект на сервер и запустите GPU сервер"
