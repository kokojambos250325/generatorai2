#!/bin/bash
# FINAL DEPLOYMENT SCRIPT - Upload files inline and restart

echo "=== FINAL DEPLOYMENT ==="

# 1. Upload response_generate.py content inline
cat > /workspace/backend/schemas/response_generate.py << 'EOF'
from typing import Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

class GenerationResponse(BaseModel):
    task_id: str = Field(description="Unique task identifier")
    status: Literal["done", "queued", "processing", "failed"] = Field(description="Task status")
    image: Optional[str] = Field(default=None, description="Base64 encoded result image")
    error: Optional[str] = Field(default=None, description="Error message")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    @classmethod
    def success(cls, image: str, task_id: Optional[str] = None):
        return cls(task_id=task_id or str(uuid.uuid4()), status="done", image=image, error=None)
    
    @classmethod
    def error(cls, error_message: str, task_id: Optional[str] = None):
        return cls(task_id=task_id or str(uuid.uuid4()), status="failed", image=None, error=error_message)
EOF

echo "✅ Updated response_generate.py"

# 2. Stop all services
pkill -9 python
sleep 3

# 3. Start services
cd /workspace
nohup /workspace/venv/bin/python gpu_server/server.py > /workspace/logs/gpu_server.log 2>&1 &
sleep 3

cd /workspace/backend
nohup /workspace/venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000 > /workspace/logs/backend.log 2>&1 &
sleep 3

cd /workspace/telegram_bot
nohup python bot.py > /workspace/logs/telegram_bot.log 2>&1 &
sleep 5

# 4. Check status
echo ""
echo "=== SERVICE STATUS ==="
ps aux | grep python | grep -E "server.py|uvicorn|bot.py" | grep -v grep || echo "No services running!"

echo ""
echo "=== BACKEND LOG ==="
tail -20 /workspace/logs/backend.log

echo ""
echo "=== TESTING API ==="
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"mode":"free","prompt":"test","style":"realism","add_face":false}' \
  -w "\nHTTP: %{http_code}\n" -s | head -20

echo ""
echo "=== DEPLOYMENT COMPLETE ==="
