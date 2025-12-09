#!/usr/bin/env python3
"""
Complete deployment to RunPod with workflow testing
"""
import subprocess
import time

SSH_USER = "p8q2agahufxw4a-64410d8e"
SSH_HOST = "ssh.runpod.io"
SSH_KEY = r"C:\Users\KIT\.ssh\id_ed25519"

def ssh_cmd(cmd, description=""):
    """Execute SSH command and show result"""
    if description:
        print(f"\n{description}")
    full_cmd = ["ssh", "-T", f"{SSH_USER}@{SSH_HOST}", "-i", SSH_KEY, cmd]
    result = subprocess.run(full_cmd, capture_output=True, text=True, timeout=120)
    
    # Filter out PTY errors
    out = result.stdout
    err = result.stderr
    if err and "PTY" not in err:
        print(f"STDERR: {err}")
    if out:
        print(out)
    return out, result.returncode

print("="*70)
print("RUNPOD FULL DEPLOYMENT & TEST")
print("="*70)

# 1. Upload files
print("\n[STEP 1] Uploading prompt_enhancer...")
with open(r"c:\projekt\generator\utils\prompt_enhancer.py", encoding="utf-8") as f:
    code = f.read()

# Create directory and upload
ssh_cmd("mkdir -p /workspace/ai-generator/utils", "[1.1] Creating utils directory")
# Upload in parts to avoid command length issues
ssh_cmd(f"echo '{code[:5000]}' > /workspace/ai-generator/utils/prompt_enhancer.py", "[1.2] Uploading part 1")
if len(code) > 5000:
    ssh_cmd(f"echo '{code[5000:]}' >> /workspace/ai-generator/utils/prompt_enhancer.py", "[1.3] Uploading part 2")

# 2. Test enhancer
ssh_cmd("""
cd /workspace/ai-generator
python3 -c "from utils.prompt_enhancer import build_full_prompt; print('Enhancer works!')"
""", "[STEP 2] Testing prompt enhancer")

# 3. Upload updated handler
print("\n[STEP 3] Uploading updated free.py handler...")
with open(r"c:\projekt\generator\telegram_bot\handlers\free.py", encoding="utf-8") as f:
    handler_code = f.read()

ssh_cmd("mkdir -p /workspace/ai-generator/telegram_bot/handlers")
# Split large file
part_size = 3000
for i in range(0, len(handler_code), part_size):
    part = handler_code[i:i+part_size]
    op = ">" if i == 0 else ">>"
    ssh_cmd(f"cat {op} /workspace/ai-generator/telegram_bot/handlers/free.py << 'EOFHANDLER'\n{part}\nEOFHANDLER")

# 4. Check services
ssh_cmd("ps aux | grep -E '(uvicorn|telegram|ComfyUI)' | grep -v grep", "[STEP 4] Checking running services")

# 5. Start services if needed
print("\n[STEP 5] Starting services...")
ssh_cmd("""
source /workspace/ComfyUI/venv/bin/activate || true
cd /workspace/ComfyUI
pgrep -f "main.py.*8188" || (nohup python main.py --listen 0.0.0.0 --port 8188 > /workspace/logs/comfyui.log 2>&1 &)
sleep 3
cd /workspace/ai-generator
pgrep -f "uvicorn.*3000" || (nohup python -m uvicorn gpu_server.server.main:app --host 0.0.0.0 --port 3000 > /workspace/logs/fastapi.log 2>&1 &)
sleep 3
echo "Services started"
ps aux | grep -E '(uvicorn|ComfyUI)' | grep -v grep
""", "Starting ComfyUI and FastAPI")

# 6. Start bot
ssh_cmd("""
source /workspace/ComfyUI/venv/bin/activate
cd /workspace/ai-generator
pkill -f run_telegram_bot || true
sleep 2
nohup python run_telegram_bot.py > /workspace/logs/bot.log 2>&1 &
sleep 3
echo "Bot started"
ps aux | grep telegram | grep -v grep
""", "[STEP 6] Starting Telegram bot")

print("\n" + "="*70)
print("✅ DEPLOYMENT COMPLETE!")
print("="*70)
print("\nEndpoints:")
print("- API: https://p8q2agahufxw4a-3000.proxy.runpod.net/api/health")
print("- ComfyUI: https://p8q2agahufxw4a-8188.proxy.runpod.net")
print("\nCheck logs:")
print("- FastAPI: ssh ... 'tail -50 /workspace/logs/fastapi.log'")
print("- Bot: ssh ... 'tail -50 /workspace/logs/bot.log'")
print("- ComfyUI: ssh ... 'tail -50 /workspace/logs/comfyui.log'")
