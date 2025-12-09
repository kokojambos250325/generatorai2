# RunPod Complete Deployment Script with User-Provided SSH Key
# This script creates temporary SSH key, deploys the infrastructure, and cleans up

param(
    [Parameter(Mandatory=$false)]
    [string]$KeyContent = ""
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "RunPod Complete Infrastructure Deployment" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# SSH connection details
$SSH_HOST = "ssh.runpod.io"
$SSH_USER = "p8q2agahufxw4a-64410d8e"
$SSH_TARGET = "${SSH_USER}@${SSH_HOST}"

# Define the SSH private key content (provided by user)
$SSH_KEY_CONTENT = @"
-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAMwAAAAtzc2gtZW
QyNTUxOQAAACCyQjEaXBtjG2vqmEarNcF+52KGAqFN8A6/Cs4sy94TDgAAAJhAiGFuQIhh
bgAAAAtzc2gtZWQyNTUxOQAAACCyQjEaXBtjG2vqmEarNcF+52KGAqFN8A6/Cs4sy94TDg
AAAEBXeIABCYH+qoK5csZ2Wc30iLllV16/Emlp+z1moTyBxbJCMRpcG2Mba+qYRqs1wX7n
YoYCoU3wDr8KzizL3hMOAAAAEtC8QERFU0tUT1AtODBRMjNKTQECAw==
-----END OPENSSH PRIVATE KEY-----
"@

# Step 1: Create temporary key file
Write-Host "[Step 1/7] Creating temporary SSH key file..." -ForegroundColor Yellow

$TempKeyPath = Join-Path $env:TEMP "runpod_deploy_key_$(Get-Date -Format 'yyyyMMdd_HHmmss')"

try {
    # Write key content ensuring proper formatting for OpenSSH
    # Use .NET to write with explicit Unix line endings
    [System.IO.File]::WriteAllText($TempKeyPath, $SSH_KEY_CONTENT.Replace("`r`n", "`n"), [System.Text.Encoding]::ASCII)
    
    # Set restrictive permissions (Windows ACL)
    $acl = Get-Acl $TempKeyPath
    $acl.SetAccessRuleProtection($true, $false)
    $accessRule = New-Object System.Security.AccessControl.FileSystemAccessRule(
        $env:USERNAME,
        "Read",
        "Allow"
    )
    $acl.AddAccessRule($accessRule)
    Set-Acl -Path $TempKeyPath -AclObject $acl
    
    Write-Host "  ✓ Temporary key created at: $TempKeyPath" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Failed to create key file: $_" -ForegroundColor Red
    exit 1
}

# Step 2: Test SSH connection
Write-Host ""
Write-Host "[Step 2/7] Testing SSH connection..." -ForegroundColor Yellow

try {
    # Fix key file permissions for SSH (Windows OpenSSH requires specific format)
    icacls $TempKeyPath /inheritance:r /grant:r "${env:USERNAME}:(R)" 2>&1 | Out-Null
    
    Write-Host "  Attempting SSH connection..." -ForegroundColor Gray
    
    # Test SSH connection with timeout
    $sshTest = Start-Job -ScriptBlock {
        param($key, $target)
        & ssh -i $key -o StrictHostKeyChecking=no -o UserKnownHostsFile=NUL -o ConnectTimeout=10 $target "whoami" 2>&1
    } -ArgumentList $TempKeyPath, $SSH_TARGET
    
    $sshTest | Wait-Job -Timeout 30 | Out-Null
    
    if ($sshTest.State -eq 'Completed') {
        $whoamiResult = Receive-Job $sshTest
        Remove-Job $sshTest -Force
        
        if ($whoamiResult -match $SSH_USER) {
            Write-Host "  ✓ SSH connection successful (user: $whoamiResult)" -ForegroundColor Green
        } else {
            Write-Host "  ✗ SSH connection failed" -ForegroundColor Red
            Write-Host "  Output: $whoamiResult" -ForegroundColor Red
            try { Remove-Item $TempKeyPath -Force -ErrorAction SilentlyContinue } catch {}
            exit 1
        }
    } else {
        Remove-Job $sshTest -Force
        Write-Host "  ✗ SSH connection timeout" -ForegroundColor Red
        try { Remove-Item $TempKeyPath -Force -ErrorAction SilentlyContinue } catch {}
        exit 1
    }
} catch {
    Write-Host "  ✗ SSH connection test failed: $_" -ForegroundColor Red
    try { Remove-Item $TempKeyPath -Force -ErrorAction SilentlyContinue } catch {}
    exit 1
}

# Step 3: Verify workspace access
Write-Host ""
Write-Host "[Step 3/7] Verifying workspace access..." -ForegroundColor Yellow

try {
    $wsCheck = ssh -i $TempKeyPath -o StrictHostKeyChecking=no -o UserKnownHostsFile=NUL $SSH_TARGET "ls -la /workspace 2>&1 | head -5" 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ Workspace accessible" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Workspace access failed" -ForegroundColor Red
        try { Remove-Item $TempKeyPath -Force -ErrorAction SilentlyContinue } catch {}
        exit 1
    }
} catch {
    Write-Host "  ✗ Workspace verification failed: $_" -ForegroundColor Red
    try { Remove-Item $TempKeyPath -Force -ErrorAction SilentlyContinue } catch {}
    exit 1
}

# Step 4: Create .runpod directory if not exists
Write-Host ""
Write-Host "[Step 4/7] Preparing remote directories..." -ForegroundColor Yellow

