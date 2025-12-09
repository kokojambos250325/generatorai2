from typing import Any, Dict
import random
import base64
import io
import torch
from models.generation_request import GenerationRequest
from pipelines.base.base_pipeline import BasePipeline


class FreePipeline(BasePipeline):
    """
    Пайплайн для свободной генерации изображений по промпту
    
    Использует:
    - SDXL в качестве базовой модели
    - Различные LoRA для стилизации
    - VAE для качественного декодирования
    - Опционально ControlNet для дополнительного контроля
    """

    async def load_models(self) -> None:
        """
        Загрузка моделей для свободной генерации через model_manager
        
        Последовательность:
        1. SDXL base model для генерации
        2. VAE для качественного вывода
        3. Коллекция LoRA моделей для разных стилей (опционально)
        4. Upscaler для увеличения разрешения (опционально)
        """
        if not self.model_manager:
            raise ValueError("ModelManager is required for FreePipeline")
        
        # Загрузка SDXL для генерации "с нуля"
        self.models['sdxl'] = self.model_manager.get_sdxl()
        if not self.models['sdxl']:
            raise ValueError("Failed to load SDXL model")
        
        # LoRA модели загружаются динамически в prepare_inputs
        # в зависимости от стиля
        
        self.loaded = True

    async def prepare_inputs(self, request: GenerationRequest) -> Dict[str, Any]:
        """
        Подготовка входных данных для свободной генерации
        
        Процесс:
        1. Обработка текстового промпта
        2. Выбор и применение LoRA на основе стиля (realistic, anime, portrait)
        3. Настройка seed для воспроизводимости
        4. Подготовка параметров генерации (steps, guidance scale, size)
        5. Опциональная подготовка ControlNet условий
        
        Args:
            request: Запрос с полями:
                - prompt: текстовое описание
                - style: стиль генерации (опционально)
                - seed: значение seed (опционально)
                - control_type: тип ControlNet (pose/depth/struct/none) (опционально)
                - control_image: изображение для conditioning (опционально)
                - control_strength: сила conditioning (опционально, default 0.7)
            
        Returns:
            Подготовленные параметры:
            - prompt: обработанный промпт
            - negative_prompt: негативный промпт
            - seed: значение seed
            - style: выбранный стиль
            - generation_params: параметры генерации
            - control_type: тип ControlNet (если используется)
            - control_conditioning: данные для conditioning (если используется)
            - control_strength: сила conditioning (если используется)
        """
        # Обработка промпта
        base_prompt = request.prompt or "high quality, detailed, masterpiece"
        
        # Определение стиля
        style = request.style or "realistic"
        
        # Добавление стилевых суффиксов к промпту
        style_suffixes = {
            "realistic": ", photorealistic, 8k uhd, high detail",
            "anime": ", anime style, vibrant colors, detailed",
            "portrait": ", professional portrait, detailed face, sharp focus"
        }
        prompt = base_prompt + style_suffixes.get(style, "")
        
        # Конструкция негативного промпта
        negative_prompts = {
            "realistic": "cartoon, anime, low quality, blurry, distorted, bad anatomy",
            "anime": "photorealistic, low quality, blurry, bad anatomy",
            "portrait": "low quality, blurry, bad face, distorted features"
        }
        negative_prompt = negative_prompts.get(style, "low quality, blurry, distorted, bad anatomy")
        
        # Подготовка seed
        seed = request.seed if request.seed is not None else random.randint(0, 2**32 - 1)
        
        # Выбор LoRA на основе стиля
        lora_model = None
        if style in ['realistic', 'anime', 'portrait']:
            lora_model = self.model_manager.get_lora(style)
        
        # Базовый результат
        result = {
            'prompt': prompt,
            'negative_prompt': negative_prompt,
            'seed': seed,
            'style': style,
            'lora_model': lora_model,
            'generation_params': {
                'num_inference_steps': 50,
                'guidance_scale': 7.5,
                'width': 1024,
                'height': 1024
            },
            # Post-processing parameters
            'quality_mode': getattr(request, 'quality_mode', 'balanced'),
            'enhance_face': getattr(request, 'enhance_face', True),
            'upscale': getattr(request, 'upscale', False)
        }
        
        # Обработка опциональных ControlNet параметров
        control_type = getattr(request, 'control_type', None)
        if control_type and control_type in ['pose', 'depth', 'struct']:
            # Валидация control_type
            result['control_type'] = control_type
            
            # Подготовка ControlNet входных данных через базовый класс
            if hasattr(request, 'control_image') and request.control_image:
                from pipelines.controlnet_base import ControlNetPipelineBase
                base = ControlNetPipelineBase(self.device, self.model_manager)
                controlnet_inputs = base.prepare_controlnet_inputs(request, control_type)
                result['control_conditioning'] = controlnet_inputs.get('control_image')
                result['control_strength'] = controlnet_inputs.get('control_strength', 0.8)
            else:
                result['control_conditioning'] = None
                result['control_strength'] = getattr(request, 'control_strength', 0.8)
        
        return result

    async def run(self, inputs: Dict[str, Any]) -> Any:
        """
        Выполнение свободной генерации с SDXL и опциональным ControlNet
        
        Процесс:
        1. Получение SDXL pipeline из self.models
        2. Проверка наличия ControlNet параметров
        3. Если ControlNet указан - загрузка модели и интеграция
        4. Применение стиля через LoRA (если указан)
        5. Генерация с использованием SDXL (+ ControlNet если есть)
        6. Опциональный апскейл результата
        7. Постобработка изображения
        8. Кодирование в base64
        
        Args:
            inputs: Подготовленные входные данные с ключами:
                - prompt: текстовый промпт
                - negative_prompt: негативный промпт
                - seed: значение seed
                - generation_params: параметры генерации
                - control_type: тип ControlNet (опционально)
                - control_conditioning: данные conditioning (опционально)
                - control_strength: сила conditioning (опционально)
            
        Returns:
            Сгенерированное изображение в base64
        """
        # Получение SDXL pipeline
        sdxl_pipeline = self.models['sdxl']
        
        # Проверка наличия ControlNet параметров
        control_type = inputs.get('control_type')
        use_controlnet = control_type is not None and control_type in ['pose', 'depth', 'struct']
        
        # Загрузка и интеграция ControlNet если требуется
        active_pipeline = sdxl_pipeline
        control_image = None
        
        if use_controlnet and self.model_manager:
            # Получение соответствующей ControlNet модели
            controlnet_model = None
            if control_type == 'pose':
                controlnet_model = self.model_manager.get_controlnet_pose()
            elif control_type == 'depth':
                controlnet_model = self.model_manager.get_controlnet_depth()
            elif control_type == 'struct':
                controlnet_model = self.model_manager.get_controlnet_struct()
            
            # Интеграция ControlNet с SDXL если модель загружена
            if controlnet_model:
                from pipelines.controlnet_base import ControlNetPipelineBase
                base = ControlNetPipelineBase(self.device, self.model_manager)
                active_pipeline = base.attach_controlnet_to_sdxl(
                    sdxl_pipeline, [controlnet_model]
                )
                # Получаем control_image если он был подготовлен
                control_image = inputs.get('control_conditioning')
                print(f"ControlNet {control_type} integrated successfully")
            else:
                print(f"Warning: ControlNet {control_type} failed to load, using base SDXL")
        
        # Применение LoRA (если есть)
        # TODO: Будущая реализация LoRA
        # if inputs.get('lora_model'):
        #     sdxl_pipeline.load_lora_weights(inputs['lora_model'])
        
        # Настройка generator для seed
        generator = torch.Generator(device=self.device).manual_seed(inputs['seed'])
        
        # Подготовка параметров генерации
        generation_kwargs = {
            'prompt': inputs['prompt'],
            'negative_prompt': inputs['negative_prompt'],
            'generator': generator,
            **inputs['generation_params']
        }
        
        # Добавляем ControlNet параметры если используется
        if use_controlnet and control_image is not None:
            generation_kwargs['image'] = control_image
            generation_kwargs['controlnet_conditioning_scale'] = inputs.get('control_strength', 0.8)
        
        # Генерация
        result = active_pipeline(**generation_kwargs).images[0]
        
        # Post-processing with PostProcessPipeline
        from pipelines.postprocess import PostProcessPipeline
        
        post_processor = PostProcessPipeline(device=self.device, model_manager=self.model_manager)
        await post_processor.load_models()
        
        # Extract quality settings from inputs
        quality_mode = inputs.get('quality_mode', 'balanced')
        enable_face_enhance = inputs.get('enhance_face', True)
        enable_upscale = inputs.get('upscale', False)
        
        # Apply post-processing and get base64 result
        result_base64 = post_processor.finalize(
            result,
            quality_mode=quality_mode,
            enable_face_enhance=enable_face_enhance,
            enable_upscale=enable_upscale
        )
        
        return result_base64


async def generate_free():
    """Свободная генерация (deprecated, используйте FreePipeline)"""
    pass


async def run(request: GenerationRequest):
    """
    Пайплайн свободной генерации
    
    Будущая логика:
    1. Использование текстового промпта из request.prompt
    2. Применение стиля из request.style (если указан)
    3. Использование seed для воспроизводимости (если указан)
    4. Отправка на GPU-сервер для генерации изображения
    5. Возврат сгенерированного изображения
    
    Args:
        request: Параметры генерации с полями prompt, style, seed
        
    Returns:
        Результат генерации (изображение в base64)
    """
    pipeline = FreePipeline()
    return await pipeline.run(request)
