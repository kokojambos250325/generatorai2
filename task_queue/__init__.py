"""
Task Queue Module
Provides task queue implementations (in-memory and Redis)
"""
from queue.task_queue import Task, TaskStatus, TaskQueue
from queue.redis_queue import RedisTaskQueue


def get_task_queue(use_redis: bool = False, **kwargs):
    """
    Factory function to get task queue instance
    
    Args:
        use_redis: Use Redis backend instead of in-memory
        **kwargs: Additional arguments for queue initialization
    
    Returns:
        TaskQueue or RedisTaskQueue instance
    """
    if use_redis:
        return RedisTaskQueue(**kwargs)
    else:
        return TaskQueue(backend="memory")


__all__ = [
    "Task",
    "TaskStatus",
    "TaskQueue",
    "RedisTaskQueue",
    "get_task_queue"
]
