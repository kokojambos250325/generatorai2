#!/usr/bin/env python3
"""
Remote deployment and testing script
"""
import subprocess
import time

def run_ssh(command):
    """Execute SSH command and return output"""
    try:
        result = subprocess.run(
            ['ssh', 'runpod', command],
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.stdout + result.stderr
    except Exception as e:
        return f"Error: {e}"

print("=== 1. Uploading response_generate.py ===")
upload_code = '''cat > /workspace/backend/schemas/response_generate.py << 'ENDFILE'
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
ENDFILE
'''
print(run_ssh(upload_code))

print("\n=== 2. Stopping services ===")
print(run_ssh("pkill -9 python; sleep 2"))

print("\n=== 3. Starting GPU Server ===")
print(run_ssh("cd /workspace && nohup /workspace/venv/bin/python gpu_server/server.py > /workspace/logs/gpu_server.log 2>&1 &"))
time.sleep(3)

print("\n=== 4. Starting Backend ===")
print(run_ssh("cd /workspace/backend && nohup /workspace/venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000 > /workspace/logs/backend.log 2>&1 &"))
time.sleep(4)

print("\n=== 5. Starting Telegram Bot ===")
print(run_ssh("cd /workspace/telegram_bot && nohup python bot.py > /workspace/logs/telegram_bot.log 2>&1 &"))
time.sleep(3)

print("\n=== 6. Checking processes ===")
processes = run_ssh("ps aux | grep python | grep -E 'server.py|uvicorn|bot.py' | grep -v grep")
print(processes)

print("\n=== 7. Backend logs ===")
logs = run_ssh("tail -25 /workspace/logs/backend.log")
print(logs)

print("\n=== 8. Testing API ===")
test_result = run_ssh("""curl -X POST http://localhost:8000/generate -H 'Content-Type: application/json' -d '{"mode":"free","prompt":"beautiful sunset","style":"realism","add_face":false,"extra_params":{"steps":20,"cfg_scale":7.5}}' -w '\\nHTTP: %{http_code}\\n' -s""")
print(test_result)

print("\n✅ DEPLOYMENT COMPLETE!")
print("\nТеперь попробуй в Telegram! Если ошибка - скопируй сюда текст.")
