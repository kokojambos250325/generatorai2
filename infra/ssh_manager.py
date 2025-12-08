#!/usr/bin/env python3
"""
SSH Manager for RunPod POD Management

Unified module for all SSH operations to RunPod POD.
Supports shell access, command execution, service management, and log viewing.

Usage:
    python ssh_manager.py shell                    # Interactive SSH session
    python ssh_manager.py exec <command>           # Execute single command
    python ssh_manager.py restart <service>        # Restart backend or gpu_server
    python ssh_manager.py logs <service> [lines]   # View service logs
    python ssh_manager.py status                   # Check all services status
"""

import sys
import os
import json
import subprocess
import argparse
from pathlib import Path
from typing import Dict, Optional, List

# Configuration file path
CONFIG_FILE = Path(__file__).parent / "ssh_config.json"


class SSHManager:
    """Manages SSH connections and operations to RunPod POD"""
    
    def __init__(self, config_path: Path = CONFIG_FILE):
        """Initialize SSH Manager with configuration"""
        self.config = self._load_config(config_path)
        self.connection = self.config["connections"][self.config["default_connection"]]
        self.workspace_path = self.config["workspace_path"]
        self.services = self.config["services"]
    
    def _load_config(self, config_path: Path) -> Dict:
        """Load SSH configuration from JSON file"""
        if not config_path.exists():
            raise FileNotFoundError(
                f"Configuration file not found: {config_path}\n"
                f"Create ssh_config.json from template"
            )
        
        with open(config_path, 'r') as f:
            return json.load(f)
    
    def _build_ssh_command(self, command: Optional[str] = None, interactive: bool = False) -> List[str]:
        """Build SSH command with proper parameters"""
        # Expand tilde in key path
        key_path = os.path.expanduser(self.connection["key_path"])
        
        ssh_cmd = [
            "ssh",
            "-i", key_path,
            "-o", "StrictHostKeyChecking=no",
            "-o", "UserKnownHostsFile=/dev/null",
            "-o", "LogLevel=ERROR",  # Suppress warnings
        ]
        
        # Add port if not default
        if self.connection.get("port", 22) != 22:
            ssh_cmd.extend(["-p", str(self.connection["port"])])
        
        # Add interactive flag if needed
        if interactive:
            ssh_cmd.append("-t")
        
        # Build user@host
        user_host = f"{self.connection['user']}@{self.connection['host']}"
        ssh_cmd.append(user_host)
        
        # Add command if provided
        if command:
            ssh_cmd.append(command)
        
        return ssh_cmd
    
    def shell(self) -> int:
        """Open interactive SSH shell"""
        print(f"Opening SSH shell to {self.connection['host']}...")
        print(f"Connection: {self.connection.get('description', 'N/A')}")
        print(f"Workspace: {self.workspace_path}")
        print("-" * 60)
        
        cmd = self._build_ssh_command(interactive=True)
        
        try:
            return subprocess.call(cmd)
        except KeyboardInterrupt:
            print("\nSSH session interrupted")
            return 0
        except Exception as e:
            print(f"Error: {e}")
            return 1
    
    def exec(self, command: str) -> int:
        """Execute single remote command and display output"""
        print(f"Executing: {command}")
        print("-" * 60)
        
        ssh_cmd = self._build_ssh_command(command=command)
        
        try:
            result = subprocess.run(ssh_cmd, capture_output=False, text=True)
            return result.returncode
        except Exception as e:
            print(f"Error executing command: {e}")
            return 1
    
    def restart(self, service: str) -> int:
        """Restart a service (backend or gpu_server)"""
        if service not in self.services:
            print(f"Error: Unknown service '{service}'")
            print(f"Available services: {', '.join(self.services.keys())}")
            return 1
        
        service_config = self.services[service]
        service_path = service_config["path"]
        start_command = service_config["start_command"]
        
        print(f"Restarting service: {service}")
        print("-" * 60)
        
        # Create restart script
        restart_script = f"""
        cd {service_path} && \
        pkill -f "{start_command}" 2>/dev/null; \
        sleep 2; \
        source {self.workspace_path}/venv/bin/activate 2>/dev/null || true; \
        nohup {start_command} > {self.workspace_path}/logs/{service}.log 2>&1 & \
        echo $! > {self.workspace_path}/{service}.pid; \
        echo "Service {service} restarted (PID: $(cat {self.workspace_path}/{service}.pid))"
        """
        
        return self.exec(restart_script)
    
    def logs(self, service: str, lines: int = 50) -> int:
        """View service logs"""
        if service not in self.services:
            print(f"Error: Unknown service '{service}'")
            print(f"Available services: {', '.join(self.services.keys())}")
            return 1
        
        log_path = self.services[service]["log_path"]
        
        print(f"Viewing logs for: {service}")
        print(f"Log file: {log_path}")
        print("-" * 60)
        
        # Tail log file
        log_command = f"tail -n {lines} {log_path} 2>/dev/null || echo 'Log file not found: {log_path}'"
        
        return self.exec(log_command)
    
    def status(self) -> int:
        """Check status of all services"""
        print("Checking service status...")
        print("=" * 60)
        
        # Create status check script
        status_script = f"""
        echo "=== System Info ===" && \
        echo "Hostname: $(hostname)" && \
        echo "Uptime: $(uptime -p 2>/dev/null || uptime)" && \
        echo "" && \
        echo "=== Disk Usage ===" && \
        df -h {self.workspace_path} 2>/dev/null | tail -1 && \
        echo "" && \
        echo "=== GPU Status ===" && \
        nvidia-smi --query-gpu=index,name,utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits 2>/dev/null || echo "nvidia-smi not available" && \
        echo "" && \
        echo "=== Service Status ===" && \
        """
        
        # Add checks for each service
        for service, config in self.services.items():
            pid_file = f"{self.workspace_path}/{service}.pid"
            status_script += f"""
        echo "Service: {service}" && \
        if [ -f {pid_file} ]; then \
            PID=$(cat {pid_file}); \
            if ps -p $PID > /dev/null 2>&1; then \
                echo "  Status: RUNNING (PID: $PID)"; \
            else \
                echo "  Status: STOPPED (stale PID file)"; \
            fi; \
        else \
            echo "  Status: STOPPED (no PID file)"; \
        fi && \
        """
        
        status_script += "echo ''"
        
        return self.exec(status_script)


