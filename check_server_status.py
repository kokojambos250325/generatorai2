#!/usr/bin/env python3
"""
Quick server status check
"""
import subprocess
import sys
from pathlib import Path

# SSH connection details
SSH_KEY = Path.home() / ".ssh" / "id_ed25519"
SERVER = "root@38.147.83.26"
PORT = "35108"

def run_ssh_command(cmd):
    """Execute SSH command"""
    ssh_cmd = [
        "ssh",
        "-i", str(SSH_KEY),
        "-p", PORT,
        "-o", "StrictHostKeyChecking=no",
        "-o", "ConnectTimeout=10",
        SERVER,
        cmd
    ]
    
    try:
        result = subprocess.run(
            ssh_cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        return "", "Timeout", 1
    except Exception as e:
        return "", str(e), 1

if __name__ == "__main__":
    print("Checking server status...")
    print(f"SSH Key: {SSH_KEY} (exists: {SSH_KEY.exists()})")
    print(f"Server: {SERVER}:{PORT}")
    print("-" * 60)
    
    # Check workspace
    stdout, stderr, code = run_ssh_command("cd /workspace && pwd && ls -la | head -20")
    if code == 0:
        print("Workspace check:")
        print(stdout)
    else:
        print(f"Error: {stderr}")
        sys.exit(1)
    
    # Check git repo
    print("\n" + "-" * 60)
    stdout, stderr, code = run_ssh_command("cd /workspace && find . -maxdepth 2 -name '.git' -type d 2>/dev/null | head -5")
    if code == 0 and stdout.strip():
        print("Git repositories found:")
        print(stdout)
    else:
        print("No git repositories found in /workspace")
    
    # Check services
    print("\n" + "-" * 60)
    stdout, stderr, code = run_ssh_command("ps aux | grep -E 'python|uvicorn|bot.py' | grep -v grep | head -10")
    if code == 0:
        print("Running services:")
        print(stdout if stdout.strip() else "No services running")

