"""
Simple test to verify RunPod SDK is working
"""
import sys

# Test 1: Import runpod
print("Test 1: Importing RunPod SDK...")
try:
    import runpod
    print("✅ RunPod SDK imported successfully")
except ImportError as e:
    print(f"❌ Failed to import runpod: {e}")
    print("\nInstall with: pip install runpod")
    sys.exit(1)

# Test 2: Simple handler
print("\nTest 2: Creating simple handler...")

def simple_handler(job):
    """Simple test handler"""
    job_input = job.get('input', {})
    message = job_input.get('message', 'Hello from RunPod!')
    
    return {
        "status": "success",
        "message": message,
        "echo": job_input
    }

print("✅ Handler created")

# Test 3: Start local server
print("\nTest 3: Starting local server...")
print("Server will be available at: http://localhost:8000")
print("Press Ctrl+C to stop")
print("\nTest with:")
print('  curl -X POST http://localhost:8000/run -H "Content-Type: application/json" -d "{\\"input\\":{\\"message\\":\\"test\\"}}"')
print()

runpod.serverless.start({"handler": simple_handler})
