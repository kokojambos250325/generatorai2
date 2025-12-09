from typing import Any, Dict
from models.generation_request import GenerationRequest
from pipelines.base.base_pipeline import BasePipeline


class FaceSwapPipeline(BasePipeline):
    """
    Пайплайн для замены лица на изображении
    
    Использует:
    - InsightFace для детекции и извлечения признаков лица
    - SDXL Inpainting для качественной замены области лица
    - ControlNet для сохранения позы и выражения
    - Face restoration модели для улучшения качества
    """

    async def load_models(self) -> None:
        """
        Загрузка моделей для замены лица через model_manager
        
        Последовательность загрузки:
        1. InsightFace для детекции и извлечения эмбеддингов лиц
        2. Face swapper модель (inswapper) для замены
        3. Face enhancer (GFPGAN/CodeFormer) для улучшения качества
        4. Опционально: SDXL для дополнительной генерации
        """
        if not self.model_manager:
            raise ValueError("ModelManager is required")
        
        # Загрузка InsightFace для работы с лицами
        self.models['insightface'] = self.model_manager.get_insightface()
        if not self.models['insightface']:
            raise ValueError("Failed to load InsightFace model")
        
        # Загрузка face swapper
        from models.face_swapper import FaceSwapper
        self.models['swapper'] = FaceSwapper(device=self.device)
        if not self.models['swapper'].load_model():
            print("Warning: Face swapper model not loaded. Face swap will not work.")
        
        # Загрузка face enhancer для улучшения качества (опционально)
        from models.face_enhancer import FaceEnhancer
        self.models['enhancer'] = FaceEnhancer(model_type="gfpgan", device=self.device)
        # Пробуем загрузить, но не критично если не удалось
        if not self.models['enhancer'].load_model():
            print("Warning: Face enhancer not loaded. Enhancement will be skipped.")
        
        # Опционально: Загрузка SDXL для дополнительной генерации
        # self.models['sdxl'] = self.model_manager.get_sdxl()
        
        self.loaded = True

    async def prepare_inputs(self, request: GenerationRequest) -> Dict[str, Any]:
        """
        Подготовка входных данных для замены лица
        
        Процесс подготовки:
        1. Загрузка исходного изображения (target) и изображения лица (source)
        2. Детекция лиц на обоих изображениях через InsightFace
        3. Извлечение эмбеддингов лица-источника
        4. Определение целевого лица для замены
        5. Сохранение bbox и ключевых точек для точной замены
        
        Args:
            request: Запрос с полями:
                - image: целевое изображение (путь или base64)
                - face_image: лицо-источник для замены (путь или base64)
            
        Returns:
            Подготовленные данные:
            - source_face: объект лица-источника с эмбеддингом
            - target_image: целевое изображение (numpy array)
            - target_faces: список обнаруженных лиц на целевом изображении
            - selected_face_index: индекс лица для замены (самое большое)
        """
        import cv2
        import base64
        import numpy as np
        from io import BytesIO
        from PIL import Image
        
        # Получение InsightFace app
        face_app = self.models.get('insightface')
        if not face_app:
            raise ValueError("InsightFace model not loaded")
        
        # Функция для загрузки изображения из разных форматов
        def load_image(image_data: str) -> np.ndarray:
            """ Загрузка изображения из base64 или пути к файлу """
            # Проверяем, является ли это путем к файлу
            import os
            if os.path.exists(image_data):
                # Загрузка из файла
                img = cv2.imread(image_data)
                if img is None:
                    raise ValueError(f"Failed to load image from {image_data}")
                return img
            else:
                # Загрузка из base64
                try:
                    # Удаляем префикс data:image/..., если он есть
                    if 'base64,' in image_data:
                        image_data = image_data.split('base64,')[1]
                    
                    image_bytes = base64.b64decode(image_data)
                    pil_image = Image.open(BytesIO(image_bytes))
                    # Конвертируем PIL RGB в OpenCV BGR
                    img = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
                    return img
                except Exception as e:
                    raise ValueError(f"Failed to decode image from base64: {e}")
        
        # Загрузка изображений
        if not request.face_image:
            raise ValueError("face_image is required for face swap")
        if not request.image:
            raise ValueError("image (target image) is required for face swap")
        
        source_img = load_image(request.face_image)
        target_img = load_image(request.image)
        
        # Детекция лиц на источнике
        source_faces = face_app.get(source_img)
        if not source_faces:
            raise ValueError("No faces detected in source image (face_image)")
        
        # Детекция лиц на целевом изображении
        target_faces = face_app.get(target_img)
        if not target_faces:
            raise ValueError("No faces detected in target image")
        
        # Выбор самого большого лица из источника
        source_face = max(source_faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))
        
        # Выбор самого большого лица из целевого изображения
        # (или можно добавить логику выбора по индексу)
        target_faces_sorted = sorted(target_faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]), reverse=True)
        selected_face_index = 0  # Индекс самого большого лица
        
        return {
            'source_face': source_face,
            'target_image': target_img,
            'target_faces': target_faces_sorted,
            'selected_face_index': selected_face_index,
            'original_request': request,
            # Post-processing parameters
            'quality_mode': getattr(request, 'quality_mode', 'balanced'),
            'enhance_face': getattr(request, 'enhance_face', True),
            'upscale': getattr(request, 'upscale', False)
        }

    async def run(self, inputs: Dict[str, Any]) -> Any:
        """
        Выполнение замены лица
        
        Поэтапный процесс замены:
        1. Извлечение подготовленных данных (source_face, target_image, target_faces)
        2. Применение face swapper для замены лица
        3. Улучшение качества заменённого лица через face enhancer
        4. Блендинг результата с исходным изображением для естественного вида
        5. Кодирование результата в base64
        
        Args:
            inputs: Подготовленные входные данные с ключами:
                - source_face: лицо-источник
                - target_image: целевое изображение
                - target_faces: список лиц на целевом изображении
                - selected_face_index: индекс лица для замены
            
        Returns:
            Изображение с заменённым лицом в base64
        """
        import base64
        import cv2
        
        # Извлечение данных
        source_face = inputs['source_face']
        target_image = inputs['target_image']
        target_faces = inputs['target_faces']
        selected_index = inputs['selected_face_index']
        
        # Получение целевого лица для замены
        target_face = target_faces[selected_index]
        
        # Замена лица
        swapper = self.models.get('swapper')
        if swapper and swapper.loaded:
            result_image = swapper.swap_face(
                source_face=source_face,
                target_image=target_image,
                target_face=target_face
            )
        else:
            print("Warning: Face swapper not loaded, returning original image")
            result_image = target_image
        
        # Post-processing with PostProcessPipeline
        from pipelines.postprocess import PostProcessPipeline
        from PIL import Image
        
        # Convert result_image (numpy BGR) to PIL Image
        result_rgb = result_image[:, :, ::-1]  # BGR to RGB
        result_pil = Image.fromarray(result_rgb)
        
        post_processor = PostProcessPipeline(device=self.device, model_manager=self.model_manager)
        await post_processor.load_models()
        
        # Extract quality settings from inputs
        quality_mode = inputs.get('quality_mode', 'balanced')
        enable_face_enhance = inputs.get('enhance_face', True)
        enable_upscale = inputs.get('upscale', False)
        
        # Apply post-processing and get base64 result
        image_base64 = post_processor.finalize(
            result_pil,
            quality_mode=quality_mode,
            enable_face_enhance=enable_face_enhance,
            enable_upscale=enable_upscale
        )
        
        return image_base64


async def swap_face():
    """Замена лица (deprecated, используйте FaceSwapPipeline)"""
    pass


async def run(request: GenerationRequest):
    """
    Пайплайн замены лица
    
    Будущая логика:
    1. Получение исходного изображения из request.image
    2. Получение изображения лица из request.face_image
    3. Детекция лица на исходном изображении
    4. Замена лица с сохранением позы и освещения
    5. Отправка на GPU-сервер для обработки
    6. Возврат изображения с заменённым лицом
    
    Args:
        request: Параметры генерации с полями image, face_image
        
    Returns:
        Результат генерации (изображение в base64)
    """
    pipeline = FaceSwapPipeline()
    return await pipeline.run(request)
