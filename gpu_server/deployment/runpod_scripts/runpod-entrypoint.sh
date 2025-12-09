#!/bin/bash

# RunPod Entrypoint Script
# Path: /workspace/.runpod/runpod-entrypoint.sh
# This script runs automatically when the pod starts

set -e

LOG_DIR="/workspace/.runpod/logs"
LOG_FILE="${LOG_DIR}/entrypoint.log"
SCRIPT_DIR="/workspace/.runpod/scripts"
START_SCRIPT="${SCRIPT_DIR}/start.sh"

# Ensure log directory exists
mkdir -p "${LOG_DIR}"

# Log function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "${LOG_FILE}"
}

log "========================================="
log "RunPod entrypoint starting"
log "========================================="

# Check if start script exists
if [ ! -f "${START_SCRIPT}" ]; then
    log "ERROR: Start script not found at ${START_SCRIPT}"
    log "Please ensure start.sh is properly deployed"
    exit 1
fi

# Make sure start script is executable
chmod +x "${START_SCRIPT}"

# Execute ComfyUI start script
log "Executing ComfyUI start script..."
bash "${START_SCRIPT}"

EXIT_CODE=$?

if [ ${EXIT_CODE} -eq 0 ]; then
    log "✓ ComfyUI started successfully"
else
    log "✗ ComfyUI start failed with exit code: ${EXIT_CODE}"
    exit ${EXIT_CODE}
fi

log "========================================="
log "RunPod entrypoint completed"
log "========================================="

# Keep the container running (if needed for some setups)
# Note: This is not blocking - the main process is already running in background
