#!/bin/bash
#
# Restart Services Script
# Restarts backend and GPU server to load new logging code
#

set -e

WORKSPACE="/workspace"
LOGS_DIR="$WORKSPACE/logs"

echo "======================================"
echo "Restarting AI Generation Services"
echo "======================================"

# Function to stop service
stop_service() {
    local service_name=$1
    local pid_file=$2
    
    if [ -f "$pid_file" ]; then
        pid=$(cat "$pid_file")
        if ps -p "$pid" > /dev/null 2>&1; then
            echo "Stopping $service_name (PID: $pid)..."
            kill "$pid"
            sleep 2
            
            # Force kill if still running
            if ps -p "$pid" > /dev/null 2>&1; then
                echo "Force stopping $service_name..."
                kill -9 "$pid"
            fi
            
            echo "$service_name stopped"
        fi
        rm -f "$pid_file"
    else
        echo "$service_name not running (no PID file)"
    fi
}

# Function to start service
start_service() {
    local service_name=$1
    local service_path=$2
    local start_command=$3
    local log_file=$4
    local pid_file=$5
    
    echo "Starting $service_name..."
    
    cd "$service_path" || {
        echo "ERROR: Failed to change to $service_path"
        return 1
    }
    
    # Start service in background
    nohup $start_command > "$log_file" 2>&1 &
    local pid=$!
    
    # Save PID
    echo "$pid" > "$pid_file"
    
    # Wait and check
    sleep 3
    if ps -p "$pid" > /dev/null 2>&1; then
        echo "$service_name started successfully (PID: $pid)"
        return 0
    else
        echo "ERROR: $service_name failed to start"
        return 1
    fi
}

# Activate virtual environment
source "$WORKSPACE/venv/bin/activate"

# Stop services (in reverse order)
echo ""
echo "Stopping services..."
echo "--------------------"
stop_service "Telegram Bot" "$WORKSPACE/telegram_bot.pid"
stop_service "Backend API" "$WORKSPACE/backend.pid"
stop_service "GPU Server" "$WORKSPACE/gpu_server.pid"

echo ""
echo "Waiting 5 seconds..."
sleep 5

# Start services
echo ""
echo "Starting services..."
echo "--------------------"

# Start GPU Server
start_service \
    "GPU Server" \
    "$WORKSPACE/gpu_server" \
    "python server.py" \
    "$LOGS_DIR/gpu_server.log" \
    "$WORKSPACE/gpu_server.pid"

echo "Waiting for GPU server to be ready..."
sleep 5

# Check GPU server health
if curl -s http://localhost:8002/health > /dev/null 2>&1; then
    echo "✓ GPU server is responding"
else
    echo "⚠ GPU server is not responding yet"
fi

# Start Backend
start_service \
    "Backend API" \
    "$WORKSPACE/backend" \
    "uvicorn main:app --host 0.0.0.0 --port 8000" \
    "$LOGS_DIR/backend.log" \
    "$WORKSPACE/backend.pid"

echo "Waiting for backend to be ready..."
sleep 5

# Check backend health
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✓ Backend is responding"
else
    echo "⚠ Backend is not responding yet"
fi

# Start Telegram Bot (if configured)
if [ -f "$WORKSPACE/telegram_bot/.env" ]; then
    start_service \
        "Telegram Bot" \
        "$WORKSPACE/telegram_bot" \
        "python bot.py" \
        "$LOGS_DIR/telegram_bot.log" \
        "$WORKSPACE/telegram_bot.pid"
else
    echo "Telegram bot .env not found, skipping"
fi

echo ""
echo "======================================"
echo "Services restarted successfully"
echo "======================================"
echo ""
echo "To view logs:"
echo "  tail -f $LOGS_DIR/backend.log"
echo "  tail -f $LOGS_DIR/gpu_server.log"
echo "  tail -f $LOGS_DIR/comfyui.log"
echo ""
