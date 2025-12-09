# RunPod SSH Connection Script
# Подключается к RunPod worker через SSH для отладки

param(
    [Parameter(Mandatory=$false)]
    [string]$Host = "",
    
    [Parameter(Mandatory=$false)]
    [int]$Port = 0
)

$SSH_KEY = "C:\Users\KIT\.ssh\id_ed25519"
$SSH_USER = "root"

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "RunPod SSH Connection" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# Если параметры не указаны, показываем инструкции
if (-not $Host -or $Port -eq 0) {
    Write-Host "Для подключения к RunPod worker:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "1. Откройте https://www.runpod.io/console/serverless" -ForegroundColor White
    Write-Host "2. Выберите ваш endpoint" -ForegroundColor White
    Write-Host "3. Перейдите во вкладку 'Workers'" -ForegroundColor White
    Write-Host "4. Нажмите 'Connect' на активном worker" -ForegroundColor White
    Write-Host "5. Скопируйте SSH команду" -ForegroundColor White
    Write-Host ""
    Write-Host "Затем запустите:" -ForegroundColor White
    Write-Host "  .\connect_runpod_ssh.ps1 -Host <hostname> -Port <port>" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Пример:" -ForegroundColor White
    Write-Host "  .\connect_runpod_ssh.ps1 -Host worker-xyz.runpod.io -Port 22" -ForegroundColor Cyan
    Write-Host ""
    
    # Попробуем получить информацию через API
    Write-Host "Пытаюсь получить список workers через API..." -ForegroundColor Yellow
    
    $API_KEY = $env:RUNPOD_API_KEY
    $GRAPHQL_URL = "https://api.runpod.io/graphql"
    
    $queryBody = '{"query": "query { myself { endpoints { id name workers { id status } } } }"}'
    
    try {
        $headers = @{
            Authorization = "Bearer $API_KEY"
            "Content-Type" = "application/json"
        }
        
        $response = Invoke-RestMethod -Uri $GRAPHQL_URL -Method Post -Body $queryBody -Headers $headers
        
        if ($response.data.myself.endpoints) {
            Write-Host "`nДоступные endpoints:" -ForegroundColor Green
            foreach ($endpoint in $response.data.myself.endpoints) {
                Write-Host "  - $($endpoint.name) ($($endpoint.id))" -ForegroundColor White
                if ($endpoint.workers) {
                    foreach ($worker in $endpoint.workers) {
                        Write-Host "    Worker: $($worker.id) - Status: $($worker.status)" -ForegroundColor Gray
                    }
                } else {
                    Write-Host "    Нет активных workers" -ForegroundColor Gray
                }
            }
        }
    } catch {
        Write-Host "Не удалось получить информацию через API: $_" -ForegroundColor Red
    }
    
    exit 0
}

# Подключение к указанному хосту
Write-Host "Connecting to RunPod worker..." -ForegroundColor Yellow
Write-Host "Host: $Host" -ForegroundColor White
Write-Host "Port: $Port" -ForegroundColor White
Write-Host "User: $SSH_USER" -ForegroundColor White
Write-Host "Key: $SSH_KEY" -ForegroundColor White
Write-Host ""

# Проверка существования ключа
if (-not (Test-Path $SSH_KEY)) {
    Write-Host "✗ SSH key not found: $SSH_KEY" -ForegroundColor Red
    exit 1
}

Write-Host "✓ SSH key found" -ForegroundColor Green
Write-Host ""
Write-Host "Connecting... (Press Ctrl+C to disconnect)" -ForegroundColor Cyan
Write-Host ""

# Выполнение SSH подключения
ssh -o StrictHostKeyChecking=no `
    -o UserKnownHostsFile=NUL `
    -i $SSH_KEY `
    -p $Port `
    "$SSH_USER@$Host"

Write-Host ""
Write-Host "Disconnected from RunPod worker" -ForegroundColor Yellow
