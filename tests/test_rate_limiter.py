"""Tests for rate limiting functionality."""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock

from src.utils.rate_limiter import (
    RateLimit,
    TokenBucket,
    RateLimiter,
    rate_limiter
)
from src.middleware.rate_limit_middleware import (
    rate_limit_middleware,
    get_rate_limit_status,
    cleanup_rate_limiter
)


class TestRateLimit:
    """Test RateLimit configuration."""
    
    def test_rate_limit_creation(self):
        """Test creating a rate limit configuration."""
        rl = RateLimit(max_tokens=100, refill_rate=10, burst_size=20)
        
        assert rl.max_tokens == 100
        assert rl.refill_rate == 10
        assert rl.burst_size == 20
    
    def test_rate_limit_validation(self):
        """Test rate limit validation."""
        with pytest.raises(ValueError, match="max_tokens must be positive"):
            RateLimit(max_tokens=0, refill_rate=10, burst_size=20)
        
        with pytest.raises(ValueError, match="refill_rate must be positive"):
            RateLimit(max_tokens=100, refill_rate=0, burst_size=20)
        
        with pytest.raises(ValueError, match="burst_size must be positive"):
            RateLimit(max_tokens=100, refill_rate=10, burst_size=0)


class TestTokenBucket:
    """Test TokenBucket functionality."""
    
    def test_token_bucket_creation(self):
        """Test creating a token bucket."""
        bucket = TokenBucket(tokens=10.0, last_refill=time.time())
        
        assert bucket.tokens == 10.0
        assert bucket.last_refill > 0
    
    def test_token_consumption(self):
        """Test consuming tokens from bucket."""
        bucket = TokenBucket(tokens=10.0, last_refill=time.time())
        
        # Successful consumption
        assert bucket.consume(5) is True
        assert bucket.tokens == 5.0
        
        # Insufficient tokens
        assert bucket.consume(10) is False
        assert bucket.tokens == 5.0  # Unchanged
        
        # Consume remaining
        assert bucket.consume(5) is True
        assert bucket.tokens == 0.0
    
    def test_token_refill(self):
        """Test refilling tokens."""
        current_time = time.time()
        bucket = TokenBucket(tokens=0.0, last_refill=current_time - 10)  # 10 seconds ago
        
        rate_limit = RateLimit(max_tokens=100, refill_rate=5, burst_size=100)
        
        # Refill after 10 seconds at 5 tokens/sec = 50 tokens
        bucket.refill(rate_limit, current_time)
        
        assert bucket.tokens == 50.0
        assert bucket.last_refill == current_time
    
    def test_token_refill_cap(self):
        """Test refill doesn't exceed max tokens."""
        current_time = time.time()
        bucket = TokenBucket(tokens=50.0, last_refill=current_time - 20)  # 20 seconds ago
        
        rate_limit = RateLimit(max_tokens=100, refill_rate=5, burst_size=100)
        
        # Would refill 100 tokens, but capped at max_tokens
        bucket.refill(rate_limit, current_time)
        
        assert bucket.tokens == 100.0  # Capped at max