try {
    ssh -i $TempKeyPath -o StrictHostKeyChecking=no -o UserKnownHostsFile=NUL $SSH_TARGET "mkdir -p /workspace/.runpod/logs /workspace/.runpod/scripts" 2>&1 | Out-Null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ Remote directories prepared" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Failed to create directories" -ForegroundColor Red
        try { Remove-Item $TempKeyPath -Force -ErrorAction SilentlyContinue } catch {}
        exit 1
    }
} catch {
    Write-Host "  ✗ Directory preparation failed: $_" -ForegroundColor Red
    try { Remove-Item $TempKeyPath -Force -ErrorAction SilentlyContinue } catch {}
    exit 1
}

# Step 5: Upload setup script
Write-Host ""
Write-Host "[Step 5/7] Uploading setup script to RunPod..." -ForegroundColor Yellow

$SetupScriptPath = Join-Path $PSScriptRoot "setup_heavy_ai_pipelines.sh"

if (-not (Test-Path $SetupScriptPath)) {
    Write-Host "  ✗ Setup script not found at: $SetupScriptPath" -ForegroundColor Red
    try { Remove-Item $TempKeyPath -Force -ErrorAction SilentlyContinue } catch {}
    exit 1
}

try {
    scp -i $TempKeyPath -o StrictHostKeyChecking=no -o UserKnownHostsFile=NUL $SetupScriptPath "${SSH_TARGET}:/workspace/.runpod/setup_heavy_ai_pipelines.sh" 2>&1 | Out-Null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ Setup script uploaded successfully" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Failed to upload setup script" -ForegroundColor Red
        try { Remove-Item $TempKeyPath -Force -ErrorAction SilentlyContinue } catch {}
        exit 1
    }
} catch {
    Write-Host "  ✗ Upload failed: $_" -ForegroundColor Red
    try { Remove-Item $TempKeyPath -Force -ErrorAction SilentlyContinue } catch {}
    exit 1
}

# Step 6: Set executable permissions and execute
Write-Host ""
Write-Host "[Step 6/7] Setting permissions and executing setup..." -ForegroundColor Yellow

try {
    ssh -i $TempKeyPath -o StrictHostKeyChecking=no -o UserKnownHostsFile=NUL $SSH_TARGET "chmod +x /workspace/.runpod/setup_heavy_ai_pipelines.sh" 2>&1 | Out-Null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ Permissions set" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Failed to set permissions" -ForegroundColor Red
        try { Remove-Item $TempKeyPath -Force -ErrorAction SilentlyContinue } catch {}
        exit 1
    }
} catch {
    Write-Host "  ✗ Permission setting failed: $_" -ForegroundColor Red
    try { Remove-Item $TempKeyPath -Force -ErrorAction SilentlyContinue } catch {}
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Executing remote setup (10-15 minutes)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Execute setup script and stream output
try {
    ssh -i $TempKeyPath -o StrictHostKeyChecking=no -o UserKnownHostsFile=NUL $SSH_TARGET "bash /workspace/.runpod/setup_heavy_ai_pipelines.sh"
    
    $setupExitCode = $LASTEXITCODE
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    
    if ($setupExitCode -eq 0) {
        Write-Host "✓ Setup completed successfully!" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Green
        Write-Host ""
        Write-Host "Next steps:" -ForegroundColor Yellow
        Write-Host "1. View full report:" -ForegroundColor White
        Write-Host "   ssh -i <key> $SSH_TARGET" -ForegroundColor Gray
        Write-Host "   cat /workspace/.runpod/logs/heavy_ai_setup_report.log" -ForegroundColor Gray
        Write-Host ""
        Write-Host "2. Access ComfyUI interface:" -ForegroundColor White
        Write-Host "   https://p8q2agahufxw4a-8188.proxy.runpod.net" -ForegroundColor Gray
        Write-Host ""
        Write-Host "3. Download model weights (see setup report for instructions)" -ForegroundColor White
        Write-Host ""
    } else {
        Write-Host "✗ Setup encountered errors (exit code: $setupExitCode)" -ForegroundColor Red
        Write-Host "========================================" -ForegroundColor Red
        Write-Host ""
        Write-Host "Troubleshooting:" -ForegroundColor Yellow
        Write-Host "1. Check setup log on server:" -ForegroundColor White
        Write-Host "   cat /tmp/heavy_ai_setup_actions.log" -ForegroundColor Gray
        Write-Host ""
        Write-Host "2. Review ComfyUI logs:" -ForegroundColor White
        Write-Host "   cat /workspace/.runpod/logs/comfyui.log" -ForegroundColor Gray
        Write-Host ""
    }
} catch {
    Write-Host "✗ Setup execution failed: $_" -ForegroundColor Red
    try { Remove-Item $TempKeyPath -Force -ErrorAction SilentlyContinue } catch {}
    exit 1
}

# Step 7: Cleanup temporary key
Write-Host ""
Write-Host "[Step 7/7] Cleaning up temporary files..." -ForegroundColor Yellow

try {
    Remove-Item $TempKeyPath -Force -ErrorAction SilentlyContinue
    Write-Host "  ✓ Temporary key file removed" -ForegroundColor Green
} catch {
    Write-Host "  ⚠ Warning: Could not remove temporary key file" -ForegroundColor Yellow
    Write-Host "  Please manually delete: $TempKeyPath" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Deployment process complete!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if ($setupExitCode -eq 0) {
    Write-Host "✓ All systems ready for operation" -ForegroundColor Green
    exit 0
} else {
    Write-Host "⚠ Review logs for any issues" -ForegroundColor Yellow
    exit $setupExitCode
}
