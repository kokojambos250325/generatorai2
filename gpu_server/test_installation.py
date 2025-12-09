"""
GPU Server Quick Test
Verify installation and basic functionality
"""
import sys
import importlib.util

def check_module(module_name):
    """Check if a module can be imported"""
    spec = importlib.util.find_spec(module_name)
    return spec is not None

def main():
    print("=" * 60)
    print("GPU Server Installation Check")
    print("=" * 60)
    
    # Check Python dependencies
    print("\n1. Checking Python Dependencies:")
    dependencies = [
        "fastapi",
        "uvicorn",
        "pydantic",
        "httpx",
        "torch",
        "diffusers",
        "transformers",
        "PIL",
        "cv2",
        "numpy"
    ]
    
    missing = []
    for dep in dependencies:
        if check_module(dep):
            print(f"   ✓ {dep}")
        else:
            print(f"   ✗ {dep} (missing)")
            missing.append(dep)
    
    # Check GPU server modules
    print("\n2. Checking GPU Server Modules:")
    modules = [
        "gpu_server.server.main",
        "gpu_server.server.router",
        "gpu_server.server.inference_worker",
        "gpu_server.server.models_loader",
        "gpu_server.server.utils.queue",
        "gpu_server.server.utils.storage",
        "gpu_server.server.utils.id",
        "gpu_server.server.pipelines.sdxl_pipeline",
        "gpu_server.server.pipelines.controlnet_pipeline",
        "gpu_server.server.pipelines.faceswap_pipeline",
        "gpu_server.server.pipelines.faceconsistent_pipeline",
        "gpu_server.server.pipelines.clothes_pipeline"
    ]
    
    module_errors = []
    for mod in modules:
        try:
            __import__(mod)
            print(f"   ✓ {mod}")
        except Exception as e:
            print(f"   ✗ {mod} ({str(e)})")
            module_errors.append(mod)
    
    # Check CUDA availability
    print("\n3. Checking CUDA:")
    try:
        import torch
        if torch.cuda.is_available():
            print(f"   ✓ CUDA available")
            print(f"   ✓ GPU: {torch.cuda.get_device_name(0)}")
            print(f"   ✓ VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
        else:
            print(f"   ⚠ CUDA not available (CPU mode will be used)")
    except Exception as e:
        print(f"   ✗ Error checking CUDA: {str(e)}")
    
    # Summary
    print("\n" + "=" * 60)
    if not missing and not module_errors:
        print("✓ All checks passed! GPU server is ready.")
        print("\nTo start the server:")
        print("  uvicorn gpu_server.server.main:app --host 0.0.0.0 --port 3000")
        return 0
    else:
        print("✗ Some checks failed:")
        if missing:
            print(f"  Missing dependencies: {', '.join(missing)}")
            print(f"  Install with: pip install {' '.join(missing)}")
        if module_errors:
            print(f"  Module errors: {', '.join(module_errors)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
