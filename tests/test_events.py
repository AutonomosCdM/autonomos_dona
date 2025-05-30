"""Simplified tests for event handlers."""

import pytest
from unittest.mock import Mock, MagicMock

from src.handlers.events import (
    handle_app_mention,
    handle_message,
    handle_reaction_added,
    handle_app_home_opened,
    register_event_handlers
)


class TestEventHandlers:
    """Test event handlers with basic functionality."""
    
    def test_app_mention_response(self):
        """Test app mention handler responds appropriately."""
        event = {
            "type": "app_mention",
            "user": "U123456",
            "text": "<@U789012> help",
            "ts": "1234567890.123456",
            "channel": "C123456"
        }
        say = Mock()
        context = MagicMock()
        
        handle_app_mention(event, say, context)
        
        # Should respond to mention
        say.assert_called_once()
        response = say.call_args[0][0]
        assert len(response) > 0
    
    def test_message_dm_only(self):
        """Test message handler only responds to DMs."""
        # Non-DM message
        event = {
            "type": "message",
            "user": "U123456",
            "text": "hello",
            "ts": "1234567890.123456",
            "channel": "C123456",
            "channel_type": "channel"
        }
        say = Mock()
        context = MagicMock()
        
        handle_message(event, say, context)
        
        # Should not respond to non-DMs
        say.assert_not_called()
    
    def test_reaction_handler_checkmark(self):
        """Test reaction handler processes checkmarks."""
        event = {
            "type": "reaction_added",
            "user": "U123456",
            "reaction": "white_check_mark",
            "item": {
                "type": "message",
                "channel": "C123456",
                "ts": "1234567890.123456"
            },
            "item_user": "U789012",
            "event_ts": "1234567890.123456"
        }
        
        # Just test that it handles the event without error
        try:
            handle_reaction_added(event)
            assert True
        except Exception as e:
            pytest.fail(f"Reaction handler raised exception: {e}")
    
    def test_app_home_opened(self):
        """Test app home handler publishes view."""
        # Home tab event
        event = {
            "type": "app_home_opened",
            "user": "U123456",
            "tab": "home",
            "view": {}
        }
        client = MagicMock()
        
        handle_app_home_opened(event, client)
        
        # Should publish home view
        client.views_publish.assert_called_once()
        # Check that a home view was published
        call_args = client.views_publish.call_args
        assert call_args[1]['user_id'] == 'U123456'
        assert call_args[1]['view']['type'] == 'home'
    
    def test_event_registration(self):
        """Test all events are registered."""
        app = MagicMock()
        
        register_event_handlers(app)
        
        # Check events were registered
        expected_events = [
            "app_mention",
            "message", 
            "reaction_added",
            "app_home_opened"
        ]
        
        assert app.event.call_count == len(expected_events)
        
        # Verify each event
        registered = [call[0][0] for call in app.event.call_args_list]
        for event in expected_events:
            assert event in registered