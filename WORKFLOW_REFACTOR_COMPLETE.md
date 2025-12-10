# ✅ Рефакторинг Workflow - ЗАВЕРШЕН

## Выполненные задачи

### 1. ✅ Workflow 1: free_generation.json
**Файл**: `/workspace/gpu_server/workflows/free_generation.json`

**Структура с фиксированными ID:**
- **ID 4**: `CheckpointLoaderSimple` - загрузка модели (cyberrealisticPony_v14.safetensors)
- **ID 6**: `CLIPTextEncode` - positive prompt
- **ID 7**: `CLIPTextEncode` - negative prompt  
- **ID 5**: `EmptyLatentImage` - латентка (width/height динамически)
- **ID 3**: `KSampler` - основной сэмплер (seed/steps/cfg/sampler динамически)
- **ID 8**: `VAEDecode` - декод латентки в картинку
- **ID 9**: `SaveImage` - сохранение PNG (filename_prefix: "free_gen")

**Связи:**
- 4.MODEL → 3.model
- 4.CLIP → 6.clip, 7.clip
- 4.VAE → 8.vae
- 6.CONDITIONING → 3.positive
- 7.CONDITIONING → 3.negative
- 5.LATENT → 3.latent_image
- 3.LATENT → 8.samples
- 8.IMAGE → 9.images

### 2. ✅ Workflow 2: clothes_removal.json
**Файл**: `/workspace/gpu_server/workflows/clothes_removal.json`

**Структура:**
- **ID 1**: `LoadImage` - входное изображение
- **ID 10**: `PersonSegmentation` - сегментация одежды → маска
- **ID 11**: `CannyEdgePreprocessor` - edges для ControlNet
- **ID 12**: `MiDaS-DepthMapPreprocessor` - depth-карта
- **ID 13**: `OpenposePreprocessor` - поза
- **ID 14-16**: `ControlNetLoader` - загрузка ControlNet моделей (Canny, Depth, OpenPose)
- **ID 17-19**: `ControlNetApply` - применение ControlNet (цепочка)
- **ID 4,5,6,7,8,9**: Аналогично free_generation

**Связи:**
- 1.IMAGE → 10, 11, 12, 13 (preprocessors)
- 10.MASK → 5.mask (для VAEEncode inpaint)
- 11,12,13 → 14,15,16 (ControlNet loaders)
- 6.CONDITIONING → 17 → 18 → 19 → 3.positive (через ControlNet цепочку)

### 3. ✅ Workflow 3: nsfw_face.json
**Файл**: `/workspace/gpu_server/workflows/nsfw_face.json`

**Структура:**
- **ID 20-21**: `LoadImage` - референсные лица (1-5 фото)
- **ID 22**: `InsightFaceBatchLoader` - получение face embedding
- **ID 24**: `IPAdapterApply` - внедрение face embedding в conditioning
- **ID 30**: `IPAdapterModelLoader` - загрузка IP-Adapter модели
- **ID 4,5,6,7,8,9**: Аналогично free_generation

**Связи:**
- 20,21.IMAGE → 22 (InsightFaceBatchLoader)
- 6.CONDITIONING → 24.positive
- 22.FACE_EMBED → 24 (IPAdapterApply)
- 24.CONDITIONING → 3.positive

### 4. ✅ STYLE_CONFIG обновлен
**Файл**: `backend/config.py`

