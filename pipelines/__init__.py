"""
Пакет пайплайнов генерации

Содержит реализации различных типов генерации изображений:
- ClothesPipeline: генерация одежды с использованием ControlNet
- FaceSwapPipeline: замена лица с использованием InsightFace
- FaceConsistentPipeline: генерация с сохранением идентичности лица
- FreePipeline: свободная генерация текст-в-изображение

Все пайплайны наследуются от BasePipeline и регистрируются в PIPELINE_REGISTRY.
"""

# Импорт базового класса
from pipelines.base.base_pipeline import BasePipeline

# Импорт конкретных пайплайнов
from pipelines.clothes import ClothesPipeline
from pipelines.face_swap import FaceSwapPipeline
from pipelines.face_consistent import FaceConsistentPipeline
from pipelines.free import FreePipeline

# Импорт реестра
from pipelines.registry import (
    PIPELINE_REGISTRY,
    get_pipeline_by_mode,
    register_pipeline,
    get_available_modes
)

__all__ = [
    # Базовый класс
    "BasePipeline",
    
    # Конкретные пайплайны
    "ClothesPipeline",
    "FaceSwapPipeline",
    "FaceConsistentPipeline",
    "FreePipeline",
    
    # Реестр и утилиты
    "PIPELINE_REGISTRY",
    "get_pipeline_by_mode",
    "register_pipeline",
    "get_available_modes",
]
