"""
Redis-based Task Queue Implementation
Replaces in-memory queue with distributed Redis backend for scalability
"""
import json
import logging
import redis.asyncio as redis
from typing import Any, Dict, Optional, List
from datetime import datetime, timedelta

from queue.task_queue import Task, TaskStatus

logger = logging.getLogger(__name__)


class RedisTaskQueue:
    """
    Redis-based task queue for distributed processing
    Supports multiple workers and persistence
    """
    
    def __init__(
        self,
        redis_host: str = "localhost",
        redis_port: int = 6379,
        redis_password: Optional[str] = None,
        redis_db: int = 0,
        key_prefix: str = "taskqueue",
        task_ttl: int = 86400  # 24 hours
    ):
        """
        Initialize Redis task queue
        
        Args:
            redis_host: Redis server host
            redis_port: Redis server port
            redis_password: Redis password (optional)
            redis_db: Redis database number
            key_prefix: Prefix for Redis keys
            task_ttl: Task expiration time in seconds (default: 24h)
        """
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.redis_password = redis_password
        self.redis_db = redis_db
        self.key_prefix = key_prefix
        self.task_ttl = task_ttl
        
        self.redis_client: Optional[redis.Redis] = None
        
        # Redis key patterns
        self.queue_key = f"{key_prefix}:queue"  # List of pending task IDs
        self.processing_key = f"{key_prefix}:processing"  # Set of processing task IDs
        self.task_key_pattern = f"{key_prefix}:task:{{}}"  # Hash for task data
    
    async def connect(self):
        """Establish Redis connection"""
        if self.redis_client is None:
            self.redis_client = await redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                password=self.redis_password,
                db=self.redis_db,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5
            )
            logger.info(f"Connected to Redis: {self.redis_host}:{self.redis_port}")
    
    async def disconnect(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
            self.redis_client = None
            logger.info("Disconnected from Redis")
    
    async def health_check(self) -> bool:
        """
        Check if Redis is accessible
        
        Returns:
            True if healthy
        """
        try:
            await self.connect()
            await self.redis_client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis health check failed: {str(e)}")
            return False
    
    def _task_key(self, task_id: str) -> str:
        """Generate Redis key for task data"""
        return self.task_key_pattern.format(task_id)
    
    def _task_to_dict(self, task: Task) -> Dict[str, Any]:
        """
        Convert Task object to dictionary for Redis storage
        
        Args:
            task: Task object
        
        Returns:
            Dictionary representation
        """
        return {
            "task_id": task.task_id,
            "task_type": task.task_type,
            "params": json.dumps(task.params),
            "status": task.status.value,
            "result": task.result if task.result else "",
            "error": task.error if task.error else "",
            "created_at": datetime.utcnow().isoformat()
        }
    
    def _dict_to_task(self, data: Dict[str, str]) -> Task:
        """
        Convert Redis dictionary to Task object
        
        Args:
            data: Dictionary from Redis
        
        Returns:
            Task object
        """
        task = Task(
            task_id=data["task_id"],
            task_type=data["task_type"],
            params=json.loads(data["params"])
        )
        task.status = TaskStatus(data["status"])
        task.result = data.get("result") or None
        task.error = data.get("error") or None
        return task
    
    async def enqueue(self, task: Task) -> bool:
        """
        Add task to queue
        
        Args:
            task: Task object to enqueue
        
        Returns:
            True if successfully enqueued
        """
        try:
            await self.connect()
            
            # Store task data
            task.status = TaskStatus.QUEUED
            task_data = self._task_to_dict(task)
            task_key = self._task_key(task.task_id)
            
            # Save to Redis hash
            await self.redis_client.hset(task_key, mapping=task_data)
            
            # Set expiration
            await self.redis_client.expire(task_key, self.task_ttl)
            
            # Add to queue (right push for FIFO)
            await self.redis_client.rpush(self.queue_key, task.task_id)
            
            logger.info(f"Enqueued task: {task.task_id}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to enqueue task {task.task_id}: {str(e)}")
            return False
    
    async def dequeue(self) -> Optional[Task]:
        """
        Dequeue next task from queue
        
        Returns:
            Task object or None if queue is empty
        """
        try:
            await self.connect()
            
            # Atomically move from queue to processing set (left pop)
            task_id = await self.redis_client.lpop(self.queue_key)
            
            if not task_id:
                return None
            
            # Add to processing set
            await self.redis_client.sadd(self.processing_key, task_id)
            
            # Get task data
            task_key = self._task_key(task_id)
            task_data = await self.redis_client.hgetall(task_key)
            
            if not task_data:
                logger.warning(f"Task {task_id} not found in Redis")
                await self.redis_client.srem(self.processing_key, task_id)
                return None
            
            # Update status to processing
            await self.redis_client.hset(task_key, "status", TaskStatus.PROCESSING.value)
            task_data["status"] = TaskStatus.PROCESSING.value
            
            task = self._dict_to_task(task_data)
            logger.info(f"Dequeued task: {task_id}")
            return task
        
        except Exception as e:
            logger.error(f"Failed to dequeue task: {str(e)}")
            return None
    
    async def mark_done(
        self,
        task_id: str,
        result: Any = None,
        error: Optional[str] = None
    ) -> bool:
        """
        Mark task as completed or failed
        
        Args:
            task_id: Task identifier
            result: Task result (if successful)
            error: Error message (if failed)
        
        Returns:
            True if successfully updated
        """
        try:
            await self.connect()
            
            task_key = self._task_key(task_id)
            
            # Check if task exists
            exists = await self.redis_client.exists(task_key)
            if not exists:
                logger.warning(f"Task {task_id} not found in Redis")
                return False
            
            # Update status and result/error
            if error:
                await self.redis_client.hset(task_key, mapping={
                    "status": TaskStatus.FAILED.value,
                    "error": error
                })
                logger.info(f"Marked task as FAILED: {task_id}")
            else:
                await self.redis_client.hset(task_key, mapping={
                    "status": TaskStatus.DONE.value,
                    "result": result if result else ""
                })
                logger.info(f"Marked task as DONE: {task_id}")
            
            # Remove from processing set
            await self.redis_client.srem(self.processing_key, task_id)
            
            # Extend TTL for completed tasks
            await self.redis_client.expire(task_key, self.task_ttl)
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to mark task {task_id} done: {str(e)}")
            return False
    
    async def get_task(self, task_id: str) -> Optional[Task]:
        """
        Get task by ID
        
        Args:
            task_id: Task identifier
        
        Returns:
            Task object or None if not found
        """
        try:
            await self.connect()
            
            task_key = self._task_key(task_id)
            task_data = await self.redis_client.hgetall(task_key)
            
            if not task_data:
                return None
            
            return self._dict_to_task(task_data)
        
        except Exception as e:
            logger.error(f"Failed to get task {task_id}: {str(e)}")
            return None
    
    async def get_status(self, task_id: str) -> Optional[TaskStatus]:
        """
        Get task status
        
        Args:
            task_id: Task identifier
        
        Returns:
            TaskStatus or None if not found
        """
        try:
            await self.connect()
            
            task_key = self._task_key(task_id)
            status = await self.redis_client.hget(task_key, "status")
            
            if not status:
                return None
            
            return TaskStatus(status)
        
        except Exception as e:
            logger.error(f"Failed to get status for task {task_id}: {str(e)}")
            return None
    
    async def fetch_pending_tasks(self, limit: Optional[int] = None) -> List[Task]:
        """
        Get list of pending tasks
        
        Args:
            limit: Maximum number of tasks to return
        
        Returns:
            List of pending tasks
        """
        try:
            await self.connect()
            
            # Get task IDs from queue (without removing)
            end_index = limit - 1 if limit else -1
            task_ids = await self.redis_client.lrange(self.queue_key, 0, end_index)
            
            tasks = []
            for task_id in task_ids:
                task = await self.get_task(task_id)
                if task and task.status == TaskStatus.QUEUED:
                    tasks.append(task)
            
            return tasks
        
        except Exception as e:
            logger.error(f"Failed to fetch pending tasks: {str(e)}")
            return []
    
    async def get_queue_size(self) -> int:
        """
        Get number of tasks in queue
        
        Returns:
            Queue size
        """
        try:
            await self.connect()
            return await self.redis_client.llen(self.queue_key)
        except Exception as e:
            logger.error(f"Failed to get queue size: {str(e)}")
            return 0
    
    async def get_processing_count(self) -> int:
        """
        Get number of tasks currently processing
        
        Returns:
            Processing task count
        """
        try:
            await self.connect()
            return await self.redis_client.scard(self.processing_key)
        except Exception as e:
            logger.error(f"Failed to get processing count: {str(e)}")
            return 0
    
    async def clear_queue(self) -> bool:
        """
        Clear all tasks from queue (use with caution)
        
        Returns:
            True if successful
        """
        try:
            await self.connect()
            
            # Delete queue and processing set
            await self.redis_client.delete(self.queue_key)
            await self.redis_client.delete(self.processing_key)
            
            # Find and delete all task keys
            pattern = f"{self.key_prefix}:task:*"
            cursor = 0
            while True:
                cursor, keys = await self.redis_client.scan(cursor, match=pattern, count=100)
                if keys:
                    await self.redis_client.delete(*keys)
                if cursor == 0:
                    break
            
            logger.info("Cleared all tasks from Redis queue")
            return True
        
        except Exception as e:
            logger.error(f"Failed to clear queue: {str(e)}")
            return False
    
    async def requeue_stuck_tasks(self, timeout_seconds: int = 600) -> int:
        """
        Requeue tasks stuck in processing state
        
        Args:
            timeout_seconds: Consider task stuck after this many seconds
        
        Returns:
            Number of tasks requeued
        """
        try:
            await self.connect()
            
            # Get all processing task IDs
            processing_ids = await self.redis_client.smembers(self.processing_key)
            
            requeued_count = 0
            cutoff_time = datetime.utcnow() - timedelta(seconds=timeout_seconds)
            
            for task_id in processing_ids:
                task_key = self._task_key(task_id)
                created_at_str = await self.redis_client.hget(task_key, "created_at")
                
                if not created_at_str:
                    continue
                
                created_at = datetime.fromisoformat(created_at_str)
                
                # If task has been processing too long, requeue it
                if created_at < cutoff_time:
                    # Reset status to queued
                    await self.redis_client.hset(task_key, "status", TaskStatus.QUEUED.value)
                    
                    # Move from processing back to queue
                    await self.redis_client.srem(self.processing_key, task_id)
                    await self.redis_client.rpush(self.queue_key, task_id)
                    
                    requeued_count += 1
                    logger.warning(f"Requeued stuck task: {task_id}")
            
            if requeued_count > 0:
                logger.info(f"Requeued {requeued_count} stuck tasks")
            
            return requeued_count
        
        except Exception as e:
            logger.error(f"Failed to requeue stuck tasks: {str(e)}")
            return 0
