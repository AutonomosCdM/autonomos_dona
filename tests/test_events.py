"""
Unit tests for Slack event handlers.

This module tests the event subscription handlers.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from src.handlers.events import (
    handle_app_mention,
    handle_message,
    handle_reaction_added,
    handle_app_home_opened
)


class TestAppMention:
    """Test cases for app mention events."""
    
    def test_app_mention_with_help_keyword(self):
        """Test app mention containing 'help' keyword."""
        event = {
            "user": "U123456",
            "text": "<@U789> help me please"
        }
        say = Mock()
        
        # Mock settings to provide bot user ID
        with patch('src.handlers.events.settings') as mock_settings:
            mock_settings.SLACK_BOT_USER_ID = "U789"
            handle_app_mention(event, say)
        
        say.assert_called_once()
        response = say.call_args[0][0]
        assert "Hi <@U123456>!" in response
        assert "/dona-help" in response
        assert "manage tasks" in response
    
    def test_app_mention_without_help_keyword(self):
        """Test app mention without specific keywords."""
        event = {
            "user": "U123456",
            "text": "<@U789> what's up?"
        }
        say = Mock()
        
        with patch('src.handlers.events.settings') as mock_settings:
            mock_settings.SLACK_BOT_USER_ID = "U789"
            handle_app_mention(event, say)
        
        say.assert_called_once()
        response = say.call_args[0][0]
        assert "Hi <@U123456>!" in response
        assert "You said: what's up?" in response
        assert "/dona-help" in response


class TestMessage:
    """Test cases for direct message events."""
    
    def test_direct_message_with_hello(self):
        """Test DM containing greeting."""
        event = {
            "user": "U123456",
            "text": "Hello bot!",
            "channel_type": "im"
        }
        say = Mock()
        
        handle_message(event, say)
        
        say.assert_called_once()
        response = say.call_args[0][0]
        assert "Hello <@U123456>!" in response
        assert "How can I help you today?" in response
    
    def test_direct_message_with_task_keyword(self):
        """Test DM mentioning tasks."""
        event = {
            "user": "U123456",
            "text": "I need to manage my tasks",
            "channel_type": "im"
        }
        say = Mock()
        
        handle_message(event, say)
        
        say.assert_called_once()
        response = say.call_args[0][0]
        assert "/dona-task" in response
    
    def test_channel_message_ignored(self):
        """Test that channel messages are ignored."""
        event = {
            "user": "U123456",
            "text": "Hello everyone!",
            "channel_type": "channel"
        }
        say = Mock()
        
        handle_message(event, say)
        
        say.assert_not_called()
    
    def test_bot_message_ignored(self):
        """Test that bot messages are ignored."""
        event = {
            "user": "U123456",
            "text": "Automated message",
            "channel_type": "im",
            "bot_id": "B123456"
        }
        say = Mock()
        
        handle_message(event, say)
        
        say.assert_not_called()


class TestReactionAdded:
    """Test cases for reaction added events."""
    
    def test_check_mark_reaction(self):
        """Test handling of check mark reaction."""
        event = {
            "user": "U123456",
            "reaction": "white_check_mark",
            "item": {
                "type": "message",
                "channel": "C123456",
                "ts": "1234567890.123456"
            }
        }
        
        # Should not raise any exceptions
        handle_reaction_added(event)
    
    def test_other_reaction(self):
        """Test handling of non-check mark reactions."""
        event = {
            "user": "U123456",
            "reaction": "thumbsup",
            "item": {
                "type": "message",
                "channel": "C123456",
                "ts": "1234567890.123456"
            }
        }
        
        # Should not raise any exceptions
        handle_reaction_added(event)


class TestAppHomeOpened:
    """Test cases for app home opened events."""
    
    def test_app_home_opened_publishes_view(self):
        """Test that opening app home publishes a view."""
        event = {"user": "U123456"}
        client = Mock()
        
        handle_app_home_opened(event, client)
        
        # Verify views.publish was called
        client.views_publish.assert_called_once()
        
        # Get the published view
        call_args = client.views_publish.call_args
        assert call_args.kwargs["user_id"] == "U123456"
        
        view = call_args.kwargs["view"]
        assert view["type"] == "home"
        assert len(view["blocks"]) > 0
        
        # Check for expected content
        view_str = str(view)
        assert "Welcome to Autónomos Dona" in view_str
        assert "Your Dashboard" in view_str
        assert "Today's Stats" in view_str


if __name__ == "__main__":
    pytest.main([__file__])