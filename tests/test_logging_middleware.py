"""Tests for logging middleware functionality."""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.middleware.logging_middleware import (
    logging_middleware,
    performance_middleware,
    analytics_middleware,
    RequestLogger,
    request_logger
)
from src.utils.metrics import metrics_collector, MetricsCollector, Timer


class TestLoggingMiddleware:
    """Test logging middleware functionality."""
    
    def test_logging_middleware_command(self):
        """Test logging middleware with command request."""
        # Setup
        args = {
            'command': {
                'command': '/dona-task',
                'text': 'create Test task',
                'user_id': 'U123456',
                'channel_id': 'C123456',
                'team_id': 'T123456'
            },
            'context': {}
        }
        
        next_called = False
        def mock_next():
            nonlocal next_called
            next_called = True
            # Simulate some processing time
            time.sleep(0.01)
        
        # Execute middleware
        with patch('src.middleware.logging_middleware.logger') as mock_logger:
            logging_middleware(args, mock_next)
        
        # Verify
        assert next_called
        assert 'request_id' in args['context']
        
        # Check logging calls
        assert mock_logger.info.called
        info_calls = [str(call) for call in mock_logger.info.call_args_list]
        assert any('Command request' in str(call) for call in info_calls)
        assert any('Request completed' in str(call) for call in info_calls)
    
    def test_logging_middleware_event(self):
        """Test logging middleware with event request."""
        args = {
            'event': {
                'type': 'app_mention',
                'user': 'U789012',
                'channel': 'C789012',
                'channel_type': 'channel',
                'team': 'T123456'
            },
            'context': {}
        }
        
        def mock_next():
            pass
        
        with patch('src.middleware.logging_middleware.logger') as mock_logger:
            logging_middleware(args, mock_next)
        
        # Verify event logging
        assert mock_logger.info.called
        assert any('Event request' in str(call) for call in mock_logger.info.call_args_list)
    
    def test_logging_middleware_error_handling(self):
        """Test logging middleware error handling."""
        args = {
            'command': {
                'command': '/dona-task',
                'user_id': 'U123456'
            },
            'context': {}
        }
        
        def mock_next():
            raise ValueError("Test error")
        
        with patch('src.middleware.logging_middleware.logger') as mock_logger:
            with pytest.raises(ValueError):
                logging_middleware(args, mock_next)
        
        # Verify error logging
        assert mock_logger.error.called
        error_call = str(mock_logger.error.call_args)
        assert 'Request failed' in error_call
        assert 'Test error' in error_call
    
    def test_logging_middleware_slow_request(self):
        """Test logging middleware detects slow requests."""
        args = {
            'command': {
                'command': '/dona-task',
                'user_id': 'U123456'
            },
            'context': {}
        }
        
        # Create a custom mock for metrics collector
        with patch('src.middleware.logging_middleware.logger') as mock_logger, \
             patch('src.middleware.logging_middleware.metrics_collector') as mock_metrics:
            
            # Track calls to record_request
            recorded_requests = []
            def mock_record_request(**kwargs):
                recorded_requests.append(kwargs)
            
            mock_metrics.record_request.side_effect = mock_record_request
            
            # Mock the request logger to return slow duration
            with patch.object(request_logger, 'end_request') as mock_end:
                mock_end.return_value = {
                    'request_id': 'test-123',
                    'type': 'command:/dona-task',
                    'user_id': 'U123456',
                    'duration_ms': 4000,  # 4 seconds
                    'status': 'success',
                    'error': None,
                    'metadata': {}
                }
                
                def mock_next():
                    pass
                
                logging_middleware(args, mock_next)
        
        # Check for slow request warning
        assert mock_logger.warning.called
        warning_calls = [str(call) for call in mock_logger.warning.call_args_list]
        assert any('Slow request detected' in call for call in warning_calls)


class TestPerformanceMiddleware:
    """Test performance tracking middleware."""
    
    def test_performance_middleware_tracking(self):
        """Test performance middleware tracks duration."""
        args = {'context': {}}
        
        def mock_next():
            time.sleep(0.01)
        
        performance_middleware(args, mock_next)
        
        # Check performance data added to context
        assert 'performance' in args['context']
        assert 'duration_ms' in args['context']['performance']
        assert args['context']['performance']['duration_ms'] > 0
    
    def test_performance_middleware_very_slow(self):
        """Test performance middleware logs very slow requests."""
        args = {
            'command': {'command': '/dona-task'},
            'context': {}
        }
        
        def mock_next():
            pass
        
        with patch('src.middleware.logging_middleware.logger') as mock_logger, \
             patch('time.time') as mock_time:
            
            # Make request appear to take 6 seconds
            mock_time.side_effect = [0, 6]
            
            performance_middleware(args, mock_next)
        
        # Check for very slow request warning
        assert mock_logger.warning.called
        assert 'Very slow request' in str(mock_logger.warning.call_args)


