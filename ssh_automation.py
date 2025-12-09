#!/usr/bin/env python3
"""
Stable SSH automation for RunPod using paramiko
More reliable than docker exec ssh
"""

import paramiko
import time
import sys

SSH_HOST = "ssh.runpod.io"
SSH_PORT = 22063
SSH_USER = "root"
SSH_KEY_PATH = "C:/Users/KIT/.ssh/id_ed25519"  # Your SSH key

def execute_command(command, timeout=300):
    """Execute command on RunPod via SSH with retry"""
    
    max_retries = 3
    retry_delay = 5
    
    for attempt in range(max_retries):
        try:
            print(f"[Attempt {attempt + 1}/{max_retries}] Connecting to {SSH_HOST}:{SSH_PORT}...")
            
            # Create SSH client
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Load SSH key
            key = paramiko.Ed25519Key.from_private_key_file(SSH_KEY_PATH)
            
            # Connect with keepalive
            client.connect(
                hostname=SSH_HOST,
                port=SSH_PORT,
                username=SSH_USER,
                pkey=key,
                timeout=30,
                banner_timeout=30,
                auth_timeout=30
            )
            
            # Enable keepalive
            transport = client.get_transport()
            transport.set_keepalive(30)
            
            print(f"✅ Connected! Executing: {command}")
            print("=" * 60)
            
            # Execute command
            stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
            
            # Stream output in real-time
            while True:
                line = stdout.readline()
                if not line:
                    break
                print(line, end='')
            
            # Check for errors
            exit_status = stdout.channel.recv_exit_status()
            
            if exit_status == 0:
                print("=" * 60)
                print("✅ Command completed successfully!")
                client.close()
                return True
            else:
                stderr_output = stderr.read().decode()
                print(f"❌ Command failed with exit code {exit_status}")
                print(f"Error: {stderr_output}")
                client.close()
                return False
                
        except paramiko.SSHException as e:
            print(f"❌ SSH error: {e}")
            if attempt < max_retries - 1:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            if attempt < max_retries - 1:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
    
    print(f"❌ Failed after {max_retries} attempts")
    return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ssh_automation.py 'command to execute'")
        print("\nExample:")
        print("  python ssh_automation.py 'cd /workspace/ai-generator && git pull && bash fix_all.sh'")
        sys.exit(1)
    
    command = " ".join(sys.argv[1:])
    success = execute_command(command)
    sys.exit(0 if success else 1)
