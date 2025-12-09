#!/bin/bash
cd /workspace/ai-generator
cp .env .env.backup
cat > .env << 'EOF'
GPU_SERVER_URL=http://localhost:3000/api
GPU_TIMEOUT_GENERATION=900
WORKER_TIMEOUT=900
COMFYUI_URL=http://localhost:8188
WORKFLOW_DIR=/workspace/workflows
MODEL_DIR=/workspace/ComfyUI/models
BACKEND_API_URL=http://localhost:3000/api
LOG_LEVEL=INFO
TELEGRAM_BOT_TOKEN=8420116928:AAEg1qPoL5ow6OaKzubFMXEQAuoTIEOpzXE
USE_REDIS_QUEUE=false
DEFAULT_INFERENCE_STEPS=20
DEFAULT_GUIDANCE_SCALE=7.5
MAX_IMAGE_DIMENSION=1024
EOF
echo "Updated .env file"
cat .env
