#!/usr/bin/env python3
"""
Interactive Deployment Assistant
Provides step-by-step commands to paste into SSH session
"""

import sys
from pathlib import Path

def print_header(text):
    print(f"\n{'='*70}")
    print(f"  {text}")
    print(f"{'='*70}\n")

def print_step(num, desc):
    print(f"\n[STEP {num}] {desc}")
    print("-" * 70)

def main():
    print_header("RunPod MVP Deployment - Interactive Guide")
    
    print("Due to RunPod SSH proxy limitations, you need to:")
    print("1. Open an interactive SSH session")
    print("2. Copy and paste the commands provided below")
    print()
    print("Ready? Press Enter to start...")
    input()
    
    print_step(1, "SSH into your POD")
    print("\nRun this command in PowerShell/Terminal:")
    print("\n    ssh p8q2agahufxw4a-64410d8e@ssh.runpod.io -i ~/.ssh/id_ed25519\n")
    print("After connected, press Enter to continue...")
    input()
    
    print_step(2, "Verify workspace and create structure")
    print("\nPaste these commands in SSH session:")
    print("""
cd /workspace
pwd
ls -la

# Create directory structure
mkdir -p backend/routers backend/schemas backend/services backend/clients backend/utils
mkdir -p gpu_server/workflows gpu_server/schemas gpu_server/services
mkdir -p logs

# Create __init__.py files
touch backend/__init__.py backend/routers/__init__.py backend/schemas/__init__.py
touch backend/services/__init__.py backend/clients/__init__.py backend/utils/__init__.py
touch gpu_server/__init__.py gpu_server/workflows/__init__.py
touch gpu_server/schemas/__init__.py gpu_server/services/__init__.py

# Verify structure
ls -R backend
ls -R gpu_server
""")
    print("\nAfter running above commands, press Enter...")
    input()
    
    print_step(3, "Transfer Files")
    print("\nYou have 3 options:")
    print()
    print("OPTION A: Use Git (Recommended if repo exists)")
    print("""
cd /workspace
# If you have pushed code to git repo:
git clone <your-repo-url> temp
cp -r temp/backend ./
cp -r temp/gpu_server ./
cp temp/startup.sh ./
rm -rf temp
""")
    print()
    print("OPTION B: Use rsync/scp from LOCAL machine (if direct connection works)")
    print("""
# Run from your Windows machine (NOT in SSH session):
cd C:\\projekt\\generator" -ai"
rsync -avz -e "ssh -i ~/.ssh/id_ed25519" backend/ p8q2agahufxw4a-64410d8e@ssh.runpod.io:/workspace/backend/
rsync -avz -e "ssh -i ~/.ssh/id_ed25519" gpu_server/ p8q2agahufxw4a-64410d8e@ssh.runpod.io:/workspace/gpu_server/
rsync -avz -e "ssh -i ~/.ssh/id_ed25519" startup.sh p8q2agahufxw4a-64410d8e@ssh.runpod.io:/workspace/
""")
    print()
    print("OPTION C: Manual file creation (see DEPLOYMENT_GUIDE.md)")
    print()
    print("Choose your method and complete file transfer, then press Enter...")
    input()
    
    print_step(4, "Set up Python environment")
    print("\nPaste in SSH session:")
    print("""
cd /workspace

# Create virtual environment if not exists
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "Virtual environment created"
else
    echo "Virtual environment already exists"
fi

# Activate venv
source venv/bin/activate

# Verify activation
which python
python --version
""")
    print("\nAfter running, press Enter...")
    input()
    
    print_step(5, "Install dependencies")
    print("\nPaste in SSH session:")
    print("""
cd /workspace

# Install backend dependencies
cd backend
pip install --upgrade pip
pip install -r requirements.txt

# Install GPU server dependencies
cd ../gpu_server
pip install -r requirements.txt

# Verify installations
pip list | grep fastapi
pip list | grep uvicorn
pip list | grep httpx
""")
    print("\nAfter installation completes, press Enter...")
    input()
    
    print_step(6, "Configure environment variables")
    print("\nPaste in SSH session:")
    print("""
cd /workspace

# Create backend .env
cat > backend/.env << 'EOF'
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
GPU_SERVICE_URL=http://localhost:8001
REQUEST_TIMEOUT=180
LOG_LEVEL=INFO
EOF

# Create GPU server .env
cat > gpu_server/.env << 'EOF'
GPU_SERVER_HOST=0.0.0.0
GPU_SERVER_PORT=8001
COMFYUI_API_URL=http://localhost:8188
MODELS_PATH=/workspace/models
WORKFLOWS_PATH=/workspace/gpu_server/workflows
LOG_LEVEL=INFO
EOF

# Verify .env files
cat backend/.env
cat gpu_server/.env
""")
    print("\nAfter creating .env files, press Enter...")
    input()
    
    print_step(7, "Make startup script executable")
    print("\nPaste in SSH session:")
    print("""
cd /workspace
chmod +x startup.sh
ls -la startup.sh
""")
    print("\nAfter running, press Enter...")
    input()
    
    print_step(8, "Start services")
    print("\nPaste in SSH session:")
    print("""
cd /workspace
source venv/bin/activate
./startup.sh
""")
    print("\nWait for services to start (about 10 seconds), then press Enter...")
    input()
    
    print_step(9, "Verify services are running")
    print("\nPaste in SSH session:")
    print("""
# Check process status
ps aux | grep uvicorn
ps aux | grep python.*server.py

# Check logs
tail -20 logs/backend.log
tail -20 logs/gpu_server.log

# Test health endpoints
curl http://localhost:8000/health
curl http://localhost:8001/health
""")
    print("\nAfter verification, press Enter...")
    input()
    
    print_step(10, "View directory structure")
    print("\nPaste in SSH session:")
    print("""
cd /workspace
echo "=== Backend Structure ==="
ls -R backend

echo ""
echo "=== GPU Server Structure ==="
ls -R gpu_server

echo ""
echo "=== Key Files ==="
cat backend/main.py | head -20
cat backend/config.py | head -20
cat backend/routers/health.py | head -20
cat gpu_server/server.py | head -20
cat startup.sh | head -30
""")
    
    print_header("Deployment Complete!")
    print("""
If all steps completed successfully, you now have:

✓ Backend API running on port 8000
✓ GPU Service running on port 8001  
✓ Health endpoints responding
✓ All files in /workspace
✓ Services managed by startup.sh

Next steps:
1. Test generation endpoint: curl -X POST http://localhost:8000/generate \\
     -H "Content-Type: application/json" \\
     -d '{"mode":"free","prompt":"test"}'

2. View service status anytime: python infra/ssh_manager.py status
   (after fixing SSH issues)

3. View logs: tail -f /workspace/logs/backend.log

4. Restart services: /workspace/startup.sh
""")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDeployment assistant interrupted. Resume anytime by running again.")
        sys.exit(0)
