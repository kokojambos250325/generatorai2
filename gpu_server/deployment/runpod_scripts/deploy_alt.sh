#!/bin/bash
# RunPod Deployment Script - Alternative Method
# Uses SSH cat to transfer files instead of SCP

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
    exit 1
fi

# Set proper permissions
chmod 600 "$SSH_KEY_PATH"

echo "Using SSH key: $SSH_KEY_PATH"
echo ""

# Create remote directories
echo "[1/4] Preparing remote environment..."
ssh -i "$SSH_KEY_PATH" -o StrictHostKeyChecking=no "$SSH_TARGET" "mkdir -p /workspace/.runpod/logs /workspace/.runpod/scripts; exit" 2>&1 | grep -v "WARNING\|post-quantum" || true
echo "  ✓ Directories created"

# Upload setup script via SSH cat
echo ""
echo "[2/4] Uploading setup script..."
SETUP_SCRIPT="${SCRIPT_DIR}/setup_heavy_ai_pipelines.sh"

if [ ! -f "$SETUP_SCRIPT" ]; then
    echo "  ✗ Setup script not found: $SETUP_SCRIPT"
    exit 1
fi

# Transfer file content via SSH
cat "$SETUP_SCRIPT" | ssh -i "$SSH_KEY_PATH" -o StrictHostKeyChecking=no "$SSH_TARGET" "cat > /workspace/.runpod/setup_heavy_ai_pipelines.sh; chmod +x /workspace/.runpod/setup_heavy_ai_pipelines.sh; exit" 2>&1 | grep -v "WARNING\|post-quantum" || true
echo "  ✓ Script uploaded and permissions set"

# Execute setup
echo ""
echo "[3/4] Executing remote setup..."
echo "========================================"
echo "Remote Setup Starting (10-15 minutes)"
echo "========================================"
echo ""

ssh -i "$SSH_KEY_PATH" -o StrictHostKeyChecking=no "$SSH_TARGET" "bash /workspace/.runpod/setup_heavy_ai_pipelines.sh; exit" 2>&1 | grep -v "WARNING\|post-quantum"

EXIT_CODE=${PIPESTATUS[0]}

echo ""
echo "========================================"
echo "[4/4] Deployment completed"
echo "========================================"

if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo "✓ Deployment Completed Successfully!"
    echo ""
    echo "Next Steps:"
    echo "1. View setup report:"
    echo "   ssh -i $SSH_KEY_PATH $SSH_TARGET"
    echo "   cat /workspace/.runpod/logs/heavy_ai_setup_report.log"
    echo ""
    echo "2. Access ComfyUI:"
    echo "   https://p8q2agahufxw4a-8188.proxy.runpod.net"
    echo ""
else
    echo ""
    echo "⚠ Deployment finished with exit code: $EXIT_CODE"
    echo ""
    echo "Check logs:"
    echo "   ssh -i $SSH_KEY_PATH $SSH_TARGET"
    echo "   cat /tmp/heavy_ai_setup_actions.log"
    echo ""
fi

exit $EXIT_CODE
