#!/bin/bash
# Model Installation Script for ComfyUI on RunPod GPU Server
# Run this script after ComfyUI installation

set -e  # Exit on error

echo "=========================================="
echo "ComfyUI Model Installation Script"
echo "=========================================="
echo ""

# Configuration
COMFYUI_DIR="/workspace/ComfyUI"
MODELS_DIR="$COMFYUI_DIR/models"

# Create model directories
echo "Creating model directories..."
mkdir -p "$MODELS_DIR/checkpoints"
mkdir -p "$MODELS_DIR/vae"
mkdir -p "$MODELS_DIR/loras"
mkdir -p "$MODELS_DIR/insightface/models"
mkdir -p "$MODELS_DIR/upscale_models"
mkdir -p "$MODELS_DIR/ipadapter"
mkdir -p "$MODELS_DIR/controlnet"

echo "✓ Directories created"
echo ""

# Function to download with progress
download_file() {
    local url=$1
    local output=$2
    echo "Downloading: $(basename $output)"
    wget --progress=bar:force -O "$output" "$url" 2>&1 | tail -n 1
    echo "✓ Downloaded: $(basename $output)"
}

# ==========================================
# SDXL Base Models
# ==========================================
echo "=========================================="
echo "1. Downloading SDXL Base Models (~7GB)"
echo "=========================================="

if [ ! -f "$MODELS_DIR/checkpoints/sd_xl_base_1.0.safetensors" ]; then
    echo "Downloading SDXL Base 1.0..."
    download_file \
        "https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/resolve/main/sd_xl_base_1.0.safetensors" \
        "$MODELS_DIR/checkpoints/sd_xl_base_1.0.safetensors"
else
    echo "✓ SDXL Base already exists"
fi

if [ ! -f "$MODELS_DIR/vae/sdxl_vae.safetensors" ]; then
    echo "Downloading SDXL VAE..."
    download_file \
        "https://huggingface.co/stabilityai/sdxl-vae/resolve/main/sdxl_vae.safetensors" \
        "$MODELS_DIR/vae/sdxl_vae.safetensors"
else
    echo "✓ SDXL VAE already exists"
fi

echo ""

# ==========================================
# NSFW Models (for clothes removal)
# ==========================================
echo "=========================================="
echo "2. Downloading NSFW Models (~4GB)"
echo "=========================================="

if [ ! -f "$MODELS_DIR/checkpoints/chilloutmix_NiPrunedFp32Fix.safetensors" ]; then
    echo "Downloading ChilloutMix..."
    download_file \
        "https://huggingface.co/naonovn/chilloutmix_NiPrunedFp32Fix/resolve/main/chilloutmix_NiPrunedFp32Fix.safetensors" \
        "$MODELS_DIR/checkpoints/chilloutmix_NiPrunedFp32Fix.safetensors"
else
    echo "✓ ChilloutMix already exists"
fi

echo ""

# ==========================================
# ControlNet Models
# ==========================================
echo "=========================================="
echo "3. Downloading ControlNet Models (~7.5GB)"
echo "=========================================="

if [ ! -f "$MODELS_DIR/controlnet/control-lora-canny-rank256.safetensors" ]; then
    echo "Downloading ControlNet Canny..."
    download_file \
        "https://huggingface.co/stabilityai/control-lora/resolve/main/control-LoRAs-rank256/control-lora-canny-rank256.safetensors" \
        "$MODELS_DIR/controlnet/control-lora-canny-rank256.safetensors"
else
    echo "✓ ControlNet Canny already exists"
fi

if [ ! -f "$MODELS_DIR/controlnet/control-lora-depth-rank256.safetensors" ]; then
    echo "Downloading ControlNet Depth..."
    download_file \
        "https://huggingface.co/stabilityai/control-lora/resolve/main/control-LoRAs-rank256/control-lora-depth-rank256.safetensors" \
        "$MODELS_DIR/controlnet/control-lora-depth-rank256.safetensors"
