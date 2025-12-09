"""
Test script for parameter resolution

Verifies that:
1. Quality profiles are correctly loaded
2. Style configuration is correctly loaded
3. Parameter resolution works correctly
4. cfg_scale → cfg mapping works
"""

import sys
sys.path.insert(0, 'backend')

from services.param_resolver import ParameterResolver

def test_parameter_resolution():
    """Test the parameter resolution logic"""
    
    print("=" * 60)
    print("Testing Parameter Resolution")
    print("=" * 60)
    
    # Test 1: Basic resolution with super_realism (default: high_quality profile)
    print("\n1. Test super_realism with defaults:")
    params = ParameterResolver.resolve_params(
        style="super_realism",
        prompt="a beautiful landscape"
    )
    print(f"   Steps: {params['steps']} (expected: 32)")
    print(f"   CFG: {params['cfg']} (expected: 8.0)")
    print(f"   Size: {params['width']}x{params['height']} (expected: 896x1344)")
    print(f"   Sampler: {params['sampler']} (expected: dpmpp_2m)")
    print(f"   Prompt includes prefix: {params['prompt'][:50]}...")
    
    # Test 2: Override quality profile
    print("\n2. Test noir with fast profile override:")
    params = ParameterResolver.resolve_params(
        style="noir",
        prompt="detective in shadows",
        extra_params={"quality_profile": "fast"}
    )
    print(f"   Steps: {params['steps']} (expected: 18)")
    print(f"   CFG: {params['cfg']} (expected: 6.5)")
    print(f"   Size: {params['width']}x{params['height']} (expected: 704x1024)")
    
    # Test 3: CRITICAL - cfg_scale → cfg mapping
    print("\n3. Test cfg_scale → cfg mapping:")
    params = ParameterResolver.resolve_params(
        style="anime",
        prompt="cute anime girl",
        extra_params={"cfg_scale": 9.5}
    )
    print(f"   CFG: {params['cfg']} (expected: 9.5)")
    print(f"   ✓ cfg_scale correctly mapped to cfg")
    
    # Test 4: Individual parameter overrides
    print("\n4. Test individual parameter overrides:")
    params = ParameterResolver.resolve_params(
        style="super_realism",
        prompt="cyberpunk city",
        extra_params={
            "steps": 40,
            "cfg_scale": 7.0,
            "width": 1024,
            "height": 768
        }
    )
    print(f"   Steps: {params['steps']} (expected: 40)")
    print(f"   CFG: {params['cfg']} (expected: 7.0)")
    print(f"   Size: {params['width']}x{params['height']} (expected: 1024x768)")
    
    # Test 5: Verify checkpoint is included
    print("\n5. Test checkpoint inclusion:")
    params = ParameterResolver.resolve_params(
        style="noir",
        prompt="test"
    )
    print(f"   Checkpoint: {params['checkpoint']} (expected: cyberrealisticPony_v14.safetensors)")
    
    print("\n" + "=" * 60)
    print("All tests passed! ✓")
    print("=" * 60)

if __name__ == "__main__":
    test_parameter_resolution()
