import subprocess
import sys

def run_cmd(cmd):
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    return result.returncode

# Remove files from git cache
run_cmd("git rm --cached temp_key.txt .env.local")

# Add safe files
run_cmd("git add .gitignore runpod_exec.py test_api_curl.ps1 test_comfyui_worker.py test_serverless_api.py connect_runpod_ssh.ps1 runpod_ssh_connect.py QUICK_API_REFERENCE.md")

# Reset last commit
run_cmd("git reset --soft HEAD~1")

# Create new commit without secrets
run_cmd('git commit -m "Remove secrets and use environment variables for API keys"')

# Push to remote
code = run_cmd("git push")

if code == 0:
    print("\n✅ SUCCESS! Secrets removed from repository.")
else:
    print(f"\n❌ Push failed with code {code}")
    sys.exit(1)