class TestRateLimiter:
    """Test RateLimiter functionality."""
    
    def test_rate_limiter_creation(self):
        """Test creating a rate limiter."""
        limiter = RateLimiter()
        
        assert 'global' in limiter._rate_limits
        assert 'user' in limiter._rate_limits
        assert len(limiter._buckets) == 0  # No buckets initially
    
    def test_global_rate_limit(self):
        """Test global rate limiting."""
        limiter = RateLimiter()
        limiter.set_rate_limit('global', RateLimit(max_tokens=10, refill_rate=1, burst_size=10))
        
        # Use up global limit
        for i in range(10):
            allowed, info = limiter.check_rate_limit(f"user{i}", None)
            assert allowed is True
        
        # Next request should fail
        allowed, info = limiter.check_rate_limit("user11", None)
        assert allowed is False
        assert info['limit_type'] == 'global'
        assert info['retry_after'] > 0
    
    def test_user_rate_limit(self):
        """Test per-user rate limiting."""
        limiter = RateLimiter()
        limiter.set_rate_limit('user', RateLimit(max_tokens=5, refill_rate=1, burst_size=5))
        
        # Single user can make 5 requests
        for i in range(5):
            allowed, info = limiter.check_rate_limit("user1", None)
            assert allowed is True
        
        # 6th request fails
        allowed, info = limiter.check_rate_limit("user1", None)
        assert allowed is False
        assert info['limit_type'] == 'user'
        
        # Different user can still make requests
        allowed, info = limiter.check_rate_limit("user2", None)
        assert allowed is True
    
    def test_command_rate_limit(self):
        """Test per-command rate limiting."""
        limiter = RateLimiter()
        limiter.set_rate_limit('command:/test', RateLimit(max_tokens=3, refill_rate=0.5, burst_size=3))
        
        # User can make 3 requests to /test
        for i in range(3):
            allowed, info = limiter.check_rate_limit("user1", "command:/test")
            assert allowed is True
        
        # 4th request fails
        allowed, info = limiter.check_rate_limit("user1", "command:/test")
        assert allowed is False
        assert info['limit_type'] == 'command'
        assert info['command'] == 'command:/test'
        
        # Same user can use other commands
        allowed, info = limiter.check_rate_limit("user1", "command:/other")
        assert allowed is True
    
    def test_rate_limit_refill(self):
        """Test rate limit refilling over time."""
        limiter = RateLimiter()
        limiter.set_rate_limit('user', RateLimit(max_tokens=2, refill_rate=2, burst_size=2))
        
        # Use up tokens
        limiter.check_rate_limit("user1", None)
        limiter.check_rate_limit("user1", None)
        
        # Should be rate limited
        allowed, info = limiter.check_rate_limit("user1", None)
        assert allowed is False
        
        # Wait for refill
        time.sleep(0.6)  # 0.6 seconds = 1.2 tokens refilled
        
        # Should allow one more request
        allowed, info = limiter.check_rate_limit("user1", None)
        assert allowed is True
    
    def test_get_limit_info(self):
        """Test getting rate limit information."""
        limiter = RateLimiter()
        
        # Make some requests
        limiter.check_rate_limit("user1", "command:/dona-task")
        limiter.check_rate_limit("user1", "command:/dona-task")
        
        info = limiter.get_limit_info("user1", "command:/dona-task")
        
        assert 'user_limit' in info
        assert 'tokens_remaining' in info['user_limit']
        assert info['user_limit']['tokens_remaining'] < info['user_limit']['max_tokens']
        
        assert 'command_limit' in info
        assert info['command_limit']['command'] == 'command:/dona-task'
    
    def test_cleanup_old_buckets(self):
        """Test cleaning up old buckets."""
        limiter = RateLimiter()
        
        # Create some buckets
        limiter.check_rate_limit("user1", None)
        limiter.check_rate_limit("user2", None)
        
        # Mock time to make buckets appear old
        import time as time_module
        current = time_module.time()
        
        with patch('src.utils.rate_limiter.time.time') as mock_time:
            mock_time.return_value = current + 7200  # 2 hours later
            
            removed = limiter.cleanup_old_buckets(max_age_seconds=3600)
            assert removed >= 2  # At least both user buckets should be removed
    
    def test_get_stats(self):
        """Test getting rate limiter statistics."""
        limiter = RateLimiter()
        
        # Generate some rate limit hits
        limiter.set_rate_limit('user', RateLimit(max_tokens=1, refill_rate=0.01, burst_size=1))
        
        limiter.check_rate_limit("user1", None)
        limiter.check_rate_limit("user1", None)  # This should be rate limited
        
        stats = limiter.get_stats()
        
        assert 'active_buckets' in stats
        assert 'limit_hits' in stats
        assert 'user:user1' in stats['limit_hits']
        assert stats['limit_hits']['user:user1'] == 1


