#!/bin/bash
# Деплой backend и gpu_server на RunPod
# Запускается ЛОКАЛЬНО и заливает файлы на сервер

SERVER="root@38.147.83.26"
PORT="25206"
KEY="~/.ssh/id_ed25519"

echo "=== DEPLOYING BACKEND & GPU SERVER ==="
echo ""

# 1. Копируем backend
echo "1. Copying backend..."
scp -i $KEY -P $PORT -r backend/ $SERVER:/workspace/backend/
echo "   ✅ Backend copied"

# 2. Копируем gpu_server
echo "2. Copying gpu_server..."
scp -i $KEY -P $PORT gpu_server/server.py $SERVER:/workspace/gpu_server/
scp -i $KEY -P $PORT gpu_server/comfy_client.py $SERVER:/workspace/gpu_server/
scp -i $KEY -P $PORT gpu_server/config.py $SERVER:/workspace/gpu_server/
scp -i $KEY -P $PORT gpu_server/json_logging.py $SERVER:/workspace/gpu_server/
echo "   ✅ GPU server copied"

# 3. Останавливаем старые сервисы
echo "3. Stopping old services..."
ssh -i $KEY -p $PORT $SERVER "pkill -9 -f 'backend/main.py' || true"
ssh -i $KEY -p $PORT $SERVER "pkill -9 -f 'gpu_server/server.py' || true"
sleep 2
echo "   ✅ Services stopped"

# 4. Создаём директорию для логов
echo "4. Creating log directory..."
ssh -i $KEY -p $PORT $SERVER "mkdir -p /workspace/logs"
echo "   ✅ Log directory ready"

# 5. Запускаем GPU Server
echo "5. Starting GPU Server..."
ssh -i $KEY -p $PORT $SERVER "cd /workspace && nohup python gpu_server/server.py > /workspace/logs/gpu_server.log 2>&1 &"
sleep 3
echo "   ✅ GPU Server started"

# 6. Запускаем Backend
echo "6. Starting Backend..."
ssh -i $KEY -p $PORT $SERVER "cd /workspace && nohup python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 > /workspace/logs/backend.log 2>&1 &"
sleep 3
echo "   ✅ Backend started"

# 7. Проверяем статус
echo ""
echo "7. Checking service status..."
ssh -i $KEY -p $PORT $SERVER "bash /workspace/check_services_status.sh"

echo ""
echo "=== DEPLOYMENT COMPLETE ==="
echo ""
echo "Services available at:"
echo "  - Backend:    http://localhost:8000 (via tunnel)"
echo "  - GPU Server: http://localhost:8001"
echo "  - ComfyUI:    http://localhost:8188 (via tunnel)"
echo ""
echo "To check logs:"
echo "  ssh -i $KEY -p $PORT $SERVER 'tail -f /workspace/logs/backend.log'"
echo "  ssh -i $KEY -p $PORT $SERVER 'tail -f /workspace/logs/gpu_server.log'"