def main():
    """Main entry point for SSH Manager CLI"""
    parser = argparse.ArgumentParser(
        description="SSH Manager for RunPod POD Management",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python ssh_manager.py shell                      # Interactive SSH
  python ssh_manager.py exec "ls -la /workspace"   # Run command
  python ssh_manager.py restart backend            # Restart backend
  python ssh_manager.py logs gpu_server 100        # View 100 lines of logs
  python ssh_manager.py status                     # Check all services
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Shell command
    subparsers.add_parser('shell', help='Open interactive SSH shell')
    
    # Exec command
    exec_parser = subparsers.add_parser('exec', help='Execute remote command')
    exec_parser.add_argument('remote_command', nargs='+', help='Command to execute')
    
    # Restart command
    restart_parser = subparsers.add_parser('restart', help='Restart service')
    restart_parser.add_argument('service', choices=['backend', 'gpu_server'], help='Service to restart')
    
    # Logs command
    logs_parser = subparsers.add_parser('logs', help='View service logs')
    logs_parser.add_argument('service', choices=['backend', 'gpu_server'], help='Service logs to view')
    logs_parser.add_argument('lines', type=int, nargs='?', default=50, help='Number of lines (default: 50)')
    
    # Status command
    subparsers.add_parser('status', help='Check service status')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    try:
        manager = SSHManager()
        
        if args.command == 'shell':
            return manager.shell()
        
        elif args.command == 'exec':
            command = ' '.join(args.remote_command)
            return manager.exec(command)
        
        elif args.command == 'restart':
            return manager.restart(args.service)
        
        elif args.command == 'logs':
            return manager.logs(args.service, args.lines)
        
        elif args.command == 'status':
            return manager.status()
        
        else:
            parser.print_help()
            return 1
    
    except FileNotFoundError as e:
        print(f"Configuration Error: {e}")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
