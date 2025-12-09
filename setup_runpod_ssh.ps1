# RunPod SSH Key Setup
# Показывает публичный ключ для добавления в RunPod

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "RunPod SSH Key Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$PUBLIC_KEY_PATH = "C:\Users\KIT\.ssh\runpod_serverless_key.pub"
$PRIVATE_KEY_PATH = "C:\Users\KIT\.ssh\runpod_serverless_key"

# Проверка существования ключей
if (-not (Test-Path $PUBLIC_KEY_PATH)) {
    Write-Host "✗ Публичный ключ не найден!" -ForegroundColor Red
    Write-Host "Создайте ключ командой:" -ForegroundColor Yellow
    Write-Host '  ssh-keygen -t ed25519 -f "C:\Users\KIT\.ssh\runpod_serverless_key" -C "runpod-serverless"' -ForegroundColor Gray
    exit 1
}

Write-Host "✓ SSH ключи найдены" -ForegroundColor Green
Write-Host ""

# Вывод публичного ключа
Write-Host "Ваш публичный SSH ключ:" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Gray
$publicKey = Get-Content $PUBLIC_KEY_PATH
Write-Host $publicKey -ForegroundColor White
Write-Host "========================================" -ForegroundColor Gray
Write-Host ""

# Копирование в буфер обмена
$publicKey | Set-Clipboard
Write-Host "✓ Ключ скопирован в буфер обмена!" -ForegroundColor Green
Write-Host ""

# Инструкции
Write-Host "Следующие шаги:" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Откройте RunPod Settings:" -ForegroundColor White
Write-Host "   https://www.runpod.io/console/user/settings" -ForegroundColor Blue
Write-Host ""
Write-Host "2. Перейдите в раздел 'SSH Public Keys'" -ForegroundColor White
Write-Host ""
Write-Host "3. Нажмите 'Add SSH Key'" -ForegroundColor White
Write-Host ""
Write-Host "4. Paste the key (already in clipboard):" -ForegroundColor White
Write-Host "   Press Ctrl+V to paste" -ForegroundColor Gray
Write-Host ""
Write-Host "5. Give key a name: 'RunPod Serverless 2024'" -ForegroundColor White
Write-Host ""
Write-Host "6. Click 'Add Key'" -ForegroundColor White
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "После добавления ключа в RunPod:" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "To connect to Pod use:" -ForegroundColor Yellow
Write-Host '  ssh -i "C:\Users\KIT\.ssh\runpod_serverless_key" root@HOST -p PORT' -ForegroundColor Gray
Write-Host ""
Write-Host "Or use the script:" -ForegroundColor Yellow
Write-Host "  .\connect_runpod_ssh.ps1 -Host HOST -Port PORT" -ForegroundColor Gray
Write-Host ""

# Key locations
Write-Host "Key locations:" -ForegroundColor White
Write-Host "  Public:   $PUBLIC_KEY_PATH" -ForegroundColor Gray
Write-Host "  Private:  $PRIVATE_KEY_PATH" -ForegroundColor Gray
Write-Host ""
