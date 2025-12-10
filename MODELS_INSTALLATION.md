# Инструкция по установке моделей

## 1. Полная FP32 версия CyberRealistic Pony (12.92 GB)

### Текущая ситуация:
- Установлена: pruned версия (6.5 GB)
- Нужна: полная FP32 версия (12.92 GB)

### Шаги установки:

1. **Скачайте полную версию:**
   - Перейдите на: https://civitai.com/models/443821/cyberrealistic-pony
   - Выберите версию **v15.0** или **v14.1**
   - Скачайте файл **"Full Model fp32 (12.92 GB)"**

2. **Загрузите на сервер:**
   
   **Вариант A: Через SCP (рекомендуется)**
   ```bash
   # Скачайте файл локально, затем загрузите на сервер
   scp -i ~/.ssh/id_ed25519 -P 25206 <локальный_файл>.safetensors root@38.147.83.26:/workspace/ComfyUI/models/checkpoints/cyberrealisticPony_v14.safetensors
   ```
   
   **Вариант B: Через wget на сервере (требует токен Civitai)**
   ```bash
   # На сервере, получите токен с https://civitai.com/user/account
   export CIVITAI_TOKEN="ваш_токен"
   cd /workspace/ComfyUI/models/checkpoints/
   
   # Скачайте полную версию (замените MODEL_VERSION_ID на ID версии с полной моделью)
   curl -H "Authorization: Bearer $CIVITAI_TOKEN" \
        -L "https://civitai.com/api/download/models/2469412" \
        -o cyberrealisticPony_v14.safetensors
   ```
   
   **Вариант C: Через браузер и загрузку**
   - Скачайте файл в браузере
   - Используйте WinSCP, FileZilla или другой SFTP клиент для загрузки

3. **Замените старый файл:**
   ```bash
   # На сервере
   cd /workspace/ComfyUI/models/checkpoints/
   mv cyberrealisticPony_v14.safetensors cyberrealisticPony_v14.safetensors.old
   mv cyberrealisticPony_v15.safetensors cyberrealisticPony_v14.safetensors
   # Или просто замените файл, если имя совпадает
   ```

---

## 2. ControlNet модели для SD 1.5 (для clothes removal)

### Модели для установки:
1. **control_v11p_sd15_canny.pth** - для Canny edge detection
2. **control_v11f1p_sd15_depth.pth** - для depth map
3. **control_v11p_sd15_openpose.pth** - для pose detection

### Команды для установки:

```bash
# Подключитесь к серверу
ssh -i ~/.ssh/id_ed25519 -p 25206 root@38.147.83.26

# Перейдите в директорию ControlNet
cd /workspace/ComfyUI/models/controlnet

# Скачайте модели
wget https://huggingface.co/lllyasviel/ControlNet-v1-1/resolve/main/control_v11p_sd15_canny.pth
wget https://huggingface.co/lllyasviel/ControlNet-v1-1/resolve/main/control_v11f1p_sd15_depth.pth
wget https://huggingface.co/lllyasviel/ControlNet-v1-1/resolve/main/control_v11p_sd15_openpose.pth

# Проверьте установку
ls -lh *.pth
```

### Ожидаемые размеры файлов:
- control_v11p_sd15_canny.pth: ~1.4 GB
- control_v11f1p_sd15_depth.pth: ~1.4 GB
- control_v11p_sd15_openpose.pth: ~1.4 GB

---

## 3. LoRA модели (опционально)

### Рекомендуемые LoRA модели:

1. **add_detail** - для улучшения детализации
   - Ссылка: https://civitai.com/models (поиск "add_detail")
   - Размер: ~100-200 MB

2. **eyes_detail** - для детализации глаз
   - Ссылка: https://civitai.com/models (поиск "eyes_detail")
   - Размер: ~100-200 MB

3. **realistic_vision** - для улучшения реалистичности
   - Ссылка: https://civitai.com/models (поиск "realistic_vision")
   - Размер: ~100-200 MB

### Команды для установки:

```bash
# На сервере
cd /workspace/ComfyUI/models/loras

# Скачайте LoRA модели (замените <ссылка> на прямую ссылку с Civitai)
wget <ссылка_на_lora> -O <имя_файла>.safetensors

# Пример:
# wget https://civitai.com/api/download/models/12345 -O add_detail.safetensors
```

---

## 4. Проверка установки

После установки всех моделей выполните:

```bash
# Проверка checkpoint'ов
ls -lh /workspace/ComfyUI/models/checkpoints/cyberrealisticPony*.safetensors

# Проверка ControlNet
ls -lh /workspace/ComfyUI/models/controlnet/*.pth

# Проверка LoRA
ls -lh /workspace/ComfyUI/models/loras/*.safetensors

# Перезапуск сервисов
cd /workspace/ai-generator
bash update_server.sh
```

---

## 5. Обновление конфигурации (если нужно)

Если вы установили новую версию Pony (v15 вместо v14), обновите конфигурацию:

```bash
# В файле backend/config.py измените:
# "model": "cyberrealisticPony_v14.safetensors"
# на:
# "model": "cyberrealisticPony_v15.safetensors"
# (или оставьте v14, если имя файла не изменилось)
```

---

## Примечания

- **Полная FP32 версия Pony** значительно улучшит качество генерации
- **ControlNet модели** необходимы для корректной работы clothes removal
- **LoRA модели** опциональны, но могут улучшить качество в определенных сценариях
- После установки моделей **обязательно перезапустите сервисы**

