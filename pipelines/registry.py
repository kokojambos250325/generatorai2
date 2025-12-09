from typing import Type, Optional
from pipelines.base.base_pipeline import BasePipeline
from pipelines.clothes import ClothesPipeline
from pipelines.face_swap import FaceSwapPipeline
from pipelines.face_consistent import FaceConsistentPipeline
from pipelines.free import FreePipeline
from models.model_manager import ModelManager


# Реестр пайплайнов: маппинг режима на класс пайплайна
PIPELINE_REGISTRY: dict[str, Type[BasePipeline]] = {
    "clothes": ClothesPipeline,
    "face_swap": FaceSwapPipeline,
    "face_consistent": FaceConsistentPipeline,
    "free": FreePipeline,
}


def get_pipeline_by_mode(
    mode: str, 
    device: str = "cuda", 
    model_manager: Optional[ModelManager] = None
) -> Optional[BasePipeline]:
    """
    Получение экземпляра пайплайна по режиму генерации
    
    Автоматически передаёт device и model_manager в конструктор пайплайна.
    Если model_manager не указан, создаётся новый экземпляр.
    
    Args:
        mode: Режим генерации (clothes, face_swap, face_consistent, free)
        device: Устройство для вычислений ("cuda" или "cpu")
        model_manager: Менеджер моделей (создаётся автоматически если None)
        
    Returns:
        Экземпляр соответствующего пайплайна или None если режим не найден
        
    Example:
        >>> manager = ModelManager(device="cuda")
        >>> pipeline = get_pipeline_by_mode("clothes", device="cuda", model_manager=manager)
        >>> await pipeline.load_models()
        >>> inputs = await pipeline.prepare_inputs(request)
        >>> result = await pipeline.run(inputs)
    """
    pipeline_class = PIPELINE_REGISTRY.get(mode)
    
    if pipeline_class is None:
        return None
    
    # Создание ModelManager если не передан
    if model_manager is None:
        model_manager = ModelManager(device=device)
    
    # Создание экземпляра пайплайна с device и model_manager
    return pipeline_class(device=device, model_manager=model_manager)


def register_pipeline(mode: str, pipeline_class: Type[BasePipeline]) -> None:
    """
    Регистрация нового пайплайна в реестре
    
    Позволяет динамически добавлять новые типы пайплайнов
    без изменения существующего кода.
    
    Args:
        mode: Режим генерации (ключ в реестре)
        pipeline_class: Класс пайплайна, наследующийся от BasePipeline
    """
    PIPELINE_REGISTRY[mode] = pipeline_class


def get_available_modes() -> list[str]:
    """
    Получение списка доступных режимов генерации
    
    Returns:
        Список доступных режимов
    """
    return list(PIPELINE_REGISTRY.keys())
