@echo off
REM Execute command on RunPod with retry mechanism

SET SSH_HOST=root@213.173.102.93
SET SSH_PORT=22063
SET MAX_RETRIES=5
SET RETRY_COUNT=0

:RETRY
SET /A RETRY_COUNT+=1
echo [Attempt %RETRY_COUNT%/%MAX_RETRIES%] Executing command on RunPod...

docker exec romantic_franklin ssh -o ConnectTimeout=10 -o ServerAliveInterval=5 -o ServerAliveCountMax=2 %SSH_HOST% -p %SSH_PORT% "cd /workspace/ai-generator && git pull && bash fix_all.sh"

IF %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ Command executed successfully!
    exit /b 0
)

IF %RETRY_COUNT% LSS %MAX_RETRIES% (
    echo ❌ Failed, retrying in 3 seconds...
    timeout /t 3 /nobreak >nul
    goto RETRY
)

echo.
echo ❌ Failed after %MAX_RETRIES% attempts
echo Please use RunPod Web Terminal:
echo https://www.runpod.io/console/pods
exit /b 1
