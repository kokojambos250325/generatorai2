#!/bin/bash
# RunPod MVP Deployment Script - Part 1
# Creates structure and installs dependencies

set -e
cd /workspace

echo "=== Creating Directory Structure ==="
mkdir -p backend/routers backend/schemas backend/services backend/clients backend/utils
mkdir -p gpu_server/workflows gpu_server/schemas gpu_server/services logs

touch backend/__init__.py backend/routers/__init__.py backend/schemas/__init__.py
touch backend/services/__init__.py backend/clients/__init__.py backend/utils/__init__.py
touch gpu_server/__init__.py gpu_server/workflows/__init__.py
touch gpu_server/schemas/__init__.py gpu_server/services/__init__.py

echo "✓ Structure created"
ls -R backend gpu_server

echo ""
echo "=== Setting up Python Environment ==="
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✓ Virtual environment created"
fi

source venv/bin/activate
echo "✓ Using Python: $(which python)"

echo ""
echo "=== Installing Dependencies ==="
cd backend
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo "✓ Backend dependencies installed"

cd ../gpu_server
pip install -r requirements.txt -q
echo "✓ GPU server dependencies installed"

cd /workspace
echo ""
echo "=== Part 1 Complete ==="
echo "Next: Transfer Python files, then run part 2"
