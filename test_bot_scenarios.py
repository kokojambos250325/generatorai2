#!/usr/bin/env python3
"""
Test bot scenarios by calling backend API directly
"""
import asyncio
import httpx
import json

BACKEND_URL = "http://localhost:8000"

async def test_scenario_1_realism():
    """Test 1: Free generation with realism style"""
    print("\n=== TEST 1: Realism Style ===")
    
    request_data = {
        "mode": "free",
        "prompt": "beautiful mountain landscape at sunset, photorealistic",
        "style": "realism",
        "add_face": False,
        "extra_params": {
            "steps": 25,
            "cfg_scale": 7.5,
            "seed": -1
        }
    }
    
    try:
        async with httpx.AsyncClient(timeout=180.0) as client:
            print(f"Sending request to {BACKEND_URL}/generate...")
            response = await client.post(
                f"{BACKEND_URL}/generate",
                json=request_data
            )
            
            print(f"Status: {response.status_code}")
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)[:500]}")
            
            if result.get('status') == 'done' and result.get('image'):
                print("✅ SUCCESS: Image generated!")
                print(f"   Image size: {len(result['image'])} chars (base64)")
            else:
                print(f"❌ FAILED: {result.get('error', 'No image in response')}")
                
    except Exception as e:
        print(f"❌ ERROR: {e}")


async def test_scenario_2_noir():
    """Test 2: Free generation with noir style"""
    print("\n=== TEST 2: Noir Style ===")
    
    request_data = {
        "mode": "free",
        "prompt": "detective in dark alley, film noir",
        "style": "noir",
        "add_face": False,
        "extra_params": {
            "steps": 20,
            "cfg_scale": 8.0,
            "seed": 42
        }
    }
    
    try:
        async with httpx.AsyncClient(timeout=180.0) as client:
            print(f"Sending request...")
            response = await client.post(
                f"{BACKEND_URL}/generate",
                json=request_data
            )
            
            print(f"Status: {response.status_code}")
            result = response.json()
            
            if result.get('status') == 'done' and result.get('image'):
                print("✅ SUCCESS: Noir image generated!")
            else:
                print(f"❌ FAILED: {result.get('error', 'No image')}")
                
    except Exception as e:
        print(f"❌ ERROR: {e}")


async def test_scenario_3_anime():
    """Test 3: Free generation with anime style"""
    print("\n=== TEST 3: Anime Style ===")
    
    request_data = {
        "mode": "free",
        "prompt": "anime girl with blue hair, cherry blossoms",
        "style": "anime",
        "add_face": False,
        "extra_params": {
            "steps": 30,
            "cfg_scale": 7.0
        }
    }
    
    try:
        async with httpx.AsyncClient(timeout=180.0) as client:
            print(f"Sending request...")
            response = await client.post(
                f"{BACKEND_URL}/generate",
                json=request_data
            )
            
            print(f"Status: {response.status_code}")
            result = response.json()
            
            if result.get('status') == 'done' and result.get('image'):
                print("✅ SUCCESS: Anime image generated!")
            else:
                print(f"❌ FAILED: {result.get('error', 'No image')}")
                
    except Exception as e:
        print(f"❌ ERROR: {e}")


async def main():
    """Run all test scenarios"""
    print("🤖 TESTING BOT SCENARIOS via Backend API")
    print("=" * 60)
    
    # Run tests sequentially
    await test_scenario_1_realism()
    await asyncio.sleep(2)
    
    await test_scenario_2_noir()
    await asyncio.sleep(2)
    
    await test_scenario_3_anime()
    
    print("\n" + "=" * 60)
    print("✅ All tests completed!")


if __name__ == "__main__":
    asyncio.run(main())
