#!/bin/bash
cd /workspace/ComfyUI/models

# Create upscale models directory
mkdir -p upscale_models
mkdir -p facerestore_models

echo "Downloading upscale models..."

# RealESRGAN x4plus (67MB) - основной для апскейла
wget -q --show-progress \
  "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth" \
  -O upscale_models/RealESRGAN_x4plus.pth

# RealESRGAN x4plus anime (17MB) - для anime
wget -q --show-progress \
  "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.2.4/RealESRGAN_x4plus_anime_6B.pth" \
  -O upscale_models/RealESRGAN_x4plus_anime_6B.pth

echo "Downloading face restoration models..."

# CodeFormer (376MB) - лучший для восстановления лиц
wget -q --show-progress \
  "https://github.com/sczhou/CodeFormer/releases/download/v0.1.0/codeformer.pth" \
  -O facerestore_models/codeformer.pth

# GFPGAN v1.4 (348MB) - альтернатива
wget -q --show-progress \
  "https://github.com/TencentARC/GFPGAN/releases/download/v1.3.0/GFPGANv1.4.pth" \
  -O facerestore_models/GFPGANv1.4.pth

echo "Done!"
ls -lh upscale_models/
ls -lh facerestore_models/
