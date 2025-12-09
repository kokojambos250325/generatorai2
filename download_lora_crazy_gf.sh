#!/bin/bash
cd /workspace/ComfyUI/models/loras

# Create loras directory if not exists
mkdir -p /workspace/ComfyUI/models/loras

# Download Crazy Girlfriend Mix [XL/PONY] LoRA from HuggingFace
echo "Downloading Crazy Girlfriend Mix [XL/PONY] LoRA from HuggingFace..."
wget --show-progress \
  "https://huggingface.co/John6666/crazy-girlfriend-mix-xlpony-sdxl/resolve/main/crazy-girlfriend-mix-xlpony-v1285_InstaBaddiePONY.safetensors" \
  -O crazy_girlfriend_mix_pony.safetensors

echo "Done!"
ls -lh crazy_girlfriend_mix_pony.safetensors
