#!/bin/bash
# Model Download Script for RunPod ComfyUI
# Downloads critical models for AI generation pipelines

set -e

echo "========================================"
echo "Model Download - Priority Models"
echo "========================================"
echo ""

cd /workspace/ComfyUI/models

# Function to download with progress
download_file() {
    local url=$1
    local output=$2
    local description=$3
    
    echo "Downloading: $description"
    echo "Target: $output"
    
    if [ -f "$output" ]; then
        echo "  ✓ File already exists, skipping"
        return 0
    fi
    
    wget -q --show-progress --progress=bar:force:noscroll -O "$output" "$url" 2>&1 || {
        echo "  ✗ Download failed, will retry later"
        rm -f "$output"
        return 1
    }
    
    echo "  ✓ Downloaded successfully"
}

# Priority 1: SDXL Base Models (~7GB)
echo ""
echo "[Priority 1] SDXL Base Models"
echo "========================================"

download_file \
    "https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/resolve/main/sd_xl_base_1.0.safetensors" \
    "checkpoints/sd_xl_base_1.0.safetensors" \
    "SDXL Base 1.0 (6.9GB)"

download_file \
    "https://huggingface.co/stabilityai/sdxl-vae/resolve/main/sdxl_vae.safetensors" \
    "vae/sdxl_vae.safetensors" \
    "SDXL VAE (335MB)"

# Priority 2: ControlNet Models (~7.5GB)
echo ""
echo "[Priority 2] ControlNet Models"
echo "========================================"

download_file \
    "https://huggingface.co/stabilityai/control-lora/resolve/main/control-LoRAs-rank256/control-lora-canny-rank256.safetensors" \
    "controlnet/control-lora-canny-rank256.safetensors" \
    "ControlNet Canny (2.5GB)"

download_file \
    "https://huggingface.co/stabilityai/control-lora/resolve/main/control-LoRAs-rank256/control-lora-depth-rank256.safetensors" \
    "controlnet/control-lora-depth-rank256.safetensors" \
    "ControlNet Depth (2.5GB)"

# Priority 3: Face Processing Models (~1GB)
echo ""
echo "[Priority 3] Face Processing Models"
echo "========================================"

download_file \
    "https://github.com/TencentARC/GFPGAN/releases/download/v1.3.0/GFPGANv1.4.pth" \
    "upscale/GFPGANv1.4.pth" \
    "GFPGAN v1.4 (348MB)"

download_file \
    "https://github.com/facefusion/facefusion-assets/releases/download/models/inswapper_128.onnx" \
    "insightface/models/inswapper_128.onnx" \
    "INSwapper 128 (301MB)"

# Priority 4: IP-Adapter (~1GB)
echo ""
echo "[Priority 4] IP-Adapter"
echo "========================================"

download_file \
    "https://huggingface.co/h94/IP-Adapter/resolve/main/sdxl_models/ip-adapter-plus_sdxl_vit-h.safetensors" \
    "ipadapter/ip-adapter-plus_sdxl_vit-h.safetensors" \
    "IP-Adapter Plus SDXL (1.0GB)"

echo ""
echo "========================================"
echo "Model Download Summary"
echo "========================================"
echo ""

# Check what was downloaded
echo "Downloaded models:"
du -sh checkpoints/* vae/* controlnet/* upscale/* insightface/models/* ipadapter/* 2>/dev/null || echo "  (checking...)"

echo ""
echo "Total space used:"
du -sh /workspace/ComfyUI/models/

echo ""
echo "========================================"
echo "✓ Critical models download complete!"
echo "========================================"
echo ""
echo "Next: Download optional models (Realism, Anime)"
echo "      or proceed with FastAPI setup"
