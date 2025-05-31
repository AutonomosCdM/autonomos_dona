"""Tests for Slack service functionality."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
import json

from src.services.slack_client import SlackService, get_slack_service
from slack_sdk.errors import SlackApiError


class TestSlackService:
    """Test SlackService class methods."""
    
    @pytest.fixture
    def mock_client(self):
        """Create a mock Slack WebClient."""
        return MagicMock()
    
    @pytest.fixture
    def slack_service(self, mock_client):
        """Create SlackService instance with mocked client."""
        service = SlackService()
        service.client = mock_client
        return service
    
    def test_get_user_info_success(self, slack_service, mock_client):
        """Test successful user info retrieval."""
        # Mock response
        mock_client.users_info.return_value = {
            "ok": True,
            "user": {
                "id": "U123456",
                "name": "testuser",
                "real_name": "Test User",
                "email": "test@example.com"
            }
        }
        
        result = slack_service.get_user_info("U123456")
        
        assert result is not None
        assert result["id"] == "U123456"
        assert result["name"] == "testuser"
        mock_client.users_info.assert_called_once_with(user="U123456")
    
    def test_get_user_info_error(self, slack_service, mock_client):
        """Test user info retrieval with API error."""
        # Mock API error
        mock_client.users_info.side_effect = SlackApiError(
            message="user_not_found",
            response={"ok": False, "error": "user_not_found"}
        )
        
        result = slack_service.get_user_info("U999999")
        
        assert result is None
        mock_client.users_info.assert_called_once_with(user="U999999")
    
    def test_send_dm_success(self, slack_service, mock_client):
        """Test successful DM sending."""
        # Mock successful responses
        mock_client.conversations_open.return_value = {
            "ok": True,
            "channel": {"id": "D123456"}
        }
        mock_client.chat_postMessage.return_value = {"ok": True}
        
        result = slack_service.send_dm("U123456", "Hello, test!")
        
        assert result is True
        mock_client.conversations_open.assert_called_once_with(users=["U123456"])
        mock_client.chat_postMessage.assert_called_once_with(
            channel="D123456",
            text="Hello, test!",
            blocks=None
        )
    
    def test_send_dm_with_blocks(self, slack_service, mock_client):
        """Test sending DM with blocks."""
        # Mock successful responses
        mock_client.conversations_open.return_value = {
            "ok": True,
            "channel": {"id": "D123456"}
        }
        mock_client.chat_postMessage.return_value = {"ok": True}
        
        blocks = [{"type": "section", "text": {"type": "mrkdwn", "text": "Test"}}]
        result = slack_service.send_dm("U123456", "Hello", blocks)
        
        assert result is True
        mock_client.chat_postMessage.assert_called_once_with(
            channel="D123456",
            text="Hello",
            blocks=blocks
        )
    
    def test_send_dm_error(self, slack_service, mock_client):
        """Test DM sending with error."""
        # Mock API error
        mock_client.conversations_open.side_effect = SlackApiError(
            message="channel_not_found",
            response={"ok": False, "error": "channel_not_found"}
        )
        
        result = slack_service.send_dm("U123456", "Hello")
        
        assert result is False
        mock_client.conversations_open.assert_called_once()
    
    def test_post_ephemeral_success(self, slack_service, mock_client):
        """Test successful ephemeral message posting."""
        mock_client.chat_postEphemeral.return_value = {"ok": True}
        
        result = slack_service.post_ephemeral("C123456", "U123456", "Secret message")
        
        assert result is True
        mock_client.chat_postEphemeral.assert_called_once_with(
            channel="C123456",
            user="U123456",
            text="Secret message",
            blocks=None
        )
    
    def test_post_ephemeral_error(self, slack_service, mock_client):
        """Test ephemeral message posting with error."""
        mock_client.chat_postEphemeral.side_effect = SlackApiError(
            message="not_in_channel",
            response={"ok": False, "error": "not_in_channel"}
        )
        
        result = slack_service.post_ephemeral("C123456", "U123456", "Secret message")
        
        assert result is False
    
    def test_format_task_list_empty(self):
        """Test formatting empty task list."""
        result = SlackService.format_task_list([])
        assert result == "_No tasks found_"
    
    def test_format_task_list_with_tasks(self):
        """Test formatting task list with multiple tasks."""
        tasks = [
            {
                "id": "1",
                "title": "Write tests",
                "status": "in_progress",
                "description": "Unit tests for services"
            },
            {
                "id": "2",
                "title": "Review PR",
                "status": "completed"
            },
            {
                "id": "3",
                "title": "Deploy to prod",
                "status": "pending"
            }
        ]
        
        result = SlackService.format_task_list(tasks)
        
        assert "*Your Tasks:*" in result
        assert ":large_blue_circle: *Write tests* (#1)" in result
        assert "_Unit tests for services_" in result
        assert ":white_check_mark: *Review PR* (#2)" in result
        assert ":white_circle: *Deploy to prod* (#3)" in result
    
    def test_format_time_duration(self):
        """Test time duration formatting."""
        assert SlackService.format_time_duration(0) == "0m"
        assert SlackService.format_time_duration(45) == "0m"
        assert SlackService.format_time_duration(60) == "1m"
        assert SlackService.format_time_duration(3600) == "1h"
        assert SlackService.format_time_duration(5430) == "1h 30m"
        assert SlackService.format_time_duration(7200) == "2h"
    
    def test_create_task_blocks(self):
        """Test creating task blocks for Slack display."""
        task = {
            "id": "123",
            "title": "Important Task",
            "description": "This is a test task",
            "status": "in_progress",
            "created_at": datetime(2024, 1, 15, 10, 30)
        }
        
        blocks = SlackService.create_task_blocks(task)
        
        # Check structure
        assert len(blocks) >= 4
        assert blocks[0]["type"] == "section"
        assert "*Important Task*" in blocks[0]["text"]["text"]
        
        # Check description block
        assert blocks[1]["type"] == "section"
        assert "This is a test task" in blocks[1]["text"]["text"]
        
        # Check fields
        assert blocks[2]["type"] == "section"
        assert "fields" in blocks[2]
        assert any("In Progress" in str(field) for field in blocks[2]["fields"])
        
        # Check that created_at is properly handled
        date_field = next((f for f in blocks[2]["fields"] if "Created" in f.get("text", "")), None)
        assert date_field is not None
        # Should contain timestamp
        assert "<!date^" in date_field["text"]
        
        # Check action buttons
        assert blocks[3]["type"] == "actions"
        assert len(blocks[3]["elements"]) == 3
        assert blocks[3]["elements"][0]["action_id"] == "complete_task_123"
        assert blocks[3]["elements"][1]["action_id"] == "edit_task_123"
        assert blocks[3]["elements"][2]["action_id"] == "delete_task_123"
    
    def test_create_task_blocks_minimal(self):
        """Test creating task blocks with minimal data."""
        task = {"id": "456"}
        
        blocks = SlackService.create_task_blocks(task)
        
        assert blocks[0]["text"]["text"] == "*Untitled*"
        # Should still have action buttons
        assert blocks[-1]["type"] == "actions"
        assert blocks[-1]["elements"][0]["action_id"] == "complete_task_456"
    
    @patch('src.services.slack_client._slack_service', None)
    @patch('src.services.slack_client.SlackService')
    def test_get_slack_service_singleton(self, mock_slack_service_class):
        """Test that get_slack_service returns singleton instance."""
        mock_instance = MagicMock()
        mock_slack_service_class.return_value = mock_instance
        
        # First call creates instance
        service1 = get_slack_service()
        assert service1 == mock_instance
        mock_slack_service_class.assert_called_once()
        
        # Second call returns same instance
        mock_slack_service_class.reset_mock()
        service2 = get_slack_service()
        assert service2 == service1
        mock_slack_service_class.assert_not_called()