class TestRateLimitMiddleware:
    """Test rate limiting middleware."""
    
    def test_middleware_allows_normal_requests(self):
        """Test middleware allows requests within limits."""
        args = {
            'command': {
                'command': '/dona-task',
                'user_id': 'U123456',
                'text': 'create test'
            },
            'ack': Mock(),
            'respond': Mock()
        }
        
        next_called = False
        def mock_next():
            nonlocal next_called
            next_called = True
        
        with patch('src.middleware.rate_limit_middleware.rate_limiter') as mock_limiter:
            mock_limiter.check_rate_limit.return_value = (True, None)
            
            rate_limit_middleware(args, mock_next)
        
        assert next_called is True
        args['ack'].assert_not_called()  # Should not ack in middleware
        args['respond'].assert_not_called()  # Should not respond
    
    def test_middleware_blocks_rate_limited_requests(self):
        """Test middleware blocks requests exceeding limits."""
        args = {
            'command': {
                'command': '/dona-task',
                'user_id': 'U123456',
                'text': 'create test'
            },
            'ack': Mock(),
            'respond': Mock()
        }
        
        next_called = False
        def mock_next():
            nonlocal next_called
            next_called = True
        
        with patch('src.middleware.rate_limit_middleware.rate_limiter') as mock_limiter:
            mock_limiter.check_rate_limit.return_value = (False, {
                'limit_type': 'user',
                'retry_after': 60
            })
            
            rate_limit_middleware(args, mock_next)
        
        assert next_called is False
        args['ack'].assert_called_once()
        args['respond'].assert_called_once()
        
        # Check error message
        response = args['respond'].call_args[0][0]
        assert "límite de solicitudes" in response
    
    def test_middleware_different_error_messages(self):
        """Test middleware provides appropriate error messages."""
        test_cases = [
            ('global', 'mucho tráfico'),
            ('command', 'demasiadas veces'),
            ('user', 'límite de solicitudes')
        ]
        
        for limit_type, expected_text in test_cases:
            args = {
                'command': {
                    'command': '/dona-task',
                    'user_id': 'U123456'
                },
                'ack': Mock(),
                'respond': Mock()
            }
            
            with patch('src.middleware.rate_limit_middleware.rate_limiter') as mock_limiter:
                mock_limiter.check_rate_limit.return_value = (False, {
                    'limit_type': limit_type,
                    'retry_after': 120,
                    'command': 'command:/dona-task' if limit_type == 'command' else None
                })
                
                rate_limit_middleware(args, lambda: None)
                
                response = args['respond'].call_args[0][0]
                assert expected_text in response
    
    def test_middleware_ignores_non_commands(self):
        """Test middleware ignores non-command requests."""
        args = {
            'event': {'type': 'message', 'user': 'U123456'},
            'ack': Mock()
        }
        
        next_called = False
        def mock_next():
            nonlocal next_called
            next_called = True
        
        rate_limit_middleware(args, mock_next)
        
        assert next_called is True
        args['ack'].assert_not_called()
    
    def test_get_rate_limit_status(self):
        """Test getting formatted rate limit status."""
        with patch('src.middleware.rate_limit_middleware.rate_limiter') as mock_limiter:
            mock_limiter.get_limit_info.return_value = {
                'user_limit': {
                    'tokens_remaining': 30,
                    'max_tokens': 60,
                    'refill_rate': 1
                },
                'command_limit': {
                    'command': 'command:/dona-task',
                    'tokens_remaining': 5,
                    'max_tokens': 30,
                    'refill_rate': 0.5
                }
            }
            
            status = get_rate_limit_status('U123456', 'command:/dona-task')
            
            assert "Rate Limit Status" in status
            assert "User Limit" in status
            assert "30/60 (50%)" in status
            assert "Command Limit" in status
            assert "5/30" in status
    
    def test_cleanup_rate_limiter(self):
        """Test cleanup function."""
        with patch('src.middleware.rate_limit_middleware.rate_limiter') as mock_limiter:
            mock_limiter.cleanup_old_buckets.return_value = 5
            
            cleanup_rate_limiter()
            
            mock_limiter.cleanup_old_buckets.assert_called_once()
    
    def test_cleanup_rate_limiter_error_handling(self):
        """Test cleanup handles errors gracefully."""
        with patch('src.middleware.rate_limit_middleware.rate_limiter') as mock_limiter:
            mock_limiter.cleanup_old_buckets.side_effect = Exception("Test error")
            
            # Should not raise
            cleanup_rate_limiter()