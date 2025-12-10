#!/bin/bash
# Проверка статуса всех сервисов на RunPod

echo "=== SERVICE STATUS CHECK ==="
echo ""

echo "1. Backend Status:"
if pgrep -f "backend/main.py" > /dev/null; then
    echo "   ✅ Backend is running (PID: $(pgrep -f 'backend/main.py'))"
else
    echo "   ❌ Backend is NOT running"
fi

echo ""
echo "2. GPU Server Status:"
if pgrep -f "gpu_server/server.py" > /dev/null; then
    echo "   ✅ GPU Server is running (PID: $(pgrep -f 'gpu_server/server.py'))"
else
    echo "   ❌ GPU Server is NOT running"
fi

echo ""
echo "3. ComfyUI Status:"
if pgrep -f "comfyui" > /dev/null || pgrep -f "python.*main.py" | grep -v backend | grep -v gpu_server > /dev/null; then
    echo "   ✅ ComfyUI might be running"
else
    echo "   ❌ ComfyUI is NOT running"
fi

echo ""
echo "4. Port Check:"
echo "   Backend (8000): $(ss -tlnp | grep :8000 || echo 'Not listening')"
echo "   GPU Server (8001): $(ss -tlnp | grep :8001 || echo 'Not listening')"
echo "   ComfyUI (8188): $(ss -tlnp | grep :8188 || echo 'Not listening')"

echo ""
echo "5. Recent Logs:"
echo "   Backend:"
tail -n 3 /workspace/logs/backend.log 2>/dev/null || echo "   No logs found"
echo ""
echo "   GPU Server:"
tail -n 3 /workspace/logs/gpu_server.log 2>/dev/null || echo "   No logs found"

echo ""
echo "=== END STATUS CHECK ==="
