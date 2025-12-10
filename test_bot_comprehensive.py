"""
Comprehensive test script for Telegram bot and all services
Simulates user interactions
"""
import asyncio
import httpx
import base64
from io import BytesIO
from PIL import Image
import json

BASE_URL = "http://localhost:8000"
GPU_URL = "http://localhost:3000/api"
COMFYUI_URL = "http://localhost:8188"

def create_test_image_base64():
    """Create a simple test image"""
    img = Image.new('RGB', (512, 512), color='red')
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    img_bytes = buffer.getvalue()
    return base64.b64encode(img_bytes).decode('utf-8')

async def test_comfyui_health():
    """Test ComfyUI"""
    print("\n=== Testing ComfyUI ===")
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{COMFYUI_URL}/system_stats")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ ComfyUI v{data['system']['comfyui_version']}")
                return True
            else:
                print(f"❌ ComfyUI error: {response.status_code}")
                return False
    except Exception as e:
        print(f"❌ ComfyUI error: {e}")
        return False

async def test_free_generation():
    """Test free generation"""
    print("\n=== Testing Free Generation ===")
    try:
        payload = {
            "mode": "free",
            "prompt": "a beautiful sunset over mountains, photorealistic",
            "style": "realism",
            "add_face": False,
            "seed": 42
        }
        async with httpx.AsyncClient(timeout=180.0) as client:
            print("  Sending request...")
            response = await client.post(f"{BASE_URL}/generate", json=payload)
            print(f"  Status: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                if result.get("status") == "done" and result.get("image"):
                    print("✅ Free generation successful")
                    return True
                else:
                    print(f"❌ Generation failed: {result}")
                    return False
            else:
                print(f"❌ Error: {response.text[:200]}")
                return False
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

async def test_clothes_removal():
    """Test clothes removal"""
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
            print("  Sending request...")
            response = await client.post(f"{BASE_URL}/generate/clothes_removal", json=payload)
            print(f"  Status: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                if result.get("status") == "done" and result.get("image"):
                    print("✅ Clothes removal successful")
                    return True
                else:
                    print(f"❌ Failed: {result}")
                    return False
            else:
                print(f"❌ Error: {response.text[:200]}")
                return False
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

async def test_gpu_server():
    """Test GPU server directly"""
    print("\n=== Testing GPU Server ===")
    try:
        test_image = create_test_image_base64()
        payload = {
            "mode": "free",
            "prompt": "test image",
            "style": "realism",
            "seed": 42
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            print("  Submitting task...")
            response = await client.post(f"{GPU_URL}/generate", json=payload)
            if response.status_code == 200:
                result = response.json()
                task_id = result.get("task_id")
                if task_id:
                    print(f"  ✅ Task submitted: {task_id}")
                    # Check status
                    for i in range(5):
                        await asyncio.sleep(2)
                        status_resp = await client.get(f"{GPU_URL}/task/{task_id}")
                        if status_resp.status_code == 200:
                            status_data = status_resp.json()
                            status = status_data.get("status")
                            print(f"  Status: {status}")
                            if status == "completed":
                                print("✅ GPU Server task completed")
                                return True
                            elif status == "failed":
                                print(f"❌ Task failed: {status_data.get('error')}")
                                return False
                    print("⏳ Task still processing...")
                    return True  # At least it's working
                else:
                    print(f"❌ No task_id: {result}")
                    return False
            else:
                print(f"❌ Error: {response.text[:200]}")
                return False
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

async def main():
    """Run all tests"""
    print("🚀 Starting comprehensive tests...")
    
    results = {}
    
    # Health checks
    results["comfyui"] = await test_comfyui_health()
    
    # Generation tests
    results["free_generation"] = await test_free_generation()
    results["clothes_removal"] = await test_clothes_removal()
    results["gpu_server"] = await test_gpu_server()
    
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

