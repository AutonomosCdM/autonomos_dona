"""
Rate limiting utilities for preventing command abuse.

This module implements a token bucket rate limiter that allows
burst traffic while maintaining a steady rate limit over time.
"""

import time
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from threading import Lock
from typing import Dict, Optional, Tuple

import logging

logger = logging.getLogger(__name__)


@dataclass
class RateLimit:
    """Configuration for a rate limit."""
    
    max_tokens: int  # Maximum tokens in bucket
    refill_rate: float  # Tokens per second
    burst_size: int  # Maximum burst size (usually same as max_tokens)
    
    def __post_init__(self):
        """Validate rate limit configuration."""
        if self.max_tokens <= 0:
            raise ValueError("max_tokens must be positive")
        if self.refill_rate <= 0:
            raise ValueError("refill_rate must be positive")
        if self.burst_size <= 0:
            raise ValueError("burst_size must be positive")


@dataclass
class TokenBucket:
    """Token bucket for rate limiting."""
    
    tokens: float
    last_refill: float
    
    def refill(self, rate_limit: RateLimit, current_time: float) -> None:
        """Refill tokens based on elapsed time."""
        elapsed = current_time - self.last_refill
        tokens_to_add = elapsed * rate_limit.refill_rate
        
        self.tokens = min(
            rate_limit.max_tokens,
            self.tokens + tokens_to_add
        )
        self.last_refill = current_time
    
    def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens from bucket.
        
        Returns:
            True if tokens were consumed, False if insufficient tokens
        """
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False


class RateLimiter:
    """
    Rate limiter using token bucket algorithm.
    
    Supports multiple rate limit tiers and per-user limits.
    """
    
    def __init__(self):
        """Initialize rate limiter."""
        self._buckets: Dict[str, TokenBucket] = {}
        self._lock = Lock()
        
        # Default rate limits
        self._rate_limits = {
            # Global limits (across all users)
            'global': RateLimit(
                max_tokens=1000,  # 1000 requests
                refill_rate=100,  # 100 per second
                burst_size=1000
            ),
            
            # Per-user limits
            'user': RateLimit(
                max_tokens=60,    # 60 requests
                refill_rate=1,    # 1 per second (60/min)
                burst_size=10     # Allow bursts of 10
            ),
            
            # Per-command limits
            'command:/dona-task': RateLimit(
                max_tokens=30,
                refill_rate=0.5,  # 30 per minute
                burst_size=5
            ),
            'command:/dona-remind': RateLimit(
                max_tokens=20,
                refill_rate=0.33,  # 20 per minute
                burst_size=3
            ),
            'command:/dona-summary': RateLimit(
                max_tokens=10,
                refill_rate=0.17,  # 10 per minute
                burst_size=2
            ),
            'command:/dona-metrics': RateLimit(
                max_tokens=5,
                refill_rate=0.083,  # 5 per minute
                burst_size=1
            )
        }
        
        # Track rate limit hits for monitoring
        self._limit_hits = defaultdict(int)
        self._last_reset = time.time()
    
    def set_rate_limit(self, key: str, rate_limit: RateLimit) -> None:
        """Set a custom rate limit."""
        self._rate_limits[key] = rate_limit
        logger.info(f"Set rate limit for {key}: {rate_limit}")
    
    def check_rate_limit(
        self,
        user_id: str,
        command: Optional[str] = None,
        tokens: int = 1
    ) -> Tuple[bool, Optional[Dict[str, any]]]:
        """
        Check if request is within rate limits.
        
        Args:
            user_id: User making the request
            command: Optional command being executed
            tokens: Number of tokens to consume
            
        Returns:
            Tuple of (allowed, limit_info)
            - allowed: True if request is allowed
            - limit_info: Information about the limit hit (if any)
        """
        current_time = time.time()
        
        with self._lock:
            # Check global limit
            if not self._check_limit('global', 'global', current_time, tokens):
                self._limit_hits['global'] += 1
                return False, {
                    'limit_type': 'global',
                    'retry_after': self._get_retry_after('global', 'global', tokens)
                }
            
            # Check per-user limit
            user_key = f'user:{user_id}'
            if not self._check_limit(user_key, 'user', current_time, tokens):
                self._limit_hits[user_key] += 1
                return False, {
                    'limit_type': 'user',
                    'retry_after': self._get_retry_after(user_key, 'user', tokens)
                }
            
            # Check per-command limit if applicable
            if command and command in self._rate_limits:
                command_key = f'{command}:{user_id}'
                if not self._check_limit(command_key, command, current_time, tokens):
                    self._limit_hits[command_key] += 1
                    return False, {
                        'limit_type': 'command',
                        'command': command,
                        'retry_after': self._get_retry_after(command_key, command, tokens)
                    }
            
            return True, None
    
    def _check_limit(
        self,
        bucket_key: str,
        limit_key: str,
        current_time: float,
        tokens: int
    ) -> bool:
        """Check a specific rate limit."""
        rate_limit = self._rate_limits.get(limit_key)
        if not rate_limit:
            return True  # No limit configured
        
        # Get or create bucket
        if bucket_key not in self._buckets:
            self._buckets[bucket_key] = TokenBucket(
                tokens=rate_limit.max_tokens,
                last_refill=current_time
            )
        
        bucket = self._buckets[bucket_key]
        
        # Refill bucket
        bucket.refill(rate_limit, current_time)
        
        # Try to consume tokens
        return bucket.consume(tokens)
    
    def _get_retry_after(
        self,
        bucket_key: str,
        limit_key: str,
        tokens: int
    ) -> float:
        """Calculate when the request can be retried."""
        rate_limit = self._rate_limits.get(limit_key)
        if not rate_limit:
            return 0
        
        bucket = self._buckets.get(bucket_key)
        if not bucket:
            return 0
        
        # Calculate time needed to accumulate enough tokens
        tokens_needed = tokens - bucket.tokens
        if tokens_needed <= 0:
            return 0
        
        seconds_needed = tokens_needed / rate_limit.refill_rate
        return seconds_needed
    
    def get_limit_info(self, user_id: str, command: Optional[str] = None) -> Dict[str, any]:
        """
        Get current rate limit information for a user.
        
        Returns:
            Dictionary with limit status information
        """
        current_time = time.time()
        info = {}
        
        with self._lock:
            # User limit info
            user_key = f'user:{user_id}'
            if user_key in self._buckets:
                bucket = self._buckets[user_key]
                rate_limit = self._rate_limits['user']
                bucket.refill(rate_limit, current_time)
                
                info['user_limit'] = {
                    'tokens_remaining': int(bucket.tokens),
                    'max_tokens': rate_limit.max_tokens,
                    'refill_rate': rate_limit.refill_rate
                }
            
            # Command limit info
            if command and command in self._rate_limits:
                command_key = f'{command}:{user_id}'
                if command_key in self._buckets:
                    bucket = self._buckets[command_key]
                    rate_limit = self._rate_limits[command]
                    bucket.refill(rate_limit, current_time)
                    
                    info['command_limit'] = {
                        'command': command,
                        'tokens_remaining': int(bucket.tokens),
                        'max_tokens': rate_limit.max_tokens,
                        'refill_rate': rate_limit.refill_rate
                    }
        
        return info
    
    def get_stats(self) -> Dict[str, any]:
        """Get rate limiter statistics."""
        current_time = time.time()
        
        # Reset stats every hour
        if current_time - self._last_reset > 3600:
            self._limit_hits.clear()
            self._last_reset = current_time
        
        return {
            'active_buckets': len(self._buckets),
            'limit_hits': dict(self._limit_hits),
            'stats_window_start': datetime.fromtimestamp(self._last_reset).isoformat()
        }
    
    def cleanup_old_buckets(self, max_age_seconds: int = 3600) -> int:
        """
        Clean up old unused buckets to prevent memory growth.
        
        Args:
            max_age_seconds: Remove buckets not used for this many seconds
            
        Returns:
            Number of buckets removed
        """
        current_time = time.time()
        removed = 0
        
        with self._lock:
            to_remove = []
            
            for key, bucket in self._buckets.items():
                # If bucket hasn't been refilled recently, it's inactive
                if current_time - bucket.last_refill > max_age_seconds:
                    to_remove.append(key)
            
            for key in to_remove:
                del self._buckets[key]
                removed += 1
        
        if removed > 0:
            logger.info(f"Cleaned up {removed} old rate limit buckets")
        
        return removed


# Global rate limiter instance
rate_limiter = RateLimiter()