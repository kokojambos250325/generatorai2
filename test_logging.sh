#!/bin/bash
#
# Test Logging Chain Script
# Tests complete log chain for free generation request
#

set -e

WORKSPACE="/workspace"
LOGS_DIR="$WORKSPACE/logs"
BACKEND_URL="http://localhost:8000"

echo "======================================"
echo "Testing Logging Chain"
echo "======================================"
echo ""

# Check if services are running
echo "Checking services..."
echo "--------------------"

# Check backend
if curl -s "$BACKEND_URL/health" > /dev/null 2>&1; then
    echo "✓ Backend is running"
else
    echo "✗ Backend is not responding"
    exit 1
fi

# Check GPU server
if curl -s http://localhost:8002/health > /dev/null 2>&1; then
    echo "✓ GPU server is running"
else
    echo "✗ GPU server is not responding"
    exit 1
fi

# Check ComfyUI
if curl -s http://localhost:8188/system_stats > /dev/null 2>&1; then
    echo "✓ ComfyUI is running"
else
    echo "⚠ ComfyUI may not be running (continuing anyway)"
fi

echo ""
echo "Sending test generation request..."
echo "------------------------------------"

# Create test request JSON
cat > /tmp/test_request.json <<'EOF'
{
  "mode": "free",
  "style": "super_realism",
  "prompt": "beautiful landscape with mountains and lake at sunset",
  "extra_params": {
    "quality": "balanced"
  }
}
EOF

# Send request and capture response
echo "Request payload:"
cat /tmp/test_request.json
echo ""

echo "Sending request to $BACKEND_URL/generate..."
RESPONSE=$(curl -s -X POST "$BACKEND_URL/generate" \
  -H "Content-Type: application/json" \
  -d @/tmp/test_request.json)

echo "Response received:"
echo "$RESPONSE" | jq '.' 2>/dev/null || echo "$RESPONSE"
echo ""

# Extract request_id from response if possible
REQUEST_ID=$(echo "$RESPONSE" | jq -r '.request_id // empty' 2>/dev/null)

if [ -z "$REQUEST_ID" ]; then
    echo "⚠ Could not extract request_id from response"
    echo "Waiting 5 seconds for generation to complete..."
    sleep 5
    
    # Get last request_id from backend logs
    REQUEST_ID=$(grep '"event": "generate_request"' "$LOGS_DIR/backend.log" 2>/dev/null | tail -1 | grep -o '"request_id": "[^"]*"' | cut -d'"' -f4)
fi

if [ -n "$REQUEST_ID" ]; then
    echo "Request ID: $REQUEST_ID"
    echo ""
    echo "======================================"
    echo "Verifying Log Chain"
    echo "======================================"
    echo ""
    
    # Check backend logs
    echo "Backend Events:"
    echo "---------------"
    if grep -q "$REQUEST_ID" "$LOGS_DIR/backend.log" 2>/dev/null; then
        grep "$REQUEST_ID" "$LOGS_DIR/backend.log" | jq -r '"\(.event) - \(.ts)"' 2>/dev/null || grep "$REQUEST_ID" "$LOGS_DIR/backend.log"
        BACKEND_EVENTS=$(grep -c "$REQUEST_ID" "$LOGS_DIR/backend.log")
        echo ""
        echo "✓ Found $BACKEND_EVENTS backend events for request_id: $REQUEST_ID"
    else
        echo "✗ No backend events found for request_id: $REQUEST_ID"
    fi
    echo ""
    
    # Get generation_id from backend logs
    GENERATION_ID=$(grep "$REQUEST_ID" "$LOGS_DIR/backend.log" 2>/dev/null | grep -o '"generation_id": "[^"]*"' | head -1 | cut -d'"' -f4)
    
    if [ -n "$GENERATION_ID" ]; then
        echo "Generation ID: $GENERATION_ID"
        echo ""
        
        # Check GPU server logs
        echo "GPU Server Events:"
        echo "------------------"
        if grep -q "$GENERATION_ID" "$LOGS_DIR/gpu_server.log" 2>/dev/null; then
            grep "$GENERATION_ID" "$LOGS_DIR/gpu_server.log" | jq -r '"\(.event) - \(.ts)"' 2>/dev/null || grep "$GENERATION_ID" "$LOGS_DIR/gpu_server.log"
            GPU_EVENTS=$(grep -c "$GENERATION_ID" "$LOGS_DIR/gpu_server.log")
            echo ""
            echo "✓ Found $GPU_EVENTS GPU server events for generation_id: $GENERATION_ID"
        else
            echo "✗ No GPU server events found for generation_id: $GENERATION_ID"
        fi
        echo ""
    else
        echo "⚠ Could not extract generation_id from backend logs"
        echo ""
    fi
    
    # Check for expected event types
    echo "======================================"
    echo "Expected Events Checklist"
    echo "======================================"
    echo ""
    
    echo "Backend Events (should have 5-6):"
    echo "----------------------------------"
    check_event() {
        local event_type=$1
        local log_file=$2
        local search_id=$3
        
        if grep "$search_id" "$log_file" 2>/dev/null | grep -q "\"event\": \"$event_type\""; then
            echo "✓ $event_type"
        else
            echo "✗ $event_type (missing)"
        fi
    }
    
    check_event "generate_request" "$LOGS_DIR/backend.log" "$REQUEST_ID"
    check_event "gpu_request" "$LOGS_DIR/backend.log" "$REQUEST_ID"
    check_event "gpu_response" "$LOGS_DIR/backend.log" "$REQUEST_ID"
    check_event "response_sent" "$LOGS_DIR/backend.log" "$REQUEST_ID"
    echo ""
    
    if [ -n "$GENERATION_ID" ]; then
        echo "GPU Server Events (should have 5-8):"
        echo "-------------------------------------"
        check_event "execute_request" "$LOGS_DIR/gpu_server.log" "$GENERATION_ID"
        check_event "workflow_loaded" "$LOGS_DIR/gpu_server.log" "$GENERATION_ID"
        check_event "comfyui_prompt_sent" "$LOGS_DIR/gpu_server.log" "$GENERATION_ID"
        check_event "comfyui_complete" "$LOGS_DIR/gpu_server.log" "$GENERATION_ID"
        check_event "image_retrieved" "$LOGS_DIR/gpu_server.log" "$GENERATION_ID"
        echo ""
    fi
    
    echo "======================================"
    echo "Log Chain Test Complete"
    echo "======================================"
    
else
    echo "✗ Could not find request_id to verify logging"
    echo ""
    echo "Last 5 backend log entries:"
    tail -5 "$LOGS_DIR/backend.log" 2>/dev/null || echo "Backend log not found"
fi

echo ""
echo "To view logs manually:"
echo "  tail -f $LOGS_DIR/backend.log"
echo "  tail -f $LOGS_DIR/gpu_server.log"
echo "  tail -f $LOGS_DIR/comfyui.log"
echo ""
