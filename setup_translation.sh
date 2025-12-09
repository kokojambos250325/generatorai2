#!/bin/bash
# Quick install translation dependencies

echo "Installing translation dependencies..."
cd /workspace
/workspace/venv/bin/pip install -q transformers sentencepiece protobuf

echo "Testing installation..."
/workspace/venv/bin/python3 << 'EOF'
try:
    from transformers import M2M100ForConditionalGeneration, M2M100Tokenizer
    print("✅ transformers installed")
    
    # Download model (cached if already exists)
    print("Downloading M2M100 model...")
    tokenizer = M2M100Tokenizer.from_pretrained("facebook/m2m100_418M")
    model = M2M100ForConditionalGeneration.from_pretrained("facebook/m2m100_418M")
    print("✅ Model ready")
    
    # Quick test
    tokenizer.src_lang = "ru"
    text = "красивая девушка"
    enc = tokenizer(text, return_tensors="pt")
    gen = model.generate(**enc, forced_bos_token_id=tokenizer.get_lang_id("en"), max_length=30)
    result = tokenizer.batch_decode(gen, skip_special_tokens=True)[0]
    print(f"Test: '{text}' → '{result}'")
    print("✅ Translation working!")
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)
EOF

echo ""
echo "✅ Translation service ready!"
