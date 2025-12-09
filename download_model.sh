#!/bin/bash
cd /workspace/ComfyUI/models/checkpoints

# Download CyberRealistic Pony v14.0 from HuggingFace (public, no auth)
echo "Downloading CyberRealistic Pony v14.0 (6.94 GB) from HuggingFace..."
wget --progress=bar:force --show-progress \
  "https://huggingface.co/cyberdelia/CyberRealisticPony/resolve/main/CyberRealisticPony_V14.0.safetensors?download=true" \
  -O cyberrealisticPony_v14.safetensors

echo "Download complete!"
ls -lh cyberrealisticPony_v14.safetensors
