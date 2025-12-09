"""
Local testing script for RunPod Serverless handler
Tests the handler function without deploying to RunPod
"""
import json
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Mock runpod module for local testing
class MockRunPod:
    class serverless:
        @staticmethod
        def start(config):
            print("Mock RunPod serverless started")
            print(f"Handler: {config.get('handler')}")

sys.modules['runpod'] = MockRunPod()

# Now import the handler
from runpod_handler import handler


def test_sdxl_generation():
    """Test basic SDXL generation"""
    print("\n" + "="*60)
    print("Testing SDXL Generation")
    print("="*60)
    
    job = {
        "input": {
            "pipeline": "sdxl",
            "prompt": "beautiful sunset over mountains, photorealistic, 8k",
            "negative_prompt": "ugly, blurry, low quality",
            "width": 1024,
            "height": 1024,
            "num_inference_steps": 30,
            "guidance_scale": 7.5,
            "seed": 42
        }
    }
    
    result = handler(job)
    print(f"Result: {json.dumps(result, indent=2)}")
    return result


def test_controlnet_generation():
    """Test ControlNet generation"""
    print("\n" + "="*60)
    print("Testing ControlNet Generation")
    print("="*60)
    
    job = {
        "input": {
            "pipeline": "controlnet",
            "prompt": "professional photo of a woman",
            "control_image": "base64_encoded_image_here",
            "controlnet_type": "pose",
            "width": 1024,
            "height": 1024,
            "num_inference_steps": 30,
            "seed": 42
        }
    }
    
    result = handler(job)
    print(f"Result: {json.dumps(result, indent=2)}")
    return result


def test_faceswap():
    """Test FaceSwap pipeline"""
    print("\n" + "="*60)
    print("Testing FaceSwap")
    print("="*60)
    
    job = {
        "input": {
            "pipeline": "faceswap",
            "source_image": "base64_encoded_source",
            "target_image": "base64_encoded_target"
        }
    }
    
    result = handler(job)
    print(f"Result: {json.dumps(result, indent=2)}")
    return result


def test_invalid_pipeline():
    """Test error handling for invalid pipeline"""
    print("\n" + "="*60)
    print("Testing Invalid Pipeline (Error Handling)")
    print("="*60)
    
    job = {
        "input": {
            "pipeline": "nonexistent_pipeline",
            "prompt": "test"
        }
    }
    
    result = handler(job)
    print(f"Result: {json.dumps(result, indent=2)}")
    assert "error" in result
    return result


if __name__ == "__main__":
    print("RunPod Serverless Local Testing")
    print("="*60)
    
    # Run tests
    tests = [
        test_invalid_pipeline,  # Start with error handling
        # Uncomment when ready to test with actual models:
        # test_sdxl_generation,
        # test_controlnet_generation,
        # test_faceswap,
    ]
    
    for test in tests:
        try:
            test()
        except Exception as e:
            print(f"❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*60)
    print("Testing completed")
    print("="*60)
