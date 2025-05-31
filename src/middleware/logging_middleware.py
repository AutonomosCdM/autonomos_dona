"""
Logging middleware for request tracking.

This middleware logs all incoming requests and responses for monitoring,
debugging, and analytics purposes.
"""

import json
import time
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from uuid import uuid4

from src.utils.metrics import metrics_collector

logger = logging.getLogger(__name__)


class RequestLogger:
    """Tracks and logs request metrics."""
    
    def __init__(self):
        self.active_requests: Dict[str, Dict[str, Any]] = {}
    
    def start_request(self, request_id: str, request_type: str, user_id: str, 
                      metadata: Optional[Dict[str, Any]] = None) -> None:
        """Start tracking a request."""
        self.active_requests[request_id] = {
            'type': request_type,
            'user_id': user_id,
            'start_time': time.time(),
            'metadata': metadata or {}
        }
    
    def end_request(self, request_id: str, status: str = 'success', 
                    error: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """End tracking a request and return metrics."""
        if request_id not in self.active_requests:
            return None
        
        request_data = self.active_requests.pop(request_id)
        duration = time.time() - request_data['start_time']
        
        metrics = {
            'request_id': request_id,
            'type': request_data['type'],
            'user_id': request_data['user_id'],
            'duration_ms': int(duration * 1000),
            'status': status,
            'error': error,
            'metadata': request_data['metadata']
        }
        
        return metrics


# Global request logger instance
request_logger = RequestLogger()


def logging_middleware(args, next):
    """
    Middleware that logs all incoming requests and their responses.
    
    Tracks:
    - Request type (command, event, action, etc.)
    - User information
    - Channel information
    - Response time
    - Success/failure status
    - Error details if any
    """
    request_id = str(uuid4())
    request_type = 'unknown'
    user_id = 'unknown'
    channel_id = None
    team_id = None
    
    # Extract request information
    command = getattr(args, 'command', None)
    event = getattr(args, 'event', None)
    action = getattr(args, 'action', None)
    view = getattr(args, 'view', None)
    context = getattr(args, 'context', {})
    
    if command:
        # Slash command
        request_type = f"command:{command.get('command', 'unknown')}"
        user_id = command.get('user_id', 'unknown')
        channel_id = command.get('channel_id')
        team_id = command.get('team_id')
        
        # Log command details
        logger.info(
            f"Command request: {request_id}",
            extra={
                'request_id': request_id,
                'command': command.get('command'),
                'text': command.get('text', '')[:100],  # Truncate for privacy
                'user_id': user_id,
                'channel_id': channel_id,
                'team_id': team_id
            }
        )
    
    elif event:
        # Event
        request_type = f"event:{event.get('type', 'unknown')}"
        user_id = event.get('user', 'unknown')
        channel_id = event.get('channel')
        team_id = event.get('team')
        
        # Log event details
        logger.info(
            f"Event request: {request_id}",
            extra={
                'request_id': request_id,
                'event_type': event.get('type'),
                'user_id': user_id,
                'channel_id': channel_id,
                'channel_type': event.get('channel_type'),
                'team_id': team_id
            }
        )
    
    elif action:
        # Block action
        request_type = f"action:{action.get('action_id', 'unknown')}"
        user = getattr(args, 'user', {})
        channel = getattr(args, 'channel', {})
        team = getattr(args, 'team', {})
        user_id = user.get('id', 'unknown') if user else 'unknown'
        channel_id = channel.get('id') if channel else None
        team_id = team.get('id') if team else None
        
        # Log action details
        logger.info(
            f"Action request: {request_id}",
            extra={
                'request_id': request_id,
                'action_id': action.get('action_id'),
                'action_type': action.get('type'),
                'user_id': user_id,
                'channel_id': channel_id,
                'team_id': team_id
            }
        )
    
    elif view:
        # Modal view submission
        request_type = f"view:{view.get('callback_id', 'unknown')}"
        user = getattr(args, 'user', {})
        team = getattr(args, 'team', {})
        user_id = user.get('id', 'unknown') if user else 'unknown'
        team_id = team.get('id') if team else None
        
        # Log view submission details
        logger.info(
            f"View submission: {request_id}",
            extra={
                'request_id': request_id,
                'callback_id': view.get('callback_id'),
                'user_id': user_id,
                'team_id': team_id
            }
        )
    
    # Start tracking the request
    metadata = {
        'channel_id': channel_id,
        'team_id': team_id,
        'timestamp': datetime.utcnow().isoformat()
    }
    request_logger.start_request(request_id, request_type, user_id, metadata)
    
    # Store request_id in context for error handling
    context['request_id'] = request_id
    
    try:
        # Call the next middleware or handler
        next()
        
        # Log successful completion
        metrics = request_logger.end_request(request_id, status='success')
        if metrics:
            logger.info(
                f"Request completed: {request_id}",
                extra={
                    'request_id': request_id,
                    'duration_ms': metrics['duration_ms'],
                    'request_type': request_type,
                    'user_id': user_id
                }
            )
            
            # Record metrics
            metrics_collector.record_request(
                request_type=request_type,
                duration_ms=metrics['duration_ms'],
                status='success',
                user_id=user_id,
                metadata=metadata
            )
            
            # Log slow requests
            if metrics['duration_ms'] > 3000:  # More than 3 seconds
                logger.warning(
                    f"Slow request detected: {request_id}",
                    extra={
                        'request_id': request_id,
                        'duration_ms': metrics['duration_ms'],
                        'request_type': request_type,
                        'user_id': user_id
                    }
                )
                metrics_collector.increment_counter('slow_requests')
    
    except Exception as e:
        # Log error
        error_message = str(e)
        metrics = request_logger.end_request(request_id, status='error', error=error_message)
        
        logger.error(
            f"Request failed: {request_id}",
            extra={
                'request_id': request_id,
                'error': error_message,
                'request_type': request_type,
                'user_id': user_id,
                'duration_ms': metrics['duration_ms'] if metrics else 0
            },
            exc_info=True
        )
        
        # Record error metrics
        if metrics:
            metrics_collector.record_request(
                request_type=request_type,
                duration_ms=metrics['duration_ms'],
                status='error',
                user_id=user_id,
                metadata={**metadata, 'error': error_message}
            )
        
        metrics_collector.increment_counter('errors')
        metrics_collector.increment_counter(f'errors:{request_type}')
        
        # Re-raise the exception
        raise


def performance_middleware(args, next):
    """
    Lightweight performance tracking middleware.
    
    Tracks only timing information without detailed logging.
    """
    start_time = time.time()
    
    try:
        next()
    finally:
        duration = time.time() - start_time
        
        # Get context properly from Args object
        context = getattr(args, 'context', {})
        
        # Add performance data to context for other middleware
        if 'performance' not in context:
            context['performance'] = {}
        
        context['performance']['duration_ms'] = int(duration * 1000)
        
        # Log only if very slow
        if duration > 5.0:  # More than 5 seconds
            request_type = 'unknown'
            command = getattr(args, 'command', None)
            event = getattr(args, 'event', None)
            
            if command:
                request_type = f"command:{command.get('command', 'unknown')}"
            elif event:
                request_type = f"event:{event.get('type', 'unknown')}"
            
            logger.warning(
                f"Very slow request: {request_type} took {duration:.2f}s",
                extra={'duration_seconds': duration, 'request_type': request_type}
            )


def analytics_middleware(args, next):
    """
    Middleware for collecting analytics data.
    
    Collects usage patterns for improving the bot.
    """
    analytics_data = {
        'timestamp': datetime.utcnow().isoformat(),
        'user_id': None,
        'team_id': None,
        'interaction_type': None,
        'metadata': {}
    }
    
    # Get references to args attributes
    command = getattr(args, 'command', None)
    event = getattr(args, 'event', None)
    context = getattr(args, 'context', {})
    
    # Extract analytics data based on request type
    if command:
        analytics_data.update({
            'user_id': command.get('user_id'),
            'team_id': command.get('team_id'),
            'interaction_type': 'command',
            'metadata': {
                'command': command.get('command'),
                'has_text': bool(command.get('text'))
            }
        })
    elif event:
        analytics_data.update({
            'user_id': event.get('user'),
            'team_id': event.get('team'),
            'interaction_type': 'event',
            'metadata': {
                'event_type': event.get('type'),
                'channel_type': event.get('channel_type')
            }
        })
    
    # Store analytics data in context for handlers to use
    context['analytics'] = analytics_data
    
    # Log analytics event (could be sent to analytics service)
    logger.debug(
        "Analytics event",
        extra={'analytics': analytics_data}
    )
    
    # Continue to next middleware
    next()