class TestAnalyticsMiddleware:
    """Test analytics collection middleware."""
    
    def test_analytics_middleware_command(self):
        """Test analytics middleware with command."""
        args = {
            'command': {
                'command': '/dona-task',
                'text': 'list',
                'user_id': 'U123456',
                'team_id': 'T123456'
            },
            'context': {}
        }
        
        def mock_next():
            pass
        
        analytics_middleware(args, mock_next)
        
        # Check analytics data
        assert 'analytics' in args['context']
        analytics = args['context']['analytics']
        assert analytics['user_id'] == 'U123456'
        assert analytics['team_id'] == 'T123456'
        assert analytics['interaction_type'] == 'command'
        assert analytics['metadata']['command'] == '/dona-task'
        assert analytics['metadata']['has_text'] is True
    
    def test_analytics_middleware_event(self):
        """Test analytics middleware with event."""
        args = {
            'event': {
                'type': 'message',
                'user': 'U789012',
                'team': 'T789012',
                'channel_type': 'im'
            },
            'context': {}
        }
        
        def mock_next():
            pass
        
        analytics_middleware(args, mock_next)
        
        # Check analytics data
        analytics = args['context']['analytics']
        assert analytics['user_id'] == 'U789012'
        assert analytics['interaction_type'] == 'event'
        assert analytics['metadata']['event_type'] == 'message'
        assert analytics['metadata']['channel_type'] == 'im'


class TestRequestLogger:
    """Test RequestLogger class."""
    
    def test_request_tracking(self):
        """Test request start and end tracking."""
        logger = RequestLogger()
        
        # Start request
        logger.start_request('req-123', 'command:/dona-task', 'U123456', {'channel': 'C123'})
        
        # Verify active request
        assert 'req-123' in logger.active_requests
        
        # End request
        time.sleep(0.01)  # Ensure some duration
        metrics = logger.end_request('req-123', 'success')
        
        # Verify metrics
        assert metrics is not None
        assert metrics['request_id'] == 'req-123'
        assert metrics['type'] == 'command:/dona-task'
        assert metrics['user_id'] == 'U123456'
        assert metrics['status'] == 'success'
        assert metrics['duration_ms'] > 0
        assert metrics['metadata']['channel'] == 'C123'
        
        # Verify request removed from active
        assert 'req-123' not in logger.active_requests
    
    def test_end_nonexistent_request(self):
        """Test ending a request that wasn't started."""
        logger = RequestLogger()
        
        metrics = logger.end_request('nonexistent', 'success')
        assert metrics is None


class TestMetricsCollector:
    """Test MetricsCollector functionality."""
    
    def test_record_request(self):
        """Test recording request metrics."""
        collector = MetricsCollector(window_minutes=5)
        
        # Record some requests
        collector.record_request('command:/dona-task', 100, 'success', 'U123')
        collector.record_request('command:/dona-task', 200, 'success', 'U456')
        collector.record_request('command:/dona-task', 150, 'error', 'U789')
        collector.record_request('event:message', 50, 'success', 'U123')
        
        # Get summary
        summary = collector.get_summary()
        
        # Verify summary
        assert 'command:/dona-task' in summary['request_types']
        assert 'event:message' in summary['request_types']
        
        task_stats = summary['request_types']['command:/dona-task']
        assert task_stats['count'] == 3
        assert task_stats['success_count'] == 2
        assert task_stats['error_count'] == 1
        assert task_stats['avg_duration_ms'] == 150  # (100+200+150)/3
        
        # Check counters
        assert summary['counters']['command:/dona-task:total'] == 3
        assert summary['counters']['command:/dona-task:success'] == 2
        assert summary['counters']['command:/dona-task:error'] == 1
    
    def test_user_stats(self):
        """Test getting user-specific statistics."""
        collector = MetricsCollector()
        
        # Record requests for different users
        collector.record_request('command:/dona-task', 100, 'success', 'U123')
        collector.record_request('command:/dona-help', 50, 'success', 'U123')
        collector.record_request('command:/dona-task', 200, 'success', 'U456')
        
        # Get user stats
        user_stats = collector.get_user_stats('U123')
        
        assert user_stats['user_id'] == 'U123'
        assert user_stats['total_requests'] == 2
        assert 'command:/dona-task' in user_stats['request_types']
        assert 'command:/dona-help' in user_stats['request_types']
        assert user_stats['request_types']['command:/dona-task']['count'] == 1
        assert user_stats['request_types']['command:/dona-task']['avg_duration_ms'] == 100
    
    def test_percentile_calculation(self):
        """Test percentile calculation."""
        collector = MetricsCollector()
        
        # Record requests with various durations
        for duration in [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]:
            collector.record_request('test', duration, 'success', 'U123')
        
        summary = collector.get_summary()
        stats = summary['request_types']['test']
        
        # P95 should be around 95 (95th percentile of 10-100)
        assert 90 <= stats['p95_duration_ms'] <= 100
        # P99 should be 100 (highest value)
        assert stats['p99_duration_ms'] == 100


class TestTimer:
    """Test Timer context manager."""
    
    def test_timer_basic(self):
        """Test basic timer functionality."""
        with patch('logging.getLogger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            
            with Timer("test_operation") as timer:
                time.sleep(0.01)
            
            # Check timer recorded time
            assert timer.elapsed > 0.01
            
            # Check logging
            mock_logger.debug.assert_called_once()
            debug_call = str(mock_logger.debug.call_args)
            assert "test_operation took" in debug_call
    
    def test_timer_elapsed_property(self):
        """Test timer elapsed property."""
        timer = Timer("test")
        
        # Before entering context
        assert timer.elapsed == 0
        
        # During context
        timer.__enter__()
        time.sleep(0.01)
        assert timer.elapsed > 0
        
        # After context
        timer.__exit__(None, None, None)
        final_elapsed = timer.elapsed
        assert final_elapsed > 0.01