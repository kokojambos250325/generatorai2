#!/usr/bin/env python3
"""
Test Free Generation with Prompt Enhancement
"""
import sys
sys.path.insert(0, 'c:/projekt/generator')

from utils.prompt_enhancer import build_full_prompt

print("=" * 60)
print("ТЕСТ СИСТЕМЫ УЛУЧШЕНИЯ ПРОМПТОВ")
print("=" * 60)
print()

# Тестовые запросы
test_cases = [
    ("девушка на пляже", "realism"),
    ("стройная блондинка в купальнике лежа на пляже, закат", "luxury"),
    ("красивая брюнетка в элегантном платье", "anime"),
    ("рыжая девушка сидя в комнате", "realism"),
]

for user_input, style in test_cases:
    print(f"Запрос: {user_input}")
    print(f"Стиль: {style}")
    print("-" * 60)
    
    result = build_full_prompt(user_input, style=style, auto_translate=True)
    
    print(f"Positive: {result['positive_prompt']}")
    print(f"Negative: {result['negative_prompt']}")
    print(f"Style Name: {result['style_name']}")
    print("=" * 60)
    print()
