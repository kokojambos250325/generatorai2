import subprocess
import os

os.environ['GIT_SSH_COMMAND'] = 'ssh -o StrictHostKeyChecking=accept-new'

result = subprocess.run(['git', 'push'], capture_output=True, text=True)
print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr)
print("Return code:", result.returncode)
