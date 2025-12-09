import asyncio
import time
from typing import Optional
from config import Settings, get_settings
from services.generation_service import GenerationService
from queue.task_queue import TaskQueue, Task, TaskStatus
from logger.generation_logger import GenerationLogger
from client_gpu import GPUClient
from gpu_server.schema import GPUGenerationRequest


class Worker:
    """
    Воркер для обработки задач генерации из очереди
    
    Периодически опрашивает очередь задач, извлекает задачи
    и передаёт их в GenerationService для обработки.
    """

    def __init__(
        self,
        settings: Optional[Settings] = None,
        poll_interval: int = 5
    ):
        """
        Инициализация воркера
        
        Args:
            settings: Настройки приложения
            poll_interval: Интервал опроса очереди в секундах
        """
        self.settings = settings or get_settings()
        self.poll_interval = poll_interval
        self.running = False
        
        # Инициализация компонентов
        self.task_queue = TaskQueue(backend="memory")
        self.generation_service = GenerationService(settings=self.settings)
        self.logger = GenerationLogger(
            output_format="console",
            log_level=self.settings.LOG_LEVEL
        )
        
        # Инициализация GPU клиента
        self.gpu_client = GPUClient(
            base_url=self.settings.GPU_SERVER_URL,
            api_key=self.settings.GPU_SERVER_API_KEY,
            timeout=self.settings.GPU_TIMEOUT_GENERATION,
            max_retries=self.settings.GPU_RETRY_ATTEMPTS,
            circuit_breaker_threshold=self.settings.GPU_CIRCUIT_BREAKER_THRESHOLD,
            circuit_breaker_timeout=self.settings.GPU_CIRCUIT_BREAKER_TIMEOUT
        )

    async def start_loop(self) -> None:
        """
        Запуск основного цикла обработки задач
        
        Бесконечный цикл, который:
        1. Опрашивает очередь на наличие задач в статусе PENDING
        2. Извлекает задачи из очереди
        3. Передаёт каждую задачу в GenerationService.process_task
        4. Обновляет статус задачи в очереди
        5. Повторяет через poll_interval секунд
        """
        self.running = True
        self.logger.log_update(
            task_id="worker",
            status="started",
            message="Worker started and listening for tasks"
        )
        
        while self.running:
            try:
                # Получение задач в статусе QUEUED
                pending_tasks = await self.task_queue.fetch_pending_tasks(limit=10)
                
                if pending_tasks:
                    self.logger.log_update(
                        task_id="worker",
                        status="processing",
                        message=f"Found {len(pending_tasks)} pending tasks"
                    )
                    
                    # Обработка каждой задачи
                    for task in pending_tasks:
                        # Перевод задачи в статус PROCESSING
                        from queue.task_queue import TaskStatus
                        task.status = TaskStatus.PROCESSING
                        
                        # Обработка задачи
                        await self.process_single_task(task)
                
                # Задержка перед следующим опросом
                await asyncio.sleep(self.poll_interval)
                
            except Exception as e:
                self.logger.log_error(
                    task_id="worker",
                    error=f"Error in worker loop: {str(e)}",
                    exception=e
                )
                # Продолжаем работу даже при ошибке
                await asyncio.sleep(self.poll_interval)

    async def process_single_task(self, task: Task) -> None:
        """
        Обработка одной задачи через GPU сервер
        
        Args:
            task: Задача для обработки
        """
        start_time = time.time()
        correlation_id = self.logger.generate_correlation_id(task.task_id)
        
        try:
            # Создание объекта запроса из параметров задачи
            from models.generation_request import GenerationRequest
            
            request = GenerationRequest(**task.params)
            
            # Обновление статуса задачи на PROCESSING
            task.status = TaskStatus.PROCESSING
            
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
            
            # Логирование начала отправки на GPU
            self.logger.log_gpu_submit_start(
                task_id=task.task_id,
                mode=request.mode,
                retry_count=0,
                correlation_id=correlation_id
            )
            
            submit_start = time.time()
            
            # Отправка задачи на GPU-сервер
            async with self.gpu_client as client:
                gpu_task_id = await client.send_task(gpu_request)
                
                submit_time = (time.time() - submit_start) * 1000  # в миллисекундах
                
                # Логирование успешной отправки
                self.logger.log_gpu_submit_success(
                    task_id=task.task_id,
                    gpu_task_id=gpu_task_id,
                    response_time_ms=submit_time,
                    correlation_id=correlation_id
                )
                
                # Опрос статуса GPU задачи с адаптивным интервалом
                poll_count = 0
                current_interval = self.settings.GPU_POLL_INTERVAL_MIN
                poll_start = time.time()
                
                while True:
                    elapsed = time.time() - poll_start
                    
                    # Проверка таймаута
                    if elapsed > self.settings.GPU_TIMEOUT_GENERATION:
                        self.logger.log_gpu_timeout(
                            task_id=task.task_id,
                            elapsed_time_s=elapsed,
                            timeout_threshold_s=self.settings.GPU_TIMEOUT_GENERATION,
                            correlation_id=correlation_id
                        )
                        raise Exception(f"GPU task {gpu_task_id} timeout after {elapsed:.1f}s")
                    
                    poll_count += 1
                    
                    # Логирование начала опроса
                    self.logger.log_gpu_poll_start(
                        task_id=task.task_id,
                        gpu_task_id=gpu_task_id,
                        poll_count=poll_count,
                        correlation_id=correlation_id
                    )
                    
                    # Проверка статуса
                    status = await client.check_status(gpu_task_id)
                    
                    # Логирование прогресса
                    self.logger.log_gpu_poll_progress(
                        task_id=task.task_id,
                        status=status.status,
                        progress_percent=status.progress,
                        message=status.message,
                        correlation_id=correlation_id
                    )
                    
                    if status.status == "completed":
                        # Получение результата
                        result = await client.get_result(gpu_task_id)
                        
                        total_time = time.time() - start_time
                        result_size = len(result.result_image) / 1024 if result.result_image else 0  # KB
                        
                        # Логирование получения результата
                        self.logger.log_gpu_result_retrieved(
                            task_id=task.task_id,
                            result_size_kb=result_size,
                            total_processing_time_s=total_time,
                            correlation_id=correlation_id
                        )
                        
                        # Отметка задачи как выполненной
                        await self.task_queue.mark_done(
                            task_id=task.task_id,
                            result=result.result_image
                        )
                        break
                        
                    elif status.status == "failed":
                        # Задача завершилась с ошибкой
                        raise Exception(f"GPU task failed: {status.error}")
                    
                    # Адаптивный интервал опроса
                    if elapsed > 30:
                        current_interval = min(
                            current_interval * 1.5,
                            self.settings.GPU_POLL_INTERVAL_MAX
                        )
                    
                    await asyncio.sleep(current_interval)
            
        except Exception as e:
            # Логирование ошибки
            self.logger.log_gpu_submit_failure(
                task_id=task.task_id,
                error_type=type(e).__name__,
                error_message=str(e),
                retry_count=0,
                will_retry=False,
                correlation_id=correlation_id
            )
            
            # Отметка задачи как завершённой с ошибкой
            await self.task_queue.mark_done(
                task_id=task.task_id,
                error=str(e)
            )

    async def stop(self) -> None:
        """
        Остановка воркера
        
        Завершает текущий цикл обработки и освобождает ресурсы.
        """
        pass
