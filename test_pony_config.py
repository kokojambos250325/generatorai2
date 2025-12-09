"""
Test Pony Diffusion optimized configuration
"""
import asyncio
import httpx
import json

BACKEND_URL = "http://194.147.90.53:8000"

async def test_pony_realism():
    """Test realism style with Pony Diffusion optimization"""
    print("\n=== Testing Pony Diffusion Realism ===")
    
    request_data = {
        "mode": "free",
        "prompt": "beautiful woman in elegant dress, professional photo",
        "style": "realism",
        "add_face": False,
        "extra_params": {
            "seed": -1
        }
    }
    
    async with httpx.AsyncClient(timeout=180.0) as client:
        response = await client.post(
            f"{BACKEND_URL}/generate",
            json=request_data
        )
        
        result = response.json()
        
        if result.get('status') == 'done' and result.get('image'):
            print("✅ SUCCESS: Realism image generated!")
            print(f"   Image size: {len(result['image']) / 1024 / 1024:.2f} MB (base64)")
            print(f"   Task ID: {result.get('task_id')}")
        else:
            print(f"❌ FAILED: {result.get('error', 'Unknown error')}")
            print(f"   Full response: {json.dumps(result, indent=2)}")

async def test_pony_super_realism():
    """Test super_realism style with Pony high quality profile"""
    print("\n=== Testing Pony Diffusion Super Realism ===")
    
    request_data = {
        "mode": "free",
        "prompt": "stunning portrait of a young woman, natural lighting",
        "style": "super_realism",
        "add_face": False,
        "extra_params": {
            "seed": -1
        }
    }
    
    async with httpx.AsyncClient(timeout=180.0) as client:
        response = await client.post(
            f"{BACKEND_URL}/generate",
            json=request_data
        )
        
        result = response.json()
        
        if result.get('status') == 'done' and result.get('image'):
            print("✅ SUCCESS: Super realism image generated!")
            print(f"   Image size: {len(result['image']) / 1024 / 1024:.2f} MB (base64)")
            print(f"   Task ID: {result.get('task_id')}")
        else:
            print(f"❌ FAILED: {result.get('error', 'Unknown error')}")
            print(f"   Full response: {json.dumps(result, indent=2)}")

async def test_pony_anime():
    """Test anime style with Pony Diffusion"""
    print("\n=== Testing Pony Diffusion Anime ===")
    
    request_data = {
        "mode": "free",
        "prompt": "anime girl with blue hair, detailed anime art",
        "style": "anime",
        "add_face": False,
        "extra_params": {
            "seed": -1
        }
    }
    
    async with httpx.AsyncClient(timeout=180.0) as client:
        response = await client.post(
            f"{BACKEND_URL}/generate",
            json=request_data
        )
        
        result = response.json()
        
        if result.get('status') == 'done' and result.get('image'):
            print("✅ SUCCESS: Anime image generated!")
            print(f"   Image size: {len(result['image']) / 1024 / 1024:.2f} MB (base64)")
            print(f"   Task ID: {result.get('task_id')}")
        else:
            print(f"❌ FAILED: {result.get('error', 'Unknown error')}")
            print(f"   Full response: {json.dumps(result, indent=2)}")

async def main():
    """Run all tests"""
    print("=" * 60)
    print("PONY DIFFUSION OPTIMIZATION TESTS")
    print("=" * 60)
    print("\nExpected settings:")
    print("  - CFG: 5.0 (Pony optimized)")
    print("  - Sampler: DPM++ SDE Karras / DPM++ 2M Karras")
    print("  - Steps: 30+ (balanced) or 40+ (high quality)")
    print("  - Score-based prompts: score_9, score_8_up, score_7_up")
    print("  - Resolution: 832x1216 / 896x1152")
    
    await test_pony_realism()
    await test_pony_super_realism()
    await test_pony_anime()
    
    print("\n" + "=" * 60)
    print("TESTS COMPLETED")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
