# RunPod Heavy AI Pipeline - Automated Deployment Script
# Uploads and executes comprehensive AI pipeline setup

$SSH_KEY = "~/.ssh/id_ed25519"
$SSH_USER = "p8q2agahufxw4a-64410d8e@ssh.runpod.io"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "RunPod Heavy AI Pipeline Deployment" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Upload setup script
Write-Host "[1/3] Uploading heavy AI pipeline setup script..." -ForegroundColor Yellow
$setupScript = Get-Content "$PSScriptRoot\setup_heavy_ai_pipelines.sh" -Raw
$setupScript | ssh -i $SSH_KEY -T $SSH_USER "cat > /workspace/.runpod/setup_heavy_ai_pipelines.sh" 2>&1 | Out-Null

if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ Setup script uploaded successfully" -ForegroundColor Green
} else {
    Write-Host "  ✗ Failed to upload setup script" -ForegroundColor Red
    exit 1
}

# Step 2: Set executable permissions
Write-Host "[2/3] Setting executable permissions..." -ForegroundColor Yellow
ssh -i $SSH_KEY -T $SSH_USER "chmod +x /workspace/.runpod/setup_heavy_ai_pipelines.sh" 2>&1 | Out-Null

if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ Permissions set" -ForegroundColor Green
} else {
    Write-Host "  ✗ Failed to set permissions" -ForegroundColor Red
    exit 1
}

# Step 3: Execute setup script
Write-Host "[3/3] Executing heavy AI pipeline setup..." -ForegroundColor Yellow
Write-Host ""
Write-Host "This will take 10-15 minutes. Please wait..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Execute the script and capture output
ssh -i $SSH_KEY -T $SSH_USER "bash /workspace/.runpod/setup_heavy_ai_pipelines.sh" 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "✓ Setup completed successfully!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "1. View full report: ssh to pod and run:" -ForegroundColor White
    Write-Host "   cat /workspace/.runpod/logs/heavy_ai_setup_report.log" -ForegroundColor Gray
    Write-Host ""
    Write-Host "2. Access ComfyUI interface:" -ForegroundColor White
    Write-Host "   https://p8q2agahufxw4a-8188.proxy.runpod.net" -ForegroundColor Gray
    Write-Host ""
    Write-Host "3. Download model weights (see HEAVY_AI_SETUP_GUIDE.md)" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "✗ Setup encountered errors" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Troubleshooting:" -ForegroundColor Yellow
    Write-Host "1. Check setup log:" -ForegroundColor White
    Write-Host "   ssh $SSH_USER -i $SSH_KEY" -ForegroundColor Gray
    Write-Host "   cat /tmp/heavy_ai_setup_actions.log" -ForegroundColor Gray
    Write-Host ""
    Write-Host "2. Review ComfyUI logs:" -ForegroundColor White
    Write-Host "   cat /workspace/.runpod/logs/comfyui.log" -ForegroundColor Gray
    Write-Host ""
}
