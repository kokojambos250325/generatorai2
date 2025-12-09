@echo off
REM Stable SSH connection to RunPod with auto-reconnect

SET SSH_HOST=root@213.173.102.93
SET SSH_PORT=22063

:RECONNECT
echo ========================================
echo Connecting to RunPod...
echo ========================================
echo.

docker exec -it romantic_franklin ssh -o ServerAliveInterval=30 -o ServerAliveCountMax=3 -o TCPKeepAlive=yes %SSH_HOST% -p %SSH_PORT%

echo.
echo Connection lost. Reconnecting in 3 seconds...
timeout /t 3 /nobreak >nul
goto RECONNECT
