#!/bin/bash
cd /workspace/ComfyUI/models/embeddings

# Create embeddings directory if not exists
mkdir -p /workspace/ComfyUI/models/embeddings

echo "Downloading CyberRealistic embeddings from HuggingFace..."

# CyberRealistic Positive (Pony)
echo "1. Downloading CyberRealistic Positive (Pony)..."
wget --show-progress \
  "https://huggingface.co/John6666/cyberrealistic-positive-pony-xl-embedding/resolve/main/cyberrealisticPositive_pony.safetensors" \
  -O cyberrealistic_positive_pony.safetensors

# CyberRealistic Negative  
echo "2. Downloading CyberRealistic Negative..."
wget --show-progress \
  "https://huggingface.co/datasets/Zaeb1/embeddings/resolve/main/cyberrealistic_negative.pt" \
  -O cyberrealistic_negative.pt

echo "Done!"
ls -lh
