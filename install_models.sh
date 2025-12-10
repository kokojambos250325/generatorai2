#!/bin/bash
# Скрипт для установки моделей на сервер

set -e

MODELS_DIR="/workspace/ComfyUI/models"
CHECKPOINTS_DIR="${MODELS_DIR}/checkpoints"
CONTROLNET_DIR="${MODELS_DIR}/controlnet"
LORA_DIR="${MODELS_DIR}/loras"

echo "=== УСТАНОВКА МОДЕЛЕЙ ==="
echo ""

# Создаем директории если их нет
mkdir -p "${CHECKPOINTS_DIR}"
mkdir -p "${CONTROLNET_DIR}"
mkdir -p "${LORA_DIR}"

# 1. Установка ControlNet моделей для SD 1.5
echo "1. Установка ControlNet моделей для SD 1.5..."
echo ""

CONTROLNET_MODELS=(
    "https://huggingface.co/lllyasviel/ControlNet-v1-1/resolve/main/control_v11p_sd15_canny.pth"
    "https://huggingface.co/lllyasviel/ControlNet-v1-1/resolve/main/control_v11f1p_sd15_depth.pth"
    "https://huggingface.co/lllyasviel/ControlNet-v1-1/resolve/main/control_v11p_sd15_openpose.pth"
)

for url in "${CONTROLNET_MODELS[@]}"; do
    filename=$(basename "$url")
    filepath="${CONTROLNET_DIR}/${filename}"
    
    if [ -f "$filepath" ]; then
        size=$(du -h "$filepath" | cut -f1)
        echo "   ✓ ${filename} уже установлен (${size})"
    else
        echo "   ⬇️  Скачивание ${filename}..."
        wget -q --show-progress -O "$filepath" "$url" || {
            echo "   ❌ Ошибка при скачивании ${filename}"
            echo "   Попробуйте скачать вручную: $url"
            continue
        }
        size=$(du -h "$filepath" | cut -f1)
        echo "   ✓ ${filename} установлен (${size})"
    fi
done

echo ""

# 2. Информация о полной версии Pony
echo "2. Информация о полной FP32 версии CyberRealistic Pony..."
echo "   Текущая версия: pruned (6.5 GB)"
echo "   Нужна полная версия: FP32 (12.92 GB)"
echo "   Ссылка: https://civitai.com/models/443821/cyberrealistic-pony"
echo "   После скачивания замените: ${CHECKPOINTS_DIR}/cyberrealisticPony_v14.safetensors"
echo ""

# 3. Информация о LoRA моделях
echo "3. Информация о LoRA моделях..."
echo "   Директория: ${LORA_DIR}/"
echo "   Рекомендуемые LoRA на Civitai:"
echo "      - add_detail (детализация)"
echo "      - eyes_detail (детализация глаз)"
echo "      - realistic_vision (реалистичность)"
echo ""

echo "=== УСТАНОВКА ЗАВЕРШЕНА ==="

