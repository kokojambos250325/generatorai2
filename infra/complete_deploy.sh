#!/bin/bash
# Complete MVP Deployment Script for RunPod POD
# To be executed in interactive SSH session
# Run: ssh p8q2agahufxw4a-64410d8e@ssh.runpod.io -i ~/.ssh/id_ed25519
# Then paste this entire script

set -e
cd /workspace

echo "=========================================="
echo "RunPod MVP Deployment Starting..."
echo "=========================================="

# Step 1: Create directory structure
echo ""
echo "[1/10] Creating directory structure..."
mkdir -p backend/routers backend/schemas backend/services backend/clients backend/utils
mkdir -p gpu_server/workflows gpu_server/schemas gpu_server/services
mkdir -p logs models workflows

# Create __init__.py files
touch backend/__init__.py backend/routers/__init__.py backend/schemas/__init__.py
touch backend/services/__init__.py backend/clients/__init__.py backend/utils/__init__.py
touch gpu_server/__init__.py gpu_server/workflows/__init__.py
touch gpu_server/schemas/__init__.py gpu_server/services/__init__.py

echo "✓ Structure created"

# Step 2: Create backend requirements.txt
echo ""
echo "[2/10] Creating backend/requirements.txt..."
cat > backend/requirements.txt << 'EOF'
# FastAPI and Server
fastapi==0.109.0
uvicorn[standard]==0.27.0
pydantic==2.5.3
pydantic-settings==2.1.0

# HTTP Client
httpx==0.26.0

# Image Processing
Pillow==10.2.0

# Development
python-multipart==0.0.6
EOF

echo "✓ backend/requirements.txt created"

# Step 3: Create gpu_server requirements.txt
echo ""
echo "[3/10] Creating gpu_server/requirements.txt..."
cat > gpu_server/requirements.txt << 'EOF'
# FastAPI
fastapi==0.109.0
uvicorn[standard]==0.27.0
pydantic==2.5.3
pydantic-settings==2.1.0

# HTTP Client
httpx==0.26.0

# Image Processing
Pillow==10.2.0
EOF

echo "✓ gpu_server/requirements.txt created"

# Step 4: Create Python virtual environment
echo ""
echo "[4/10] Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✓ venv created"
else
    echo "✓ venv already exists"
fi

source venv/bin/activate
echo "✓ venv activated ($(which python))"

# Step 5: Install backend dependencies
echo ""
echo "[5/10] Installing backend dependencies..."
cd backend
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo "✓ Backend dependencies installed"

# Step 6: Install GPU server dependencies
echo ""
echo "[6/10] Installing GPU server dependencies..."
cd ../gpu_server
pip install -r requirements.txt -q
echo "✓ GPU server dependencies installed"

cd /workspace

# Step 7: Create environment files
echo ""
echo "[7/10] Creating environment configuration files..."
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

# Step 8: Verify Python installations
echo ""
echo "[8/10] Verifying Python packages..."
python -c "import fastapi, uvicorn, httpx, pydantic; print('✓ All core packages available')"

# Step 9: Display structure
echo ""
echo "[9/10] Directory structure:"
ls -R backend | head -30
ls -R gpu_server | head -30

# Step 10: Final status
echo ""
echo "[10/10] Deployment phase 1 complete!"
echo ""
echo "=========================================="
echo "Next steps:"
echo "1. Transfer Python files to backend/ and gpu_server/"
echo "2. Create startup.sh"
echo "3. Run startup.sh to start services"
echo "=========================================="
echo ""
echo "Current status:"
echo "- Virtual environment: $(which python)"
echo "- Working directory: $(pwd)"
echo "- Backend structure: $(ls -la backend | wc -l) items"
echo "- GPU server structure: $(ls -la gpu_server | wc -l) items"
