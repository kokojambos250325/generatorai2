# RunPod Serverless API - cURL Examples
# Тестирование endpoint через HTTP запросы

param(
    [Parameter(Mandatory=$false)]
    [string]$EndpointId = $env:ENDPOINT_ID,
    
    [Parameter(Mandatory=$false)]
    [string]$ApiKey = $env:RUNPOD_API_KEY
)

$BASE_URL = "https://api.runpod.ai/v2"

if (-not $EndpointId) {
    Write-Host "❌ Error: ENDPOINT_ID not set!" -ForegroundColor Red
    Write-Host "Set it with: `$env:ENDPOINT_ID='your-endpoint-id'" -ForegroundColor Yellow
    exit 1
}

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "RunPod Serverless API Tests" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "API Key: $($ApiKey.Substring(0,20))..." -ForegroundColor White
Write-Host "Endpoint: $EndpointId" -ForegroundColor White
Write-Host ""

function Test-SyncRequest {
    Write-Host "Test 1: Sync Request (/runsync)" -ForegroundColor Yellow
    Write-Host "Submitting job and waiting for result..." -ForegroundColor Gray
    
    $body = @{
        input = @{
            mode = "free"
            params = @{
                prompt = "beautiful sunset over mountains, photorealistic, 8k"
                negative_prompt = "ugly, blurry, low quality"
                width = 1024
                height = 1024
                steps = 30
                cfg_scale = 7.5
                seed = 42
            }
        }
    } | ConvertTo-Json -Depth 10
    
    $response = Invoke-RestMethod `
        -Uri "$BASE_URL/$EndpointId/runsync" `
        -Method Post `
        -Headers @{
            "Authorization" = "Bearer $ApiKey"
            "Content-Type" = "application/json"
        } `
        -Body $body `
        -TimeoutSec 300
    
    Write-Host "✅ Response received!" -ForegroundColor Green
    Write-Host "Status: $($response.status)" -ForegroundColor White
    
    if ($response.status -eq "success") {
        # Сохраняем изображение
        $imageBytes = [Convert]::FromBase64String($response.image)
        [IO.File]::WriteAllBytes("$PWD\output_sync.png", $imageBytes)
        Write-Host "✅ Image saved to: output_sync.png" -ForegroundColor Green
        Write-Host "Size: $($imageBytes.Length) bytes" -ForegroundColor Gray
    } else {
        Write-Host "❌ Error: $($response.error)" -ForegroundColor Red
    }
    
    Write-Host ""
}

function Test-AsyncRequest {
    Write-Host "Test 2: Async Request (/run)" -ForegroundColor Yellow
    Write-Host "Submitting job..." -ForegroundColor Gray
    
    $body = @{
        input = @{
            mode = "free"
            params = @{
                prompt = "anime style girl with blue hair, detailed"
                width = 1024
                height = 1024
                steps = 25
                seed = 123
            }
        }
    } | ConvertTo-Json -Depth 10
    
    # Отправляем job
    $response = Invoke-RestMethod `
        -Uri "$BASE_URL/$EndpointId/run" `
        -Method Post `
        -Headers @{
            "Authorization" = "Bearer $ApiKey"
            "Content-Type" = "application/json"
        } `
        -Body $body
    
    $jobId = $response.id
    Write-Host "✅ Job submitted: $jobId" -ForegroundColor Green
    Write-Host "Status: $($response.status)" -ForegroundColor Gray
    
    # Проверяем статус
    Write-Host "Checking status..." -ForegroundColor Gray
    Start-Sleep -Seconds 2
    
    $statusResponse = Invoke-RestMethod `
        -Uri "$BASE_URL/$EndpointId/status/$jobId" `
        -Method Get `
        -Headers @{
            "Authorization" = "Bearer $ApiKey"
        }
    
    Write-Host "Current status: $($statusResponse.status)" -ForegroundColor White
    
    # Ждём завершения (polling)
    $maxRetries = 60
    $retries = 0
    
    Write-Host "Waiting for completion..." -ForegroundColor Gray
    
    while ($retries -lt $maxRetries) {
        $statusResponse = Invoke-RestMethod `
            -Uri "$BASE_URL/$EndpointId/status/$jobId" `
            -Method Get `
            -Headers @{
                "Authorization" = "Bearer $ApiKey"
            }
        
        if ($statusResponse.status -eq "COMPLETED") {
            Write-Host "✅ Job completed!" -ForegroundColor Green
            
            $output = $statusResponse.output
            if ($output.status -eq "success") {
                $imageBytes = [Convert]::FromBase64String($output.image)
                [IO.File]::WriteAllBytes("$PWD\output_async.png", $imageBytes)
                Write-Host "✅ Image saved to: output_async.png" -ForegroundColor Green
            } else {
                Write-Host "❌ Error: $($output.error)" -ForegroundColor Red
            }
            break
        } elseif ($statusResponse.status -eq "FAILED") {
            Write-Host "❌ Job failed: $($statusResponse.error)" -ForegroundColor Red
            break
        }
        
        Write-Host "." -NoNewline
        Start-Sleep -Seconds 5
        $retries++
    }
    
    if ($retries -eq $maxRetries) {
        Write-Host "`n⏱️  Timeout waiting for job" -ForegroundColor Yellow
    }
    
    Write-Host ""
}

function Test-HealthCheck {
    Write-Host "Test 3: Health Check (/health)" -ForegroundColor Yellow
    
    $response = Invoke-RestMethod `
        -Uri "$BASE_URL/$EndpointId/health" `
        -Method Get `
        -Headers @{
            "Authorization" = "Bearer $ApiKey"
        }
    
    Write-Host "✅ Endpoint is healthy!" -ForegroundColor Green
    Write-Host ($response | ConvertTo-Json -Depth 5) -ForegroundColor Gray
    Write-Host ""
}

function Test-CancelJob {
    param([string]$JobId)
    
    Write-Host "Test 4: Cancel Job (/cancel/$JobId)" -ForegroundColor Yellow
    
    $response = Invoke-RestMethod `
        -Uri "$BASE_URL/$EndpointId/cancel/$JobId" `
        -Method Post `
        -Headers @{
            "Authorization" = "Bearer $ApiKey"
        }
    
    Write-Host "✅ Job cancelled" -ForegroundColor Green
    Write-Host ($response | ConvertTo-Json) -ForegroundColor Gray
    Write-Host ""
}

# Меню
Write-Host "Choose test:" -ForegroundColor Cyan
Write-Host "1. Sync request (/runsync)" -ForegroundColor White
Write-Host "2. Async request (/run)" -ForegroundColor White
Write-Host "3. Health check" -ForegroundColor White
Write-Host "4. All tests" -ForegroundColor White
Write-Host ""

$choice = Read-Host "Enter choice (1-4)"

switch ($choice) {
    "1" { Test-SyncRequest }
    "2" { Test-AsyncRequest }
    "3" { Test-HealthCheck }
    "4" {
        Test-HealthCheck
        Test-SyncRequest
        Test-AsyncRequest
    }
    default { Write-Host "Invalid choice" -ForegroundColor Red }
}

Write-Host "Done!" -ForegroundColor Green
