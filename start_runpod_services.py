#!/usr/bin/env python3
"""Start services on RunPod via SSH"""
import subprocess
import time

SSH_USER = "p8q2agahufxw4a-64410d8e"
SSH_HOST = "ssh.runpod.io"
SSH_KEY = r"C:\Users\KIT\.ssh\id_ed25519"

def ssh_exec(command):
    """Execute command via SSH"""
    cmd = ["ssh", "-T", f"{SSH_USER}@{SSH_HOST}", "-i", SSH_KEY, command]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    return result.stdout, result.stderr, result.returncode

def start_services():
    print("🚀 Starting services on RunPod...\n")
    
    # Start ComfyUI
    print("[1/2] Starting ComfyUI on port 8188...")
    cmd = """
    source /workspace/ComfyUI/venv/bin/activate
    cd /workspace/ComfyUI
    nohup python main.py --listen 0.0.0.0 --port 8188 > /workspace/logs/comfyui.log 2>&1 &
    echo "ComfyUI PID: $!"
    """
    out, err, code = ssh_exec(cmd)
    if out:
        print(f"  {out.strip()}")
    if err and "Error" not in err:
        print(f"  {err.strip()}")
    
    time.sleep(3)
    
    # Start FastAPI
    print("\n[2/2] Starting FastAPI on port 3000...")
    cmd = """
    source /workspace/ComfyUI/venv/bin/activate
    cd /workspace/ai-generator
    export PYTHONPATH=/workspace/ai-generator
    nohup python -m uvicorn gpu_server.server.main:app --host 0.0.0.0 --port 3000 > /workspace/logs/fastapi.log 2>&1 &
    echo "FastAPI PID: $!"
    """
    out, err, code = ssh_exec(cmd)
    if out:
        print(f"  {out.strip()}")
    if err and "Error" not in err:
        print(f"  {err.strip()}")
    
    time.sleep(3)
    
    # Check status
    print("\n✅ Checking services...")
    cmd = "ps aux | grep -E '(ComfyUI|uvicorn)' | grep -v grep"
    out, err, code = ssh_exec(cmd)
    if out:
        print(out)
    else:
        print("  ⚠️  No services found running")
    
    print("\n📊 Endpoints:")
    print("  - ComfyUI:  https://p8q2agahufxw4a-8188.proxy.runpod.net")
    print("  - FastAPI:  https://p8q2agahufxw4a-3000.proxy.runpod.net/api/health")

if __name__ == "__main__":
    try:
        start_services()
    except Exception as e:
        print(f"\n❌ Error: {e}")
