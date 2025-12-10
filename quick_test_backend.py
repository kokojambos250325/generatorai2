#!/usr/bin/env python3
"""Быстрый тест backend через SSH туннель"""
import requests
import json

print("=== QUICK BACKEND TEST ===\n")

# Тест health endpoint
print("1. Testing health endpoint...")
try:
    response = requests.get("http://localhost:8000/health", timeout=10)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {json.dumps(response.json(), indent=2)}")
    print("   ✅ Health check OK\n")
except Exception as e:
    print(f"   ❌ Error: {e}\n")
    exit(1)

# Тест root endpoint
print("2. Testing root endpoint...")
try:
    response = requests.get("http://localhost:8000/", timeout=5)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {json.dumps(response.json(), indent=2)}")
    print("   ✅ Root endpoint OK\n")
except Exception as e:
    print(f"   ❌ Error: {e}\n")

print("=== TEST COMPLETE ===")
