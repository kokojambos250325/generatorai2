import sys
sys.path.insert(0, r'c:\projekt\generator')

from utils.prompt_enhancer import build_full_prompt

tests = [
    ("девушка на пляже", "realism"),
    ("стройная блондинка", "luxury"),
    ("красивая брюнетка", "anime")
]

for prompt, style in tests:
    result = build_full_prompt(prompt, style)
    print(f"\nPrompt: {prompt}")
    print(f"Style: {style}")
    print(f"Positive: {result['positive_prompt'][:100]}...")
    print("-" * 60)
