#!/bin/bash

echo "🔧 Fixing ComfyUI dependencies..."

# Activate ComfyUI venv
source /workspace/ComfyUI/venv/bin/activate

# Install missing packages
echo "📦 Installing tqdm and related packages..."
pip install tqdm transformers[torch] accelerate safetensors huggingface-hub --no-cache-dir

# Deactivate venv
deactivate

echo "✅ Dependencies fixed!"
echo "🔄 Now restart services with: bash /workspace/startup_all_services.sh"
