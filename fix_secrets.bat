@echo off
git rm --cached temp_key.txt .env.local 2>nul
git add .gitignore runpod_exec.py test_api_curl.ps1 test_comfyui_worker.py test_serverless_api.py .github/workflows/deploy.yml push_changes.ps1
git reset --soft HEAD^
git commit -m "auto: Remove secrets and fix API key references"
git push
echo Done!
pause
