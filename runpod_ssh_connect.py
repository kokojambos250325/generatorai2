"""
SSH connection to RunPod Serverless Workers
Uses RunPod API to get SSH credentials and connect
"""
import requests
import subprocess
import json
import sys
import os

# RunPod API credentials
RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY", "")
GRAPHQL_URL = "https://api.runpod.io/graphql"

def get_active_workers(endpoint_id=None):
    """Get list of active serverless workers"""
    
    query = """
    query GetWorkers($input: EndpointWorkersInput) {
      myself {
        endpoints {
          id
          name
          workers(input: $input) {
            id
            status
            sshConnectionString
          }
        }
      }
    }
    """
    
    variables = {}
    if endpoint_id:
        variables = {"input": {"endpointId": endpoint_id}}
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {RUNPOD_API_KEY}"
    }
    
    response = requests.post(
        GRAPHQL_URL,
        json={"query": query, "variables": variables},
        headers=headers
    )
    
    if response.status_code == 200:
        result = response.json()
        if "data" in result and result["data"]["myself"]:
            return result["data"]["myself"]["endpoints"]
    
    return None


def list_endpoints():
    """List all available endpoints and their workers"""
    print("Fetching RunPod endpoints...")
    print("=" * 60)
    
    endpoints = get_active_workers()
    
    if not endpoints:
        print("No endpoints found or API error")
        return
    
    for endpoint in endpoints:
        print(f"\nEndpoint: {endpoint['name']} ({endpoint['id']})")
        workers = endpoint.get('workers', [])
        
        if not workers:
            print("  No active workers")
            continue
        
        for i, worker in enumerate(workers):
            status = worker.get('status', 'unknown')
            ssh_conn = worker.get('sshConnectionString', 'N/A')
            worker_id = worker.get('id', 'unknown')
            
            print(f"  [{i+1}] Worker ID: {worker_id}")
            print(f"      Status: {status}")
            print(f"      SSH: {ssh_conn}")


def connect_to_worker(endpoint_id=None, worker_index=0):
    """Connect to a specific worker via SSH"""
    
    endpoints = get_active_workers(endpoint_id)
    
    if not endpoints:
        print("No endpoints found")
        return False
    
    # Find endpoint with active workers
    target_endpoint = None
    for endpoint in endpoints:
        workers = endpoint.get('workers', [])
        if workers and len(workers) > worker_index:
            target_endpoint = endpoint
            break
    
    if not target_endpoint:
        print("No active workers found")
        return False
    
    worker = target_endpoint['workers'][worker_index]
    ssh_conn = worker.get('sshConnectionString')
    
    if not ssh_conn:
        print(f"No SSH connection string for worker {worker.get('id')}")
        return False
    
    print(f"Connecting to worker: {worker.get('id')}")
    print(f"SSH: {ssh_conn}")
    print("=" * 60)
    
    # Parse SSH connection string (format: ssh root@<host> -p <port> -i ~/.ssh/id_ed25519)
    # Extract host and port
    parts = ssh_conn.split()
    
    # Build SSH command
    ssh_cmd = [
        "ssh",
        "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile=NUL",  # Windows compatible
        "-i", "C:/Users/KIT/.ssh/id_ed25519",
    ]
    
    # Parse connection string to extract host, port
    for i, part in enumerate(parts):
        if part.startswith("root@"):
            ssh_cmd.append(part)
        elif part == "-p" and i + 1 < len(parts):
            ssh_cmd.extend(["-p", parts[i + 1]])
    
    print(f"Executing: {' '.join(ssh_cmd)}")
    print("\nPress Ctrl+C to disconnect\n")
    
    # Execute SSH connection
    try:
        subprocess.run(ssh_cmd)
        return True
    except KeyboardInterrupt:
        print("\nDisconnected")
        return True
    except Exception as e:
        print(f"SSH connection failed: {e}")
        return False


def main():
    if len(sys.argv) < 2:
        print("RunPod Serverless SSH Tool")
        print("=" * 60)
        print("\nUsage:")
        print("  python runpod_ssh_connect.py list              - List all endpoints and workers")
        print("  python runpod_ssh_connect.py connect           - Connect to first available worker")
        print("  python runpod_ssh_connect.py connect <index>   - Connect to specific worker by index")
        print("\nEnvironment:")
        print("  RUNPOD_API_KEY - Your RunPod API key (required)")
        print("\nExample:")
        print("  python runpod_ssh_connect.py list")
        print("  python runpod_ssh_connect.py connect 0")
        sys.exit(0)
    
    command = sys.argv[1]
    
    if command == "list":
        list_endpoints()
    
    elif command == "connect":
        worker_index = 0
        if len(sys.argv) > 2:
            worker_index = int(sys.argv[2])
        
        connect_to_worker(worker_index=worker_index)
    
    else:
        print(f"Unknown command: {command}")
        print("Available commands: list, connect")
        sys.exit(1)


if __name__ == "__main__":
    main()
