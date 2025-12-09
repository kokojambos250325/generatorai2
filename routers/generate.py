from fastapi import APIRouter, HTTPException
from models.generation_request import GenerationRequest
from models.generation_response import GenerationResponse
from utils.ids import generate_task_id
from queue.task_queue import TaskQueue, Task, TaskStatus
from client_gpu import GPUClient
from gpu_server.schema import GPUGenerationRequest
from config import get_settings

router = APIRouter(prefix="/generate", tags=["generation"])

# Инициализация очереди задач
task_queue = TaskQueue(backend="memory")

# Инициализация GPU клиента с расширенными параметрами
settings = get_settings()
gpu_client = GPUClient(
    base_url=settings.GPU_SERVER_URL,
    api_key=settings.GPU_SERVER_API_KEY,
    timeout=settings.GPU_TIMEOUT_GENERATION,
    max_retries=settings.GPU_RETRY_ATTEMPTS,
    circuit_breaker_threshold=settings.GPU_CIRCUIT_BREAKER_THRESHOLD,
    circuit_breaker_timeout=settings.GPU_CIRCUIT_BREAKER_TIMEOUT
)


@router.post("", response_model=GenerationResponse)
async def create_generation(request: GenerationRequest) -> GenerationResponse:
    """
    Создание задачи генерации
    
    Принимает запрос на генерацию, создаёт задачу в очереди,
    отправляет на GPU-сервер и возвращает ID задачи для отслеживания статуса.
    """
    # Генерация уникального ID задачи
    task_id = generate_task_id(prefix=request.mode)
    
    # Создание задачи
    task = Task(
        task_id=task_id,
        task_type=request.mode,
        params=request.model_dump()
    )
    
    # Добавление задачи в очередь
    await task_queue.enqueue(task)
    
    # Подготовка запроса для GPU-сервера
    gpu_request = GPUGenerationRequest(
        mode=request.mode,
        prompt=request.prompt,
        image=request.image,
        face_image=request.face_image,
        clothes_image=request.clothes_image,
        style=request.style,
        seed=request.seed
    )
    
    # Отправка задачи на GPU-сервер
    async with gpu_client as client:
        gpu_task_id = await client.send_task(gpu_request)
    # Сохраняем соответствие между backend-задачей и GPU-задачей
    task.gpu_task_id = gpu_task_id
    
    # Возврат ответа с ID задачи
    return GenerationResponse(
        task_id=task_id,
        status="queued",
        message="Task has been queued for processing"
    )


@router.get("/result/{task_id}", response_model=GenerationResponse)
async def get_generation_result(task_id: str) -> GenerationResponse:
    """
    Получение результата генерации по task_id
    
    Возвращает результат генерации если задача завершена,
    или текущий статус если задача еще обрабатывается.
    
    Args:
        task_id: Уникальный ID задачи генерации
        
    Returns:
        GenerationResponse с результатом или статусом
        
    Raises:
        HTTPException: Если задача не найдена (404)
    """
    # Получение задачи из очереди
    task = await task_queue.get_task(task_id)
    
    if task is None:
        raise HTTPException(
            status_code=404,
            detail=f"Task with ID {task_id} not found"
        )
    
    # Если уже завершена или упала — возвращаем как есть
    if task.status == TaskStatus.DONE:
        return GenerationResponse(
            task_id=task_id,
            status="completed",
            result_image=task.result,
            message="Generation completed successfully"
        )
    elif task.status == TaskStatus.FAILED:
        return GenerationResponse(
            task_id=task_id,
            status="failed",
            message=f"Generation failed: {task.error}"
        )
    
    # Если задача в очереди/обрабатывается и привязана к GPU — проверяем статус на GPU сервере
    if task.gpu_task_id:
        async with gpu_client as client:
            gpu_status = await client.check_status(task.gpu_task_id)
            
            if gpu_status.status == "completed":
                gpu_result = await client.get_result(task.gpu_task_id)
                # Обновляем локальную очередь как DONE
                await task_queue.mark_done(task_id, result=gpu_result.result_image)
                return GenerationResponse(
                    task_id=task_id,
                    status="completed",
                    result_image=gpu_result.result_image,
                    message="Generation completed successfully"
                )
            elif gpu_status.status == "failed":
                await task_queue.mark_done(task_id, error=gpu_status.error or "GPU task failed")
                return GenerationResponse(
                    task_id=task_id,
                    status="failed",
                    message=f"Generation failed: {gpu_status.error or 'Unknown error'}"
                )
            else:
                # pending/processing — возвращаем промежуточный статус
                mapped_status = "processing" if gpu_status.status == "processing" else "queued"
                return GenerationResponse(
                    task_id=task_id,
                    status=mapped_status,
                    message=gpu_status.message or f"Task is currently {gpu_status.status} on GPU server"
                )
    
    # Фолбэк: нет gpu_task_id — возвращаем локальный статус
    if task.status == TaskStatus.PROCESSING:
        return GenerationResponse(
            task_id=task_id,
            status="processing",
            message="Task is currently being processed"
        )
    elif task.status == TaskStatus.QUEUED:
        return GenerationResponse(
            task_id=task_id,
            status="queued",
            message="Task is queued and waiting for processing"
        )
    else:
        return GenerationResponse(
            task_id=task_id,
            status=task.status.value,
            message=f"Task status: {task.status.value}"
        )
