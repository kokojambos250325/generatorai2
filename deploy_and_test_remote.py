#!/usr/bin/env python3
"""Deploy and test workflow on RunPod via SSH"""
import subprocess
import sys

SSH_USER = "p8q2agahufxw4a-64410d8e"
SSH_HOST = "ssh.runpod.io"
SSH_KEY = r"C:\Users\KIT\.ssh\id_ed25519"

def ssh_exec(cmd):
    """Execute command on RunPod"""
    full_cmd = ["ssh", "-T", f"{SSH_USER}@{SSH_HOST}", "-i", SSH_KEY, cmd]
    result = subprocess.run(full_cmd, capture_output=True, text=True, timeout=60)
    return result.stdout, result.stderr, result.returncode

print("=" * 60)
print("DEPLOYING AND TESTING ON RUNPOD")
print("=" * 60)

# Step 1: Check current directory
print("\n[1/6] Checking workspace...")
out, err, code = ssh_exec("pwd && ls /workspace/ai-generator")
print(out)
if err:
    print(f"Error: {err}")

# Step 2: Upload prompt_enhancer.py
print("\n[2/6] Creating utils/prompt_enhancer.py...")
enhancer_code = open(r"c:\projekt\generator\utils\prompt_enhancer.py", "r", encoding="utf-8").read()
# Escape special chars for bash
enhancer_code_escaped = enhancer_code.replace("'", "'\"'\"'")
cmd = f"cat > /workspace/ai-generator/utils/prompt_enhancer.py << 'EOFPY'\n{enhancer_code}\nEOFPY"
out, err, code = ssh_exec(cmd)
if code == 0:
    print("✓ prompt_enhancer.py uploaded")
else:
    print(f"✗ Upload failed: {err}")

# Step 3: Test prompt enhancer
print("\n[3/6] Testing prompt enhancer...")
test_cmd = """
cd /workspace/ai-generator
source /workspace/ComfyUI/venv/bin/activate
python3 -c "
from utils.prompt_enhancer import build_full_prompt
result = build_full_prompt('девушка на пляже', 'realism')
print('✓ Test passed')
print('Positive:', result['positive_prompt'][:80])
"
"""
out, err, code = ssh_exec(test_cmd)
print(out)
if err and "Error" in err:
    print(f"Error: {err}")

# Step 4: Check if bot is running
print("\n[4/6] Checking bot status...")
out, err, code = ssh_exec("ps aux | grep telegram_bot | grep -v grep")
if out.strip():
    print("✓ Bot is running:")
    print(out)
else:
    print("⚠ Bot is not running")

# Step 5: Check FastAPI status
print("\n[5/6] Checking FastAPI status...")
out, err, code = ssh_exec("ps aux | grep uvicorn | grep -v grep")
if out.strip():
    print("✓ FastAPI is running:")
    print(out)
else:
    print("⚠ FastAPI is not running - starting it...")
    start_cmd = """
    source /workspace/ComfyUI/venv/bin/activate
    cd /workspace/ai-generator
    nohup python -m uvicorn gpu_server.server.main:app --host 0.0.0.0 --port 3000 > /workspace/logs/fastapi.log 2>&1 &
    sleep 3
    echo "Started"
    """
    out, err, code = ssh_exec(start_cmd)
    print(out)

# Step 6: Test API health
print("\n[6/6] Testing API health...")
out, err, code = ssh_exec("curl -s http://127.0.0.1:3000/api/health")
print(out if out else "⚠ No response from API")

print("\n" + "=" * 60)
print("DEPLOYMENT COMPLETE")
print("=" * 60)
print("\nPublic endpoints:")
print("- FastAPI: https://p8q2agahufxw4a-3000.proxy.runpod.net/api/health")
print("- ComfyUI: https://p8q2agahufxw4a-8188.proxy.runpod.net")
