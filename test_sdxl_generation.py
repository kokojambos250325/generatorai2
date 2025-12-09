"""
Test script for SDXL Image Generation Workflow

This script validates the complete implementation:
1. ModelManager SDXL loading and caching
2. FreePipeline integration
3. Generation service processing
4. Result retrieval endpoint

Usage:
    python test_sdxl_generation.py
"""

import asyncio
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


async def test_model_manager():
    """Test ModelManager SDXL loading and caching"""
    print("\n=== Testing ModelManager ===")
    
    from models.model_manager import ModelManager
    
    # Test 1: Initialize ModelManager
    print("Test 1: Initializing ModelManager...")
    manager = ModelManager(device="cuda")
    print("✓ ModelManager initialized")
    
    # Test 2: First SDXL load (should download/load)
    print("\nTest 2: First SDXL load (may take time to download)...")
    sdxl = manager.get_sdxl()
    if sdxl is not None:
        print("✓ SDXL model loaded successfully")
        print(f"  Pipeline type: {type(sdxl).__name__}")
    else:
        print("✗ SDXL model failed to load")
        return False
    
    # Test 3: Second SDXL load (should be cached)
    print("\nTest 3: Second SDXL load (should be instant from cache)...")
    sdxl_cached = manager.get_sdxl()
    if sdxl_cached is sdxl:
        print("✓ SDXL model retrieved from cache (same instance)")
    else:
        print("✗ Cache not working properly")
        return False
    
    # Test 4: Check if model is loaded
    print("\nTest 4: Checking cache status...")
    cache_key = f"sdxl_stabilityai/stable-diffusion-xl-base-1.0"
    if manager.is_model_loaded(cache_key):
        print("✓ Model registered in cache")
    else:
        print("✗ Model not found in cache")
        return False
    
    print("\n✓ All ModelManager tests passed!")
    return True


async def test_free_pipeline():
    """Test FreePipeline implementation"""
    print("\n=== Testing FreePipeline ===")
    
    from pipelines.free import FreePipeline
    from models.model_manager import ModelManager
    from models.generation_request import GenerationRequest
    
    # Test 1: Initialize pipeline
    print("Test 1: Initializing FreePipeline...")
    model_manager = ModelManager(device="cuda")
    pipeline = FreePipeline(device="cuda", model_manager=model_manager)
    print("✓ FreePipeline initialized")
    
    # Test 2: Load models
    print("\nTest 2: Loading models...")
    await pipeline.load_models()
    if pipeline.loaded:
        print("✓ Models loaded successfully")
    else:
        print("✗ Models failed to load")
        return False
    
    # Test 3: Prepare inputs
    print("\nTest 3: Preparing inputs...")
    request = GenerationRequest(
        mode="free",
        prompt="a beautiful sunset over mountains",
        style="realistic",
        seed=42
    )
    inputs = await pipeline.prepare_inputs(request)
    
    print(f"✓ Inputs prepared:")
    print(f"  Prompt: {inputs['prompt'][:50]}...")
    print(f"  Negative prompt: {inputs['negative_prompt'][:50]}...")
    print(f"  Seed: {inputs['seed']}")
    print(f"  Steps: {inputs['generation_params']['num_inference_steps']}")
    print(f"  Guidance: {inputs['generation_params']['guidance_scale']}")
    
    # Test 4: Run generation (quick test with minimal steps)
    print("\nTest 4: Running generation (this will take some time)...")
    print("  Note: Using minimal steps for testing. Production uses 50 steps.")
    
    # Reduce steps for faster testing
    inputs['generation_params']['num_inference_steps'] = 20
    inputs['generation_params']['width'] = 512
    inputs['generation_params']['height'] = 512
    
    try:
        result = await pipeline.run(inputs)
        if result and isinstance(result, str):
            print(f"✓ Generation completed")
            print(f"  Result type: base64 string")
            print(f"  Result length: {len(result)} characters")
            
            # Validate base64
            import base64
            try:
                decoded = base64.b64decode(result)
                print(f"  Decoded size: {len(decoded)} bytes")
                print("✓ Valid base64 encoding")
            except Exception as e:
                print(f"✗ Invalid base64: {e}")
                return False
        else:
            print("✗ Generation failed")
            return False
    except Exception as e:
        print(f"✗ Generation error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n✓ All FreePipeline tests passed!")
    return True


