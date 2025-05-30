"""Pytest configuration and shared fixtures for Autónomos Dona tests."""

import os
import sys
from typing import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Set up test environment variables BEFORE any imports
os.environ["SLACK_BOT_TOKEN"] = "xoxb-test-token"
os.environ["SLACK_APP_TOKEN"] = "xapp-test-token"
os.environ["SLACK_SIGNING_SECRET"] = "test-signing-secret"
os.environ["SUPABASE_URL"] = "https://test.supabase.co"
os.environ["SUPABASE_KEY"] = "test-supabase-key"
os.environ["LOG_LEVEL"] = "DEBUG"

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

# Add src to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


@pytest.fixture
def mock_slack_app():
    """Mock Slack Bolt App instance."""
    app = MagicMock(spec=App)
    app.client = MagicMock()
    app.client.chat_postMessage = AsyncMock()
    app.client.users_info = AsyncMock()
    app.client.conversations_info = AsyncMock()
    return app


@pytest.fixture
def mock_socket_handler():
    """Mock Socket Mode Handler."""
    handler = MagicMock(spec=SocketModeHandler)
    handler.start = MagicMock()
    handler.close = MagicMock()
    return handler


@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client."""
    with patch("src.services.supabase_client.supabase") as mock_client:
        # Mock table operations
        mock_table = MagicMock()
        mock_table.insert = MagicMock()
        mock_table.select = MagicMock()
        mock_table.update = MagicMock()
        mock_table.delete = MagicMock()
        
        # Chain methods for Supabase query builder pattern
        mock_table.insert.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.update.return_value = mock_table
        mock_table.delete.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.execute.return_value = MagicMock(data=[])
        
        mock_client.table.return_value = mock_table
        yield mock_client


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Set up test environment variables."""
    test_env = {
        "SLACK_BOT_TOKEN": "xoxb-test-token",
        "SLACK_APP_TOKEN": "xapp-test-token",
        "SLACK_SIGNING_SECRET": "test-signing-secret",
        "SUPABASE_URL": "https://test.supabase.co",
        "SUPABASE_KEY": "test-supabase-key",
        "LOG_LEVEL": "DEBUG",
    }
    
    for key, value in test_env.items():
        monkeypatch.setenv(key, value)
    
    return test_env


@pytest.fixture
def sample_slack_event():
    """Sample Slack event for testing."""
    return {
        "type": "message",
        "channel": "C1234567890",
        "user": "U1234567890",
        "text": "Hello Dona!",
        "ts": "1234567890.123456",
        "event_ts": "1234567890.123456",
        "channel_type": "channel",
    }


@pytest.fixture
def sample_slack_command():
    """Sample Slack slash command for testing."""
    return {
        "token": "test-token",
        "team_id": "T1234567890",
        "team_domain": "test-workspace",
        "channel_id": "C1234567890",
        "channel_name": "general",
        "user_id": "U1234567890",
        "user_name": "testuser",
        "command": "/task",
        "text": "create Buy coffee",
        "response_url": "https://hooks.slack.com/commands/test",
        "trigger_id": "123456.7890",
    }


@pytest.fixture
def sample_task_data():
    """Sample task data for testing."""
    return {
        "id": "task-123",
        "title": "Buy coffee",
        "description": "Get coffee beans from the store",
        "assigned_to": "U1234567890",
        "created_by": "U1234567890",
        "status": "pending",
        "priority": "medium",
        "due_date": "2024-12-31T23:59:59Z",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
    }


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "slack_user_id": "U1234567890",
        "name": "Test User",
        "email": "test@autonomos.ai",
        "role": "team_member",
        "created_at": "2024-01-01T00:00:00Z",
    }


@pytest.fixture
async def async_mock():
    """Helper for creating async mocks."""
    def _async_mock(*args, **kwargs):
        return AsyncMock(*args, **kwargs)
    return _async_mock


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: Unit tests that don't require external services"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests that may require external services"
    )
    config.addinivalue_line(
        "markers", "slow: Tests that take longer to execute"
    )


# Async test support
pytest_plugins = ["pytest_asyncio"]