#!/bin/bash

# ComfyUI Auto-Start Script for RunPod
# Path: /workspace/.runpod/scripts/start.sh

set -e

# Configuration
WORKSPACE_DIR="/workspace/ComfyUI"
VENV_DIR="${WORKSPACE_DIR}/venv"
LOG_DIR="/workspace/.runpod/logs"
LOG_FILE="${LOG_DIR}/comfyui.log"
PID_FILE="/workspace/.runpod/comfyui.pid"

# Ensure log directory exists
mkdir -p "${LOG_DIR}"

# Log function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "${LOG_FILE}"
}

log "========================================="
log "Starting ComfyUI initialization"
log "========================================="

# Check if workspace directory exists
if [ ! -d "${WORKSPACE_DIR}" ]; then
    log "ERROR: ComfyUI directory not found at ${WORKSPACE_DIR}"
    exit 1
fi

# Check if venv exists
if [ ! -d "${VENV_DIR}" ]; then
    log "ERROR: Virtual environment not found at ${VENV_DIR}"
    log "Please create venv first: python -m venv ${VENV_DIR}"
    exit 1
fi

# Change to workspace directory
cd "${WORKSPACE_DIR}"
log "Changed to directory: $(pwd)"

# Activate virtual environment
log "Activating virtual environment..."
source "${VENV_DIR}/bin/activate"

# Verify Python is available
if ! command -v python &> /dev/null; then
    log "ERROR: Python not found in virtual environment"
    exit 1
fi

log "Python version: $(python --version)"

# Check if main.py exists
if [ ! -f "main.py" ]; then
    log "ERROR: main.py not found in ${WORKSPACE_DIR}"
    exit 1
fi

# Check dependencies
log "Checking dependencies..."
python -c "import torch; print(f'PyTorch version: {torch.__version__}')" >> "${LOG_FILE}" 2>&1 || {
    log "WARNING: PyTorch not found or import failed"
}

# Kill existing ComfyUI process if running
if [ -f "${PID_FILE}" ]; then
    OLD_PID=$(cat "${PID_FILE}")
    if ps -p "${OLD_PID}" > /dev/null 2>&1; then
        log "Stopping existing ComfyUI process (PID: ${OLD_PID})..."
        kill "${OLD_PID}" 2>/dev/null || true
        sleep 2
    fi
    rm -f "${PID_FILE}"
fi

# Start ComfyUI in background
log "Starting ComfyUI server on 0.0.0.0:8188..."
nohup python main.py \
    --listen 0.0.0.0 \
    --port 8188 \
    --disable-auto-launch \
    >> "${LOG_FILE}" 2>&1 &

# Save PID
COMFYUI_PID=$!
echo "${COMFYUI_PID}" > "${PID_FILE}"

log "ComfyUI started with PID: ${COMFYUI_PID}"

# Wait a few seconds and verify process is running
sleep 5

if ps -p "${COMFYUI_PID}" > /dev/null 2>&1; then
    log "✓ ComfyUI is running successfully"
    log "Access UI at: http://<POD_IP>:8188"
    log "Log file: ${LOG_FILE}"
else
    log "✗ ERROR: ComfyUI process died after startup"
    log "Check logs at: ${LOG_FILE}"
    exit 1
fi

log "========================================="
log "ComfyUI startup completed"
log "========================================="
