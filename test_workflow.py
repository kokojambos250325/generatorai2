#!/usr/bin/env python3
"""
Quick test of free generation workflow
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("TESTING FREE GENERATION WORKFLOW")
print("=" * 60)

# Test 1: Import prompt enhancer
print("\n[1/4] Testing prompt_enhancer import...")
try:
    from utils.prompt_enhancer import build_full_prompt
    print("✓ prompt_enhancer imported successfully")
except Exception as e:
    print(f"✗ Failed to import: {e}")
    sys.exit(1)

# Test 2: Test prompt enhancement
print("\n[2/4] Testing prompt enhancement...")
try:
    test_input = "девушка на пляже"
    result = build_full_prompt(test_input, style="realism")
    print(f"✓ Input: {test_input}")
    print(f"✓ Output: {result['positive_prompt'][:80]}...")
    print(f"✓ Style: {result['style_name']}")
except Exception as e:
    print(f"✗ Enhancement failed: {e}")
    sys.exit(1)

# Test 3: Import telegram handlers
print("\n[3/4] Testing telegram handler imports...")
try:
    from telegram_bot.handlers.free import (
        handle_free_generation,
        handle_style_choice,
        process_free_prompt,
        WAITING_STYLE_CHOICE,
        WAITING_FREE_PROMPT
    )
    print("✓ All handlers imported successfully")
    print(f"✓ States: WAITING_STYLE_CHOICE={WAITING_STYLE_CHOICE}, WAITING_FREE_PROMPT={WAITING_FREE_PROMPT}")
except Exception as e:
    print(f"✗ Handler import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Check bot configuration
print("\n[4/4] Testing bot configuration...")
try:
    from telegram_bot.config import get_bot_settings
    settings = get_bot_settings()
    if settings.TELEGRAM_BOT_TOKEN:
        print("✓ Bot token configured")
    else:
        print("⚠ Bot token not configured (check .env)")
    
    if settings.BACKEND_API_URL:
        print(f"✓ Backend API URL: {settings.BACKEND_API_URL}")
    else:
        print("⚠ Backend API URL not configured")
except Exception as e:
    print(f"✗ Configuration failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("✅ WORKFLOW TEST COMPLETE")
print("=" * 60)
print("\nNext steps:")
print("1. Ensure TELEGRAM_BOT_TOKEN is set in .env")
print("2. Ensure BACKEND_API_URL points to your RunPod endpoint")
print("3. Start services on RunPod: python start_runpod_services.py")
print("4. Run bot: python run_telegram_bot.py")
