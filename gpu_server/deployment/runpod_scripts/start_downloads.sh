#!/bin/bash
# Start model downloads in background

cd /workspace

# Kill any existing download processes
pkill -f download_models.sh 2>/dev/null || true

# Start download in background with nohup
nohup bash /workspace/download_models.sh > /workspace/download.log 2>&1 &
DOWNLOAD_PID=$!

# Save PID
echo $DOWNLOAD_PID > /workspace/download.pid

# Wait a moment and verify process started
sleep 2

if ps -p $DOWNLOAD_PID > /dev/null 2>&1; then
    echo "✓ Download started successfully (PID: $DOWNLOAD_PID)"
    echo ""
    echo "To monitor progress:"
    echo "  tail -f /workspace/download.log"
    echo "  ls -lh /workspace/ComfyUI/models/checkpoints/"
    echo ""
    echo "Process will continue running in background"
else
    echo "✗ Failed to start download process"
    cat /workspace/download.log 2>/dev/null || echo "No log file found"
    exit 1
fi
