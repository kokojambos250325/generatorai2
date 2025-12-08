# ComfyUI Workflows Documentation

## Overview

This directory contains ComfyUI workflow JSON files for the MVP image generation modes. These workflows must be created in the ComfyUI web interface and exported as JSON files.

**MVP Workflows:**
- `free_generation.json` - Text-to-image generation with style selection
- `clothes_removal.json` - Clothes removal with pose preservation

## Important Notes

⚠️ **These workflow files CANNOT be created programmatically.** They must be built using the ComfyUI web interface.

The files in this directory are **placeholders** that document the required structure. You must:
1. Open ComfyUI web interface (http://localhost:8188)
2. Build the workflow using the node editor
3. Export as JSON
4. Save to this directory

## Workflow Creation Guide

### Prerequisites

Before creating workflows, ensure the following are installed in ComfyUI:

**Required Nodes/Extensions:**
- Base ComfyUI nodes (included by default)
- ControlNet nodes (for clothes_removal)
- LoRA loader nodes
- IP-Adapter nodes (for future face modes)

**Required Models in `/workspace/models`:**
- Checkpoints: SDXL base, Anything V5, Chilloutmix
- VAE models
- LoRA weights
- ControlNet models (OpenPose, Depth, Canny)

---

## 1. Free Generation Workflow

**File:** `free_generation.json`

**Purpose:** Text-to-image generation with 4 style presets (realism, lux, anime, chatgpt)

### Required Nodes

1. **Load Checkpoint** 
   - Parameter: `model` (dynamic)
   - Maps to model names: sd_xl_base_1.0, anything_v5

2. **VAE Loader** (if separate VAE needed)
   - Parameter: `vae` (dynamic)

3. **LoRA Loader** (optional)
   - Parameter: `lora` (dynamic, can be null)
   - Parameter: `strength` (default: 0.7)

4. **CLIP Text Encode (Positive)**
   - Parameter: `prompt` (dynamic)
   - User's text prompt goes here

5. **CLIP Text Encode (Negative)**
   - Parameter: `negative_prompt` (dynamic)
   - Style-specific negative prompts

6. **Empty Latent Image**
   - Parameters: `width`, `height` (dynamic, default: 1024x1024)

7. **KSampler**
   - Parameters:
     - `steps` (dynamic, default: 30, range: 20-50)
     - `cfg` (dynamic, default: 7.5, range: 5-15)
     - `seed` (dynamic, default: -1 for random)
     - `sampler_name` (dynamic, default: "euler_a")
     - `scheduler` (default: "normal")
     - `denoise` (default: 1.0)

8. **VAE Decode**
   - Decodes latent to image

9. **Save Image**
   - Parameter: `filename_prefix` (default: "free_gen_")
   - Saves to ComfyUI output directory

### Parameter Injection Points

The GPU server will inject these parameters:

```json
{
  "prompt": "user's text description",
  "negative_prompt": "style-specific negative",
  "model": "sd_xl_base_1.0",
  "lora": "realistic_vision",
  "steps": 30,
  "cfg_scale": 7.5,
  "seed": -1,
  "sampler": "euler_a",
  "width": 1024,
  "height": 1024
}
```

### Style Configurations

**Realism:**
- Model: sd_xl_base_1.0
- LoRA: realistic_vision
- Negative: "cartoon, anime, 3d, illustration, painting"

**Lux:**
- Model: sd_xl_base_1.0
- LoRA: glossy_lux
- Negative: "low quality, blurry, bad anatomy"

**Anime:**
- Model: anything_v5
- LoRA: anime_style
- Negative: "realistic, photo, 3d"

**ChatGPT:**
- Model: sd_xl_base_1.0
- LoRA: none
- Negative: "nsfw, explicit, nude"

---

## 2. Clothes Removal Workflow

**File:** `clothes_removal.json`

**Purpose:** Remove clothing while preserving pose, depth, and body structure using 3 ControlNets

### Required Nodes

1. **Load Image**
   - Parameter: `target_image` (dynamic, base64 will be converted to file)
   - The clothed source image

2. **Load Checkpoint**
   - Parameter: `model` (dynamic)
   - Use: chilloutmix or anime_nsfw

3. **ControlNet Preprocessors** (3 parallel paths)

   **Path A - OpenPose:**
   - OpenPose Preprocessor node
   - Detects body pose/skeleton

   **Path B - Depth:**
   - Midas Depth Preprocessor node
   - Extracts depth map

   **Path C - Canny:**
   - Canny Edge Preprocessor node
   - Extracts edge information

4. **ControlNet Loaders** (3 instances)
   - Load OpenPose ControlNet model
   - Load Depth ControlNet model
   - Load Canny ControlNet model

5. **ControlNet Apply** (3 instances)
   - Apply each ControlNet to conditioning
   - Parameters: `strength` (0.8-1.0 for strong preservation)

6. **Cloth Segmentation** (if available)
   - Segment clothing regions
   - Generate mask for inpainting

7. **CLIP Text Encode (Positive)**
   - Prompt: describes desired result
   - Example: "nude body, natural skin, detailed anatomy"

8. **CLIP Text Encode (Negative)**
   - Parameter: `negative_prompt` (dynamic)
   - Default: "clothing, dressed, covered, clothes, shirt, pants"

9. **KSampler (Inpaint)**
   - Uses generated mask
   - Multiple ControlNet conditioning
   - Parameters:
     - `steps`: 40-50 (higher for quality)
     - `cfg`: 7-9
     - `denoise`: 0.7-0.85 (preserve original structure)

10. **VAE Decode**

11. **Upscale** (optional, for quality)
    - Use ESRGAN or similar
    - 2x upscale

12. **Save Image**
    - Parameter: `filename_prefix` (default: "clothes_removal_")

### Parameter Injection Points

```json
{
  "target_image": "base64_encoded_image",
  "model": "chilloutmix",
  "strength": 0.8,
  "controlnet": {
    "openpose": true,
    "depth": true,
    "canny": true
  },
  "negative_prompt": "clothing, dressed, covered"
}
```

### Critical Requirements

1. **All 3 ControlNets must be active** - This ensures pose, depth, and structure preservation
2. **High denoising strength** (0.7-0.85) - Removes clothing effectively
3. **Multiple conditioning paths** - Combine all ControlNet conditions before sampling
4. **Proper masking** - Use segmentation to target only clothing areas

---

## Creating Workflows in ComfyUI

### Step-by-Step Process

1. **Start ComfyUI**
   ```bash
   cd /workspace/ComfyUI
   python main.py
   ```

2. **Access Web Interface**
   - Open browser: http://localhost:8188
   - You should see the node editor

3. **Build Workflow**
   - Right-click → Add Node → Select node type
   - Connect nodes by dragging from output to input
   - Configure default parameters
   - Test with sample inputs

4. **Test Workflow**
   - Click "Queue Prompt" to test execution
   - Check output images
   - Verify all parameters work correctly

5. **Export Workflow**
   - Click "Save" button
   - Choose "Save API Format" (NOT "Save Workflow")
   - This exports the JSON with node structure
   - Save as `free_generation.json` or `clothes_removal.json`

6. **Copy to Project**
   ```bash
   cp workflow.json /workspace/gpu_server/workflows/free_generation.json
   ```

7. **Update Parameter Injection**
   - Review exported JSON structure
   - Update `comfy_client.py` → `inject_parameters()` method
   - Map parameter names to node IDs in the JSON

---

## Parameter Injection Implementation

After creating workflows, you must implement parameter injection in `comfy_client.py`.

### Example JSON Structure

```json
{
  "1": {
    "class_type": "CheckpointLoaderSimple",
    "inputs": {
      "ckpt_name": "sd_xl_base_1.0.safetensors"
    }
  },
  "6": {
    "class_type": "CLIPTextEncode",
    "inputs": {
      "text": "PROMPT_PLACEHOLDER",
      "clip": ["1", 1]
    }
  },
  "3": {
    "class_type": "KSampler",
    "inputs": {
      "seed": -1,
      "steps": 30,
      "cfg": 7.5,
      "sampler_name": "euler_a",
      ...
    }
  }
}
```

### Injection Logic

```python
def inject_parameters(self, workflow: Dict, params: Dict) -> Dict:
    """Inject parameters into workflow nodes"""
    
    # Find checkpoint loader node and update model
    for node_id, node in workflow.items():
        if node.get("class_type") == "CheckpointLoaderSimple":
            node["inputs"]["ckpt_name"] = params["model"]
        
        # Find text encode nodes and update prompts
        if node.get("class_type") == "CLIPTextEncode":
            if "PROMPT_PLACEHOLDER" in node["inputs"]["text"]:
                node["inputs"]["text"] = params["prompt"]
            if "NEGATIVE_PLACEHOLDER" in node["inputs"]["text"]:
                node["inputs"]["text"] = params["negative_prompt"]
        
        # Find KSampler and update parameters
        if node.get("class_type") == "KSampler":
            node["inputs"]["steps"] = params.get("steps", 30)
            node["inputs"]["cfg"] = params.get("cfg_scale", 7.5)
            node["inputs"]["seed"] = params.get("seed", -1)
    
    return workflow
```

---

## Testing Workflows

### Manual Testing in ComfyUI

1. Load workflow in web interface
2. Set test parameters:
   - Free gen: "a beautiful mountain landscape"
   - Clothes removal: Upload test image
3. Queue and verify output
4. Check generation time (should be under targets)

### API Testing

```python
# Test via GPU server API
import requests

response = requests.post("http://localhost:8001/generate", json={
    "workflow": "free_generation",
    "params": {
        "prompt": "test prompt",
        "model": "sd_xl_base_1.0",
        "steps": 30
    }
})

print(response.json())
```

---

## Troubleshooting

### Common Issues

1. **Workflow fails to load**
   - Check JSON syntax
   - Verify all required custom nodes are installed
   - Check model paths in nodes

2. **Parameter injection doesn't work**
   - Review workflow JSON structure
   - Update node IDs in `inject_parameters()`
   - Verify parameter names match

3. **Generation fails**
   - Check ComfyUI logs: `/workspace/ComfyUI/comfyui.log`
   - Verify models exist at specified paths
   - Check GPU memory (use nvidia-smi)

4. **Output image not found**
   - Check Save Image node configuration
   - Verify output directory exists
   - Check file permissions

---

## Next Steps

1. **Create free_generation.json**
   - Build in ComfyUI
   - Test with all 4 styles
   - Export and save

2. **Create clothes_removal.json**
   - Build with 3 ControlNets
   - Test segmentation
   - Verify pose preservation
   - Export and save

3. **Implement Parameter Injection**
   - Update `comfy_client.py`
   - Map all parameters
   - Test end-to-end

4. **Integration Testing**
   - Test Backend → GPU Server → ComfyUI flow
   - Verify all parameters work
   - Check error handling

---

## Resources

- **ComfyUI Documentation**: https://github.com/comfyanonymous/ComfyUI
- **ControlNet Guide**: https://github.com/lllyasviel/ControlNet
- **Model Downloads**: Hugging Face, CivitAI
- **Design Document**: `/.qoder/quests/system-architecture-design.md`

---

**Last Updated:** December 8, 2025  
**Status:** Workflows must be created manually in ComfyUI
