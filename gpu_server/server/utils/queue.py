"""
Task Queue Management
In-memory task queue with status tracking
"""
import logging
import threading
from typing import Optional, Dict, Any
from datetime import datetime

from gpu_server.schema import GPUGenerationRequest, GPUGenerationStatus
from gpu_server.server.utils.id import generate_task_id

logger = logging.getLogger(__name__)


class TaskQueue:
    """
    In-memory task queue with thread-safe operations
    """
    
    def __init__(self):
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self.pending_queue: list = []
        self.lock = threading.Lock()
    
    def enqueue_task(self, request: GPUGenerationRequest) -> str:
        """
        Add new task to queue
        
        Args:
            request: Generation request parameters
            
        Returns:
            task_id: Unique task identifier
        """
        task_id = generate_task_id()
        
        with self.lock:
            task = {
                "task_id": task_id,
                "status": "pending",
                "request": request,
                "result_path": None,
                "error": None,
                "progress": 0.0,
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
            
            self.tasks[task_id] = task
            self.pending_queue.append(task_id)
        
        logger.info(f"Task {task_id} enqueued")
        return task_id
    
    def dequeue_task(self) -> Optional[Dict[str, Any]]:
        """
        Get next pending task (FIFO)
        
        Returns:
            Task dictionary or None if queue empty
        """
        with self.lock:
            if not self.pending_queue:
                return None
            
            task_id = self.pending_queue.pop(0)
            task = self.tasks.get(task_id)
            
            if task:
                task["status"] = "processing"
                task["updated_at"] = datetime.now()
            
            return task
    
    def get_status(self, task_id: str) -> Optional[GPUGenerationStatus]:
        """
        Get task status
        
        Args:
            task_id: Task identifier
            
        Returns:
            GPUGenerationStatus or None if not found
        """
        with self.lock:
            task = self.tasks.get(task_id)
            
            if not task:
                return None
            
            return GPUGenerationStatus(
                task_id=task_id,
                status=task["status"],
                progress=task["progress"],
                message=f"Task {task['status']}",
                error=task["error"]
            )
    
    def update_status(self, task_id: str, status: str, progress: float = None):
        """
        Update task status
        
        Args:
            task_id: Task identifier
            status: New status (pending, processing, completed, failed)
            progress: Progress value 0.0-1.0
        """
        with self.lock:
            task = self.tasks.get(task_id)
            
            if task:
                task["status"] = status
                task["updated_at"] = datetime.now()
                
                if progress is not None:
                    task["progress"] = progress
                
                logger.debug(f"Task {task_id} status updated to {status}")
    
    def set_result(self, task_id: str, result_path: str):
        """
        Set task result path and mark completed
        
        Args:
            task_id: Task identifier
            result_path: Path to result image
        """
        with self.lock:
            task = self.tasks.get(task_id)
            
            if task:
                task["status"] = "completed"
                task["result_path"] = result_path
                task["progress"] = 1.0
                task["updated_at"] = datetime.now()
                
                logger.info(f"Task {task_id} completed")
    
    def set_error(self, task_id: str, error: str):
        """
        Set task error and mark failed
        
        Args:
            task_id: Task identifier
            error: Error message
        """
        with self.lock:
            task = self.tasks.get(task_id)
            
            if task:
                task["status"] = "failed"
                task["error"] = error
                task["updated_at"] = datetime.now()
                
                logger.error(f"Task {task_id} failed: {error}")
    
    def get_queue_size(self) -> int:
        """
        Get number of pending tasks
        
        Returns:
            Number of tasks in pending queue
        """
        with self.lock:
            return len(self.pending_queue)
    
    def cleanup_old_tasks(self, max_age_hours: int = 24):
        """
        Remove old completed/failed tasks
        
        Args:
            max_age_hours: Maximum age in hours
        """
        with self.lock:
            now = datetime.now()
            to_delete = []
            
            for task_id, task in self.tasks.items():
                if task["status"] in ["completed", "failed"]:
                    age_hours = (now - task["updated_at"]).total_seconds() / 3600
                    if age_hours > max_age_hours:
                        to_delete.append(task_id)
            
            for task_id in to_delete:
                del self.tasks[task_id]
                logger.info(f"Task {task_id} cleaned up (age > {max_age_hours}h)")


# Global instance
task_queue = TaskQueue()
