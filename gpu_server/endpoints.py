"""
URL-константы для взаимодействия с GPU-сервером
"""

# Базовый URL GPU-сервера (будет переопределён через конфигурацию)
GPU_SERVER_BASE_URL = "http://gpu-server"

# Эндпоинт для отправки задачи на генерацию
SEND_TASK_URL = f"{GPU_SERVER_BASE_URL}/api/generate"

# Эндпоинт для проверки статуса задачи
CHECK_STATUS_URL = f"{GPU_SERVER_BASE_URL}/api/task"

# Эндпоинт для получения результата задачи
GET_RESULT_URL = f"{GPU_SERVER_BASE_URL}/api/result"
