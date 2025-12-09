#!/bin/bash
# Check model download status

SSH_KEY_PATH="/f/generator/gpu_server/deployment/runpod_scripts/coder_key"
SSH_TARGET="p8q2agahufxw4a-64410d8e@ssh.runpod.io"

echo "Checking download status..."
echo ""

# Create a status check script to run remotely
STATUS_CMD='
if [ -f /workspace/download.pid ]; then
    PID=$(cat /workspace/download.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo "✓ Download process is RUNNING (PID: $PID)"
        echo ""
        echo "Recent download activity:"
        tail -20 /workspace/download.log 2>/dev/null || echo "  No log available yet"
        echo ""
        echo "Downloaded models:"
        find /workspace/ComfyUI/models -name "*.safetensors" -o -name "*.pth" 2>/dev/null | while read file; do
            size=$(ls -lh "$file" | awk "{print \$5}")
            echo "  $size - $(basename $file)"
        done
    else
        echo "✗ Download process NOT running (PID $PID exited)"
        echo ""
        echo "Last 20 lines of log:"
        tail -20 /workspace/download.log 2>/dev/null || echo "  No log file"
    fi
else
    echo "⚠ No download.pid file found"
    echo "Checking for running wget processes:"
    ps aux | grep wget | grep -v grep || echo "  No wget processes running"
fi
exit
'

ssh -i "$SSH_KEY_PATH" -o StrictHostKeyChecking=no "$SSH_TARGET" "$STATUS_CMD" 2>&1 | grep -v "WARNING\|post-quantum\|PTY" || true
