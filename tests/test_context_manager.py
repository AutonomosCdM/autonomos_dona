"""Tests for the context manager module."""

import pytest
from unittest.mock import Mock, MagicMock
from slack_sdk.errors import SlackApiError

from src.utils.context_manager import ContextManager, ContextType


class TestContextManager:
    """Test suite for ContextManager."""
    
    @pytest.fixture
    def mock_slack_client(self):
        """Create a mock Slack client."""
        return Mock()
    
    @pytest.fixture
    def context_manager(self, mock_slack_client):
        """Create a ContextManager instance."""
        return ContextManager(mock_slack_client)
    
    def test_dm_channel_detection(self, context_manager):
        """Test that DM channels are detected as private."""
        # DM channels start with 'D'
        assert context_manager.get_context_type("D12345") == ContextType.PRIVATE
    
    def test_private_channel_detection(self, context_manager):
        """Test that private channels are detected as private."""
        # Private channels start with 'G'
        assert context_manager.get_context_type("G12345") == ContextType.PRIVATE
    
    def test_public_channel_detection(self, context_manager, mock_slack_client):
        """Test that public channels are detected correctly."""
        # Mock the API response for a public channel
        mock_slack_client.conversations_info.return_value = {
            'ok': True,
            'channel': {
                'id': 'C12345',
                'is_private': False,
                'is_im': False,
                'is_mpim': False
            }
        }
        
        assert context_manager.get_context_type("C12345") == ContextType.PUBLIC
    
    def test_private_channel_via_api(self, context_manager, mock_slack_client):
        """Test that private channels are detected via API."""
        # Mock the API response for a private channel
        mock_slack_client.conversations_info.return_value = {
            'ok': True,
            'channel': {
                'id': 'C12345',
                'is_private': True,
                'is_im': False,
                'is_mpim': False
            }
        }
        
        assert context_manager.get_context_type("C12345") == ContextType.PRIVATE
    
    def test_im_channel_detection(self, context_manager, mock_slack_client):
        """Test that IM channels are detected as private."""
        # Mock the API response for an IM
        mock_slack_client.conversations_info.return_value = {
            'ok': True,
            'channel': {
                'id': 'C12345',
                'is_private': False,
                'is_im': True,
                'is_mpim': False
            }
        }
        
        assert context_manager.get_context_type("C12345") == ContextType.PRIVATE
    
    def test_channel_not_found_fallback(self, context_manager, mock_slack_client):
        """Test fallback when channel is not found."""
        # Mock channel not found error
        error_response = {'error': 'channel_not_found'}
        mock_slack_client.conversations_info.side_effect = SlackApiError(
            message="Channel not found",
            response=error_response
        )
        
        # Mock successful conversations.open
        mock_slack_client.conversations_open.return_value = {
            'ok': True,
            'channel': {
                'id': 'D12345',
                'is_im': True
            }
        }
        
        assert context_manager.get_context_type("D12345") == ContextType.PRIVATE
    
    def test_api_error_handling(self, context_manager, mock_slack_client):
        """Test handling of API errors."""
        # Mock generic API error
        error_response = {'error': 'internal_error'}
        mock_slack_client.conversations_info.side_effect = SlackApiError(
            message="Internal error",
            response=error_response
        )
        
        assert context_manager.get_context_type("C12345") == ContextType.UNKNOWN
    
    def test_channel_cache(self, context_manager, mock_slack_client):
        """Test that channel info is cached."""
        # Mock the API response
        mock_slack_client.conversations_info.return_value = {
            'ok': True,
            'channel': {
                'id': 'C12345',
                'is_private': False,
                'is_im': False,
                'is_mpim': False
            }
        }
        
        # First call
        context_manager.get_context_type("C12345")
        # Second call should use cache
        context_manager.get_context_type("C12345")
        
        # API should only be called once
        assert mock_slack_client.conversations_info.call_count == 1
    
    def test_privacy_level(self, context_manager):
        """Test privacy level determination."""
        assert context_manager.get_privacy_level(ContextType.PRIVATE) == "confidential"
        assert context_manager.get_privacy_level(ContextType.PUBLIC) == "team"
        assert context_manager.get_privacy_level(ContextType.UNKNOWN) == "unknown"
    
    def test_format_response_private(self, context_manager):
        """Test response formatting for private context."""
        message = "here's your info"
        result = context_manager.format_response(message, ContextType.PRIVATE, "U12345")
        assert result == "<@U12345>, here's your info"
    
    def test_format_response_public(self, context_manager):
        """Test response formatting for public context."""
        message = "here's the team info"
        result = context_manager.format_response(message, ContextType.PUBLIC, "U12345")
        assert result == "here's the team info"
    
    def test_allowed_commands(self, context_manager):
        """Test command permissions based on context."""
        # Private context has more commands
        private_commands = context_manager.get_allowed_commands(ContextType.PRIVATE, "U12345")
        assert private_commands["config"] is True
        assert private_commands["sensitive"] is True
        
        # Public context has fewer commands
        public_commands = context_manager.get_allowed_commands(ContextType.PUBLIC, "U12345")
        assert "config" not in public_commands
        assert "sensitive" not in public_commands
        assert public_commands["help"] is True
    
    def test_clear_cache(self, context_manager, mock_slack_client):
        """Test cache clearing."""
        # Populate cache
        mock_slack_client.conversations_info.return_value = {
            'ok': True,
            'channel': {'id': 'C12345', 'is_private': False}
        }
        context_manager.get_context_type("C12345")
        
        # Clear cache
        context_manager.clear_cache()
        
        # Next call should hit API again
        context_manager.get_context_type("C12345")
        assert mock_slack_client.conversations_info.call_count == 2