"""
Rate limiter for Telegram Bot
"""
import time
import logging
from typing import Dict
from collections import defaultdict
from telegram_bot.config import get_bot_settings

logger = logging.getLogger(__name__)
settings = get_bot_settings()


class RateLimiter:
    """Simple rate limiter for user requests"""
    
    def __init__(self):
        self.user_requests: Dict[int, list] = defaultdict(list)
        self.max_requests = settings.MAX_REQUESTS_PER_USER
        self.window_seconds = settings.RATE_LIMIT_WINDOW_SECONDS
    
    def check_rate_limit(self, user_id: int) -> tuple[bool, int]:
        """
        Check if user is within rate limit
        
        Args:
            user_id: Telegram user ID
        
        Returns:
            (is_allowed, remaining_requests)
        """
        current_time = time.time()
        
        # Get user's request history
        request_times = self.user_requests[user_id]
        
        # Remove requests outside the time window
        request_times[:] = [
            t for t in request_times 
            if current_time - t < self.window_seconds
        ]
        
        # Check if limit exceeded
        if len(request_times) >= self.max_requests:
            logger.warning(f"Rate limit exceeded for user {user_id}")
            return False, 0
        
        # Add current request
        request_times.append(current_time)
        
        remaining = self.max_requests - len(request_times)
        logger.debug(f"Rate limit check for user {user_id}: {remaining} requests remaining")
        
        return True, remaining
    
    def get_reset_time(self, user_id: int) -> int:
        """
        Get time until rate limit resets
        
        Args:
            user_id: Telegram user ID
        
        Returns:
            Seconds until reset
        """
        request_times = self.user_requests[user_id]
        
        if not request_times:
            return 0
        
        current_time = time.time()
        oldest_request = min(request_times)
        
        elapsed = current_time - oldest_request
        remaining = max(0, self.window_seconds - elapsed)
        
        return int(remaining)
    
    def reset_user(self, user_id: int):
        """
        Reset rate limit for a specific user
        
        Args:
            user_id: Telegram user ID
        """
        if user_id in self.user_requests:
            del self.user_requests[user_id]
            logger.info(f"Rate limit reset for user {user_id}")
