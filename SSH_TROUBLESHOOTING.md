# Решение проблем с SSH подключением в VS Code Remote

## Проблема
VS Code Remote SSH не может подключиться к серверу:
- `Connection closed by 38.147.83.26 port 25206`
- `Попытка записи в несуществующий канал`
- `Failed to parse remote port from server output`

## Решения

### 1. Проверка базового SSH подключения

Сначала убедитесь, что SSH работает из командной строки:

```bash
# Windows PowerShell
ssh -i ~/.ssh/id_ed25519 -p 25206 root@38.147.83.26 "echo 'Test OK'"
```

Если это работает, проблема в конфигурации VS Code.

### 2. Настройка SSH конфигурации для VS Code

Создайте/отредактируйте файл `C:\Users\KIT\.ssh\config`:

```ssh-config
Host runpod
    HostName 38.147.83.26
    Port 25206
    User root
    IdentityFile C:\Users\KIT\.ssh\id_ed25519
    ServerAliveInterval 60
    ServerAliveCountMax 3
    TCPKeepAlive yes
    ConnectTimeout 30
    StrictHostKeyChecking no
    UserKnownHostsFile C:\Users\KIT\.ssh\known_hosts
```

### 3. Проверка прав доступа к SSH ключу

```powershell
# В PowerShell (от администратора)
icacls C:\Users\KIT\.ssh\id_ed25519
# Должно быть: NT AUTHORITY\SYSTEM:(F), BUILTIN\Administrators:(F), KIT\KIT:(F)

# Если нет прав, установите:
icacls C:\Users\KIT\.ssh\id_ed25519 /grant "KIT\KIT:(F)"
```

### 4. Настройки VS Code Remote SSH

В VS Code откройте настройки (Ctrl+,) и найдите `remote.SSH`:

```json
{
    "remote.SSH.connectTimeout": 60,
    "remote.SSH.serverInstallPath": {
        "runpod": "/root/.vscode-server"
    },
    "remote.SSH.useLocalServer": false,
    "remote.SSH.showLoginTerminal": true,
    "remote.SSH.enableDynamicForwarding": true,
    "remote.SSH.enableRemoteCommand": false
}
```

### 5. Очистка кэша VS Code Remote

```powershell
# Закройте VS Code, затем выполните:
Remove-Item -Recurse -Force "$env:USERPROFILE\.vscode-server" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "$env:USERPROFILE\AppData\Roaming\Code\logs" -ErrorAction SilentlyContinue
```

### 6. Альтернативный способ подключения

Если VS Code Remote не работает, используйте:

**Вариант A: WinSCP + Notepad++**
- WinSCP для файлов
- Notepad++ с плагином NppFTP для редактирования

**Вариант B: MobaXterm**
- Полноценный SSH клиент с встроенным редактором

**Вариант C: Прямое редактирование через SSH**
```bash
# Подключитесь через обычный SSH
ssh -i ~/.ssh/id_ed25519 -p 25206 root@38.147.83.26

# Используйте nano/vim для редактирования
nano /workspace/ai-generator/file.py
```

### 7. Проверка SSH сервера на RunPod

Подключитесь через обычный SSH и проверьте:

```bash
ssh -i ~/.ssh/id_ed25519 -p 25206 root@38.147.83.26

# Проверьте SSH сервер
systemctl status sshd
# или
service ssh status

# Проверьте логи
tail -50 /var/log/auth.log
# или
journalctl -u ssh -n 50
```

### 8. Обновление VS Code Remote SSH

1. Откройте VS Code
2. Перейдите в Extensions (Ctrl+Shift+X)
3. Найдите "Remote - SSH"
4. Обновите расширение до последней версии
5. Перезапустите VS Code

### 9. Проверка файрвола RunPod

Возможно, RunPod блокирует некоторые SSH функции. Проверьте настройки Pod:
- Убедитесь, что SSH порт 25206 открыт
- Проверьте, не включены ли ограничения на SSH соединения

### 10. Временное решение

Пока проблема не решена, используйте обычный SSH терминал:

```powershell
# Создайте ярлык для быстрого подключения
ssh -i C:\Users\KIT\.ssh\id_ed25519 -p 25206 root@38.147.83.26
```

## Диагностика

Выполните эти команды для диагностики:

```powershell
# 1. Проверка SSH ключа
ssh-keygen -l -f C:\Users\KIT\.ssh\id_ed25519.pub

# 2. Тест подключения с подробным выводом
ssh -v -i C:\Users\KIT\.ssh\id_ed25519 -p 25206 root@38.147.83.26

# 3. Проверка конфигурации
ssh -F C:\Users\KIT\.ssh\config -T runpod
```

## Если ничего не помогает

1. Пересоздайте SSH ключ:
```powershell
ssh-keygen -t ed25519 -f C:\Users\KIT\.ssh\id_ed25519_new -C "runpod"
```

2. Добавьте новый публичный ключ на сервер:
```bash
# На сервере
echo "новый_публичный_ключ" >> ~/.ssh/authorized_keys
```

3. Обновите SSH config для использования нового ключа

