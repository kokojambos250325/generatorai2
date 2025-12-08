#!/usr/bin/env python3
"""
File deployment script for RunPod POD
Uses SCP to transfer files since SSH command execution has PTY limitations
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def load_config():
    """Load SSH configuration"""
    config_path = Path(__file__).parent / "ssh_config.json"
    with open(config_path, 'r') as f:
        config = json.load(f)
    return config

def scp_file(local_path, remote_path, config):
    """Copy file to POD using SCP"""
    connection = config["connections"][config["default_connection"]]
    key_path = os.path.expanduser(connection["key_path"])
    user_host = f"{connection['user']}@{connection['host']}"
    
    scp_cmd = [
        "scp",
        "-i", key_path,
        "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile=/dev/null",
        "-o", "LogLevel=ERROR",
        local_path,
        f"{user_host}:{remote_path}"
    ]
    
    print(f"Uploading {local_path} -> {remote_path}")
    result = subprocess.run(scp_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return False
    return True

def main():
    if len(sys.argv) < 3:
        print("Usage: python deploy_file.py <local_file> <remote_path>")
        return 1
    
    local_file = sys.argv[1]
    remote_path = sys.argv[2]
    
    if not os.path.exists(local_file):
        print(f"Error: Local file not found: {local_file}")
        return 1
    
    config = load_config()
    
    if scp_file(local_file, remote_path, config):
        print("Upload successful")
        return 0
    else:
        print("Upload failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
