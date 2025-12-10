# Рефакторинг Workflow - Итоговый отчет

## ✅ Выполнено

### 1. Workflow 1: free_generation.json
- ✅ Фиксированные ID нод: 3, 4, 5, 6, 7, 8, 9
- ✅ Структура:
  - **4**: CheckpointLoaderSimple (cyberrealisticPony_v14.safetensors)
  - **6**: CLIPTextEncode (positive prompt)
  - **7**: CLIPTextEncode (negative prompt)
  - **5**: EmptyLatentImage (width/height)
  - **3**: KSampler (seed/steps/cfg/sampler)
  - **8**: VAEDecode
  - **9**: SaveImage (filename_prefix: "free_gen")

### 2. Workflow 2: clothes_removal.json
- ✅ Упрощенная структура с фиксированными ID
- ✅ Ноды:
  - **1**: LoadImage (входное изображение)
  - **10**: PersonSegmentation (маска одежды)
  - **11-13**: Preprocessors (Canny, Depth, OpenPose)
  - **14-16**: ControlNetLoaders
  - **17-19**: ControlNetApply (цепочка)
  - **3**: KSampler (positive от 19, через ControlNet)
  - **4,5,6,7,8,9**: Аналогично free_generation

### 3. Workflow 3: nsfw_face.json
- ✅ Упрощенная структура
- ✅ Ноды:
  - **20-21**: LoadImage (референсные лица)
  - **22**: InsightFaceBatchLoader (face embedding)
  - **24**: IPAdapterApply (face embedding + conditioning)
  - **30**: IPAdapterModelLoader
  - **3**: KSampler (positive от 24 через IP-Adapter)
  - **4,5,6,7,8,9**: Аналогично free_generation

### 4. STYLE_CONFIG обновлен
- ✅ **noir**: 
  - model: cyberrealisticPony_v14.safetensors
  - default_quality_profile: "balanced"
  - prompt_prefix: "noir style, high contrast black and white..."
  
- ✅ **super_realism**:
  - model: cyberrealisticPony_v14.safetensors
  - default_quality_profile: "high_quality"
  - prompt_prefix: "ultra realistic, 8k, detailed skin texture..."
  
- ✅ **anime**:
  - model: animeModelXL.safetensors
  - default_quality_profile: "balanced"
  - prompt_prefix: "anime illustration, highly detailed..."

### 5. Quality Profiles
- ✅ **fast**: 18 steps, cfg 6.5, 704×1024, euler
- ✅ **balanced**: 26 steps, cfg 7.5, 832×1216, euler
- ✅ **high_quality**: 32 steps, cfg 8.0, 896×1344, dpmpp_2m

### 6. comfy_client.py
- ✅ Добавлена поддержка параметра `denoise` в KSampler
- ✅ Сохранена поддержка всех существующих параметров (seed, steps, cfg, sampler, scheduler)

## 📋 Структура параметров

### Формат extra_params
```json
{
  "quality_profile": "fast" | "balanced" | "high_quality",
  "steps": 30,
  "cfg_scale": 7.5,  // автоматически маппится в cfg
  "sampler": "euler",
  "seed": 42,  // -1 = случайный
  "width": 832,
  "height": 1216,
  "denoise": 1.0
}
```

### Разрешение параметров
1. Берется `default_quality_profile` из STYLE_CONFIG
2. Если в extra_params есть `quality_profile` - перекрывает
3. Индивидуальные параметры из extra_params перекрывают профиль
4. `cfg_scale` автоматически маппится в `cfg` для GPU сервера

## 🔗 Связи в workflow

### free_generation
- 4.MODEL → 3.model
- 4.CLIP → 6.clip, 7.clip
- 4.VAE → 8.vae
- 6.CONDITIONING → 3.positive
- 7.CONDITIONING → 3.negative
- 5.LATENT → 3.latent_image
- 3.LATENT → 8.samples
- 8.IMAGE → 9.images

### clothes_removal
- 1.IMAGE → 10, 11, 12, 13 (preprocessors)
- 10.MASK → 5.mask (для VAEEncode)
- 11,12,13 → 14,15,16 (ControlNet loaders)
- 6.CONDITIONING → 17 → 18 → 19 → 3.positive
- Остальное аналогично free_generation

### nsfw_face
- 20,21.IMAGE → 22 (InsightFaceBatchLoader)
- 6.CONDITIONING → 24.positive
- 22.FACE_EMBED → 24 (IPAdapterApply)
- 24.CONDITIONING → 3.positive
- Остальное аналогично free_generation

## 📝 Коммиты

- `9263247` - Refactor workflows: fixed node IDs, updated STYLE_CONFIG and quality profiles

## ⚠️ Важные замечания

1. **Модели**: 
   - Для anime нужен отдельный checkpoint: `animeModelXL.safetensors`
   - Для остальных стилей используется `cyberrealisticPony_v14.safetensors`

2. **ComfyUI ноды**:
   - Убедитесь, что установлены все необходимые custom nodes:
     - PersonSegmentation
     - InsightFaceBatchLoader
     - IPAdapterApply
     - ControlNet loaders

3. **Параметры**:
   - Все параметры инжектируются через `comfy_client.inject_parameters()`
   - ID нод фиксированы и не должны меняться

## 🧪 Следующие шаги

1. Синхронизировать изменения на сервере
2. Перезапустить backend и GPU server
3. Протестировать генерацию с новыми workflow
4. Проверить работу всех трех режимов

