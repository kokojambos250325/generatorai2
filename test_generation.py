#!/usr/bin/env python3
"""
Test generation with new workflows
"""
import httpx
import json
import base64
import sys

BACKEND_URL = "http://127.0.0.1:8000"

def test_free_generation():
    """Test free_generation workflow"""
    print("=" * 60)
    print("Test 1: Free Generation (noir style)")
    print("=" * 60)
    
    request = {
        "mode": "free",
        "prompt": "beautiful woman on the beach at sunset",
        "style": "noir",
        "extra_params": {
            "quality_profile": "balanced",
            "seed": 42
        }
    }
    
    try:
        with httpx.Client(timeout=180.0) as client:
            response = client.post(
                f"{BACKEND_URL}/generate",
                json=request
            )
            
            print(f"Status Code: {response.status_code}")
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)[:500]}...")
            
            if result.get("status") == "done" and result.get("image"):
                print("✅ SUCCESS: Image generated")
                return True
            else:
                print(f"❌ FAILED: {result.get('error', 'Unknown error')}")
                return False
                
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def test_health():
    """Test backend health"""
    print("=" * 60)
    print("Test 0: Backend Health Check")
    print("=" * 60)
    
    try:
        with httpx.Client(timeout=5.0) as client:
            response = client.get(f"{BACKEND_URL}/health")
            print(f"Status Code: {response.status_code}")
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
            return response.status_code == 200
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


if __name__ == "__main__":
    print("\n🧪 Testing Generation Workflows\n")
    
    # Test health
    if not test_health():
        print("\n❌ Backend is not healthy. Exiting.")
        sys.exit(1)
    
    print("\n")
    
    # Test free generation
    success = test_free_generation()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ Test completed successfully")
    else:
        print("❌ Test failed")
    print("=" * 60)

