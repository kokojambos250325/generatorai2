@echo off
echo Fixing ComfyUI dependencies on RunPod...

python ssh_runner.py "source /workspace/ComfyUI/venv/bin/activate && pip install tqdm transformers[torch] accelerate safetensors huggingface-hub --no-cache-dir && deactivate && echo 'Dependencies installed!' && bash /workspace/startup_all_services.sh"

echo.
echo Done! Check the output above.
pause
