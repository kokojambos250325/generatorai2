"""
Direct API test - bypass Telegram bot
"""
import asyncio
import httpx
import json

async def test_generation():
    """Test generation API directly"""
    
    # Test request
    request_data = {
        "mode": "free",
        "prompt": "beautiful sunset over mountains, photorealistic",
        "style": "realism",
        "add_face": False,
        "extra_params": {
            "steps": 26,
            "cfg_scale": 7.5,
            "seed": -1
        }
    }
    
    print("=" * 60)
    print("DIRECT API TEST")
    print("=" * 60)
    print(f"Request: {json.dumps(request_data, indent=2)}")
    print("\nSending to backend...")
    
    try:
        # Use SSH tunnel or direct connection
        # Assuming port forwarding: ssh -L 8000:localhost:8000 runpod
        async with httpx.AsyncClient(timeout=180.0) as client:
            response = await client.post(
                "http://localhost:8000/generate",
                json=request_data
            )
            
            print(f"\nStatus Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"Response Status: {result.get('status')}")
                
                if result.get('status') == 'done':
                    print("✅ SUCCESS!")
                    print(f"Image data length: {len(result.get('image', ''))} chars")
                    print(f"Task ID: {result.get('task_id')}")
                else:
                    print(f"❌ FAILED: {result.get('error')}")
            else:
                print(f"❌ HTTP ERROR: {response.status_code}")
                print(f"Response: {response.text}")
    
    except httpx.ConnectError as e:
        print(f"❌ CONNECTION ERROR: {e}")
        print("\nHint: Make sure to set up SSH port forwarding:")
        print("  ssh -L 8000:localhost:8000 runpod")
    
    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(test_generation())
