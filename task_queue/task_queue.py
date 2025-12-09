from typing import Any, Dict, Optional, List
from enum import Enum


# Хранилище задач в памяти (словарь: task_id -> Task)
QUEUE_STORAGE: Dict[str, "Task"] = {}


class TaskStatus(Enum):
    """Статусы задач в очереди"""
    PENDING = "pending"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    DONE = "done"
    FAILED = "failed"


class Task:
    """Модель задачи в очереди"""
    def __init__(self, task_id: str, task_type: str, params: Dict[str, Any]):
        self.task_id = task_id
        self.task_type = task_type
        self.params = params
        self.status = TaskStatus.QUEUED
        self.result: Optional[Any] = None
        self.error: Optional[str] = None
        self.gpu_task_id: Optional[str] = None


class TaskQueue:
    """
    Очередь задач для управления генерацией.
    Поддерживает как in-memory, так и Redis реализацию.
    """

    def __init__(self, backend: str = "memory"):
        """
        Инициализация очереди задач
        
        Args:
            backend: Тип бэкенда ('memory' или 'redis')
        """
        self.backend = backend
        self._init_backend()

    def _init_backend(self):
        """Инициализация выбранного бэкенда"""
        pass

    async def enqueue(self, task: Task) -> bool:
        """
        Добавление задачи в очередь
        
        Args:
            task: Объект задачи для добавления
            
        Returns:
            True если задача успешно добавлена
        """
        # Добавление задачи в хранилище
        QUEUE_STORAGE[task.task_id] = task
        task.status = TaskStatus.QUEUED
        return True

    async def dequeue(self) -> Optional[Task]:
        """
        Извлечение следующей задачи из очереди
        
        Returns:
            Объект задачи или None если очередь пуста
        """
        # Поиск первой задачи в статусе QUEUED
        for task_id, task in QUEUE_STORAGE.items():
            if task.status == TaskStatus.QUEUED:
                task.status = TaskStatus.PROCESSING
                return task
        return None

    async def mark_done(self, task_id: str, result: Any = None, error: Optional[str] = None) -> bool:
        """
        Отметка задачи как завершенной
        
        Args:
            task_id: ID задачи
            result: Результат выполнения задачи
            error: Сообщение об ошибке (если есть)
            
        Returns:
            True если задача успешно обновлена
        """
        if task_id not in QUEUE_STORAGE:
            return False
        
        task = QUEUE_STORAGE[task_id]
        
        if error:
            task.status = TaskStatus.FAILED
            task.error = error
        else:
            task.status = TaskStatus.DONE
            task.result = result
        
        return True

    async def get_task(self, task_id: str) -> Optional[Task]:
        """
        Получение задачи по ID
        
        Args:
            task_id: ID задачи
            
        Returns:
            Объект задачи или None если не найдена
        """
        return QUEUE_STORAGE.get(task_id)

    async def get_status(self, task_id: str) -> Optional[TaskStatus]:
        """
        Получение статуса задачи
        
        Args:
            task_id: ID задачи
            
        Returns:
            Статус задачи или None если задача не найдена
        """
        task = QUEUE_STORAGE.get(task_id)
        return task.status if task else None

    async def fetch_pending_tasks(self, limit: Optional[int] = None) -> List[Task]:
        """
        Получение списка задач в статусе QUEUED
        
        Возвращает задачи, готовые к обработке.
        Используется воркерами для извлечения задач из очереди.
        
        Args:
            limit: Максимальное количество задач для возврата (None = все)
            
        Returns:
            Список задач в статусе QUEUED
        """
        pending_tasks = [
            task for task in QUEUE_STORAGE.values()
            if task.status == TaskStatus.QUEUED
        ]
        
        if limit:
            return pending_tasks[:limit]
        return pending_tasks
