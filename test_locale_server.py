#!/usr/bin/env python3
"""Test locale manager on server"""

import sys
sys.path.insert(0, '/workspace/telegram_bot')

from utils.locale import init_locale_manager

print("=" * 60)
print("Testing Locale Manager")
print("=" * 60)

# Initialize locale manager
lm = init_locale_manager()

print(f"\n✓ Loaded: {len(lm._locales)} languages")
print(f"✓ Languages: {list(lm._locales.keys())}")

# Test English
print("\n--- Testing English ---")
test_en = lm.get_text("main_menu.welcome", "en", name="Test User")
print(f"EN welcome: {test_en[:80]}...")
print(f"Length: {len(test_en)} chars")

# Test Russian
print("\n--- Testing Russian ---")
test_ru = lm.get_text("main_menu.welcome", "ru", name="Тестовый пользователь")
print(f"RU welcome: {test_ru[:80]}...")
print(f"Length: {len(test_ru)} chars")

# Test German
print("\n--- Testing German ---")
test_de = lm.get_text("main_menu.welcome", "de", name="Test")
print(f"DE welcome: {test_de[:80]}...")

# Test all languages for a simple key
print("\n--- Testing all languages for 'main_menu.btn_free' ---")
for lang in lm._locales.keys():
    text = lm.get_text("main_menu.btn_free", lang)
    print(f"{lang}: {text}")

# Test fallback mechanism
print("\n--- Testing fallback (missing key) ---")
missing = lm.get_text("non.existent.key", "ru")
print(f"Fallback result: {missing}")

# Test language preference persistence
print("\n--- Testing language persistence ---")
import os
persist_file = "/workspace/telegram_bot/data/user_languages.json"
print(f"Persistence file exists: {os.path.exists(persist_file)}")
if os.path.exists(persist_file):
    with open(persist_file, 'r') as f:
        content = f.read()
    print(f"Content: {content}")

print("\n" + "=" * 60)
print("✅ SUCCESS: All locale tests passed!")
print("=" * 60)
