#!/bin/bash
# Команды для установки моделей (выполните на сервере)

echo "=== УСТАНОВКА CONTROLNET МОДЕЛЕЙ ==="
cd /workspace/ComfyUI/models/controlnet

echo "Скачивание control_v11p_sd15_canny.pth..."
wget -q --show-progress https://huggingface.co/lllyasviel/ControlNet-v1-1/resolve/main/control_v11p_sd15_canny.pth -O control_v11p_sd15_canny.pth

echo "Скачивание control_v11f1p_sd15_depth.pth..."
wget -q --show-progress https://huggingface.co/lllyasviel/ControlNet-v1-1/resolve/main/control_v11f1p_sd15_depth.pth -O control_v11f1p_sd15_depth.pth

echo "Скачивание control_v11p_sd15_openpose.pth..."
wget -q --show-progress https://huggingface.co/lllyasviel/ControlNet-v1-1/resolve/main/control_v11p_sd15_openpose.pth -O control_v11p_sd15_openpose.pth

echo ""
echo "Проверка установленных файлов:"
ls -lh *.pth

echo ""
echo "=== ГОТОВО ==="
echo ""
echo "Следующие шаги:"
echo "1. Скачайте полную FP32 версию Pony (12.92 GB) с https://civitai.com/models/443821/cyberrealistic-pony"
echo "2. Загрузите на сервер в /workspace/ComfyUI/models/checkpoints/"
echo "3. Замените cyberrealisticPony_v14.safetensors"
echo "4. При необходимости добавьте LoRA модели в /workspace/ComfyUI/models/loras/"
echo "5. Перезапустите сервисы: cd /workspace/ai-generator && bash update_server.sh"

