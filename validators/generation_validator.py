"""
Валидатор запросов генерации

Проверяет корректность входных данных перед обработкой пайплайнами.
"""

from typing import Optional
from models.generation_request import GenerationRequest


class GenerationValidator:
    """
    Валидатор для проверки запросов генерации
    
    Выполняет проверки:
    - Корректность режима генерации (mode)
    - Наличие обязательных полей для каждого режима
    - Валидность параметров (размеры, seed, и т.д.)
    - Формат изображений (base64, пути к файлам)
    """
    
    VALID_MODES = ['face_swap', 'face_consistent', 'clothes', 'free']
    
    def __init__(self):
        """Инициализация валидатора"""
        self.errors: list[str] = []
    
    def validate_request(self, request: GenerationRequest) -> GenerationRequest:
        """
        Валидация запроса генерации
        
        Проверяет запрос на корректность и наличие всех необходимых полей
        в зависимости от режима генерации.
        
        Проверки по режимам:
        - face_swap: требуется face_image и target_image
        - face_consistent: требуется face_image и prompt
        - clothes: требуется clothes_image (и опционально base_image)
        - free: требуется prompt
        
        Args:
            request: Запрос на валидацию
            
        Returns:
            Валидированный запрос (пока без изменений)
            
        Raises:
            ValueError: Если валидация не прошла
        
        Будущая реализация:
        ```python
        self.errors = []
        
        # Проверка режима
        if not hasattr(request, 'mode') or not request.mode:
            self.errors.append("Field 'mode' is required")
        elif request.mode not in self.VALID_MODES:
            self.errors.append(f"Invalid mode: {request.mode}. Must be one of {self.VALID_MODES}")
        
        # Проверка полей в зависимости от режима
        if request.mode == 'face_swap':
            if not hasattr(request, 'face_image') or not request.face_image:
                self.errors.append("Field 'face_image' is required for face_swap mode")
            if not hasattr(request, 'target_image') or not request.target_image:
                self.errors.append("Field 'target_image' is required for face_swap mode")
        
        elif request.mode == 'face_consistent':
            if not hasattr(request, 'face_image') or not request.face_image:
                self.errors.append("Field 'face_image' is required for face_consistent mode")
            if not hasattr(request, 'prompt') or not request.prompt:
                self.errors.append("Field 'prompt' is required for face_consistent mode")
        
        elif request.mode == 'clothes':
            if not hasattr(request, 'clothes_image') or not request.clothes_image:
                self.errors.append("Field 'clothes_image' is required for clothes mode")
        
        elif request.mode == 'free':
            if not hasattr(request, 'prompt') or not request.prompt:
                self.errors.append("Field 'prompt' is required for free mode")
        
        # Опциональные проверки параметров
        if hasattr(request, 'seed') and request.seed is not None:
            if not isinstance(request.seed, int) or request.seed < 0:
                self.errors.append("Field 'seed' must be a positive integer")
        
        if hasattr(request, 'width') and request.width is not None:
            if request.width not in [512, 768, 1024, 1280, 1536]:
                self.errors.append("Field 'width' must be one of [512, 768, 1024, 1280, 1536]")
        
        if hasattr(request, 'height') and request.height is not None:
            if request.height not in [512, 768, 1024, 1280, 1536]:
                self.errors.append("Field 'height' must be one of [512, 768, 1024, 1280, 1536]")
        
        # Если есть ошибки - выбрасываем исключение
        if self.errors:
            raise ValueError(f"Validation failed: {'; '.join(self.errors)}")
        
        return request
        ```
        """
        # Пока возвращаем без изменений (заглушка)
        return request
    
    def validate_image_field(self, image_data: Optional[str], field_name: str) -> bool:
        """
        Проверка корректности поля с изображением
        
        Проверяет что изображение либо валидный base64, либо существующий файл.
        
        Args:
            image_data: Данные изображения (base64 или путь)
            field_name: Название поля для ошибки
            
        Returns:
            True если валидно
        
        Будущая реализация:
        ```python
        import base64
        import os
        
        if not image_data:
            return False
        
        # Проверка на base64
        try:
            base64.b64decode(image_data)
            return True
        except Exception:
            pass
        
        # Проверка на файл
        if os.path.isfile(image_data):
            return True
        
        self.errors.append(f"Field '{field_name}' must be valid base64 or file path")
        return False
        ```
        """
        return True
    
    def get_errors(self) -> list[str]:
        """
        Получение списка ошибок валидации
        
        Returns:
            Список сообщений об ошибках
        """
        return self.errors
    
    def clear_errors(self) -> None:
        """Очистка списка ошибок"""
        self.errors = []
