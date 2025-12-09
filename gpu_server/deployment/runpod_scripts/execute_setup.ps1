# RunPod ComfyUI Complete Setup Execution Script
# This script uploads and executes the setup script on RunPod

$SSH_KEY = "~/.ssh/id_ed25519"
$SSH_USER = "p8q2agahufxw4a-64410d8e@ssh.runpod.io"
$SCRIPT_PATH = "$PSScriptRoot\setup_comfyui.sh"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "RunPod ComfyUI Complete Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Function to execute SSH command
function Invoke-RunPodSSH {
    param(
        [string]$Command
    )
    
    $result = ssh -i $SSH_KEY -T $SSH_USER $Command 2>&1
    return $result | Where-Object { $_ -notmatch 'PTY' }
}

# Step 1: Upload setup script
Write-Host "[1/3] Uploading setup script to RunPod..." -ForegroundColor Yellow
$scriptContent = Get-Content $SCRIPT_PATH -Raw
$scriptContent | ssh -i $SSH_KEY -T $SSH_USER "cat > /workspace/.runpod/setup_comfyui.sh" 2>&1 | Out-Null

# Set permissions
ssh -i $SSH_KEY -T $SSH_USER "chmod +x /workspace/.runpod/setup_comfyui.sh" 2>&1 | Out-Null
Write-Host "✓ Script uploaded" -ForegroundColor Green

# Step 2: Execute setup script
Write-Host ""
Write-Host "[2/3] Executing setup on RunPod (this may take 5-10 minutes)..." -ForegroundColor Yellow
Write-Host "Please wait..." -ForegroundColor Gray
Write-Host ""

# Execute and save output
$output = Invoke-RunPodSSH "bash /workspace/.runpod/setup_comfyui.sh"

# Save output to file
$outputFile = "$PSScriptRoot\setup_execution_log.txt"
$output | Out-File -FilePath $outputFile -Encoding UTF8

Write-Host "✓ Setup execution completed" -ForegroundColor Green
Write-Host "Output saved to: $outputFile" -ForegroundColor Gray

# Step 3: Retrieve final report
Write-Host ""
Write-Host "[3/3] Retrieving setup report..." -ForegroundColor Yellow

$report = Invoke-RunPodSSH "cat /workspace/.runpod/logs/setup_report.log"
$reportFile = "$PSScriptRoot\setup_report.txt"
$report | Out-File -FilePath $reportFile -Encoding UTF8

Write-Host "✓ Report retrieved" -ForegroundColor Green
Write-Host "Report saved to: $reportFile" -ForegroundColor Gray

# Display summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Setup Process Completed!" -ForegroundColor Green  
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor White
Write-Host "1. Review the setup report: $reportFile" -ForegroundColor Gray
Write-Host "2. Check ComfyUI status:" -ForegroundColor Gray
Write-Host "   ssh -i $SSH_KEY -T $SSH_USER 'ps aux | grep main.py'" -ForegroundColor DarkGray
Write-Host "3. View logs:" -ForegroundColor Gray
Write-Host "   ssh -i $SSH_KEY -T $SSH_USER 'tail -n 50 /workspace/.runpod/logs/comfyui.log'" -ForegroundColor DarkGray
Write-Host ""

# Show last few lines of output
Write-Host "Last lines of setup output:" -ForegroundColor White
Write-Host "----------------------------" -ForegroundColor Gray
$output | Select-Object -Last 20 | ForEach-Object { Write-Host $_ -ForegroundColor DarkGray }
