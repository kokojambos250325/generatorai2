#!/bin/bash
# RunPod MVP Deployment Script - Part 2
# Configures environment and starts services

set -e
cd /workspace

echo "=== Creating Environment Files ==="
cat > backend/.env << 'EOF'
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
GPU_SERVICE_URL=http://localhost:8001
REQUEST_TIMEOUT=180
LOG_LEVEL=INFO
EOF

cat > gpu_server/.env << 'EOF'
GPU_SERVER_HOST=0.0.0.0
GPU_SERVER_PORT=8001
COMFYUI_API_URL=http://localhost:8188
MODELS_PATH=/workspace/models
WORKFLOWS_PATH=/workspace/gpu_server/workflows
LOG_LEVEL=INFO
EOF

echo "✓ Environment files created"

echo ""
echo "=== Making Startup Script Executable ==="
chmod +x startup.sh
echo "✓ startup.sh is executable"

echo ""
echo "=== Starting Services ==="
source venv/bin/activate
./startup.sh

echo ""
echo "=== Waiting for services to start ==="
sleep 10

echo ""
echo "=== Testing Health Endpoints ==="
echo "Backend health:"
curl -s http://localhost:8000/health | python -m json.tool || echo "Backend not responding"

echo ""
echo "GPU server health:"
curl -s http://localhost:8001/health | python -m json.tool || echo "GPU server not responding"

echo ""
echo "=== Deployment Complete ==="
echo "Services running:"
ps aux | grep -E "(uvicorn|python.*server.py)" | grep -v grep

echo ""
echo "View logs:"
echo "  tail -f logs/backend.log"
echo "  tail -f logs/gpu_server.log"
