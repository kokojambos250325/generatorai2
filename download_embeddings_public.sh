#!/bin/bash
# Скрипт для скачивания публичных embeddings

cd /workspace/ComfyUI/models/embeddings
mkdir -p /workspace/ComfyUI/models/embeddings

echo "Downloading public embeddings..."

# Negative embedding для улучшения качества
echo "1. Downloading BadDream negative embedding..."
wget --show-progress \
  "https://huggingface.co/datasets/Nerfgun3/bad_prompt_version2/resolve/main/bad_prompt_version2.pt" \
  -O bad_dream.pt

# EasyNegative
echo "2. Downloading EasyNegative embedding..."
wget --show-progress \
  "https://huggingface.co/embed/EasyNegative/resolve/main/EasyNegative.safetensors" \
  -O easynegative.safetensors

echo "Done!"
ls -lh
