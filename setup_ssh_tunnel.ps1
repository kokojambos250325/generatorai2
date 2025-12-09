# SSH Tunnel to RunPod ComfyUI
# Создаёт туннель для доступа к ComfyUI на RunPod с локального компьютера

param(
    [Parameter(Mandatory=$false)]
    [string]$Host = "nlrtkvylv1s0cw-22.proxy.runpod.net",
    
    [Parameter(Mandatory=$false)]
    [int]$Port = 22537,
    
    [Parameter(Mandatory=$false)]
    [int]$LocalPort = 8188
)

$SSH_KEY = "C:\Users\KIT\.ssh\runpod_serverless_key"
$SSH_USER = "root"

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "SSH Tunnel to RunPod ComfyUI" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Setting up SSH tunnel..." -ForegroundColor Yellow
Write-Host "  Remote Host: $Host" -ForegroundColor White
Write-Host "  SSH Port:    $Port" -ForegroundColor White
Write-Host "  Local Port:  $LocalPort" -ForegroundColor White
Write-Host ""

Write-Host "ComfyUI will be available at:" -ForegroundColor Green
Write-Host "  http://localhost:$LocalPort" -ForegroundColor Cyan
Write-Host ""

Write-Host "Press Ctrl+C to stop tunnel" -ForegroundColor Yellow
Write-Host ""

# Создаём SSH туннель
# -L локальный_порт:localhost:удалённый_порт
ssh -i $SSH_KEY `
    -L "${LocalPort}:localhost:8188" `
    -o StrictHostKeyChecking=no `
    -o UserKnownHostsFile=NUL `
    -N `
    -p $Port `
    "${SSH_USER}@${Host}"

Write-Host ""
Write-Host "Tunnel closed" -ForegroundColor Yellow
