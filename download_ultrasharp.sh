#!/bin/bash
cd /workspace/ComfyUI/models/upscale_models

echo "Downloading 4x-UltraSharp upscaler..."
wget --show-progress \
  "https://huggingface.co/Kim2091/UltraSharp/resolve/main/4x-UltraSharp.pth" \
  -O 4x-UltraSharp.pth

echo "Done!"
ls -lh 4x-UltraSharp.pth
