"""
Test script for all backend and GPU endpoints
"""
import httpx
import base64
import json
import asyncio
from io import BytesIO
from PIL import Image

# Create a simple test image (1x1 pixel PNG)
def create_test_image_base64():
    img = Image.new('RGB', (512, 512), color='red')
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    img_bytes = buffer.getvalue()
    return base64.b64encode(img_bytes).decode('utf-8')

BASE_URL = "http://localhost:8000"
GPU_URL = "http://localhost:3000/api"

async def test_backend_health():
    """Test backend health endpoint"""
    print("\n=== Testing Backend Health ===")
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{BASE_URL}/health")
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                print("✅ Backend is healthy")
                return True
            else:
                print(f"❌ Backend health check failed: {response.text}")
                return False
    except Exception as e:
        print(f"❌ Backend health check error: {e}")
        return False

async def test_gpu_health():
    """Test GPU server health endpoint"""
    print("\n=== Testing GPU Server Health ===")
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{GPU_URL}/health")
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                print("✅ GPU Server is healthy")
                return True
            else:
                print(f"❌ GPU Server health check failed: {response.text}")
                return False
    except Exception as e:
        print(f"❌ GPU Server health check error: {e}")
        return False

async def test_free_generation():
    """Test free generation endpoint"""
    print("\n=== Testing Free Generation ===")
    try:
        test_image = create_test_image_base64()
        payload = {
            "mode": "free",
            "prompt": "a beautiful landscape, mountains, sunset",
            "style": "realism",
            "add_face": False,
            "seed": 42
        }
        async with httpx.AsyncClient(timeout=180.0) as client:
            response = await client.post(f"{BASE_URL}/generate", json=payload)
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                if result.get("status") == "done" and result.get("image"):
                    print("✅ Free generation successful")
                    return True
                else:
                    print(f"❌ Free generation failed: {result}")
                    return False
            else:
                print(f"❌ Free generation error: {response.text}")
                return False
    except Exception as e:
        print(f"❌ Free generation exception: {e}")
        return False

async def test_clothes_removal():
    """Test clothes removal endpoint"""
    print("\n=== Testing Clothes Removal ===")
    try:
        test_image = create_test_image_base64()
        payload = {
            "mode": "clothes_removal",
            "target_image": test_image,
            "style": "realism",
            "controlnet_strength": 0.8,
            "inpaint_denoise": 0.75,
            "segmentation_threshold": 0.7,
            "seed": 42
        }
        async with httpx.AsyncClient(timeout=180.0) as client:
            response = await client.post(f"{BASE_URL}/generate/clothes_removal", json=payload)
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                if result.get("status") == "done" and result.get("image"):
                    print("✅ Clothes removal successful")
                    return True
                else:
                    print(f"❌ Clothes removal failed: {result}")
                    return False
            else:
                print(f"❌ Clothes removal error: {response.text}")
                return False
    except Exception as e:
        print(f"❌ Clothes removal exception: {e}")
        return False

async def test_gpu_submit_task():
    """Test GPU server task submission"""
    print("\n=== Testing GPU Server Task Submission ===")
    try:
        test_image = create_test_image_base64()
        payload = {
            "mode": "clothes_removal",
            "image": test_image,
            "style": "realism",
            "seed": 42
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(f"{GPU_URL}/generate", json=payload)
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                task_id = result.get("task_id")
                if task_id:
                    print(f"✅ Task submitted: {task_id}")
                    # Check status
                    status_response = await client.get(f"{GPU_URL}/task/{task_id}")
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        print(f"✅ Task status: {status_data.get('status')}")
                        return True
                else:
                    print(f"❌ No task_id in response: {result}")
                    return False
            else:
                print(f"❌ Task submission error: {response.text}")
                return False
    except Exception as e:
        print(f"❌ Task submission exception: {e}")
        return False

async def main():
    """Run all tests"""
    print("🚀 Starting comprehensive endpoint tests...")
    
    results = {}
    
    # Health checks
    results["backend_health"] = await test_backend_health()
    results["gpu_health"] = await test_gpu_health()
    
    # Endpoint tests
    results["free_generation"] = await test_free_generation()
    results["clothes_removal"] = await test_clothes_removal()
    results["gpu_submit"] = await test_gpu_submit_task()
    
    # Summary
    print("\n" + "="*50)
    print("📊 TEST SUMMARY")
    print("="*50)
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:30} {status}")
    
    total = len(results)
    passed = sum(results.values())
    print(f"\nTotal: {total}, Passed: {passed}, Failed: {total - passed}")

if __name__ == "__main__":
    asyncio.run(main())

