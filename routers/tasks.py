from fastapi import APIRouter, HTTPException
from models.generation_response import GenerationResponse
from queue.task_queue import TaskQueue, TaskStatus

router = APIRouter(prefix="/task", tags=["tasks"])

# Инициализация очереди задач
task_queue = TaskQueue(backend="memory")


@router.get("/{task_id}", response_model=GenerationResponse)
async def get_task_status(task_id: str) -> GenerationResponse:
    """
    Получение статуса задачи генерации
    
    Возвращает текущий статус задачи, результат (если готов)
    и дополнительную информацию.
    
    Args:
        task_id: Уникальный ID задачи
        
    Returns:
        Информация о статусе задачи
        
    Raises:
        HTTPException: Если задача не найдена
    """
    # Получение статуса задачи из очереди
    status = await task_queue.get_status(task_id)
    
    if status is None:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Получение полной информации о задаче
    task = await task_queue.get_task(task_id)
    
    # Преобразование статуса TaskStatus в строку
    status_str = status.value if status else "unknown"
    
    # Формирование ответа
    response = GenerationResponse(
        task_id=task_id,
        status=status_str,
        result_image=None,  # Пока без результата
        message=None
    )
    
    # Добавление результата если задача завершена
    if task and status == TaskStatus.DONE:
        # Подготовка для получения результата с GPU-сервера
        # TODO: Интеграция с GPUClient для получения result_image
        response.result_image = task.result.get("image") if task.result else None
        response.message = "Task completed successfully"
    elif task and status == TaskStatus.FAILED:
        response.message = f"Task failed: {task.error}"
    elif status == TaskStatus.PROCESSING:
        response.message = "Task is being processed"
    elif status == TaskStatus.QUEUED:
        response.message = "Task is queued for processing"
    
    return response
