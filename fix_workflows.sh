#!/bin/bash
cd /workspace

# Fix seed in free.json
python3 << 'PYEOF'
import json, pathlib

# Fix free.json - set seed to random number
p = pathlib.Path("/workspace/workflows/free.json")
data = json.loads(p.read_text())
for node in data.values():
    if isinstance(node, dict) and node.get("class_type") == "KSampler":
        if node["inputs"].get("seed") is None:
            node["inputs"]["seed"] = 42
p.write_text(json.dumps(data, indent=2))
print("Fixed seed in free.json")

# Create new clothes_removal.json with NudeNet nodes
clothes_workflow = {
    "1": {
        "inputs": {
            "image": "source_image.png",
            "upload": "image"
        },
        "class_type": "LoadImage",
        "_meta": {"title": "Load Source Image"}
    },
    "2": {
        "inputs": {
            "ckpt_name": "sd_xl_base_1.0.safetensors"
        },
        "class_type": "CheckpointLoaderSimple",
        "_meta": {"title": "Load Checkpoint"}
    },
    "3": {
        "inputs": {
            "image": ["1", 0]
        },
        "class_type": "NudeNetDetector",
        "_meta": {"title": "Detect Clothes Areas"}
    },
    "4": {
        "inputs": {
            "pixels": ["1", 0],
            "vae": ["2", 2]
        },
        "class_type": "VAEEncode",
        "_meta": {"title": "VAE Encode"}
    },
    "5": {
        "inputs": {
            "text": "nude, naked body, natural skin, photorealistic, high quality, detailed skin texture",
            "clip": ["2", 1]
        },
        "class_type": "CLIPTextEncode",
        "_meta": {"title": "Positive Prompt"}
    },
    "6": {
        "inputs": {
            "text": "clothes, clothing, dressed, censored, low quality, blurry",
            "clip": ["2", 1]
        },
        "class_type": "CLIPTextEncode",
        "_meta": {"title": "Negative Prompt"}
    },
    "7": {
        "inputs": {
            "seed": 42,
            "steps": 30,
            "cfg": 7.5,
            "sampler_name": "dpmpp_2m_sde",
            "scheduler": "karras",
            "denoise": 0.85,
            "model": ["2", 0],
            "positive": ["5", 0],
            "negative": ["6", 0],
            "latent_image": ["4", 0]
        },
        "class_type": "KSampler",
        "_meta": {"title": "KSampler"}
    },
    "8": {
        "inputs": {
            "samples": ["7", 0],
            "vae": ["2", 2]
        },
        "class_type": "VAEDecode",
        "_meta": {"title": "VAE Decode"}
    },
    "9": {
        "inputs": {
            "filename_prefix": "clothes_removal",
            "images": ["8", 0]
        },
        "class_type": "SaveImage",
        "_meta": {"title": "Save Result"}
    }
}

p2 = pathlib.Path("/workspace/workflows/clothes_removal.json")
p2.write_text(json.dumps(clothes_workflow, indent=2))
print("Created new clothes_removal.json with basic inpaint workflow")
PYEOF

echo "Workflows fixed!"
