import httpx
from typing import Optional
from datetime import datetime, timedelta
from enum import Enum
from gpu_server.schema import GPUGenerationRequest, GPUGenerationStatus, GPUGenerationResult


class CircuitState(Enum):
    """Circuit Breaker States"""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """
    Circuit Breaker pattern implementation for GPU server
    Prevents cascading failures when GPU server is down
    """
    
    def __init__(self, failure_threshold: int = 5, timeout_seconds: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.consecutive_failures = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = CircuitState.CLOSED
    
    def record_success(self):
        """Record successful request"""
        self.consecutive_failures = 0
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.CLOSED
    
    def record_failure(self):
        """Record failed request"""
        self.consecutive_failures += 1
        self.last_failure_time = datetime.utcnow()
        
        if self.consecutive_failures >= self.failure_threshold:
            self.state = CircuitState.OPEN
    
    def can_attempt(self) -> bool:
        """Check if request can be attempted"""
        if self.state == CircuitState.CLOSED:
            return True
        
        if self.state == CircuitState.OPEN:
            # Check if timeout has passed
            if self.last_failure_time:
                elapsed = datetime.utcnow() - self.last_failure_time
                if elapsed.total_seconds() >= self.timeout_seconds:
                    self.state = CircuitState.HALF_OPEN
                    return True
            return False
        
        # HALF_OPEN state: allow one test request
        return True
    
    def get_state_info(self) -> dict:
        """Get current circuit breaker state information"""
        return {
            "state": self.state.value,
            "consecutive_failures": self.consecutive_failures,
            "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None
        }


class GPUClient:
    """Клиент для взаимодействия с удалённым GPU-сервером"""

    def __init__(
        self,
        base_url: str,
        api_key: str = "",
        timeout: int = 600,
        max_retries: int = 3,
        circuit_breaker_threshold: int = 5,
        circuit_breaker_timeout: int = 60
    ):
        self.base_url = base_url
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self.client: Optional[httpx.AsyncClient] = None
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=circuit_breaker_threshold,
            timeout_seconds=circuit_breaker_timeout
        )

    async def __aenter__(self):
        """Инициализация async context manager"""
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            headers=headers
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Закрытие async context manager"""
        if self.client:
            await self.client.aclose()

    async def send_task(self, request: GPUGenerationRequest) -> str:
        """
        Отправка задачи на GPU-сервер с retry логикой и circuit breaker
        
        Args:
            request: Параметры генерации
            
        Returns:
            task_id присвоенный GPU-сервером
            
        Raises:
            Exception: При превышении количества попыток или критической ошибке
        """
        import asyncio
        
        # Check circuit breaker before attempting
        if not self.circuit_breaker.can_attempt():
            raise Exception(
                f"Circuit breaker OPEN. GPU server unavailable. "
                f"Will retry after {self.circuit_breaker.timeout_seconds}s. "
                f"State: {self.circuit_breaker.get_state_info()}"
            )
        
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                # Отправка POST запроса на GPU-сервер
                response = await self.client.post(
                    "/api/generate",
                    json=request.model_dump(exclude_none=True)
                )
                response.raise_for_status()
                
                # Извлечение task_id из ответа
                data = response.json()
                task_id = data.get("task_id")
                
                if not task_id:
                    raise Exception("No task_id in response")
                
                # Success - record in circuit breaker
                self.circuit_breaker.record_success()
                return task_id
                
            except httpx.TimeoutException as e:
                last_error = f"GPU server timeout: {str(e)}"
                self.circuit_breaker.record_failure()
                if attempt < self.max_retries - 1:
                    wait_time = min(2 ** attempt, 30)  # Exponential backoff, max 30s
                    await asyncio.sleep(wait_time)
                    continue
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:  # Rate limit
                    last_error = f"GPU server rate limit: {str(e)}"
                    if attempt < self.max_retries - 1:
                        wait_time = min(2 ** (attempt + 2), 60)  # Longer backoff for rate limits
                        await asyncio.sleep(wait_time)
                        continue
                elif e.response.status_code >= 500:  # Server errors, retry
                    last_error = f"GPU server error {e.response.status_code}: {str(e)}"
                    self.circuit_breaker.record_failure()
                    if attempt < self.max_retries - 1:
                        wait_time = min(2 ** attempt, 30)
                        await asyncio.sleep(wait_time)
                        continue
                else:  # Client errors, don't retry
                    raise Exception(f"GPU server client error: {str(e)}")
            except Exception as e:
                last_error = f"GPU server error: {str(e)}"
                self.circuit_breaker.record_failure()
                break
        
        raise Exception(f"Failed to send task after {self.max_retries} attempts: {last_error}")

    async def check_status(self, task_id: str) -> GPUGenerationStatus:
        """
        Проверка статуса задачи на GPU-сервере
        
        Args:
            task_id: ID задачи на GPU-сервере
            
        Returns:
            Статус выполнения задачи
            
        Raises:
            Exception: При ошибке запроса
        """
        try:
            # Отправка GET запроса для проверки статуса
            response = await self.client.get(f"/api/task/{task_id}")
            response.raise_for_status()
            
            # Парсинг ответа в модель статуса
            data = response.json()
            return GPUGenerationStatus(**data)
            
        except httpx.TimeoutException as e:
            raise Exception(f"GPU server timeout: {str(e)}")
        except httpx.HTTPStatusError as e:
            raise Exception(f"GPU server HTTP error {e.response.status_code}: {str(e)}")
        except Exception as e:
            raise Exception(f"GPU server error: {str(e)}")

    async def get_result(self, task_id: str) -> GPUGenerationResult:
        """
        Получение результата выполненной задачи
        
        Args:
            task_id: ID задачи на GPU-сервере
            
        Returns:
            Результат генерации
            
        Raises:
            Exception: При ошибке запроса
        """
        try:
            # Отправка GET запроса для получения результата
            response = await self.client.get(f"/api/result/{task_id}")
            response.raise_for_status()
            
            # Парсинг ответа в модель результата
            data = response.json()
            return GPUGenerationResult(**data)
            
        except httpx.TimeoutException as e:
            raise Exception(f"GPU server timeout: {str(e)}")
        except httpx.HTTPStatusError as e:
            raise Exception(f"GPU server HTTP error {e.response.status_code}: {str(e)}")
        except Exception as e:
            raise Exception(f"GPU server error: {str(e)}")
    
    async def poll_until_complete(self, task_id: str, poll_interval: int = 2, max_wait: int = 600) -> GPUGenerationResult:
        """
        Poll task status until completion with adaptive polling
        
        Args:
            task_id: Task identifier
            poll_interval: Initial polling interval in seconds
            max_wait: Maximum wait time in seconds
            
        Returns:
            GPUGenerationResult when task completes
            
        Raises:
            Exception: If task fails or timeout exceeded
        """
        import asyncio
        import time
        
        start_time = time.time()
        current_interval = poll_interval
        
        while True:
            elapsed = time.time() - start_time
            
            if elapsed > max_wait:
                raise Exception(f"Task {task_id} polling timeout after {max_wait}s")
            
            # Check status
            status = await self.check_status(task_id)
            
            if status.status == "completed":
                return await self.get_result(task_id)
            elif status.status == "failed":
                raise Exception(f"Task {task_id} failed: {status.error}")
            
            # Adaptive polling: increase interval after 30 seconds
            if elapsed > 30:
                current_interval = 5
            
            await asyncio.sleep(current_interval)
    
    async def check_health(self) -> dict:
        """
        Query GPU server health endpoint to verify readiness
        
        Returns comprehensive health status including:
        - Overall status (ok/degraded/error)
        - GPU availability
        - Individual model loading status
        - GPU and server metrics
        
        Returns:
            Health status dictionary
            
        Raises:
            Exception: If server unreachable or health check fails
            
        Example:
            >>> async with GPUClient(base_url, api_key) as client:
            ...     health = await client.check_health()
            ...     if health['status'] == 'error':
            ...         raise Exception("GPU server not ready")
            ...     elif health['status'] == 'degraded':
            ...         logger.warning("GPU server degraded: some models missing")
        """
        try:
            response = await self.client.get("/health")
            response.raise_for_status()
            
            health_data = response.json()
            return health_data
            
        except httpx.TimeoutException as e:
            raise Exception(f"GPU server health check timeout: {str(e)}")
        except httpx.HTTPStatusError as e:
            raise Exception(f"GPU server health check HTTP error {e.response.status_code}: {str(e)}")
        except Exception as e:
            raise Exception(f"GPU server health check error: {str(e)}")
