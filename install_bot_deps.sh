#!/bin/sh
cd /workspace/ai-generator
. /workspace/ComfyUI/venv/bin/activate
pip install -q python-telegram-bot python-dotenv pydantic-settings requests
echo "DEPENDENCIES_INSTALLED"
