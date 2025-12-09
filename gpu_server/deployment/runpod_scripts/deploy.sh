#!/bin/bash
# RunPod Deployment Script for Git Bash
# Deploys complete AI infrastructure to RunPod server

set -e

echo "========================================"
echo "RunPod Infrastructure Deployment"
echo "========================================"
echo ""

# SSH connection details
SSH_HOST="ssh.runpod.io"
SSH_USER="p8q2agahufxw4a-64410d8e"
SSH_TARGET="${SSH_USER}@${SSH_HOST}"
SSH_KEY="coder_key"

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SSH_KEY_PATH="${SCRIPT_DIR}/${SSH_KEY}"

# Verify key file exists
if [ ! -f "$SSH_KEY_PATH" ]; then
    echo "✗ SSH key file not found: $SSH_KEY_PATH"
    echo "Please ensure coder_key exists in: $SCRIPT_DIR"
    exit 1
fi

# Set proper permissions for SSH key
chmod 600 "$SSH_KEY_PATH"

echo "Using SSH key: $SSH_KEY_PATH"
echo ""

# Test SSH connection
echo "[1/5] Testing SSH connection..."
if ssh -i "$SSH_KEY_PATH" -o StrictHostKeyChecking=no -o ConnectTimeout=15 "$SSH_TARGET" "echo 'Connected successfully'; exit" 2>&1 | grep -q "Connected successfully"; then
    echo "  ✓ SSH connection successful"
else
    echo "  ⚠ SSH test had issues, but continuing with deployment..."
fi

# Create remote directories
echo ""
echo "[2/5] Preparing remote directories..."
ssh -i "$SSH_KEY_PATH" -o StrictHostKeyChecking=no "$SSH_TARGET" "mkdir -p /workspace/.runpod/logs /workspace/.runpod/scripts; exit" 2>&1 >/dev/null
echo "  ✓ Command sent"

# Upload setup script
echo ""
echo "[3/5] Uploading setup script..."
SETUP_SCRIPT="${SCRIPT_DIR}/setup_heavy_ai_pipelines.sh"

if [ ! -f "$SETUP_SCRIPT" ]; then
    echo "  ✗ Setup script not found: $SETUP_SCRIPT"
    exit 1
fi

scp -i "$SSH_KEY_PATH" -o StrictHostKeyChecking=no "$SETUP_SCRIPT" "${SSH_TARGET}:/workspace/.runpod/setup_heavy_ai_pipelines.sh" 2>&1 >/dev/null
echo "  ✓ Script uploaded"

# Set executable permissions
echo ""
echo "[4/5] Setting script permissions..."
ssh -i "$SSH_KEY_PATH" -o StrictHostKeyChecking=no "$SSH_TARGET" "chmod +x /workspace/.runpod/setup_heavy_ai_pipelines.sh; exit" 2>&1 >/dev/null
echo "  ✓ Permissions set"

# Execute setup
echo ""
echo "[5/5] Executing remote setup..."
echo "========================================"
echo "Remote Setup Starting (10-15 minutes)"
echo "========================================"
echo ""

ssh -i "$SSH_KEY_PATH" -o StrictHostKeyChecking=no "$SSH_TARGET" "bash /workspace/.runpod/setup_heavy_ai_pipelines.sh; exit"

EXIT_CODE=$?

echo ""
echo "========================================"

if [ $EXIT_CODE -eq 0 ]; then
    echo "✓ Deployment Completed Successfully!"
    echo "========================================"
    echo ""
    echo "Next Steps:"
    echo ""
    echo "1. View full setup report:"
    echo "   ssh -i $SSH_KEY_PATH $SSH_TARGET"
    echo "   cat /workspace/.runpod/logs/heavy_ai_setup_report.log"
    echo ""
    echo "2. Access ComfyUI web interface:"
    echo "   https://p8q2agahufxw4a-8188.proxy.runpod.net"
    echo ""
    echo "3. Download model weights (see documentation):"
    echo "   F:/generator/gpu_server/MODEL_INSTALLATION.md"
    echo ""
    echo "4. Configure FastAPI server (next task)"
    echo ""
else
    echo "✗ Deployment Encountered Issues"
    echo "========================================"
    echo ""
    echo "Exit Code: $EXIT_CODE"
    echo ""
    echo "Troubleshooting:"
    echo "1. SSH to server:"
    echo "   ssh -i $SSH_KEY_PATH $SSH_TARGET"
    echo ""
    echo "2. Check setup logs:"
    echo "   cat /tmp/heavy_ai_setup_actions.log"
    echo "   cat /workspace/.runpod/logs/comfyui.log"
    echo ""
fi

exit $EXIT_CODE
