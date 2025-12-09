from typing import Optional
from pydantic import BaseModel, Field


class GPUGenerationRequest(BaseModel):
    """
    Запрос на генерацию для GPU-сервера
    """
    mode: str = Field(..., description="Режим генерации: free, clothes, face_swap, face_consistent")
    prompt: Optional[str] = Field(None, description="Текстовый промпт")
    image: Optional[str] = Field(None, description="Базовое изображение (base64)")
    face_image: Optional[str] = Field(None, description="Изображение лица (base64)")
    clothes_image: Optional[str] = Field(None, description="Изображение одежды (base64)")
    style: Optional[str] = Field(None, description="Стиль генерации")
    seed: Optional[int] = Field(None, description="Seed для воспроизводимости")


class GPUGenerationStatus(BaseModel):
    """
    Статус задачи на GPU-сервере
    """
    task_id: str = Field(..., description="ID задачи на GPU-сервере")
    status: str = Field(..., description="Статус: pending, processing, completed, failed")
    progress: Optional[float] = Field(None, description="Прогресс выполнения (0.0-1.0)")
    message: Optional[str] = Field(None, description="Сообщение о текущем состоянии")
    error: Optional[str] = Field(None, description="Описание ошибки (если есть)")


class GPUGenerationResult(BaseModel):
    """
    Результат генерации с GPU-сервера
    """
    task_id: str = Field(..., description="ID задачи на GPU-сервере")
    status: str = Field(..., description="Финальный статус задачи")
    result_image: Optional[str] = Field(None, description="Результат генерации (base64)")
    error: Optional[str] = Field(None, description="Описание ошибки (если есть)")