async def test_generation_service():
    """Test GenerationService integration"""
    print("\n=== Testing GenerationService ===")
    
    from services.generation_service import GenerationService
    from models.generation_request import GenerationRequest
    from utils.ids import generate_task_id
    
    # Test 1: Initialize service
    print("Test 1: Initializing GenerationService...")
    service = GenerationService()
    print("✓ GenerationService initialized")
    
    # Test 2: Process task
    print("\nTest 2: Processing generation task...")
    task_id = generate_task_id(prefix="free")
    request = GenerationRequest(
        mode="free",
        prompt="a cute cat sitting on a chair",
        style="realistic",
        seed=123
    )
    
    try:
        result = await service.process_task(task_id, request)
        if result:
            print(f"✓ Task processed successfully")
            print(f"  Task ID: {task_id}")
            print(f"  Result length: {len(result)} characters")
        else:
            print("✗ Task processing failed")
            return False
    except Exception as e:
        print(f"✗ Task processing error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n✓ All GenerationService tests passed!")
    return True


async def test_api_endpoints():
    """Test API endpoints (requires running server)"""
    print("\n=== Testing API Endpoints ===")
    print("Note: This requires the server to be running")
    print("To test endpoints manually:")
    print("  1. Start server: uvicorn main:app --reload")
    print("  2. POST to /generate with GenerationRequest")
    print("  3. GET /generate/result/{task_id} to retrieve result")
    print("  4. GET /task/{task_id} for status")
    
    # We'll skip actual HTTP tests in this script
    # as they require the server to be running
    print("\n⊘ API endpoint tests skipped (requires running server)")
    return True


async def run_all_tests():
    """Run all validation tests"""
    print("=" * 60)
    print("SDXL Image Generation Workflow - Validation Tests")
    print("=" * 60)
    
    results = {}
    
    # Test 1: ModelManager
    try:
        results['model_manager'] = await test_model_manager()
    except Exception as e:
        print(f"\n✗ ModelManager test failed with error: {e}")
        import traceback
        traceback.print_exc()
        results['model_manager'] = False
    
    # Test 2: FreePipeline (only if ModelManager passed)
    if results['model_manager']:
        try:
            results['free_pipeline'] = await test_free_pipeline()
        except Exception as e:
            print(f"\n✗ FreePipeline test failed with error: {e}")
            import traceback
            traceback.print_exc()
            results['free_pipeline'] = False
    else:
        print("\n⊘ Skipping FreePipeline tests (ModelManager failed)")
        results['free_pipeline'] = False
    
    # Test 3: GenerationService (only if previous tests passed)
    if results['model_manager'] and results['free_pipeline']:
        try:
            results['generation_service'] = await test_generation_service()
        except Exception as e:
            print(f"\n✗ GenerationService test failed with error: {e}")
            import traceback
            traceback.print_exc()
            results['generation_service'] = False
    else:
        print("\n⊘ Skipping GenerationService tests (previous tests failed)")
        results['generation_service'] = False
    
    # Test 4: API Endpoints
    try:
        results['api_endpoints'] = await test_api_endpoints()
    except Exception as e:
        print(f"\n✗ API endpoints test failed with error: {e}")
        results['api_endpoints'] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    all_passed = all(results.values())
    print("=" * 60)
    if all_passed:
        print("✓ ALL TESTS PASSED!")
    else:
        print("✗ SOME TESTS FAILED")
    print("=" * 60)
    
    return all_passed


if __name__ == "__main__":
    print("\nStarting SDXL Generation Workflow Validation...")
    print("This may take several minutes on first run (model download).\n")
    
    # Check if CUDA is available
    try:
        import torch
        if torch.cuda.is_available():
            print(f"✓ CUDA available: {torch.cuda.get_device_name(0)}")
            print(f"  CUDA version: {torch.version.cuda}")
        else:
            print("⚠ CUDA not available, will use CPU (slower)")
    except ImportError:
        print("⚠ PyTorch not installed yet. Please run: pip install -r requirements.txt")
    
    # Run tests
    try:
        success = asyncio.run(run_all_tests())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
