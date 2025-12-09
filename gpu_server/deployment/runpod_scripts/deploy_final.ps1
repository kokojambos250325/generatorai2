# RunPod Deployment Script - Using Existing SSH Key
# Key location: C:\Windows\System32\coder_key

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "RunPod Infrastructure Deployment" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# SSH connection details
$SSH_HOST = "ssh.runpod.io"
$SSH_USER = "p8q2agahufxw4a-64410d8e"
$SSH_TARGET = "${SSH_USER}@${SSH_HOST}"
$SSH_KEY = Join-Path $PSScriptRoot "coder_key"

# Verify key file exists
if (-not (Test-Path $SSH_KEY)) {
    Write-Host "✗ SSH key file not found: $SSH_KEY" -ForegroundColor Red
    exit 1
}

Write-Host "Using SSH key: $SSH_KEY" -ForegroundColor Gray
Write-Host ""

# Test SSH connection
Write-Host "[1/5] Testing SSH connection..." -ForegroundColor Yellow
$testResult = ssh -i $SSH_KEY -o StrictHostKeyChecking=no -o UserKnownHostsFile=NUL -o ConnectTimeout=15 -t $SSH_TARGET "echo 'Connected successfully'" 2>&1

if ($testResult -match "Connected successfully") {
    Write-Host "  ✓ SSH connection successful" -ForegroundColor Green
} else {
    Write-Host "  ✗ SSH connection failed" -ForegroundColor Red
    Write-Host "  Output: $testResult" -ForegroundColor Gray
    exit 1
}

# Create remote directories
Write-Host ""
Write-Host "[2/5] Preparing remote directories..." -ForegroundColor Yellow
ssh -i $SSH_KEY -o StrictHostKeyChecking=no -o UserKnownHostsFile=NUL -t $SSH_TARGET "mkdir -p /workspace/.runpod/logs /workspace/.runpod/scripts" 2>&1 | Out-Null

if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ Directories created" -ForegroundColor Green
} else {
    Write-Host "  ✗ Failed to create directories" -ForegroundColor Red
    exit 1
}

# Upload setup script
Write-Host ""
Write-Host "[3/5] Uploading setup script..." -ForegroundColor Yellow
$SetupScript = Join-Path $PSScriptRoot "setup_heavy_ai_pipelines.sh"

if (-not (Test-Path $SetupScript)) {
    Write-Host "  ✗ Setup script not found: $SetupScript" -ForegroundColor Red
    exit 1
}

scp -i $SSH_KEY -o StrictHostKeyChecking=no -o UserKnownHostsFile=NUL $SetupScript "${SSH_TARGET}:/workspace/.runpod/setup_heavy_ai_pipelines.sh" 2>&1 | Out-Null

if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ Script uploaded successfully" -ForegroundColor Green
} else {
    Write-Host "  ✗ Upload failed" -ForegroundColor Red
    exit 1
}

# Set executable permissions
Write-Host ""
Write-Host "[4/5] Setting script permissions..." -ForegroundColor Yellow
ssh -i $SSH_KEY -o StrictHostKeyChecking=no -o UserKnownHostsFile=NUL -t $SSH_TARGET "chmod +x /workspace/.runpod/setup_heavy_ai_pipelines.sh" 2>&1 | Out-Null

if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ Permissions set" -ForegroundColor Green
} else {
    Write-Host "  ✗ Failed to set permissions" -ForegroundColor Red
    exit 1
}

# Execute setup
Write-Host ""
Write-Host "[5/5] Executing remote setup..." -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Remote Setup Starting (10-15 minutes)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

ssh -i $SSH_KEY -o StrictHostKeyChecking=no -o UserKnownHostsFile=NUL -t $SSH_TARGET "bash /workspace/.runpod/setup_heavy_ai_pipelines.sh"

$exitCode = $LASTEXITCODE

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan

if ($exitCode -eq 0) {
    Write-Host "✓ Deployment Completed Successfully!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next Steps:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "1. View full setup report:" -ForegroundColor White
    Write-Host "   ssh -i $SSH_KEY $SSH_TARGET" -ForegroundColor Gray
    Write-Host "   cat /workspace/.runpod/logs/heavy_ai_setup_report.log" -ForegroundColor Gray
    Write-Host ""
    Write-Host "2. Access ComfyUI web interface:" -ForegroundColor White
    Write-Host "   https://p8q2agahufxw4a-8188.proxy.runpod.net" -ForegroundColor Gray
    Write-Host ""
    Write-Host "3. Download model weights (see documentation):" -ForegroundColor White
    Write-Host "   F:\generator\gpu_server\MODEL_INSTALLATION.md" -ForegroundColor Gray
    Write-Host ""
    Write-Host "4. Configure FastAPI server (next task)" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host "✗ Deployment Encountered Issues" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Exit Code: $exitCode" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Troubleshooting:" -ForegroundColor Yellow
    Write-Host "1. SSH to server:" -ForegroundColor White
    Write-Host "   ssh -i $SSH_KEY $SSH_TARGET" -ForegroundColor Gray
    Write-Host ""
    Write-Host "2. Check setup logs:" -ForegroundColor White
    Write-Host "   cat /tmp/heavy_ai_setup_actions.log" -ForegroundColor Gray
    Write-Host "   cat /workspace/.runpod/logs/comfyui.log" -ForegroundColor Gray
    Write-Host ""
}

exit $exitCode
