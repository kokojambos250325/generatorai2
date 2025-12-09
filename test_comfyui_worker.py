"""
Тест готового RunPod ComfyUI Worker
"""

import runpod
import base64
import json
from pathlib import Path

# Настройки
RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY", "")
ENDPOINT_ID = input("Enter your Endpoint ID: ").strip()

if not ENDPOINT_ID:
    print("❌ Endpoint ID required!")
    exit(1)

runpod.api_key = RUNPOD_API_KEY
endpoint = runpod.Endpoint(ENDPOINT_ID)

print("=" * 60)
print("RunPod ComfyUI Worker Test")
print("=" * 60)
print(f"Endpoint ID: {ENDPOINT_ID}")
print()

# Базовый SDXL workflow
workflow = {
    "3": {
        "class_type": "KSampler",
        "inputs": {
            "seed": 42,
            "steps": 20,
            "cfg": 7.5,
            "sampler_name": "euler",
            "scheduler": "normal",
            "denoise": 1,
            "model": ["4", 0],
            "positive": ["6", 0],
            "negative": ["7", 0],
            "latent_image": ["5", 0]
        }
    },
    "4": {
        "class_type": "CheckpointLoaderSimple",
        "inputs": {
            "ckpt_name": "sd_xl_base_1.0.safetensors"  # Измените на вашу модель
        }
    },
    "5": {
        "class_type": "EmptyLatentImage",
        "inputs": {
            "width": 1024,
            "height": 1024,
            "batch_size": 1
        }
    },
    "6": {
        "class_type": "CLIPTextEncode",
        "inputs": {
            "text": "beautiful sunset over mountains, photorealistic, detailed, 8k",
            "clip": ["4", 1]
        }
    },
    "7": {
        "class_type": "CLIPTextEncode",
        "inputs": {
            "text": "ugly, blurry, low quality, cartoon",
            "clip": ["4", 1]
        }
    },
    "8": {
        "class_type": "VAEDecode",
        "inputs": {
            "samples": ["3", 0],
            "vae": ["4", 2]
        }
    },
    "9": {
        "class_type": "SaveImage",
        "inputs": {
            "filename_prefix": "ComfyUI",
            "images": ["8", 0]
        }
    }
}

print("📤 Sending request to RunPod...")
print("⏳ This may take 10-60 seconds (cold start + generation)...")
print()

try:
    result = endpoint.run_sync(
        {
            "input": {
                "workflow": workflow
            }
        },
        timeout=300  # 5 минут
    )
    
    print("✅ Response received!")
    print()
    
    # Вывод статуса
    status = result.get('status', 'UNKNOWN')
    print(f"Status: {status}")
    
    if status == 'COMPLETED':
        # Извлекаем изображения
        output = result.get('output', {})
        images = output.get('images', [])
        
        if images:
            print(f"✅ Generated {len(images)} image(s)")
            
            # Сохраняем
            for i, img_base64 in enumerate(images):
                try:
                    img_bytes = base64.b64decode(img_base64)
                    output_path = Path(f"comfyui_output_{i}.png")
                    output_path.write_bytes(img_bytes)
                    print(f"   💾 Saved: {output_path.absolute()}")
                    print(f"   📊 Size: {len(img_bytes):,} bytes")
                except Exception as e:
                    print(f"   ❌ Error saving image {i}: {e}")
        else:
            print("⚠️  No images in output")
            print("Output:", json.dumps(output, indent=2))
    
    elif status == 'FAILED':
        print("❌ Generation failed")
        error = result.get('error', 'Unknown error')
        print(f"Error: {error}")
    
    else:
        print(f"⚠️  Unexpected status: {status}")
        print("Full response:")
        print(json.dumps(result, indent=2))

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 60)
print("Test completed!")
print("=" * 60)
