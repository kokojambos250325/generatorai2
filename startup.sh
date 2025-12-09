#!/bin/bash
#
# Startup Script for RunPod POD
# Automatically starts all services on POD boot
#
# Location: /workspace/startup.sh
# Make executable: chmod +x /workspace/startup.sh
#

set -e  # Exit on error

# Configuration
WORKSPACE="/workspace"
VENV_PATH="$WORKSPACE/venv"
LOGS_DIR="$WORKSPACE/logs"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
}

# Start logging to file
exec > >(tee -a "$LOGS_DIR/startup.log") 2>&1

log "======================================"
log "Starting AI Generation Services"
log "======================================"

# Create logs directory if it doesn't exist
mkdir -p "$LOGS_DIR"

# Check if virtual environment exists
if [ ! -d "$VENV_PATH" ]; then
    log_warn "Virtual environment not found at $VENV_PATH"
    log "Creating virtual environment..."
    python3 -m venv "$VENV_PATH"
fi

# Activate virtual environment
log "Activating virtual environment..."
source "$VENV_PATH/bin/activate"

# Function to start a service
start_service() {
    local service_name=$1
    local service_path=$2
    local start_command=$3
    local log_file=$4
    local pid_file=$5
    
    log "Starting $service_name..."
    
    # Check if service is already running
    if [ -f "$pid_file" ]; then
        old_pid=$(cat "$pid_file")
        if ps -p "$old_pid" > /dev/null 2>&1; then
            log_warn "$service_name is already running (PID: $old_pid)"
            return 0
        else
            log_warn "Found stale PID file for $service_name, cleaning up..."
            rm "$pid_file"
        fi
    fi
    
    # Change to service directory
    cd "$service_path" || {
        log_error "Failed to change to $service_path"
        return 1
    }
    
    # Start service in background
    nohup $start_command > "$log_file" 2>&1 &
    local pid=$!
    
    # Save PID
    echo "$pid" > "$pid_file"
    
    # Wait a moment and check if process started successfully
    sleep 2
    if ps -p "$pid" > /dev/null 2>&1; then
        log "$service_name started successfully (PID: $pid)"
        return 0
    else
        log_error "$service_name failed to start"
        return 1
    fi
}

# Start GPU Server (must start first)
log "======================================"
log "Starting GPU Server"
log "======================================"

start_service \
    "GPU Server" \
    "$WORKSPACE/gpu_server" \
    "python server.py" \
    "$LOGS_DIR/gpu_server.log" \
    "$WORKSPACE/gpu_server.pid"

# Wait for GPU server to be ready
log "Waiting for GPU server to be ready..."
sleep 5

# Check GPU server health
if curl -s http://localhost:8002/health > /dev/null 2>&1; then
    log "GPU server is responding"
else
    log_warn "GPU server is not responding yet (this may be normal on first start)"
fi

# Start Backend API
log "======================================"
log "Starting Backend API"
log "======================================"

start_service \
    "Backend API" \
    "$WORKSPACE/backend" \
    "uvicorn main:app --host 0.0.0.0 --port 8000" \
    "$LOGS_DIR/backend.log" \
    "$WORKSPACE/backend.pid"

# Wait for backend to be ready
log "Waiting for backend to be ready..."
sleep 5

# Check backend health
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    log "Backend is responding"
else
    log_warn "Backend is not responding yet"
fi

# Optional: Start Telegram Bot (if configured)
if [ -f "$WORKSPACE/telegram_bot/.env" ]; then
    log "======================================"
    log "Starting Telegram Bot"
    log "======================================"
    
    start_service \
        "Telegram Bot" \
        "$WORKSPACE/telegram_bot" \
        "python bot.py" \
        "$LOGS_DIR/telegram_bot.log" \
        "$WORKSPACE/telegram_bot.pid"
else
    log_warn "Telegram bot .env not found, skipping bot startup"
fi

# Display status
log "======================================"
log "Startup Complete"
log "======================================"
log ""
log "Service Status:"
log "---------------"

# Check GPU Server
if [ -f "$WORKSPACE/gpu_server.pid" ]; then
    pid=$(cat "$WORKSPACE/gpu_server.pid")
    if ps -p "$pid" > /dev/null 2>&1; then
        log "✓ GPU Server: RUNNING (PID: $pid)"
    else
        log_error "✗ GPU Server: FAILED"
    fi
else
    log_error "✗ GPU Server: NO PID FILE"
fi

# Check Backend
if [ -f "$WORKSPACE/backend.pid" ]; then
    pid=$(cat "$WORKSPACE/backend.pid")
    if ps -p "$pid" > /dev/null 2>&1; then
        log "✓ Backend API: RUNNING (PID: $pid)"
    else
        log_error "✗ Backend API: FAILED"
    fi
else
    log_error "✗ Backend API: NO PID FILE"
fi

# Check Telegram Bot (optional)
if [ -f "$WORKSPACE/telegram_bot.pid" ]; then
    pid=$(cat "$WORKSPACE/telegram_bot.pid")
    if ps -p "$pid" > /dev/null 2>&1; then
        log "✓ Telegram Bot: RUNNING (PID: $pid)"
    else
        log_error "✗ Telegram Bot: FAILED"
    fi
fi

log ""
log "Logs location: $LOGS_DIR"
log "To view logs: tail -f $LOGS_DIR/<service>.log"
log "To check status: python infra/ssh_manager.py status"
log ""
log "======================================"

# Keep script running (optional, for container environments)
# wait
