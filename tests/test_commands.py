"""Simplified tests for command handlers that work without complex mocking."""

import pytest
from unittest.mock import Mock, MagicMock, patch

from src.handlers.commands import (
    handle_dona_command,
    handle_help_command,
    handle_task_command,
    handle_remind_command,
    handle_summary_command,
    handle_status_command,
    register_command_handlers
)
from src.utils.context_manager import ContextType


class TestCommandHandlers:
    """Test command handlers with basic functionality."""
    
    @patch('src.handlers.commands.get_slack_service')
    def test_dona_help_response(self, mock_get_slack_service):
        """Test that /dona with help text calls help handler."""
        # Mock the slack service
        mock_slack_service = MagicMock()
        mock_slack_service.context_manager.get_context_type.return_value = ContextType.PUBLIC
        mock_get_slack_service.return_value = mock_slack_service
        
        ack = Mock()
        respond = Mock()
        command = {
            "user_id": "U123456",
            "text": "help",
            "channel_id": "C123456"
        }
        
        # Mock app with supabase
        app_mock = MagicMock()
        app_mock._supabase = MagicMock()
        context = {"is_private": False, "user_id": "U123456", "app": app_mock}
        
        handle_dona_command(ack, respond, command, context)
        
        # The dona command calls ack once and responds with help text
        assert ack.call_count == 1
        # Should respond with help information
        assert respond.call_count == 1
        # Verify response contains help text
        response = respond.call_args[0][0]
        assert "Soy Dona" in response
        assert "Comandos disponibles" in response
    
    @patch('src.handlers.commands.get_slack_service')
    def test_help_command_response(self, mock_get_slack_service):
        """Test help command returns help text."""
        # Mock the slack service
        mock_slack_service = MagicMock()
        mock_slack_service.context_manager.get_context_type.return_value = ContextType.PUBLIC
        mock_get_slack_service.return_value = mock_slack_service
        
        ack = Mock()
        respond = Mock()
        command = {"user_id": "U123456", "channel_id": "C123456"}
        
        handle_help_command(ack, respond, command)
        
        ack.assert_called_once()
        respond.assert_called_once()
        response = respond.call_args[0][0]
        
        # Check for key elements in help text
        assert "/dona" in response
        assert "/dona-task" in response
        assert "/dona-help" in response or "Soy Dona" in response
    
    def test_task_command_without_app(self):
        """Test task command handles missing app gracefully."""
        ack = Mock()
        respond = Mock()
        command = {
            "user_id": "U123456",
            "text": "create Test task",
            "channel_id": "C123456"
        }
        
        handle_task_command(ack, respond, command)
        
        ack.assert_called_once()
        respond.assert_called_once()
        # Should respond with error since app is missing
        response = respond.call_args[0][0]
        assert "error" in response.lower() or "ocurrió" in response.lower()
    
    def test_task_command_invalid_action(self):
        """Test task command with invalid action."""
        ack = Mock()
        respond = Mock()
        command = {
            "user_id": "U123456",
            "text": "invalid",
            "channel_id": "C123456"
        }
        
        handle_task_command(ack, respond, command)
        
        ack.assert_called_once()
        respond.assert_called_once()
        response = respond.call_args[0][0]
        
        # Should show usage
        assert "create" in response
        assert "list" in response
        assert "update" in response
    
    def test_remind_command_empty_text(self):
        """Test remind command with empty text."""
        ack = Mock()
        respond = Mock()
        command = {
            "user_id": "U123456",
            "text": "",
            "channel_id": "C123456"
        }
        
        handle_remind_command(ack, respond, command)
        
        ack.assert_called_once()
        respond.assert_called_once()
        response = respond.call_args[0][0]
        
        # Should show usage or error message in Spanish
        assert "especifica" in response or "Usage" in response
    
    @patch('src.handlers.commands.get_supabase_service')
    def test_summary_command_period_validation(self, mock_get_supabase_service):
        """Test summary command validates period."""
        # Mock the supabase service
        mock_supabase_service = MagicMock()
        mock_get_supabase_service.return_value = mock_supabase_service
        
        ack = Mock()
        respond = Mock()
        command = {
            "user_id": "U123456",
            "text": "invalid",
            "channel_id": "C123456"
        }
        
        handle_summary_command(ack, respond, command)
        
        ack.assert_called_once()
        respond.assert_called_once()
        response = respond.call_args[0][0]
        
        # Should mention valid periods
        assert "today" in response or "hoy" in response
        assert "week" in response or "semana" in response
    
    @patch('src.handlers.commands.get_supabase_service')
    def test_status_command_without_service(self, mock_get_supabase_service):
        """Test status command handles missing service gracefully."""
        # Mock the supabase service
        mock_supabase_service = MagicMock()
        mock_get_supabase_service.return_value = mock_supabase_service
        
        ack = Mock()
        respond = Mock()
        command = {
            "user_id": "U123456",
            "channel_id": "C123456"
        }
        
        handle_status_command(ack, respond, command)
        
        ack.assert_called_once()
        respond.assert_called_once()
        # Status command returns mock data when no service is available
        response = respond.call_args[0][0]
        # The mock status response includes "Status" or task info
        assert "status" in response.lower() or "tasks" in response.lower()
    
    def test_command_registration(self):
        """Test all commands are registered."""
        app = MagicMock()
        
        register_command_handlers(app)
        
        # Check commands were registered
        expected_commands = [
            "/dona",
            "/dona-help",
            "/dona-task",
            "/dona-remind",
            "/dona-summary",
            "/dona-status",
            "/dona-metrics",
            "/dona-limits",
            "/dona-config"
        ]
        
        assert app.command.call_count == len(expected_commands)
        
        # Verify each command
        registered = [call[0][0] for call in app.command.call_args_list]
        for cmd in expected_commands:
            assert cmd in registered