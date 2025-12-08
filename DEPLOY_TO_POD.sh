#!/bin/bash
################################################################################
# ЕДИНЫЙ СКРИПТ РАЗВЕРТЫВАНИЯ MVP НА RUNPOD POD
# Вставьте весь скрипт в интерактивную SSH сессию POD
################################################################################

set -e
cd /workspace

echo "=================================================="
echo "  RunPod MVP Deployment - Complete Setup"
echo "=================================================="

# Step 1: Clone repository
echo ""
echo "[1/8] Cloning repository from GitHub..."
if [ -d "temp_repo" ]; then
    rm -rf temp_repo
fi
git clone https://github.com/kokojambos250325/generatorai2.git temp_repo
echo "✓ Repository cloned"

# Step 2: Copy files to workspace
echo ""
echo "[2/8] Copying files to /workspace..."
cp -r temp_repo/backend ./
cp -r temp_repo/gpu_server ./
cp temp_repo/startup.sh ./
cp -r temp_repo/infra ./
echo "✓ Files copied"

# Cleanup
rm -rf temp_repo
echo "✓ Temporary files removed"

# Step 3: Create necessary directories
echo ""
echo "[3/8] Creating additional directories..."
mkdir -p logs models workflows
echo "✓ Directories created"

# Step 4: Setup Python virtual environment
echo ""
echo "[4/8] Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✓ venv created"
else
    echo "✓ venv already exists"
fi

source venv/bin/activate
echo "✓ venv activated: $(which python)"
python --version

# Step 5: Install backend dependencies
echo ""
echo "[5/8] Installing backend dependencies..."
cd backend
pip install --upgrade pip -q
pip install -r requirements.txt
echo "✓ Backend dependencies installed"

# Step 6: Install GPU server dependencies
echo ""
echo "[6/8] Installing GPU server dependencies..."
cd ../gpu_server
pip install -r requirements.txt
echo "✓ GPU server dependencies installed"

cd /workspace

# Step 7: Create .env files
echo ""
echo "[7/8] Creating environment configuration..."
cp backend/.env.template backend/.env
cp gpu_server/.env.template gpu_server/.env
echo "✓ .env files created"

# Step 8: Make startup script executable
echo ""
echo "[8/8] Setting up startup script..."
chmod +x startup.sh
echo "✓ startup.sh is executable"

# Display final structure
echo ""
echo "=================================================="
echo "  DEPLOYMENT COMPLETE!"
echo "=================================================="
echo ""
echo "Directory structure:"
ls -la /workspace/
echo ""
echo "Backend files:"
ls -la backend/ | head -15
echo ""
echo "GPU server files:"
ls -la gpu_server/ | head -15
echo ""
echo "=================================================="
echo "  STARTING SERVICES..."
echo "=================================================="

# Start services
source venv/bin/activate
./startup.sh

# Wait for services to start
echo ""
echo "Waiting 15 seconds for services to initialize..."
sleep 15

# Test health endpoints
echo ""
echo "=================================================="
echo "  TESTING SERVICES"
echo "=================================================="
echo ""
echo "Backend health check:"
curl -s http://localhost:8000/health || echo "❌ Backend not responding"
echo ""
echo ""
echo "GPU server health check:"
curl -s http://localhost:8001/health || echo "❌ GPU server not responding"

echo ""
echo "=================================================="
echo "  STATUS"
echo "=================================================="
echo "Running processes:"
ps aux | grep -E "(uvicorn|python.*server.py)" | grep -v grep

echo ""
echo "Logs available at:"
echo "  - /workspace/logs/backend.log"
echo "  - /workspace/logs/gpu_server.log"
echo ""
echo "View logs: tail -f /workspace/logs/backend.log"
echo "=================================================="
