#!/usr/bin/env python3
"""Upload startup script to RunPod via SSH"""
import subprocess
import sys

SCRIPT_CONTENT = '''#!/bin/bash
set -e
echo "🚀 AI Generator - RunPod Startup"
sleep 5
source /workspace/ComfyUI/venv/bin/activate
echo "[1/2] Starting ComfyUI..."
cd /workspace/ComfyUI
nohup python main.py --listen 0.0.0.0 --port 8188 > /workspace/logs/comfyui.log 2>&1 &
sleep 5
echo "[2/2] Starting FastAPI..."
cd /workspace/ai-generator
export PYTHONPATH=/workspace/ai-generator
nohup python -m uvicorn gpu_server.server.main:app --host 0.0.0.0 --port 3000 > /workspace/logs/fastapi.log 2>&1 &
sleep 3
echo "✅ Services started"
ps aux | grep -E "(ComfyUI|uvicorn)" | grep -v grep || true
'''

SSH_USER = "p8q2agahufxw4a-64410d8e"
SSH_HOST = "ssh.runpod.io"
SSH_KEY = r"C:\Users\KIT\.ssh\id_ed25519"

def upload_script():
    # Create script on remote
    cmd = [
        "ssh", "-T",
        f"{SSH_USER}@{SSH_HOST}",
        "-i", SSH_KEY,
        f"cat > /workspace/startup.sh << 'EOFSCRIPT'\n{SCRIPT_CONTENT}\nEOFSCRIPT\nchmod +x /workspace/startup.sh"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print("✓ Startup script uploaded to /workspace/startup.sh")
        return True
    else:
        print(f"✗ Upload failed: {result.stderr}")
        return False

def test_script():
    cmd = [
        "ssh", "-T",
        f"{SSH_USER}@{SSH_HOST}",
        "-i", SSH_KEY,
        "bash /workspace/startup.sh"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    return result.returncode == 0

if __name__ == "__main__":
    print("Uploading startup script to RunPod...")
    if upload_script():
        print("\nTesting startup script...")
        test_script()
