#!/bin/bash
# Deploy and start model downloads on RunPod

set -e

SSH_KEY_PATH="/f/generator/gpu_server/deployment/runpod_scripts/coder_key"
SSH_TARGET="p8q2agahufxw4a-64410d8e@ssh.runpod.io"

echo "========================================"
echo "Model Download Deployment"
echo "========================================"
echo ""

# Upload download script
echo "[1/3] Uploading download script..."
cat download_models.sh | ssh -i "$SSH_KEY_PATH" -o StrictHostKeyChecking=no "$SSH_TARGET" "cat > /workspace/download_models.sh && chmod +x /workspace/download_models.sh && exit" 2>&1 | grep -v "WARNING\|post-quantum\|PTY" || true
echo "  ✓ Download script uploaded"
echo ""

# Upload starter script
echo "[2/3] Uploading starter script..."
cat start_downloads.sh | ssh -i "$SSH_KEY_PATH" -o StrictHostKeyChecking=no "$SSH_TARGET" "cat > /workspace/start_downloads.sh && chmod +x /workspace/start_downloads.sh && exit" 2>&1 | grep -v "WARNING\|post-quantum\|PTY" || true
echo "  ✓ Starter script uploaded"
echo ""

# Execute starter
echo "[3/3] Starting download process..."
ssh -i "$SSH_KEY_PATH" -o StrictHostKeyChecking=no "$SSH_TARGET" "bash /workspace/start_downloads.sh; exit" 2>&1 | grep -v "WARNING\|post-quantum\|PTY" || true

echo ""
echo "========================================"
echo "Downloads Started"
echo "========================================"
echo ""
echo "✓ Download scripts deployed and execution initiated"
echo ""
echo "Models being downloaded (~16GB total):"
echo "  1. SDXL Base 1.0 (6.9GB)"
echo "  2. SDXL VAE (335MB)"
echo "  3. ControlNet Canny (2.5GB)"
echo "  4. ControlNet Depth (2.5GB)"
echo "  5. GFPGAN v1.4 (348MB)"
echo "  6. INSwapper 128 (301MB)"
echo "  7. IP-Adapter Plus SDXL (1.0GB)"
echo ""
echo "To monitor progress, connect to server via RunPod Web Terminal:"
echo "  https://www.runpod.io/console/pods"
echo ""
echo "Commands to check status on server:"
echo "  tail -f /workspace/download.log"
echo "  ls -lh /workspace/ComfyUI/models/checkpoints/"
echo "  ps aux | grep wget"
echo ""
