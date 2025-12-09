#!/bin/bash
cd /workspace/ComfyUI/models/vae

# Download SDXL VAE (335MB) - улучшает качество изображений
echo "Downloading SDXL VAE (335MB)..."
wget -q --show-progress \
  "https://huggingface.co/stabilityai/sdxl-vae/resolve/main/sdxl_vae.safetensors" \
  -O sdxl_vae.safetensors

# Download SDXL VAE fp16 (195MB) - быстрее, меньше памяти
echo "Downloading SDXL VAE fp16 (195MB)..."
wget -q --show-progress \
  "https://huggingface.co/madebyollin/sdxl-vae-fp16-fix/resolve/main/sdxl_vae.safetensors" \
  -O sdxl_vae_fp16.safetensors

echo "Done!"
ls -lh
