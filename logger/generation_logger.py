from typing import Any, Dict, Optional
from datetime import datetime
from enum import Enum
import logging
import json
import uuid


class LogLevel(Enum):
    """Уровни логирования"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class GenerationLogger:
    """
    Логгер для отслеживания процесса генерации.
    Поддерживает вывод в консоль и JSON-формат.
    Включает поддержку GPU-специфичных событий и correlation IDs.
    """

    def __init__(self, output_format: str = "console", log_level: str = "INFO"):
        """
        Инициализация логгера
        
        Args:
            output_format: Формат вывода ('console' или 'json')
            log_level: Уровень логирования (DEBUG, INFO, WARNING, ERROR)
        """
        self.output_format = output_format
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(getattr(logging, log_level.upper()))
        
        # Настройка обработчика
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            if output_format == "json":
                formatter = logging.Formatter('%(message)s')
            else:
                formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def _init_logger(self):
        """Инициализация логгера (legacy method)"""
        pass
    
    def generate_correlation_id(self, task_id: str) -> str:
        """
        Генерация correlation ID для трассировки запросов
        
        Args:
            task_id: ID задачи
            
        Returns:
            Correlation ID в формате {task_id}-{timestamp}-{random}
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        random_suffix = str(uuid.uuid4())[:8]
        return f"{task_id}-{timestamp}-{random_suffix}"

    def log_start(
        self,
        task_id: str,
        task_type: str,
        params: Dict[str, Any],
        timestamp: Optional[datetime] = None
    ) -> None:
        """
        Логирование начала генерации
        
        Args:
            task_id: ID задачи
            task_type: Тип задачи генерации
            params: Параметры генерации
            timestamp: Временная метка (если не указана, используется текущее время)
        """
        timestamp = timestamp or datetime.utcnow()
        print(f"[START] Task {task_id} ({task_type}) started at {timestamp}")

    def log_update(
        self,
        task_id: str,
        status: str,
        message: Optional[str] = None,
        progress: Optional[float] = None,
        timestamp: Optional[datetime] = None
    ) -> None:
        """
        Логирование обновления статуса генерации
        
        Args:
            task_id: ID задачи
            status: Текущий статус
            message: Дополнительное сообщение
            progress: Прогресс выполнения (0.0 - 1.0)
            timestamp: Временная метка
        """
        timestamp = timestamp or datetime.utcnow()
        progress_str = f" {progress*100:.1f}%" if progress is not None else ""
        msg_str = f" - {message}" if message else ""
        print(f"[UPDATE] Task {task_id}: {status}{progress_str}{msg_str} at {timestamp}")

    def log_finish(
        self,
        task_id: str,
        success: bool,
        result: Optional[Any] = None,
        error: Optional[str] = None,
        duration: Optional[float] = None,
        timestamp: Optional[datetime] = None
    ) -> None:
        """
        Логирование завершения генерации
        
        Args:
            task_id: ID задачи
            success: Успешно ли завершена задача
            result: Результат выполнения
            error: Сообщение об ошибке (если есть)
            duration: Длительность выполнения в секундах
            timestamp: Временная метка
        """
        timestamp = timestamp or datetime.utcnow()
        status = "SUCCESS" if success else "FAILED"
        duration_str = f" (duration: {duration:.2f}s)" if duration else ""
        error_str = f" - Error: {error}" if error else ""
        print(f"[FINISH] Task {task_id}: {status}{duration_str}{error_str} at {timestamp}")

    def log_error(
        self,
        task_id: str,
        error: str,
        exception: Optional[Exception] = None,
        timestamp: Optional[datetime] = None
    ) -> None:
        """
        Логирование ошибки
        
        Args:
            task_id: ID задачи
            error: Сообщение об ошибке
            exception: Объект исключения
            timestamp: Временная метка
        """
        timestamp = timestamp or datetime.utcnow()
        exc_str = f" ({type(exception).__name__})" if exception else ""
        print(f"[ERROR] Task {task_id}: {error}{exc_str} at {timestamp}")

    def _format_message(self, level: LogLevel, data: Dict[str, Any]) -> str:
        """
        Форматирование сообщения для вывода
        
        Args:
            level: Уровень логирования
            data: Данные для логирования
            
        Returns:
            Отформатированное сообщение
        """
        if self.output_format == "json":
            return json.dumps(data)
        else:
            return str(data)
    
    # ===== GPU-Specific Logging Methods =====
    
    def log_gpu_submit_start(
        self,
        task_id: str,
        mode: str,
        retry_count: int = 0,
        correlation_id: Optional[str] = None
    ) -> None:
        """Логирование начала отправки на GPU сервер"""
        correlation_id = correlation_id or self.generate_correlation_id(task_id)
        self.logger.info(
            f"[GPU_SUBMIT_START] task_id={task_id} mode={mode} "
            f"retry={retry_count} correlation_id={correlation_id}"
        )
    
    def log_gpu_submit_success(
        self,
        task_id: str,
        gpu_task_id: str,
        response_time_ms: float,
        correlation_id: Optional[str] = None
    ) -> None:
        """Логирование успешной отправки на GPU"""
        self.logger.info(
            f"[GPU_SUBMIT_SUCCESS] task_id={task_id} gpu_task_id={gpu_task_id} "
            f"response_time_ms={response_time_ms:.2f} correlation_id={correlation_id}"
        )
    
    def log_gpu_submit_failure(
        self,
        task_id: str,
        error_type: str,
        error_message: str,
        retry_count: int,
        will_retry: bool,
        correlation_id: Optional[str] = None
    ) -> None:
        """Логирование ошибки отправки на GPU"""
        self.logger.error(
            f"[GPU_SUBMIT_FAILURE] task_id={task_id} error_type={error_type} "
            f"error={error_message} retry={retry_count} will_retry={will_retry} "
            f"correlation_id={correlation_id}"
        )
    
    def log_gpu_poll_start(
        self,
        task_id: str,
        gpu_task_id: str,
        poll_count: int,
        correlation_id: Optional[str] = None
    ) -> None:
        """Логирование начала опроса статуса GPU"""
        self.logger.debug(
            f"[GPU_POLL_START] task_id={task_id} gpu_task_id={gpu_task_id} "
            f"poll_count={poll_count} correlation_id={correlation_id}"
        )
    
    def log_gpu_poll_progress(
        self,
        task_id: str,
        status: str,
        progress_percent: Optional[float] = None,
        message: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> None:
        """Логирование прогресса выполнения на GPU"""
        progress_str = f" progress={progress_percent:.1f}%" if progress_percent else ""
        msg_str = f" message='{message}'" if message else ""
        self.logger.info(
            f"[GPU_POLL_PROGRESS] task_id={task_id} status={status}"
            f"{progress_str}{msg_str} correlation_id={correlation_id}"
        )
    
    def log_gpu_result_retrieved(
        self,
        task_id: str,
        result_size_kb: float,
        total_processing_time_s: float,
        correlation_id: Optional[str] = None
    ) -> None:
        """Логирование получения результата с GPU"""
        self.logger.info(
            f"[GPU_RESULT_RETRIEVED] task_id={task_id} "
            f"result_size_kb={result_size_kb:.2f} "
            f"total_time_s={total_processing_time_s:.2f} "
            f"correlation_id={correlation_id}"
        )
    
    def log_gpu_timeout(
        self,
        task_id: str,
        elapsed_time_s: float,
        timeout_threshold_s: int,
        correlation_id: Optional[str] = None
    ) -> None:
        """Логирование таймаута GPU операции"""
        self.logger.warning(
            f"[GPU_TIMEOUT] task_id={task_id} "
            f"elapsed_time_s={elapsed_time_s:.2f} "
            f"timeout_threshold_s={timeout_threshold_s} "
            f"correlation_id={correlation_id}"
        )
    
    def log_gpu_circuit_open(
        self,
        consecutive_failures: int,
        circuit_open_until: datetime
    ) -> None:
        """Логирование открытия circuit breaker"""
        self.logger.error(
            f"[GPU_CIRCUIT_OPEN] consecutive_failures={consecutive_failures} "
            f"circuit_open_until={circuit_open_until.isoformat()}"
        )
    
    def log_gpu_circuit_closed(
        self,
        test_request_success: bool,
        circuit_status: str
    ) -> None:
        """Логирование закрытия circuit breaker"""
        self.logger.info(
            f"[GPU_CIRCUIT_CLOSED] test_success={test_request_success} "
            f"circuit_status={circuit_status}"
        )
