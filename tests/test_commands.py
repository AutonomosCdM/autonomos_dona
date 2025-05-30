"""
Unit tests for Slack command handlers.

This module tests the slash command implementations.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from src.handlers.commands import (
    handle_help_command,
    handle_task_command,
    handle_time_command,
    handle_status_command
)


class TestHelpCommand:
    """Test cases for the /dona-help command."""
    
    def test_help_command_responds_with_help_text(self):
        """Test that help command returns appropriate help text."""
        # Mock Slack functions
        ack = Mock()
        respond = Mock()
        command = {"user_id": "U123456"}
        
        # Execute command
        handle_help_command(ack, respond, command)
        
        # Verify ack was called
        ack.assert_called_once()
        
        # Verify respond was called with help text
        respond.assert_called_once()
        response_text = respond.call_args[0][0]
        assert "Welcome to Autónomos Dona Bot!" in response_text
        assert "/dona-help" in response_text
        assert "/dona-task" in response_text
        assert "/dona-time" in response_text


class TestTaskCommand:
    """Test cases for the /dona-task command."""
    
    def test_task_command_without_action(self):
        """Test task command without specifying an action."""
        ack = Mock()
        respond = Mock()
        command = {"user_id": "U123456", "text": ""}
        
        handle_task_command(ack, respond, command)
        
        ack.assert_called_once()
        respond.assert_called_with("Please specify an action: `create`, `list`, or `update`")
    
    def test_task_create_without_description(self):
        """Test task create without a description."""
        ack = Mock()
        respond = Mock()
        command = {"user_id": "U123456", "text": "create"}
        
        handle_task_command(ack, respond, command)
        
        ack.assert_called_once()
        respond.assert_called_with("Please provide a task description")
    
    def test_task_create_with_description(self):
        """Test task create with a valid description."""
        ack = Mock()
        respond = Mock()
        command = {"user_id": "U123456", "text": "create Fix login bug"}
        
        handle_task_command(ack, respond, command)
        
        ack.assert_called_once()
        respond.assert_called_once()
        response_text = respond.call_args[0][0]
        assert "Task created" in response_text
        assert "Fix login bug" in response_text
    
    def test_task_list_action(self):
        """Test task list action."""
        ack = Mock()
        respond = Mock()
        command = {"user_id": "U123456", "text": "list"}
        
        handle_task_command(ack, respond, command)
        
        ack.assert_called_once()
        respond.assert_called_once()
        response_text = respond.call_args[0][0]
        assert "Your tasks:" in response_text


class TestTimeCommand:
    """Test cases for the /dona-time command."""
    
    def test_time_command_without_action(self):
        """Test time command without specifying an action."""
        ack = Mock()
        respond = Mock()
        command = {"user_id": "U123456", "text": ""}
        
        handle_time_command(ack, respond, command)
        
        ack.assert_called_once()
        respond.assert_called_with("Please specify an action: `start`, `stop`, or `log`")
    
    def test_time_start_action(self):
        """Test time start action."""
        ack = Mock()
        respond = Mock()
        command = {"user_id": "U123456", "text": "start"}
        
        handle_time_command(ack, respond, command)
        
        ack.assert_called_once()
        respond.assert_called_once()
        response_text = respond.call_args[0][0]
        assert "Time tracking started" in response_text
    
    def test_time_stop_action(self):
        """Test time stop action."""
        ack = Mock()
        respond = Mock()
        command = {"user_id": "U123456", "text": "stop"}
        
        handle_time_command(ack, respond, command)
        
        ack.assert_called_once()
        respond.assert_called_once()
        response_text = respond.call_args[0][0]
        assert "Time tracking stopped" in response_text


class TestStatusCommand:
    """Test cases for the /dona-status command."""
    
    def test_status_command_returns_user_status(self):
        """Test that status command returns user's status information."""
        ack = Mock()
        respond = Mock()
        command = {"user_id": "U123456"}
        
        handle_status_command(ack, respond, command)
        
        ack.assert_called_once()
        respond.assert_called_once()
        response_text = respond.call_args[0][0]
        assert "Your Status" in response_text
        assert "Active Tasks" in response_text
        assert "Time Today" in response_text


if __name__ == "__main__":
    pytest.main([__file__])