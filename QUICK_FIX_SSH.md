# Быстрое решение проблемы SSH в VS Code

## Проблема
`Connection closed by 38.147.83.26 port 25206` при попытке подключения через VS Code Remote SSH.

## Быстрое решение

### Шаг 1: Проверьте, работает ли SSH вообще

Откройте PowerShell и выполните:
```powershell
ssh -i C:\Users\KIT\.ssh\id_ed25519 -p 25206 root@38.147.83.26
```

**Если это НЕ работает** - проблема на сервере RunPod, не в VS Code.

### Шаг 2: Если SSH работает, но VS Code нет

1. **Обновите SSH config** (`C:\Users\KIT\.ssh\config`):
```
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
```

2. **Очистите кэш VS Code**:
```powershell
Remove-Item -Recurse -Force "$env:USERPROFILE\.vscode-server" -ErrorAction SilentlyContinue
```

3. **Перезапустите VS Code**

4. **Попробуйте подключиться снова**: `Remote-SSH: Connect to Host -> runpod`

### Шаг 3: Если ничего не помогает

Используйте **RunPod Web Terminal**:
1. Откройте панель управления RunPod
2. Найдите "Web Terminal" 
3. Используйте его для работы с сервером

Или используйте обычный SSH терминал для работы с файлами через `nano`/`vim`.

## Проверка SSH ключа на сервере

Если SSH не работает вообще, проверьте ключ на сервере:

1. Подключитесь через **RunPod Web Terminal**
2. Выполните:
```bash
cat ~/.ssh/authorized_keys
# Убедитесь, что там есть ваш публичный ключ

# Если нет, добавьте его:
echo "ваш_публичный_ключ_из_id_ed25519.pub" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

## Альтернативные инструменты

- **MobaXterm** - полноценный SSH клиент с редактором
- **WinSCP + Notepad++** - для работы с файлами
- **PuTTY** - классический SSH клиент