```python
STYLE_CONFIG = {
    "noir": {
        "model": "cyberrealisticPony_v14.safetensors",
        "negative_prompt": "low quality, bad anatomy, jpeg artifacts...",
        "prompt_prefix": "noir style, high contrast black and white...",
        "default_quality_profile": "balanced",
        "default_sampler": "euler",
        "default_steps": 26,
        "default_cfg": 7.5,
        "default_resolution": {"width": 832, "height": 1216}
    },
    "super_realism": {
        "model": "cyberrealisticPony_v14.safetensors",
        "negative_prompt": "cartoon, anime, 3d, illustration...",
        "prompt_prefix": "ultra realistic, 8k, detailed skin texture...",
        "default_quality_profile": "high_quality",
        "default_sampler": "dpmpp_2m",
        "default_steps": 32,
        "default_cfg": 8.0,
        "default_resolution": {"width": 896, "height": 1344}
    },
    "anime": {
        "model": "animeModelXL.safetensors",
        "negative_prompt": "photo, realistic, 3d, lowres...",
        "prompt_prefix": "anime illustration, highly detailed...",
        "default_quality_profile": "balanced",
        "default_sampler": "euler",
        "default_steps": 24,
        "default_cfg": 7.0,
        "default_resolution": {"width": 768, "height": 1152}
    }
}
```

### 5. ✅ Quality Profiles
**Файл**: `backend/services/param_resolver.py`

```python
QUALITY_PROFILES = {
    "fast": {
        "steps": 18,
        "cfg": 6.5,
        "width": 704,
        "height": 1024,
        "sampler": "euler",
        "scheduler": "normal"
    },
    "balanced": {
        "steps": 26,
        "cfg": 7.5,
        "width": 832,
        "height": 1216,
        "sampler": "euler",
        "scheduler": "normal"
    },
    "high_quality": {
        "steps": 32,
        "cfg": 8.0,
        "width": 896,
        "height": 1344,
        "sampler": "dpmpp_2m",
        "scheduler": "karras"
    }
}
```

### 6. ✅ comfy_client.py обновлен
- ✅ Добавлена поддержка параметра `denoise` в KSampler
- ✅ Сохранена поддержка всех существующих параметров

## Формат extra_params

```json
{
  "quality_profile": "fast" | "balanced" | "high_quality",
  "steps": 30,
  "cfg_scale": 7.5,  // автоматически маппится в cfg
  "sampler": "euler",
  "scheduler": "normal",
  "seed": 42,  // -1 = случайный
  "width": 832,
  "height": 1216,
  "denoise": 1.0
}
```

## Логика разрешения параметров

1. Берется `default_quality_profile` из STYLE_CONFIG[style]
2. Если в extra_params есть `quality_profile` - перекрывает
3. Индивидуальные параметры из extra_params перекрывают профиль
4. `cfg_scale` автоматически маппится в `cfg` для GPU сервера
5. `prompt_prefix` из стиля добавляется к пользовательскому промпту

## Коммиты

- `9263247` - Refactor workflows: fixed node IDs, updated STYLE_CONFIG and quality profiles
- `9c0f33a` - Fix: Properly handle GPU server error responses (status=failed)
- `271cbd1` - Fix: Add support for noir and super_realism styles in bot handler

## Синхронизация

- ✅ Локальные изменения закоммичены
- ✅ Изменения отправлены в GitHub
- ✅ Изменения синхронизированы на сервере (RunPod)
- ⏳ Backend требует перезапуска для применения изменений

## Важные замечания

1. **Модели на сервере**:
   - ✅ `cyberrealisticPony_v14.safetensors` - для noir/super_realism/realism
   - ⚠️ `animeModelXL.safetensors` - для anime (требуется установка)

2. **ComfyUI Custom Nodes** (требуются на сервере):
   - PersonSegmentation
   - InsightFaceBatchLoader
   - IPAdapterApply + IPAdapterModelLoader
   - ControlNet loaders (Canny, Depth, OpenPose)

3. **ComfyUI должен быть запущен** на порту 8188 для работы генерации

## Следующие шаги

1. ✅ Перезапустить backend на сервере
2. ⏳ Проверить работу генерации с новыми workflow
3. ⏳ Протестировать все три режима (free, clothes_removal, nsfw_face)
4. ⏳ Убедиться что ComfyUI запущен и доступен

## Статус

**✅ РЕФАКТОРИНГ ЗАВЕРШЕН**

Все workflow приведены к понятным графам с фиксированными ID нод.
STYLE_CONFIG и quality profiles настроены согласно требованиям.

