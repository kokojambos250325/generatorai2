#!/usr/bin/env python3
"""Test remote API through SSH tunnel"""
import requests

API_BASE = "https://p8q2agahufxw4a-3000.proxy.runpod.net"

def test_health():
    try:
        r = requests.get(f"{API_BASE}/api/health", timeout=5)
        print(f"✓ Health check: {r.status_code}")
        print(f"  Response: {r.json()}")
        return True
    except Exception as e:
        print(f"✗ Health check failed: {e}")
        return False

def test_root():
    try:
        r = requests.get(f"{API_BASE}/", timeout=5)
        print(f"✓ Root endpoint: {r.status_code}")
        print(f"  Response: {r.json()}")
        return True
    except Exception as e:
        print(f"✗ Root endpoint failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing remote API via SSH tunnel...\n")
    test_health()
    print()
    test_root()
