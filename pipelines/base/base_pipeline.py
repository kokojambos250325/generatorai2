from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

# TYPE_CHECKING для избежания циклических импортов
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from models.model_manager import ModelManager


class BasePipeline(ABC):
    """
    Базовый абстрактный класс для всех пайплайнов генерации
    
    Определяет общий интерфейс для загрузки моделей, подготовки данных и генерации.
    Все конкретные пайплайны должны наследоваться от этого класса.
    """
    
    def __init__(self, device: str = "cuda", model_manager: Optional["ModelManager"] = None):
        """
        Инициализация базового пайплайна
        
        Args:
            device: Устройство для вычислений ("cuda" или "cpu")
            model_manager: Менеджер моделей для загрузки и кэширования
        """
        self.device = device
        self.model_manager = model_manager
        self.models: Dict[str, Any] = {}
        self.models_loaded = False
        self.loaded: bool = False
    
    @abstractmethod
    async def load_models(self) -> None:
        """
        Загрузка моделей для генерации через model_manager
        
        Этот метод должен:
        1. Использовать self.model_manager для получения необходимых моделей
        2. Загрузить SDXL через model_manager.get_sdxl()
        3. При необходимости загрузить ControlNet через model_manager.get_controlnet()
        4. При необходимости загрузить LoRA через model_manager.get_lora()
        5. При необходимости загрузить InsightFace через model_manager.get_insightface()
        6. Сохранить загруженные модели в self.models
        7. Установить self.loaded = True после успешной загрузки
        
        Raises:
            ValueError: Если model_manager не был передан при инициализации
        
        Example:
            >>> async def load_models(self):
            >>>     if not self.model_manager:
            >>>         raise ValueError("ModelManager is required")
            >>>     self.models['sdxl'] = self.model_manager.get_sdxl()
            >>>     self.loaded = True
        """
        pass
    
    @abstractmethod
    async def prepare_inputs(self, request: Any) -> Dict[str, Any]:
        """
        Подготовка входных данных для генерации
        
        Преобразует запрос пользователя в формат,
        необходимый для конкретной модели генерации.
        
        Args:
            request: Объект запроса с параметрами генерации
            
        Returns:
            Подготовленные входные данные для модели
        """
        pass
    
    @abstractmethod
    async def run(self, inputs: Dict[str, Any]) -> Any:
        """
        Выполнение генерации
        
        Запускает процесс генерации на основе подготовленных входных данных.
        
        Args:
            inputs: Подготовленные входные данные
            
        Returns:
            Результат генерации (изображение в base64 или другие данные)
        """
        pass
