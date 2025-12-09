#!/bin/bash
# Complete Model Installation Script for AI Generator
# Downloads all required models for all pipelines

set -e

echo "========================================="
echo "📦 AI Generator - Complete Model Installation"
echo "========================================="
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Model directory
MODEL_DIR="/workspace/ComfyUI/models"

# Create all required directories
echo -e "${BLUE}[1/6] Creating model directories...${NC}"
mkdir -p ${MODEL_DIR}/checkpoints
mkdir -p ${MODEL_DIR}/controlnet
mkdir -p ${MODEL_DIR}/ipadapter
mkdir -p ${MODEL_DIR}/clip_vision
mkdir -p ${MODEL_DIR}/insightface/models
mkdir -p ${MODEL_DIR}/vae
echo -e "${GREEN}✓ Directories created${NC}"

# Function to download with progress
download_model() {
    local url=$1
    local output=$2
    local description=$3
    
    echo -e "${BLUE}Downloading: ${description}${NC}"
    if [ -f "$output" ]; then
        echo -e "${YELLOW}  ⚠ File already exists, skipping${NC}"
    else
        wget -q --show-progress -O "$output" "$url" || {
            echo -e "${YELLOW}  ⚠ Download failed, will retry${NC}"
            return 1
        }
        echo -e "${GREEN}  ✓ Downloaded${NC}"
    fi
}

# ============================================
# SDXL Base Models (~13GB)
# ============================================
echo ""
echo -e "${BLUE}[2/6] SDXL Base Models${NC}"

download_model \
    "https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/resolve/main/sd_xl_base_1.0.safetensors" \
    "${MODEL_DIR}/checkpoints/sd_xl_base_1.0.safetensors" \
    "SDXL Base 1.0 (6.6 GB)"

download_model \
    "https://huggingface.co/stabilityai/stable-diffusion-xl-refiner-1.0/resolve/main/sd_xl_refiner_1.0.safetensors" \
    "${MODEL_DIR}/checkpoints/sd_xl_refiner_1.0.safetensors" \
    "SDXL Refiner 1.0 (6.1 GB)"

# ============================================
# ControlNet Models (~9GB)
# ============================================
echo ""
echo -e "${BLUE}[3/6] ControlNet Models${NC}"

download_model \
    "https://huggingface.co/lllyasviel/sd_control_collection/resolve/main/diffusers_xl_canny_mid.safetensors" \
    "${MODEL_DIR}/controlnet/diffusers_xl_canny_mid.safetensors" \
    "ControlNet Canny SDXL (5.0 GB)"

download_model \
    "https://huggingface.co/thibaud/controlnet-openpose-sdxl-1.0/resolve/main/control-lora-openposeXL2-rank256.safetensors" \
    "${MODEL_DIR}/controlnet/control-lora-openposeXL2-rank256.safetensors" \
    "ControlNet OpenPose SDXL (1.5 GB)"

download_model \
    "https://huggingface.co/diffusers/controlnet-depth-sdxl-1.0/resolve/main/diffusion_pytorch_model.safetensors" \
    "${MODEL_DIR}/controlnet/controlnet-depth-sdxl-1.0.safetensors" \
    "ControlNet Depth SDXL (2.5 GB)"

# ============================================
# IP-Adapter Models (~3.5GB)
# ============================================
echo ""
echo -e "${BLUE}[4/6] IP-Adapter Models${NC}"

download_model \
    "https://huggingface.co/h94/IP-Adapter/resolve/main/sdxl_models/ip-adapter_sdxl.safetensors" \
    "${MODEL_DIR}/ipadapter/ip-adapter_sdxl.safetensors" \
    "IP-Adapter SDXL (689 MB)"

download_model \
    "https://huggingface.co/h94/IP-Adapter-FaceID/resolve/main/ip-adapter-faceid_sdxl.bin" \
    "${MODEL_DIR}/ipadapter/ip-adapter-faceid_sdxl.bin" \
    "IP-Adapter FaceID SDXL (656 MB)"

mkdir -p ${MODEL_DIR}/clip_vision/SD1.5
download_model \
    "https://huggingface.co/h94/IP-Adapter/resolve/main/models/image_encoder/model.safetensors" \
    "${MODEL_DIR}/clip_vision/SD1.5/model.safetensors" \
    "CLIP Vision Model (2.5 GB)"

# ============================================
# InsightFace Models (~400MB)
# ============================================
echo ""
echo -e "${BLUE}[5/6] InsightFace Models${NC}"

cd ${MODEL_DIR}/insightface/models
if [ ! -d "antelopev2" ]; then
    echo "Downloading antelopev2 pack..."
    wget -q --show-progress https://github.com/deepinsight/insightface/releases/download/v0.7/antelopev2.zip
    unzip -q antelopev2.zip
    rm antelopev2.zip
    echo -e "${GREEN}  ✓ antelopev2 installed${NC}"
else
    echo -e "${YELLOW}  ⚠ antelopev2 already installed${NC}"
fi

# ============================================
# VAE Models (~335MB)
# ============================================
echo ""
echo -e "${BLUE}[6/6] VAE Models${NC}"

download_model \
    "https://huggingface.co/stabilityai/sdxl-vae/resolve/main/sdxl_vae.safetensors" \
    "${MODEL_DIR}/vae/sdxl_vae.safetensors" \
    "SDXL VAE (335 MB)"

# ============================================
# Summary
# ============================================
echo ""
echo "========================================="
echo -e "${GREEN}✅ Model Installation Complete!${NC}"
echo "========================================="
echo ""

TOTAL_SIZE=$(du -sh ${MODEL_DIR} | cut -f1)
echo "📊 Total model size: $TOTAL_SIZE"

echo ""
echo "📁 Installed models:"
echo "  - SDXL Base + Refiner: ✓"
echo "  - ControlNet (Canny, OpenPose, Depth): ✓"
echo "  - IP-Adapter + FaceID: ✓"
echo "  - CLIP Vision: ✓"
echo "  - InsightFace (antelopev2): ✓"
echo "  - SDXL VAE: ✓"

echo ""
echo "🎯 Ready pipelines:"
echo "  ✓ Free Generation (SDXL)"
echo "  ✓ Face Swap (SDXL + ControlNet + InsightFace)"
echo "  ✓ Face Consistent (SDXL + IP-Adapter)"
echo "  ✓ Clothes Removal (SDXL + ControlNet)"

echo ""
echo "🔄 Next steps:"
echo "  1. Restart FastAPI server to load models"
echo "  2. Test model loading via /health endpoint"
echo "  3. Configure Telegram bot"
echo ""
