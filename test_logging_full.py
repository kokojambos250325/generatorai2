#!/usr/bin/env python3
"""
Полное тестирование логирования через SSH туннель
Проверяет все три режима генерации
"""
import requests
import json
import time
import sys
from pathlib import Path

# Конфигурация
BACKEND_URL = "http://localhost:8000"  # Через SSH туннель
LOG_FILE = "/workspace/logs/backend.log"  # Путь на удалённом сервере

def test_free_generation():
    """Тест режима free generation"""
    print("\n=== TEST 1: Free Generation ===")
    
    payload = {
        "mode": "free",
        "style": "realistic",
        "prompt": "beautiful woman, professional photo",
        "add_face": False,
        "extra_params": {
            "steps": 20,
            "cfg": 7.0
        }
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/generate",
            json=payload,
            timeout=120
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_free_generation_with_face():
    """Тест режима free generation с лицом"""
    print("\n=== TEST 2: Free Generation with Face ===")
    
    payload = {
        "mode": "free",
        "style": "realistic",
        "prompt": "beautiful woman in elegant dress",
        "add_face": True,
        "face_images": [
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        ],
        "extra_params": {
            "steps": 25,
            "cfg": 7.5
        }
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/generate",
            json=payload,
            timeout=120
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_nsfw_face():
    """Тест режима NSFW face"""
    print("\n=== TEST 3: NSFW Face ===")
    
    payload = {
        "style": "realistic",
        "scene_prompt": "bedroom scene, soft lighting",
        "face_images": [
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        ],
        "extra_params": {
            "steps": 30,
            "cfg": 8.0
        }
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/generate/nsfw_face",
            json=payload,
            timeout=120
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def check_backend_health():
    """Проверка доступности backend"""
    print("\n=== Checking Backend Health ===")
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Backend not available: {e}")
        return False


def main():
    print("=" * 60)
    print("LOGGING TEST SUITE")
    print("=" * 60)
    
    # Проверка доступности backend
    if not check_backend_health():
        print("\n❌ Backend is not available. Check SSH tunnel and services.")
        print("   Run: ssh -i ~/.ssh/id_ed25519 -p 25206 -L 8000:127.0.0.1:8000 -N root@38.147.83.26")
        return 1
    
    print("\n✅ Backend is available")
    
    # Запуск тестов
    results = []
    
    print("\n" + "=" * 60)
    print("Running Tests...")
    print("=" * 60)
    
    # Тест 1
    time.sleep(1)
    results.append(("Free Generation", test_free_generation()))
    
    # Тест 2
    time.sleep(2)
    results.append(("Free Gen with Face", test_free_generation_with_face()))
    
    # Тест 3
    time.sleep(2)
    results.append(("NSFW Face", test_nsfw_face()))
    
    # Результаты
    print("\n" + "=" * 60)
    print("TEST RESULTS")
    print("=" * 60)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:.<40} {status}")
    
    # Инструкции для проверки логов
    print("\n" + "=" * 60)
    print("LOG VERIFICATION")
    print("=" * 60)
    print("\nTo check logs on server, run:")
    print(f"  ssh root@38.147.83.26 -p 25206 'tail -n 50 {LOG_FILE}'")
    print("\nTo check JSON format:")
    print(f"  ssh root@38.147.83.26 -p 25206 'tail -n 10 {LOG_FILE} | jq .'")
    print("\nTo check request tracing:")
    print(f"  ssh root@38.147.83.26 -p 25206 'grep request_id {LOG_FILE} | tail -n 5'")
    
    # Финальный статус
    all_passed = all(result for _, result in results)
    if all_passed:
        print("\n✅ All tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
