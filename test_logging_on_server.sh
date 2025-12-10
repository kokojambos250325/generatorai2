#!/bin/bash
# Тест логирования напрямую на сервере RunPod

echo "=== LOGGING TEST ON SERVER ==="
echo ""

# 1. Проверка backend
echo "1. Checking Backend..."
BACKEND_HEALTH=$(curl -s http://127.0.0.1:8000/health)
echo "   Response: $BACKEND_HEALTH"

# 2. Простой тестовый запрос
echo ""
echo "2. Sending test generation request..."
curl -s -X POST http://127.0.0.1:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "free",
    "style": "realistic",
    "prompt": "test image",
    "add_face": false,
    "extra_params": {"steps": 5, "cfg_scale": 7.0}
  }' | head -c 200

echo ""
echo ""

# 3. Проверка логов
echo "3. Checking logs..."
echo ""
echo "=== Last 10 lines of backend.log ==="
tail -n 10 /workspace/logs/backend.log

echo ""
echo "=== Last 10 lines of gpu_server.log ==="
tail -n 10 /workspace/logs/gpu_server.log

echo ""
echo "=== END TEST ==="
