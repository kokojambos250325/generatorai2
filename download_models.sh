#!/bin/bash
# Скрипт для скачивания моделей на сервер

set -e

echo "=== СКАЧИВАНИЕ МОДЕЛЕЙ ==="
echo ""

CHECKPOINTS_DIR="/workspace/ComfyUI/models/checkpoints"
LORA_DIR="/workspace/ComfyUI/models/loras"
CONTROLNET_DIR="/workspace/ComfyUI/models/controlnet"

# Проверка ControlNet моделей
echo "1. Проверка ControlNet моделей..."
cd "$CONTROLNET_DIR"
CONTROLNET_MODELS=(
    "https://huggingface.co/lllyasviel/ControlNet-v1-1/resolve/main/control_v11p_sd15_canny.pth"
    "https://huggingface.co/lllyasviel/ControlNet-v1-1/resolve/main/control_v11f1p_sd15_depth.pth"
    "https://huggingface.co/lllyasviel/ControlNet-v1-1/resolve/main/control_v11p_sd15_openpose.pth"
)

for url in "${CONTROLNET_MODELS[@]}"; do
    filename=$(basename "$url")
    if [ ! -f "$filename" ] || [ ! -s "$filename" ]; then
        echo "   Скачивание $filename..."
        wget -q --show-progress -O "$filename" "$url" || echo "   Ошибка: $filename"
    else
        size=$(du -h "$filename" | cut -f1)
        echo "   ✓ $filename уже установлен ($size)"
    fi
done

echo ""

# Информация о Pony модели
echo "2. Полная FP32 версия CyberRealistic Pony..."
echo "   ⚠️  Требуется ручная загрузка с Civitai"
echo "   Ссылка: https://civitai.com/models/443821/cyberrealistic-pony"
echo "   Версия: Full Model fp32 (12.92 GB)"
echo "   После скачивания замените: $CHECKPOINTS_DIR/cyberrealisticPony_v14.safetensors"
echo ""

# Популярные LoRA модели (попробуем скачать через Civitai API)
echo "3. Популярные LoRA модели для улучшения качества..."
cd "$LORA_DIR"

# Популярные LoRA модели с Civitai (ID моделей)
LORA_MODELS=(
    # "128713:add_detail"  # Add Detail LoRA
    # Попробуем найти другие популярные модели
)

echo "   Рекомендуемые LoRA модели (скачайте вручную с Civitai):"
echo "   - add_detail (детализация)"
echo "   - eyes_detail (детализация глаз)"  
echo "   - realistic_vision (реалистичность)"
echo "   - detail_tweaker (улучшение деталей)"
echo ""

echo "=== ПРОВЕРКА УСТАНОВЛЕННЫХ МОДЕЛЕЙ ==="
echo ""
echo "Checkpoints:"
ls -lh "$CHECKPOINTS_DIR"/*.safetensors 2>/dev/null | awk '{print "   "$9" ("$5")"}' || echo "   Нет checkpoint'ов"
echo ""
echo "ControlNet:"
ls -lh "$CONTROLNET_DIR"/*.pth 2>/dev/null | awk '{print "   "$9" ("$5")"}' || echo "   Нет ControlNet моделей"
echo ""
echo "LoRA:"
ls -lh "$LORA_DIR"/*.safetensors 2>/dev/null | awk '{print "   "$9" ("$5")"}' | grep -v "put_loras" || echo "   Нет LoRA моделей"

echo ""
echo "=== ГОТОВО ==="

