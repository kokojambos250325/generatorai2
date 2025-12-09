#!/bin/bash
# Install translation model dependencies and download M2M100 model

echo "=================================================="
echo "Installing Translation Service Dependencies"
echo "=================================================="

# Activate virtual environment
source /workspace/venv/bin/activate

# Install required packages
echo ""
echo "Installing transformers, sentencepiece, protobuf..."
pip install transformers sentencepiece protobuf --quiet

# Test installation
echo ""
echo "Testing installation..."
python3 << EOF
try:
    from transformers import M2M100ForConditionalGeneration, M2M100Tokenizer
    print("✅ transformers imported successfully")
    
    import sentencepiece
    print("✅ sentencepiece imported successfully")
    
    print("\nDownloading M2M100 model (facebook/m2m100_418M)...")
    print("This will download ~1.2GB, please wait...")
    
    tokenizer = M2M100Tokenizer.from_pretrained("facebook/m2m100_418M")
    model = M2M100ForConditionalGeneration.from_pretrained("facebook/m2m100_418M")
    
    print("✅ M2M100 model downloaded successfully")
    print(f"   Model size: {sum(p.numel() for p in model.parameters())/1e6:.1f}M parameters")
    
    # Test translation
    print("\nTesting translation (Russian → English)...")
    tokenizer.src_lang = "ru"
    text = "красивая девушка на пляже"
    encoded = tokenizer(text, return_tensors="pt")
    generated = model.generate(**encoded, forced_bos_token_id=tokenizer.get_lang_id("en"))
    result = tokenizer.batch_decode(generated, skip_special_tokens=True)[0]
    print(f"   Input (RU): {text}")
    print(f"   Output (EN): {result}")
    
    print("\n✅ SUCCESS: Translation service ready!")
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    exit(1)
EOF

echo ""
echo "=================================================="
echo "Installation Complete!"
echo "=================================================="
