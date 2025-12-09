"""
RunPod Serverless API Client
Отправка запросов к вашему Serverless endpoint
"""

import os
import runpod
import base64
import json
from pathlib import Path

# Настройка API ключа
RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY", "")
ENDPOINT_ID = os.getenv("ENDPOINT_ID", "")  # Вставьте ID вашего endpoint

runpod.api_key = RUNPOD_API_KEY


def test_sync_request():
    """Синхронный запрос - ждёт завершения и возвращает результат"""
    print("=" * 60)
    print("SYNC REQUEST (/runsync)")
    print("=" * 60)
    
    if not ENDPOINT_ID:
        print("❌ Error: ENDPOINT_ID not set!")
        print("Set it with: $env:ENDPOINT_ID='your-endpoint-id'")
        return
    
    endpoint = runpod.Endpoint(ENDPOINT_ID)
    
    try:
        print("Submitting job...")
        result = endpoint.run_sync(
            {
                "mode": "free",
                "params": {
                    "prompt": "beautiful sunset over mountains, photorealistic, 8k",
                    "negative_prompt": "ugly, blurry, low quality",
                    "width": 1024,
                    "height": 1024,
                    "steps": 30,
                    "cfg_scale": 7.5,
                    "seed": 42
                }
            },
            timeout=300  # 5 минут timeout
        )
        
        print("\n✅ Job completed!")
        print(f"Status: {result.get('status')}")
        
        if result.get('status') == 'success':
            # Сохраняем изображение
            image_b64 = result.get('image')
            if image_b64:
                image_bytes = base64.b64decode(image_b64)
                output_path = Path("output_sync.png")
                output_path.write_bytes(image_bytes)
                print(f"✅ Image saved to: {output_path.absolute()}")
                print(f"Size: {len(image_bytes)} bytes")
        else:
            print(f"❌ Error: {result.get('error')}")
            
    except TimeoutError:
        print("❌ Job timed out after 5 minutes")
    except Exception as e:
        print(f"❌ Error: {e}")


def test_async_request():
    """Асинхронный запрос - возвращает job ID, нужно проверять статус"""
    print("\n" + "=" * 60)
    print("ASYNC REQUEST (/run)")
    print("=" * 60)
    
    if not ENDPOINT_ID:
        print("❌ Error: ENDPOINT_ID not set!")
        return
    
    endpoint = runpod.Endpoint(ENDPOINT_ID)
    
    try:
        print("Submitting job...")
        job = endpoint.run(
            {
                "mode": "free",
                "params": {
                    "prompt": "anime style girl with blue hair, detailed, high quality",
                    "width": 1024,
                    "height": 1024,
                    "steps": 25,
                    "seed": 123
                }
            }
        )
        
        job_id = job.get('id')
        print(f"✅ Job submitted: {job_id}")
        print(f"Status: {job.get('status')}")
        
        # Проверяем статус
        print("\nChecking status...")
        status = endpoint.status(job_id)
        print(f"Current status: {status.get('status')}")
        
        # Ждём завершения (опционально)
        print("\nWaiting for completion...")
        result = job.result(timeout=300)
        
        print("\n✅ Job completed!")
        
        if result.get('status') == 'success':
            image_b64 = result.get('image')
            if image_b64:
                image_bytes = base64.b64decode(image_b64)
                output_path = Path("output_async.png")
                output_path.write_bytes(image_bytes)
                print(f"✅ Image saved to: {output_path.absolute()}")
        else:
            print(f"❌ Error: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ Error: {e}")


def test_face_swap():
    """Пример Face Swap запроса"""
    print("\n" + "=" * 60)
    print("FACE SWAP REQUEST")
    print("=" * 60)
    
    if not ENDPOINT_ID:
        print("❌ Error: ENDPOINT_ID not set!")
        return
    
    # Загружаем тестовые изображения (если есть)
    source_path = Path("test_source.jpg")
    target_path = Path("test_target.jpg")
    
    if not source_path.exists() or not target_path.exists():
        print("⚠️  Need test images: test_source.jpg and test_target.jpg")
        return
    
    # Кодируем в base64
    source_b64 = base64.b64encode(source_path.read_bytes()).decode('utf-8')
    target_b64 = base64.b64encode(target_path.read_bytes()).decode('utf-8')
    
    endpoint = runpod.Endpoint(ENDPOINT_ID)
    
    try:
        print("Submitting face swap job...")
        result = endpoint.run_sync(
            {
                "mode": "face_swap",
                "params": {
                    "source_image": source_b64,
                    "target_image": target_b64,
                    "face_restore_strength": 0.8
                }
            },
            timeout=300
        )
        
        print("\n✅ Face swap completed!")
        
        if result.get('status') == 'success':
            image_b64 = result.get('image')
            if image_b64:
                image_bytes = base64.b64decode(image_b64)
                output_path = Path("output_face_swap.png")
                output_path.write_bytes(image_bytes)
                print(f"✅ Image saved to: {output_path.absolute()}")
        else:
            print(f"❌ Error: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ Error: {e}")


def check_health():
    """Проверка здоровья endpoint"""
    print("\n" + "=" * 60)
    print("ENDPOINT HEALTH CHECK")
    print("=" * 60)
    
    if not ENDPOINT_ID:
        print("❌ Error: ENDPOINT_ID not set!")
        return
    
    endpoint = runpod.Endpoint(ENDPOINT_ID)
    
    try:
        health = endpoint.health()
        print(f"✅ Endpoint is healthy!")
        print(f"Workers: {health.get('workers', {})}")
        print(f"Jobs: {health.get('jobs', {})}")
        
    except Exception as e:
        print(f"❌ Health check failed: {e}")


if __name__ == "__main__":
    print("RunPod Serverless API Client")
    print(f"API Key: {RUNPOD_API_KEY[:20]}...")
    print(f"Endpoint ID: {ENDPOINT_ID or 'NOT SET'}")
    
    if not ENDPOINT_ID:
        print("\n⚠️  Please set ENDPOINT_ID first:")
        print("PowerShell: $env:ENDPOINT_ID='your-endpoint-id'")
        print("Bash: export ENDPOINT_ID='your-endpoint-id'")
        exit(1)
    
    # Меню
    print("\n" + "=" * 60)
    print("Choose test:")
    print("1. Sync request (text-to-image)")
    print("2. Async request (text-to-image)")
    print("3. Face swap")
    print("4. Health check")
    print("5. All tests")
    print("=" * 60)
    
    choice = input("Enter choice (1-5): ").strip()
    
    if choice == "1":
        test_sync_request()
    elif choice == "2":
        test_async_request()
    elif choice == "3":
        test_face_swap()
    elif choice == "4":
        check_health()
    elif choice == "5":
        check_health()
        test_sync_request()
        test_async_request()
    else:
        print("Invalid choice")
