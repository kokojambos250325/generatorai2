import subprocess

def run(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    return result.returncode

run("git checkout main")
run("git add QUICK_API_REFERENCE.md")
run('git commit -m "Remove API keys from documentation"')
code = run("git push")

print("\n✅ Done!" if code == 0 else f"\n❌ Failed with code {code}")
