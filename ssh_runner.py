import subprocess
import time
import sys

def run_ssh_command(command: str, max_attempts=3, timeout=10):
    """Выполнить команду на RunPod через WSL SSH с несколькими попытками"""
    
    ssh_cmd = [
        "wsl", "-d", "docker-desktop",
        "timeout", str(timeout),
        "ssh",
        "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile=/dev/null",
        "-o", "ConnectTimeout=5",
        "-o", "ServerAliveInterval=2",
        "root@nlrtkvylv1s0cw-22.proxy.runpod.net",
        "-p", "22537",
        "-i", "/root/.ssh/id_ed25519",
        command
    ]
    
    for attempt in range(1, max_attempts + 1):
        print(f"Попытка {attempt}/{max_attempts}...", file=sys.stderr)
        try:
            result = subprocess.run(
                ssh_cmd,
                capture_output=True,
                text=True,
                timeout=timeout + 5
            )
            
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout
            
            if "Connection" in result.stderr and attempt < max_attempts:
                print(f"Таймаут, повтор через 2 сек...", file=sys.stderr)
                time.sleep(2)
                continue
                
            return result.stdout if result.stdout else result.stderr
            
        except subprocess.TimeoutExpired:
            if attempt < max_attempts:
                print(f"Превышено время ожидания, повтор...", file=sys.stderr)
                time.sleep(2)
                continue
            return "ERROR: Timeout"
    
    return "ERROR: Все попытки исчерпаны"

# Предопределённые команды
COMMANDS = {
    "status": "ps aux | grep -E 'telegram_bot|uvicorn|main.py' | grep -v grep",
    "botlog": "tail -50 /tmp/bot.log",
    "gpulog": "tail -50 /tmp/gpu.log",
    "comfylog": "tail -50 /tmp/comfyui.log",
    "restart": "pkill -9 -f telegram_bot; pkill -9 -f uvicorn; pkill -9 -f 'main.py --listen'; sleep 2; cd /workspace/ComfyUI && nohup python main.py --listen > /tmp/comfyui.log 2>&1 & sleep 3; cd /workspace/ai-generator && export PYTHONPATH=/workspace/ai-generator && nohup python -m uvicorn gpu_server.server.main:app --host 0.0.0.0 --port 3000 > /tmp/gpu.log 2>&1 & sleep 3; nohup python -m telegram_bot.bot > /tmp/bot.log 2>&1 & sleep 2; echo 'DONE'"
}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование:")
        print("  python ssh_runner.py status    - проверить процессы")
        print("  python ssh_runner.py botlog    - лог бота")
        print("  python ssh_runner.py gpulog    - лог GPU сервера")
        print("  python ssh_runner.py comfylog  - лог ComfyUI")
        print("  python ssh_runner.py restart   - перезапуск всех сервисов")
        sys.exit(1)
    
    action = sys.argv[1]
    if action in COMMANDS:
        cmd = COMMANDS[action]
    else:
        cmd = " ".join(sys.argv[1:])
    
    output = run_ssh_command(cmd, max_attempts=5, timeout=15)
    print(output)
