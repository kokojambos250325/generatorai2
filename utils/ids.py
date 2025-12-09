import uuid
from datetime import datetime


def generate_task_id(prefix: str = "task") -> str:
    """
    Генерация уникального ID для задачи генерации
    
    Args:
        prefix: Префикс для ID (по умолчанию "task")
        
    Returns:
        Уникальный ID в формате: prefix_timestamp_uuid
        
    Example:
        >>> task_id = generate_task_id("clothes")
        >>> # clothes_20231206_123456_a1b2c3d4e5f6
    """
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    unique_id = uuid.uuid4().hex[:12]
    return f"{prefix}_{timestamp}_{unique_id}"


def is_valid_task_id(task_id: str) -> bool:
    """
    Проверка валидности ID задачи
    
    Args:
        task_id: ID задачи для проверки
        
    Returns:
        True если ID валиден
    """
    if not task_id:
        return False
    parts = task_id.split("_")
    return len(parts) >= 3
