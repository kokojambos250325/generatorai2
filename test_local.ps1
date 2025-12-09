# Local RunPod Handler Testing Script
# Tests your ComfyUI handler locally before deployment

param(
    [Parameter(Mandatory=$false)]
    [int]$Port = 8000,
    
    [Parameter(Mandatory=$false)]
    [string]$LogLevel = "INFO",
    
    [Parameter(Mandatory=$false)]
    [int]$Workers = 1
)

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "RunPod Local Testing Server" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Starting local server..." -ForegroundColor Yellow
Write-Host "  Port:        $Port" -ForegroundColor White
Write-Host "  Log Level:   $LogLevel" -ForegroundColor White
Write-Host "  Workers:     $Workers" -ForegroundColor White
Write-Host ""

Write-Host "Server will be available at:" -ForegroundColor Green
Write-Host "  http://localhost:$Port" -ForegroundColor Cyan
Write-Host ""

Write-Host "Send test request:" -ForegroundColor Yellow
Write-Host '  Invoke-RestMethod -Uri "http://localhost:' + $Port + '/run" -Method Post -Body (ConvertTo-Json @{input=@{prompt="test"}}) -ContentType "application/json"' -ForegroundColor Gray
Write-Host ""

Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""

# Start the handler
python handler.py `
    --rp_serve_api `
    --rp_api_port $Port `
    --rp_api_concurrency $Workers `
    --rp_log_level $LogLevel
