"""
Metrics collection and reporting utilities.

This module provides utilities for collecting and reporting
application metrics for monitoring and observability.
"""

import time
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from threading import Lock

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Collects and aggregates application metrics."""
    
    def __init__(self, window_minutes: int = 5):
        """
        Initialize metrics collector.
        
        Args:
            window_minutes: Time window for metric aggregation
        """
        self.window_minutes = window_minutes
        self._metrics: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self._counters: Dict[str, int] = defaultdict(int)
        self._lock = Lock()
    
    def record_request(self, request_type: str, duration_ms: int, 
                      status: str, user_id: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Record a request metric."""
        with self._lock:
            metric = {
                'timestamp': datetime.utcnow(),
                'duration_ms': duration_ms,
                'status': status,
                'user_id': user_id,
                'metadata': metadata or {}
            }
            
            self._metrics[request_type].append(metric)
            
            # Increment counters
            self._counters[f"{request_type}:total"] += 1
            self._counters[f"{request_type}:{status}"] += 1
            
            # Clean old metrics
            self._clean_old_metrics()
    
    def increment_counter(self, name: str, value: int = 1) -> None:
        """Increment a counter metric."""
        with self._lock:
            self._counters[name] += value
    
    def get_counter(self, name: str) -> int:
        """Get current counter value."""
        return self._counters.get(name, 0)
    
    def _clean_old_metrics(self) -> None:
        """Remove metrics older than the window."""
        cutoff = datetime.utcnow() - timedelta(minutes=self.window_minutes)
        
        for request_type in list(self._metrics.keys()):
            self._metrics[request_type] = [
                m for m in self._metrics[request_type]
                if m['timestamp'] > cutoff
            ]
            
            # Remove empty lists
            if not self._metrics[request_type]:
                del self._metrics[request_type]
    
    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary for the current window."""
        with self._lock:
            self._clean_old_metrics()
            
            summary = {
                'window_minutes': self.window_minutes,
                'timestamp': datetime.utcnow().isoformat(),
                'request_types': {},
                'counters': dict(self._counters)
            }
            
            # Calculate statistics for each request type
            for request_type, metrics in self._metrics.items():
                if not metrics:
                    continue
                
                durations = [m['duration_ms'] for m in metrics]
                success_count = sum(1 for m in metrics if m['status'] == 'success')
                error_count = sum(1 for m in metrics if m['status'] == 'error')
                
                summary['request_types'][request_type] = {
                    'count': len(metrics),
                    'success_count': success_count,
                    'error_count': error_count,
                    'error_rate': error_count / len(metrics) if metrics else 0,
                    'avg_duration_ms': sum(durations) / len(durations) if durations else 0,
                    'min_duration_ms': min(durations) if durations else 0,
                    'max_duration_ms': max(durations) if durations else 0,
                    'p95_duration_ms': self._percentile(durations, 95) if durations else 0,
                    'p99_duration_ms': self._percentile(durations, 99) if durations else 0
                }
            
            return summary
    
    def _percentile(self, values: List[float], percentile: float) -> float:
        """Calculate percentile of a list of values."""
        if not values:
            return 0
        
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile / 100)
        
        if index >= len(sorted_values):
            return sorted_values[-1]
        
        return sorted_values[index]
    
    def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """Get statistics for a specific user."""
        with self._lock:
            user_metrics = []
            
            for request_type, metrics in self._metrics.items():
                user_metrics.extend([
                    {**m, 'request_type': request_type}
                    for m in metrics if m['user_id'] == user_id
                ])
            
            if not user_metrics:
                return {
                    'user_id': user_id,
                    'total_requests': 0,
                    'request_types': {}
                }
            
            # Group by request type
            by_type = defaultdict(list)
            for m in user_metrics:
                by_type[m['request_type']].append(m)
            
            stats = {
                'user_id': user_id,
                'total_requests': len(user_metrics),
                'request_types': {}
            }
            
            for request_type, type_metrics in by_type.items():
                durations = [m['duration_ms'] for m in type_metrics]
                stats['request_types'][request_type] = {
                    'count': len(type_metrics),
                    'avg_duration_ms': sum(durations) / len(durations) if durations else 0
                }
            
            return stats
    
    def log_summary(self) -> None:
        """Log current metrics summary."""
        summary = self.get_summary()
        
        logger.info(
            "Metrics summary",
            extra={'metrics': summary}
        )
        
        # Log warnings for high error rates
        for request_type, stats in summary['request_types'].items():
            if stats['error_rate'] > 0.1:  # More than 10% errors
                logger.warning(
                    f"High error rate for {request_type}: {stats['error_rate']:.2%}",
                    extra={
                        'request_type': request_type,
                        'error_rate': stats['error_rate'],
                        'error_count': stats['error_count'],
                        'total_count': stats['count']
                    }
                )


# Global metrics collector instance
metrics_collector = MetricsCollector()


class Timer:
    """Context manager for timing code execution."""
    
    def __init__(self, name: str, logger: Optional[logging.Logger] = None):
        """
        Initialize timer.
        
        Args:
            name: Name for the timing measurement
            logger: Optional logger for output
        """
        self.name = name
        self.logger = logger or logging.getLogger(__name__)
        self.start_time = None
        self.end_time = None
    
    def __enter__(self):
        """Start timing."""
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """End timing and log result."""
        self.end_time = time.time()
        duration = self.end_time - self.start_time
        
        self.logger.debug(
            f"{self.name} took {duration:.3f}s",
            extra={
                'timer_name': self.name,
                'duration_seconds': duration
            }
        )
    
    @property
    def elapsed(self) -> float:
        """Get elapsed time in seconds."""
        if self.start_time is None:
            return 0
        
        end = self.end_time or time.time()
        return end - self.start_time


def track_execution_time(func):
    """Decorator to track function execution time."""
    def wrapper(*args, **kwargs):
        with Timer(f"{func.__module__}.{func.__name__}"):
            return func(*args, **kwargs)
    return wrapper