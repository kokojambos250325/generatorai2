#!/bin/bash
# Универсальный скрипт скачивания LoRA
# Можно использовать для разных LoRA моделей

cd /workspace/ComfyUI/models/loras
mkdir -p /workspace/ComfyUI/models/loras

echo "Downloading LoRA models from public sources..."

# Detail Tweaker LoRA (публичная, улучшает детализацию)
echo "1. Downloading Detail Tweaker LoRA..."
wget --show-progress \
  "https://huggingface.co/2vXpSwA7/iroiro-lora/resolve/main/test_DT_enhancer/add_detail.safetensors" \
  -O add_detail.safetensors

# Реалистичная детализация глаз
echo "2. Downloading Eye Detail LoRA..."
wget --show-progress \
  "https://huggingface.co/2vXpSwA7/iroiro-lora/resolve/main/EyesGen/EyesGen.safetensors" \
  -O eyes_detail.safetensors

echo "Done!"
ls -lh
