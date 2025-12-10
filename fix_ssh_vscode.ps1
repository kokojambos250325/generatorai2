# Скрипт для исправления проблем с SSH в VS Code Remote

Write-Host "=== ИСПРАВЛЕНИЕ SSH ДЛЯ VS CODE REMOTE ===" -ForegroundColor Cyan
Write-Host ""

# 1. Обновление SSH config
Write-Host "1. Обновление SSH config..." -ForegroundColor Yellow
$sshConfig = @"
Host runpod
    HostName 38.147.83.26
    Port 25206
    User root
    IdentityFile C:/Users/KIT/.ssh/id_ed25519
    ServerAliveInterval 30
    ServerAliveCountMax 3
    TCPKeepAlive yes
    ConnectTimeout 20
    StrictHostKeyChecking no
    UserKnownHostsFile C:/Users/KIT/.ssh/known_hosts
    LogLevel ERROR
    Compression yes
    ControlMaster auto
    ControlPath ~/.ssh/control-%r@%h:%p
    ControlPersist 10m
"@

$configPath = "$env:USERPROFILE\.ssh\config"
$sshConfig | Out-File -FilePath $configPath -Encoding utf8 -Force
Write-Host "   ✓ SSH config обновлен" -ForegroundColor Green
Write-Host ""

# 2. Проверка прав доступа к ключу
Write-Host "2. Проверка прав доступа к SSH ключу..." -ForegroundColor Yellow
$keyPath = "$env:USERPROFILE\.ssh\id_ed25519"
if (Test-Path $keyPath) {
    $acl = Get-Acl $keyPath
    Write-Host "   ✓ Ключ найден: $keyPath" -ForegroundColor Green
    Write-Host "   Права доступа:" -ForegroundColor Gray
    $acl.Access | ForEach-Object { Write-Host "     $($_.IdentityReference): $($_.FileSystemRights)" -ForegroundColor Gray }
} else {
    Write-Host "   ❌ SSH ключ не найден: $keyPath" -ForegroundColor Red
}
Write-Host ""

# 3. Очистка кэша VS Code Remote
Write-Host "3. Очистка кэша VS Code Remote..." -ForegroundColor Yellow
$vscodeCachePaths = @(
    "$env:USERPROFILE\.vscode-server",
    "$env:APPDATA\Code\logs",
    "$env:APPDATA\Code\CachedData"
)

foreach ($path in $vscodeCachePaths) {
    if (Test-Path $path) {
        try {
            Remove-Item -Path $path -Recurse -Force -ErrorAction SilentlyContinue
            Write-Host "   ✓ Очищен: $path" -ForegroundColor Green
        } catch {
            Write-Host "   ⚠ Не удалось очистить: $path" -ForegroundColor Yellow
        }
    }
}
Write-Host ""

# 4. Тест SSH подключения
Write-Host "4. Тест SSH подключения..." -ForegroundColor Yellow
try {
    $result = ssh -o ConnectTimeout=10 runpod "echo 'SSH OK'" 2>&1
    if ($result -match "SSH OK") {
        Write-Host "   ✓ SSH подключение работает!" -ForegroundColor Green
    } else {
        Write-Host "   ⚠ SSH подключение имеет проблемы:" -ForegroundColor Yellow
        Write-Host "   $result" -ForegroundColor Gray
    }
} catch {
    Write-Host "   ❌ Ошибка SSH подключения: $_" -ForegroundColor Red
}
Write-Host ""

# 5. Рекомендации
Write-Host "=== РЕКОМЕНДАЦИИ ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Перезапустите VS Code" -ForegroundColor Yellow
Write-Host "2. Попробуйте подключиться через: Remote-SSH: Connect to Host -> runpod" -ForegroundColor Yellow
Write-Host "3. Если не работает, используйте обычный SSH терминал:" -ForegroundColor Yellow
Write-Host "   ssh runpod" -ForegroundColor Gray
Write-Host ""
Write-Host "4. Проверьте настройки VS Code Remote SSH:" -ForegroundColor Yellow
Write-Host "   - Откройте Settings (Ctrl+,)" -ForegroundColor Gray
Write-Host "   - Найдите 'remote.SSH'" -ForegroundColor Gray
Write-Host "   - Установите 'remote.SSH.connectTimeout': 60" -ForegroundColor Gray
Write-Host "   - Установите 'remote.SSH.showLoginTerminal': true" -ForegroundColor Gray
Write-Host ""

Write-Host "=== ГОТОВО ===" -ForegroundColor Green

