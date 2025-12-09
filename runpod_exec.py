#!/usr/bin/env python3
"""
Execute commands on RunPod via GraphQL API
More stable than SSH for automation
"""

import requests
import json
import time
import sys

# Get from https://www.runpod.io/console/user/settings
RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY", "")
POD_ID = "e8d54a336b62"  # Your current pod

GRAPHQL_URL = "https://api.runpod.io/graphql"

def execute_command(command: str):
    """Execute command on RunPod pod via API"""
    
    query = """
    mutation ExecuteCommand($input: PodExecuteCommandInput!) {
      podExecuteCommand(input: $input) {
        id
        output
        error
      }
    }
    """
    
    variables = {
        "input": {
            "podId": POD_ID,
            "command": command
        }
    }
    
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
        if "data" in result and result["data"]["podExecuteCommand"]:
            output = result["data"]["podExecuteCommand"]["output"]
            error = result["data"]["podExecuteCommand"]["error"]
            
            if output:
                print(output)
            if error:
                print(f"Error: {error}", file=sys.stderr)
                
            return output, error
        else:
            print(f"API Error: {result}", file=sys.stderr)
    else:
        print(f"HTTP Error: {response.status_code} - {response.text}", file=sys.stderr)
    
    return None, None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python runpod_exec.py 'command to execute'")
        sys.exit(1)
    
    command = " ".join(sys.argv[1:])
    print(f"Executing: {command}")
    print("=" * 50)
    
    execute_command(command)
