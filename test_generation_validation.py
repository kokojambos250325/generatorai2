"""
System Validation Test
Tests free_generation with different styles and validates quality parameters.
"""
import httpx
import asyncio
import base64
import json
import time
from pathlib import Path
from datetime import datetime


# Backend API URL
BACKEND_URL = "http://localhost:8000"

# Test prompts for different styles
TEST_PROMPTS = {
    "noir": "elegant woman in 1940s style hat, dramatic lighting, film noir aesthetic, vintage black and white photography",
    "super_realism": "portrait of a young woman with natural skin, professional photography, soft natural lighting, 8k uhd, high detail",
    "anime": "anime girl with long blue hair, school uniform, cherry blossoms falling, detailed anime art style, vibrant colors"
}

# Test parameters
VALIDATION_CFG = 9.5
VALIDATION_STEPS = 28


async def test_style_generation(style: str, prompt: str, index: int):
    """
    Test image generation for specific style
    
    Args:
        style: Style name (noir, super_realism, anime)
        prompt: Text prompt
        index: Test index (1-5)
    
    Returns:
        dict: Test result with metadata
    """
    print(f"\n{'='*60}")
    print(f"Test #{index}: Style={style}")
    print(f"{'='*60}")
    print(f"Prompt: {prompt}")
    
    # Prepare request
    request_data = {
        "mode": "free",
        "prompt": prompt,
        "style": style,
        "add_face": False,
        "extra_params": {
            "steps": VALIDATION_STEPS,
            "cfg_scale": VALIDATION_CFG,
            "seed": -1  # Random seed for variety
        }
    }
    
    print(f"\nRequest params:")
    print(f"  - steps: {VALIDATION_STEPS}")
    print(f"  - cfg_scale: {VALIDATION_CFG}")
    print(f"  - style: {style}")
    
    start_time = time.time()
    
    try:
        async with httpx.AsyncClient(timeout=180.0) as client:
            print(f"\nSending request to {BACKEND_URL}/generate...")
            response = await client.post(
                f"{BACKEND_URL}/generate",
                json=request_data
            )
            
            response.raise_for_status()
            result = response.json()
            
            elapsed_time = time.time() - start_time
            
            if result['status'] == 'done' and result['image']:
                print(f"✅ Generation SUCCESS (took {elapsed_time:.1f}s)")
                
                # Save image
                output_dir = Path("test_outputs")
                output_dir.mkdir(exist_ok=True)
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{style}_{index}_{timestamp}.png"
                filepath = output_dir / filename
                
                image_data = base64.b64decode(result['image'])
                with open(filepath, 'wb') as f:
                    f.write(image_data)
                
                print(f"💾 Saved to: {filepath}")
                print(f"📊 Image size: {len(image_data) / 1024:.1f} KB")
                
                return {
                    "success": True,
                    "style": style,
                    "index": index,
                    "elapsed_time": elapsed_time,
                    "filepath": str(filepath),
                    "image_size_kb": len(image_data) / 1024,
                    "request_params": {
                        "steps": VALIDATION_STEPS,
                        "cfg_scale": VALIDATION_CFG
                    }
                }
            else:
                error_msg = result.get('error', 'Unknown error')
                print(f"❌ Generation FAILED: {error_msg}")
                return {
                    "success": False,
                    "style": style,
                    "index": index,
                    "error": error_msg
                }
    
    except httpx.TimeoutException:
        print(f"❌ TIMEOUT after {time.time() - start_time:.1f}s")
        return {
            "success": False,
            "style": style,
            "index": index,
            "error": "Timeout"
        }
    
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return {
            "success": False,
            "style": style,
            "index": index,
            "error": str(e)
        }


async def run_validation_tests():
    """Run complete validation test suite"""
    print("\n" + "="*60)
    print("SYSTEM VALIDATION TEST")
    print("="*60)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Validation params: steps={VALIDATION_STEPS}, cfg={VALIDATION_CFG}")
    print("="*60)
    
    all_results = []
    
    # Test each style
    for style, base_prompt in TEST_PROMPTS.items():
        print(f"\n\n{'#'*60}")
        print(f"# Testing Style: {style.upper()}")
        print(f"{'#'*60}")
        
        # Generate 5 images per style
        for i in range(1, 6):
            result = await test_style_generation(style, base_prompt, i)
            all_results.append(result)
            
            # Small delay between generations
            if i < 5:
                print("\nWaiting 3 seconds before next generation...")
                await asyncio.sleep(3)
    
    # Print summary
    print("\n\n" + "="*60)
    print("VALIDATION SUMMARY")
    print("="*60)
    
    successful = [r for r in all_results if r['success']]
    failed = [r for r in all_results if not r['success']]
    
    print(f"\n📊 Total tests: {len(all_results)}")
    print(f"✅ Successful: {len(successful)}")
    print(f"❌ Failed: {len(failed)}")
    
    if successful:
        avg_time = sum(r['elapsed_time'] for r in successful) / len(successful)
        avg_size = sum(r['image_size_kb'] for r in successful) / len(successful)
        print(f"\n⏱️  Average generation time: {avg_time:.1f}s")
        print(f"📦 Average image size: {avg_size:.1f} KB")
    
    # Group by style
    print(f"\n📋 Results by style:")
    for style in TEST_PROMPTS.keys():
        style_results = [r for r in all_results if r['style'] == style]
        style_success = [r for r in style_results if r['success']]
        print(f"  {style}: {len(style_success)}/5 successful")
    
    if failed:
        print(f"\n⚠️  Failed tests:")
        for r in failed:
            print(f"  - {r['style']} #{r['index']}: {r['error']}")
    
    # Save detailed report
    report_file = Path("test_outputs") / "validation_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "total_tests": len(all_results),
            "successful": len(successful),
            "failed": len(failed),
            "validation_params": {
                "steps": VALIDATION_STEPS,
                "cfg_scale": VALIDATION_CFG
            },
            "results": all_results
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 Detailed report saved to: {report_file}")
    
    return len(failed) == 0


if __name__ == "__main__":
    success = asyncio.run(run_validation_tests())
    exit(0 if success else 1)
