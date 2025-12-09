"""
Local testing script for RunPod handler
Tests without deploying to cloud
"""
import requests
import json
import base64
import time
from pathlib import Path

# Configuration
API_URL = "http://localhost:8000"

def test_basic_generation():
    """Test basic text-to-image generation"""
    print("\n" + "="*60)
    print("Test 1: Basic Text-to-Image Generation")
    print("="*60)
    
    payload = {
        "input": {
            "mode": "free",
            "params": {
                "prompt": "beautiful landscape, mountains, sunset, photorealistic, 8k",
                "negative_prompt": "ugly, blurry, low quality",
                "width": 512,
                "height": 512,
                "steps": 20,
                "cfg_scale": 7.5,
                "seed": 42
            }
        }
    }
    
    print("Sending request...")
    start_time = time.time()
    
    response = requests.post(
        f"{API_URL}/runsync",
        json=payload,
        timeout=300
    )
    
    elapsed = time.time() - start_time
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Success in {elapsed:.2f}s")
        print(f"Status: {result.get('status')}")
        
        if 'image' in result:
            # Save image
            image_data = base64.b64decode(result['image'])
            output_path = Path("output_test_basic.png")
            output_path.write_bytes(image_data)
            print(f"💾 Image saved: {output_path}")
            print(f"📊 Size: {len(image_data) / 1024:.2f} KB")
        
        return True
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.text)
        return False


def test_face_swap():
    """Test face swap (requires source and target images)"""
    print("\n" + "="*60)
    print("Test 2: Face Swap")
    print("="*60)
    
    # This is a placeholder - you would need actual images
    payload = {
        "input": {
            "mode": "face_swap",
            "params": {
                "source_image": "base64_encoded_source_image",
                "target_image": "base64_encoded_target_image"
            }
        }
    }
    
    print("⚠️  Skipped: Requires actual face images")
    print("To test: provide base64 encoded images in params")
    return True


def test_error_handling():
    """Test error handling with invalid input"""
    print("\n" + "="*60)
    print("Test 3: Error Handling")
    print("="*60)
    
    payload = {
        "input": {
            "mode": "invalid_mode",
            "params": {}
        }
    }
    
    print("Sending invalid request...")
    
    response = requests.post(
        f"{API_URL}/runsync",
        json=payload,
        timeout=30
    )
    
    result = response.json()
    
    if result.get('status') == 'error':
        print("✅ Error handling works correctly")
        print(f"Error: {result.get('error')}")
        return True
    else:
        print("❌ Should have returned error")
        return False


def check_server():
    """Check if local server is running"""
    print("\n" + "="*60)
    print("Checking Local Server")
    print("="*60)
    
    try:
        response = requests.get(f"{API_URL}/", timeout=5)
        print("✅ Server is running")
        return True
    except requests.exceptions.ConnectionError:
        print("❌ Server is not running")
        print("\nStart the server with:")
        print("  python handler.py --rp_serve_api")
        return False


if __name__ == "__main__":
    print("="*60)
    print("RunPod Handler Local Testing")
    print("="*60)
    
    # Check server
    if not check_server():
        exit(1)
    
    # Run tests
    tests = [
        ("Basic Generation", test_basic_generation),
        ("Face Swap", test_face_swap),
        ("Error Handling", test_error_handling),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test crashed: {e}")
            failed += 1
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print("="*60)
