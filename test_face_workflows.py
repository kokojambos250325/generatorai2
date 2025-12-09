#!/usr/bin/env python3
"""
Test Script for Face-Integrated Generation Modes

Tests the implementation of three new generation modes:
1. Free Generation with Face
2. Enhanced Clothes Removal
3. NSFW with Face

Usage:
    python test_face_workflows.py
"""

import asyncio
import base64
import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))


async def test_workflow_loading():
    """Test that all workflow JSON files can be loaded"""
    print("=" * 60)
    print("TEST 1: Workflow JSON Loading")
    print("=" * 60)
    
    workflows = [
        "gpu_server/workflows/free_generation_face.json",
        "gpu_server/workflows/clothes_removal.json",
        "gpu_server/workflows/nsfw_face.json"
    ]
    
    for workflow_path in workflows:
        try:
            with open(workflow_path, 'r') as f:
                workflow = json.load(f)
            
            print(f"✓ {workflow_path}: Loaded successfully")
            print(f"  - Node count: {len(workflow)}")
            print(f"  - Node IDs: {', '.join(workflow.keys())}")
        except Exception as e:
            print(f"✗ {workflow_path}: Failed to load - {e}")
            return False
    
    print("\n✓ All workflows loaded successfully\n")
    return True


async def test_workflow_adapters():
    """Test that workflow adapters can be instantiated"""
    print("=" * 60)
    print("TEST 2: Workflow Adapter Initialization")
    print("=" * 60)
    
    try:
        from gpu_server.workflow_adapter import (
            FreeGenerationFaceAdapter,
            ClothesRemovalEnhancedAdapter,
            NSFWFaceAdapter,
            get_adapter
        )
        
        # Test direct instantiation
        adapters_to_test = [
            ("FreeGenerationFaceAdapter", FreeGenerationFaceAdapter),
            ("ClothesRemovalEnhancedAdapter", ClothesRemovalEnhancedAdapter),
            ("NSFWFaceAdapter", NSFWFaceAdapter)
        ]
        
        for name, adapter_class in adapters_to_test:
            try:
                adapter = adapter_class(workflow_dir="gpu_server/workflows")
                print(f"✓ {name}: Instantiated successfully")
                print(f"  - Workflow file: {adapter.get_workflow_filename()}")
            except Exception as e:
                print(f"✗ {name}: Failed - {e}")
                return False
        
        # Test factory function
        modes = ["free_generation_face", "clothes_removal", "nsfw_face"]
        for mode in modes:
            try:
                adapter = get_adapter(mode, workflow_dir="gpu_server/workflows")
                print(f"✓ get_adapter('{mode}'): Success")
            except Exception as e:
                print(f"✗ get_adapter('{mode}'): Failed - {e}")
                return False
        
        print("\n✓ All adapters initialized successfully\n")
        return True
    
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False


async def test_request_schemas():
    """Test that request schemas can be validated"""
    print("=" * 60)
    print("TEST 3: Request Schema Validation")
    print("=" * 60)
    
    try:
        from backend.schemas.request_free import (
            FreeGenerationRequest,
            NSFWFaceRequest
        )
        from backend.schemas.request_clothes import ClothesRemovalRequest
        
        # Test FreeGenerationRequest with face
        try:
            req = FreeGenerationRequest(
                mode="free",
                prompt="beautiful portrait",
                style="realism",
                add_face=True,
                face_images=["base64_image_1"],
                face_strength=0.75
            )
            print(f"✓ FreeGenerationRequest (with face): Valid")
            print(f"  - add_face: {req.add_face}")
            print(f"  - face_images count: {len(req.face_images) if req.face_images else 0}")
        except Exception as e:
            print(f"✗ FreeGenerationRequest: {e}")
            return False
        
        # Test NSFWFaceRequest
        try:
            req = NSFWFaceRequest(
                mode="nsfw_face",
                face_images=["base64_1", "base64_2"],
                scene_prompt="artistic portrait",
                style="lux",
                face_strength=0.8
            )
            print(f"✓ NSFWFaceRequest: Valid")
            print(f"  - face_images count: {len(req.face_images)}")
            print(f"  - scene_prompt length: {len(req.scene_prompt)}")
        except Exception as e:
            print(f"✗ NSFWFaceRequest: {e}")
            return False
        
        # Test ClothesRemovalRequest with new params
        try:
            req = ClothesRemovalRequest(
                mode="clothes_removal",
                target_image="/9j/base64data",
                style="realism",
                controlnet_strength=0.8,
                inpaint_denoise=0.75,
                segmentation_threshold=0.7
            )
            print(f"✓ ClothesRemovalRequest: Valid")
            print(f"  - controlnet_strength: {req.controlnet_strength}")
            print(f"  - inpaint_denoise: {req.inpaint_denoise}")
        except Exception as e:
            print(f"✗ ClothesRemovalRequest: {e}")
            return False
        
        print("\n✓ All schemas validated successfully\n")
        return True
    
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False


async def test_style_config():
    """Test that all styles are properly configured"""
    print("=" * 60)
    print("TEST 4: Style Configuration")
    print("=" * 60)
    
    try:
        from backend.config import STYLE_CONFIG
        
        expected_styles = ["noir", "super_realism", "realism", "lux", "anime", "chatgpt"]
        
        for style in expected_styles:
            if style in STYLE_CONFIG:
                config = STYLE_CONFIG[style]
                print(f"✓ Style '{style}': Configured")
                print(f"  - Model: {config['model']}")
                print(f"  - Profile: {config['default_quality_profile']}")
                print(f"  - Prefix: {config['prompt_prefix'][:50]}...")
            else:
                print(f"✗ Style '{style}': Missing")
                return False
        
        print(f"\n✓ All {len(expected_styles)} styles configured\n")
        return True
    
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False


async def test_service_instantiation():
    """Test that services can be instantiated"""
    print("=" * 60)
    print("TEST 5: Service Instantiation")
    print("=" * 60)
    
    try:
        from backend.services.free_generation_face import FreeGenerationFaceService
        from backend.services.nsfw_face import NSFWFaceService
        from backend.clients.gpu_client import GPUClient
        
        # Create mock GPU client
        gpu_client = GPUClient("http://localhost:8002", 180)
        
        # Test services
        services = [
            ("FreeGenerationFaceService", FreeGenerationFaceService),
            ("NSFWFaceService", NSFWFaceService)
        ]
        
        for name, service_class in services:
            try:
                service = service_class(gpu_client, request_id="test-123")
                print(f"✓ {name}: Instantiated")
            except Exception as e:
                print(f"✗ {name}: Failed - {e}")
                return False
        
        print("\n✓ All services instantiated successfully\n")
        return True
    
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False


async def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("FACE-INTEGRATED GENERATION MODES - VALIDATION TESTS")
    print("=" * 60 + "\n")
    
    tests = [
        ("Workflow JSON Loading", test_workflow_loading),
        ("Workflow Adapters", test_workflow_adapters),
        ("Request Schemas", test_request_schemas),
        ("Style Configuration", test_style_config),
        ("Service Instantiation", test_service_instantiation)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ {test_name} crashed: {e}\n")
            results.append((test_name, False))
    
    # Print summary
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Implementation is ready for integration testing.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
