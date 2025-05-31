"""Tests for interaction logging functionality."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

from src.services.supabase_client import SupabaseService


class TestInteractionLogging:
    """Test suite for logging conversations and messages."""
    
    @pytest.fixture
    def mock_supabase_client(self):
        """Create a mock Supabase client."""
        mock_client = MagicMock()
        mock_client.table.return_value = mock_client
        mock_client.select.return_value = mock_client
        mock_client.eq.return_value = mock_client
        mock_client.insert.return_value = mock_client
        mock_client.execute.return_value = MagicMock(data=[])
        return mock_client
    
    @pytest.fixture
    def supabase_service(self, mock_supabase_client):
        """Create a SupabaseService instance with mocked client."""
        with patch('src.services.supabase_client.create_client', return_value=mock_supabase_client):
            service = SupabaseService()
            service.client = mock_supabase_client
            return service
    
    def test_create_conversation(self, supabase_service, mock_supabase_client):
        """Test creating a new conversation."""
        # Mock user exists
        mock_supabase_client.execute.side_effect = [
            MagicMock(data=[{"id": "user-123", "slack_user_id": "U123456"}]),  # get_or_create_user
            MagicMock(data=[{"id": "conv-123"}])  # create_conversation
        ]
        
        conversation_data = {
            "slack_channel_id": "C123456",
            "user_id": "U123456",
            "context_type": "public",
            "status": "active"
        }
        
        result = supabase_service.create_conversation(conversation_data)
        
        assert result["id"] == "conv-123"
        assert mock_supabase_client.insert.called
    
    def test_get_or_create_conversation_existing(self, supabase_service, mock_supabase_client):
        """Test getting existing conversation."""
        # Mock user and conversation exist
        mock_supabase_client.execute.side_effect = [
            MagicMock(data=[{"id": "user-123"}]),  # get_or_create_user
            MagicMock(data=[{"id": "conv-123", "status": "active"}])  # existing conversation
        ]
        
        result = supabase_service.get_or_create_conversation(
            channel_id="C123456",
            user_id="U123456",
            context_type="public"
        )
        
        assert result["id"] == "conv-123"
        assert result["status"] == "active"
    
    def test_get_or_create_conversation_new(self, supabase_service, mock_supabase_client):
        """Test creating new conversation when none exists."""
        # Mock user exists but no conversation
        mock_supabase_client.execute.side_effect = [
            MagicMock(data=[{"id": "user-123"}]),  # get_or_create_user
            MagicMock(data=[]),  # no existing conversation
            MagicMock(data=[{"id": "user-123"}]),  # get_or_create_user again
            MagicMock(data=[{"id": "conv-new"}])  # create new conversation
        ]
        
        result = supabase_service.get_or_create_conversation(
            channel_id="C123456",
            user_id="U123456",
            context_type="private"
        )
        
        assert result["id"] == "conv-new"
    
    def test_log_message(self, supabase_service, mock_supabase_client):
        """Test logging a message."""
        mock_supabase_client.execute.return_value = MagicMock(
            data=[{"id": "msg-123", "content": "Test message"}]
        )
        
        message_data = {
            "conversation_id": "conv-123",
            "sender_type": "user",
            "sender_id": "U123456",
            "content": "Test message",
            "slack_message_ts": "1234567890.123456",
            "metadata": {"test": True}
        }
        
        result = supabase_service.log_message(message_data)
        
        assert result["id"] == "msg-123"
        assert result["content"] == "Test message"
        assert mock_supabase_client.insert.called
    
    def test_log_message_with_intent(self, supabase_service, mock_supabase_client):
        """Test logging a message with detected intent."""
        mock_supabase_client.execute.return_value = MagicMock(
            data=[{"id": "msg-123", "intent_detected": "task_request"}]
        )
        
        message_data = {
            "conversation_id": "conv-123",
            "sender_type": "dona",
            "sender_id": "dona",
            "content": "I'll help you create a task",
            "intent_detected": "task_request"
        }
        
        result = supabase_service.log_message(message_data)
        
        assert result["intent_detected"] == "task_request"
    
    def test_log_activity(self, supabase_service, mock_supabase_client):
        """Test logging an activity."""
        # Mock user exists
        mock_supabase_client.execute.side_effect = [
            MagicMock(data=[{"id": "user-123"}]),  # get_or_create_user
            MagicMock(data=[{"id": "activity-123"}])  # create activity
        ]
        
        activity_data = {
            "slack_user_id": "U123456",
            "activity_type": "slash_command",
            "entity_type": "command",
            "metadata": {"command": "/dona"}
        }
        
        result = supabase_service.log_activity(activity_data)
        
        assert result["id"] == "activity-123"
        assert mock_supabase_client.insert.call_count == 1
    
    def test_log_activity_with_user_id(self, supabase_service, mock_supabase_client):
        """Test logging activity with direct user_id."""
        mock_supabase_client.execute.return_value = MagicMock(
            data=[{"id": "activity-123"}]
        )
        
        activity_data = {
            "user_id": "user-123",
            "activity_type": "task_created",
            "entity_type": "task",
            "entity_id": "task-456"
        }
        
        result = supabase_service.log_activity(activity_data)
        
        assert result["id"] == "activity-123"
        # Should only call table once for activity_logs insert
        assert mock_supabase_client.table.call_count == 1
    
    def test_conversation_with_thread(self, supabase_service, mock_supabase_client):
        """Test conversation with thread timestamp."""
        mock_supabase_client.execute.side_effect = [
            MagicMock(data=[{"id": "user-123"}]),  # get_or_create_user
            MagicMock(data=[]),  # no existing conversation
            MagicMock(data=[{"id": "user-123"}]),  # get_or_create_user for create
            MagicMock(data=[{"id": "conv-thread"}])  # create conversation
        ]
        
        result = supabase_service.get_or_create_conversation(
            channel_id="C123456",
            user_id="U123456",
            context_type="public",
            thread_ts="1234567890.123456"
        )
        
        assert result["id"] == "conv-thread"
        # Verify thread_ts was included in query
        eq_calls = mock_supabase_client.eq.call_args_list
        thread_call = any(
            call[0] == ("slack_thread_ts", "1234567890.123456") 
            for call in eq_calls
        )
        assert thread_call