else
    echo "✓ ControlNet Depth already exists"
fi

echo ""

# ==========================================
# Face Restoration Models
# ==========================================
echo "=========================================="
echo "4. Downloading Face Restoration Models (~350MB)"
echo "=========================================="

if [ ! -f "$MODELS_DIR/upscale_models/GFPGANv1.4.pth" ]; then
    echo "Downloading GFPGAN v1.4..."
    download_file \
        "https://github.com/TencentARC/GFPGAN/releases/download/v1.3.0/GFPGANv1.4.pth" \
        "$MODELS_DIR/upscale_models/GFPGANv1.4.pth"
else
    echo "✓ GFPGAN already exists"
fi

echo ""

# ==========================================
# InsightFace Models
# ==========================================
echo "=========================================="
echo "5. Installing InsightFace Models (~400MB)"
echo "=========================================="

# InsightFace models are auto-downloaded by the library
# Just ensure the library is installed
pip install insightface onnxruntime-gpu --quiet

echo "✓ InsightFace library installed (models will auto-download on first use)"
echo ""

# ==========================================
# IP-Adapter Models
# ==========================================
echo "=========================================="
echo "6. Downloading IP-Adapter Models (~1GB)"
echo "=========================================="

if [ ! -f "$MODELS_DIR/ipadapter/ip-adapter-plus_sdxl_vit-h.safetensors" ]; then
    echo "Downloading IP-Adapter Plus SDXL..."
    download_file \
        "https://huggingface.co/h94/IP-Adapter/resolve/main/sdxl_models/ip-adapter-plus_sdxl_vit-h.safetensors" \
        "$MODELS_DIR/ipadapter/ip-adapter-plus_sdxl_vit-h.safetensors"
else
    echo "✓ IP-Adapter already exists"
fi

echo ""

# ==========================================
# Quality Enhancement LoRAs
# ==========================================
echo "=========================================="
echo "7. Downloading Quality LoRAs (~500MB)"
echo "=========================================="

if [ ! -f "$MODELS_DIR/loras/add_detail.safetensors" ]; then
    echo "Downloading Detail Tweaker LoRA..."
    download_file \
        "https://civitai.com/api/download/models/87153" \
        "$MODELS_DIR/loras/add_detail.safetensors"
else
    echo "✓ Detail LoRA already exists"
fi

echo ""

# ==========================================
# Summary
# ==========================================
echo "=========================================="
echo "Installation Summary"
echo "=========================================="
echo ""

# Calculate total size
TOTAL_SIZE=$(du -sh "$MODELS_DIR" | cut -f1)
echo "Total models size: $TOTAL_SIZE"
echo ""

echo "Installed models:"
echo "  ✓ SDXL Base + VAE"
echo "  ✓ NSFW Models (ChilloutMix)"
echo "  ✓ ControlNet (Canny, Depth)"
echo "  ✓ Face Restoration (GFPGAN)"
echo "  ✓ InsightFace (auto-download)"
echo "  ✓ IP-Adapter Plus SDXL"
echo "  ✓ Quality Enhancement LoRAs"
echo ""

echo "Model directories:"
echo "  Checkpoints: $MODELS_DIR/checkpoints/"
echo "  VAE: $MODELS_DIR/vae/"
echo "  ControlNet: $MODELS_DIR/controlnet/"
echo "  IP-Adapter: $MODELS_DIR/ipadapter/"
echo "  Face Restoration: $MODELS_DIR/upscale_models/"
echo "  LoRAs: $MODELS_DIR/loras/"
echo "  InsightFace: $MODELS_DIR/insightface/"
echo ""

echo "=========================================="
echo "Installation Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Start ComfyUI: cd $COMFYUI_DIR && python main.py"
echo "2. Access web UI: http://your-gpu-server:8188"
echo "3. Test workflows in ComfyUI interface"
echo "4. Deploy GPU server code"
echo ""
