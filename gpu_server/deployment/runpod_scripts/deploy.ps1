# RunPod ComfyUI Auto-Start Deployment Script
# This script uploads the necessary files to RunPod

$SSH_KEY = "~/.ssh/id_ed25519"
$SSH_USER = "p8q2agahufxw4a-64410d8e@ssh.runpod.io"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "RunPod ComfyUI Auto-Start Deployment" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Create directories
Write-Host "[1/4] Creating directories on RunPod..." -ForegroundColor Yellow
ssh -i $SSH_KEY -T $SSH_USER "mkdir -p /workspace/.runpod/scripts /workspace/.runpod/logs" 2>&1 | Out-Null

# Step 2: Upload start.sh
Write-Host "[2/4] Uploading start.sh..." -ForegroundColor Yellow
$startShContent = Get-Content "$PSScriptRoot\start.sh" -Raw
$startShContent | ssh -i $SSH_KEY -T $SSH_USER "cat > /workspace/.runpod/scripts/start.sh" 2>&1 | Out-Null

# Step 3: Upload runpod-entrypoint.sh
Write-Host "[3/4] Uploading runpod-entrypoint.sh..." -ForegroundColor Yellow
$entrypointContent = Get-Content "$PSScriptRoot\runpod-entrypoint.sh" -Raw
$entrypointContent | ssh -i $SSH_KEY -T $SSH_USER "cat > /workspace/.runpod/runpod-entrypoint.sh" 2>&1 | Out-Null

# Step 4: Set permissions
Write-Host "[4/4] Setting executable permissions..." -ForegroundColor Yellow
ssh -i $SSH_KEY -T $SSH_USER "chmod +x /workspace/.runpod/scripts/start.sh /workspace/.runpod/runpod-entrypoint.sh" 2>&1 | Out-Null

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "✓ Deployment Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Файлы развёрнуты на RunPod:" -ForegroundColor White
Write-Host "  • /workspace/.runpod/scripts/start.sh" -ForegroundColor Gray
Write-Host "  • /workspace/.runpod/runpod-entrypoint.sh" -ForegroundColor Gray
Write-Host ""
Write-Host "Следующие шаги:" -ForegroundColor White
Write-Host "  1. Откройте RunPod Web Terminal" -ForegroundColor Gray
Write-Host "  2. Проверьте установку ComfyUI:" -ForegroundColor Gray
Write-Host "     ls -la /workspace/ComfyUI" -ForegroundColor DarkGray
Write-Host "  3. Если нет venv, создайте:" -ForegroundColor Gray
Write-Host "     cd /workspace/ComfyUI && python -m venv venv" -ForegroundColor DarkGray
Write-Host "  4. Протестируйте запуск:" -ForegroundColor Gray
Write-Host "     bash /workspace/.runpod/scripts/start.sh" -ForegroundColor DarkGray
Write-Host "  5. Проверьте процесс:" -ForegroundColor Gray
Write-Host "     ps aux | grep main.py" -ForegroundColor DarkGray
Write-Host "  6. Проверьте логи:" -ForegroundColor Gray
Write-Host "     cat /workspace/.runpod/logs/comfyui.log" -ForegroundColor DarkGray
Write-Host "  7. Перезапустите pod для проверки автостарта" -ForegroundColor Gray
Write-Host ""
