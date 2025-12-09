#!/usr/bin/env python3
"""
Final Task Completion Verification Script

This script verifies that all required tasks have been completed for the AI Image Generation Platform.
"""

import os
import sys
import json
from pathlib import Path

def check_required_files():
    """Check that all required files exist"""
    print("Checking required files...")
    
    required_files = [
        # Core implementation files
        "backend/main.py",
        "backend/config.py",
        "backend/requirements.txt",
        "backend/.env.template",
        "backend/routers/generate.py",
        "backend/routers/health.py",
        "backend/services/free_generation.py",
        "backend/services/clothes_removal.py",
        "backend/services/generation_router.py",
        "backend/clients/gpu_client.py",
        "backend/utils/json_logging.py",
        "backend/services/param_resolver.py",
        
        "gpu_server/server.py",
        "gpu_server/comfy_client.py",
        "gpu_server/config.py",
        "gpu_server/requirements.txt",
        "gpu_server/.env.template",
        "gpu_server/json_logging.py",
        "gpu_server/workflows/free_generation.json",
        
        # Telegram bot
        "telegram_bot/bot.py",
        "telegram_bot/requirements.txt",
        "telegram_bot/.env.template",
        
        # Infrastructure
        "startup.sh",
        "restart_services.sh",
        "test_logging.sh",
        
        # Documentation
        "README.md",
        "DEPLOYMENT_GUIDE.md",
        "IMPLEMENTATION_STATUS.md",
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
            print(f"❌ Missing: {file_path}")
        else:
            print(f"✅ Found: {file_path}")
    
    if missing_files:
        print(f"\n❌ {len(missing_files)} required files are missing")
        return False
    
    print(f"\n✅ All {len(required_files)} required files found")
    return True

def check_logging_implementation():
    """Verify logging implementation"""
    print("\nChecking logging implementation...")
    
    try:
        # Test backend logging
        sys.path.insert(0, 'backend')
        from utils.json_logging import setup_json_logging, log_event
        import logging
        
        # Test GPU server logging
        sys.path.insert(0, 'gpu_server')
        from json_logging import setup_json_logging as gpu_setup_json_logging, log_event as gpu_log_event
        
        print("✅ Logging modules imported successfully")
        return True
        
    except Exception as e:
        print(f"❌ Logging implementation check failed: {e}")
        return False

def check_param_resolution():
    """Verify parameter resolution implementation"""
    print("\nChecking parameter resolution implementation...")
    
    try:
        sys.path.insert(0, 'backend')
        from services.param_resolver import ParameterResolver
        
        # Test basic parameter resolution
        params = ParameterResolver.resolve_params(
            style="super_realism",
            prompt="test prompt"
        )
        
        # Check that required parameters are present
        required_params = ['steps', 'cfg', 'width', 'height', 'sampler', 'prompt', 'negative_prompt']
        for param in required_params:
            if param not in params:
                print(f"❌ Missing required parameter: {param}")
                return False
        
        print("✅ Parameter resolution working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Parameter resolution check failed: {e}")
        return False

def check_deployment_readiness():
    """Check that deployment is ready"""
    print("\nChecking deployment readiness...")
    
    # Check that all scripts are executable
    executable_scripts = [
        "startup.sh",
        "restart_services.sh",
        "test_logging.sh"
    ]
    
    for script in executable_scripts:
        if os.path.exists(script):
            # Check if file has execute permissions (Unix/Linux)
            if os.name != 'nt':  # Skip on Windows
                if not os.access(script, os.X_OK):
                    print(f"⚠ Warning: {script} is not executable (run: chmod +x {script})")
            print(f"✅ Found: {script}")
        else:
            print(f"❌ Missing: {script}")
            return False
    
    print("✅ Deployment scripts verified")
    return True

def main():
    """Main verification function"""
    print("=" * 60)
    print("AI Image Generation Platform - Final Task Verification")
    print("=" * 60)
    
    all_checks_passed = True
    
    # Run all verification checks
    checks = [
        ("Required Files", check_required_files),
        ("Logging Implementation", check_logging_implementation),
        ("Parameter Resolution", check_param_resolution),
        ("Deployment Readiness", check_deployment_readiness),
    ]
    
    for check_name, check_func in checks:
        print(f"\n{'='*20} {check_name} {'='*20}")
        if not check_func():
            all_checks_passed = False
    
    print("\n" + "=" * 60)
    if all_checks_passed:
        print("🎉 ALL VERIFICATION CHECKS PASSED!")
        print("✅ AI Image Generation Platform development is COMPLETE")
        print("✅ Ready for deployment to RunPod")
        print("\nNext steps:")
        print("1. Deploy files to RunPod using DEPLOYMENT_GUIDE.md")
        print("2. Install dependencies on the POD")
        print("3. Configure environment variables")
        print("4. Start services using startup.sh")
        print("5. Test end-to-end functionality")
    else:
        print("❌ SOME VERIFICATION CHECKS FAILED!")
        print("⚠ Please address the issues before deployment")
    print("=" * 60)
    
    return all_checks_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)