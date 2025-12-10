#!/bin/bash
# Полный скрипт для скачивания всех моделей
# Использование: bash download_all_models.sh [CIVITAI_TOKEN]

set -e

CIVITAI_TOKEN="${1:-}"
CHECKPOINTS_DIR="/workspace/ComfyUI/models/checkpoints"
LORA_DIR="/workspace/ComfyUI/models/loras"
CONTROLNET_DIR="/workspace/ComfyUI/models/controlnet"

echo "=== СКАЧИВАНИЕ ВСЕХ МОДЕЛЕЙ ==="
echo ""

# 1. ControlNet модели
echo "1. Установка ControlNet моделей для SD 1.5..."
cd "$CONTROLNET_DIR"

CONTROLNET_URLS=(
    "https://huggingface.co/lllyasviel/ControlNet-v1-1/resolve/main/control_v11p_sd15_canny.pth"
    "https://huggingface.co/lllyasviel/ControlNet-v1-1/resolve/main/control_v11f1p_sd15_depth.pth"
    "https://huggingface.co/lllyasviel/ControlNet-v1-1/resolve/main/control_v11p_sd15_openpose.pth"
)

for url in "${CONTROLNET_URLS[@]}"; do
    filename=$(basename "$url")
    if [ -f "$filename" ] && [ -s "$filename" ]; then
        size=$(du -h "$filename" | cut -f1)
        echo "   ✓ $filename уже установлен ($size)"
    else
        echo "   ⬇️  Скачивание $filename..."
        wget -q --show-progress -O "$filename" "$url" && {
            size=$(du -h "$filename" | cut -f1)
            echo "   ✓ $filename установлен ($size)"
        } || echo "   ❌ Ошибка при скачивании $filename"
    fi
done

echo ""

# 2. Полная версия Pony
echo "2. Полная FP32 версия CyberRealistic Pony..."
cd "$CHECKPOINTS_DIR"

if [ -f "cyberrealisticPony_v14.safetensors" ]; then
    current_size=$(du -h "cyberrealisticPony_v14.safetensors" | cut -f1)
    echo "   Текущая версия: $current_size"
    
    # Проверяем размер (полная версия ~12.92 GB, pruned ~6.5 GB)
    size_bytes=$(stat -f%z "cyberrealisticPony_v14.safetensors" 2>/dev/null || stat -c%s "cyberrealisticPony_v14.safetensors" 2>/dev/null || echo "0")
    size_gb=$((size_bytes / 1024 / 1024 / 1024))
    
    if [ "$size_gb" -lt 10 ]; then
        echo "   ⚠️  Обнаружена pruned версия (нужна полная 12.92 GB)"
        
        if [ -n "$CIVITAI_TOKEN" ]; then
            echo "   ⬇️  Скачивание полной версии через Civitai API..."
            # MODEL_VERSION_ID для полной версии v15.0 (нужно обновить при необходимости)
            curl -H "Authorization: Bearer $CIVITAI_TOKEN" \
                 -L "https://civitai.com/api/download/models/2469412" \
                 -o cyberrealisticPony_v14.safetensors.new && {
                mv cyberrealisticPony_v14.safetensors cyberrealisticPony_v14.safetensors.old
                mv cyberrealisticPony_v14.safetensors.new cyberrealisticPony_v14.safetensors
                echo "   ✓ Полная версия установлена"
            } || echo "   ❌ Ошибка при скачивании через API"
        else
            echo "   📝 Для автоматической загрузки укажите CIVITAI_TOKEN:"
            echo "      bash download_all_models.sh YOUR_CIVITAI_TOKEN"
            echo "   Или скачайте вручную с: https://civitai.com/models/443821/cyberrealistic-pony"
        fi
    else
        echo "   ✓ Полная версия уже установлена"
    fi
else
    echo "   ❌ Модель не найдена!"
    if [ -n "$CIVITAI_TOKEN" ]; then
        echo "   ⬇️  Скачивание через Civitai API..."
        curl -H "Authorization: Bearer $CIVITAI_TOKEN" \
             -L "https://civitai.com/api/download/models/2469412" \
             -o cyberrealisticPony_v14.safetensors && \
        echo "   ✓ Модель установлена" || echo "   ❌ Ошибка"
    else
        echo "   📝 Скачайте модель вручную с Civitai"
    fi
fi

echo ""

# 3. LoRA модели (популярные для улучшения качества)
echo "3. Популярные LoRA модели..."
cd "$LORA_DIR"

# Популярные LoRA модели (ID с Civitai)
# Примечание: ID могут измениться, проверьте актуальные на Civitai
LORA_MODELS=(
    # "128713:add_detail.safetensors"  # Add Detail LoRA
    # Добавьте другие популярные LoRA здесь
)

if [ -n "$CIVITAI_TOKEN" ] && [ ${#LORA_MODELS[@]} -gt 0 ]; then
    for lora in "${LORA_MODELS[@]}"; do
        IFS=':' read -r model_id filename <<< "$lora"
        if [ ! -f "$filename" ] || [ ! -s "$filename" ]; then
            echo "   ⬇️  Скачивание $filename..."
            curl -H "Authorization: Bearer $CIVITAI_TOKEN" \
                 -L "https://civitai.com/api/download/models/$model_id" \
                 -o "$filename" && \
            echo "   ✓ $filename установлен" || echo "   ❌ Ошибка: $filename"
        else
            size=$(du -h "$filename" | cut -f1)
            echo "   ✓ $filename уже установлен ($size)"
        fi
    done
else
    echo "   📝 Рекомендуемые LoRA модели (скачайте вручную с Civitai):"
    echo "      - add_detail (детализация)"
    echo "      - eyes_detail (детализация глаз)"
    echo "      - realistic_vision (реалистичность)"
    echo "      - detail_tweaker (улучшение деталей)"
    if [ -z "$CIVITAI_TOKEN" ]; then
        echo ""
        echo "   💡 Для автоматической загрузки LoRA укажите CIVITAI_TOKEN"
    fi
fi

echo ""
echo "=== ПРОВЕРКА УСТАНОВЛЕННЫХ МОДЕЛЕЙ ==="
echo ""
echo "Checkpoints:"
ls -lh "$CHECKPOINTS_DIR"/*.safetensors 2>/dev/null | awk '{printf "   %-50s %s\n", $9, $5}' || echo "   Нет checkpoint'ов"
echo ""
echo "ControlNet:"
ls -lh "$CONTROLNET_DIR"/*.pth 2>/dev/null | awk '{printf "   %-50s %s\n", $9, $5}' || echo "   Нет ControlNet моделей"
echo ""
echo "LoRA:"
ls -lh "$LORA_DIR"/*.safetensors 2>/dev/null | awk '{printf "   %-50s %s\n", $9, $5}' | grep -v "put_loras" || echo "   Нет LoRA моделей"

echo ""
echo "=== ГОТОВО ==="
echo ""
echo "💡 Для получения CIVITAI_TOKEN:"
echo "   1. Зарегистрируйтесь на https://civitai.com"
echo "   2. Перейдите в https://civitai.com/user/account"
echo "   3. Скопируйте API Token"
echo "   4. Запустите: bash download_all_models.sh YOUR_TOKEN"

