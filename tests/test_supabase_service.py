"""Tests for Supabase service functionality."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timedelta

from src.services.supabase_client import SupabaseService, get_supabase_service


class TestSupabaseService:
    """Test SupabaseService class methods."""
    
    @pytest.fixture
    def mock_client(self):
        """Create a mock Supabase client."""
        client = MagicMock()
        # Create a mock table object that supports method chaining
        table_mock = MagicMock()
        
        # Make all methods return the table_mock for chaining
        table_mock.select.return_value = table_mock
        table_mock.insert.return_value = table_mock
        table_mock.update.return_value = table_mock
        table_mock.eq.return_value = table_mock
        table_mock.gte.return_value = table_mock
        table_mock.lte.return_value = table_mock
        table_mock.order.return_value = table_mock
        
        # Make table() return our mock
        client.table.return_value = table_mock
        
        return client
    
    @pytest.fixture
    def supabase_service(self, mock_client):
        """Create SupabaseService instance with mocked client."""
        with patch('src.services.supabase_client.create_client', return_value=mock_client):
            service = SupabaseService()
            return service
    
    def test_get_or_create_user_existing(self, supabase_service, mock_client):
        """Test getting existing user."""
        # Mock existing user
        existing_user = {
            "id": 1,
            "slack_user_id": "U123456",
            "slack_workspace_id": "W123456",
            "created_at": "2024-01-01T00:00:00"
        }
        # Access the table mock
        table_mock = mock_client.table.return_value
        table_mock.execute.return_value.data = [existing_user]
        
        result = supabase_service.get_or_create_user("U123456", "W123456")
        
        assert result == existing_user
        mock_client.table.assert_called_with("users")
        table_mock.select.assert_called_with("*")
        table_mock.eq.assert_any_call("slack_user_id", "U123456")
        table_mock.eq.assert_any_call("slack_workspace_id", "W123456")
    
    def test_get_or_create_user_new(self, supabase_service, mock_client):
        """Test creating new user when not exists."""
        # Access the table mock
        table_mock = mock_client.table.return_value
        # First query returns empty (user doesn't exist)
        table_mock.execute.side_effect = [
            MagicMock(data=[]),  # First select returns empty
            MagicMock(data=[{    # Insert returns new user
                "id": 2,
                "slack_user_id": "U789012",
                "slack_workspace_id": "W123456",
                "created_at": "2024-01-15T10:30:00"
            }])
        ]
        
        result = supabase_service.get_or_create_user("U789012", "W123456")
        
        assert result["slack_user_id"] == "U789012"
        assert result["slack_workspace_id"] == "W123456"
        table_mock.insert.assert_called_once()
        insert_data = table_mock.insert.call_args[0][0]
        assert insert_data["slack_user_id"] == "U789012"
        assert insert_data["slack_workspace_id"] == "W123456"
        assert "created_at" in insert_data
    
    def test_create_task_success(self, supabase_service, mock_client):
        """Test successful task creation."""
        task_data = {
            "assigned_to": "U123456",
            "created_by": "U123456",
            "description": "Test task",
            "priority": "high",
            "channel_id": "C123456"
        }
        
        created_task = {
            "id": 1,
            "assigned_to": "U123456",
            "created_by": "U123456",
            "description": "Test task",
            "status": "pending",
            "priority": "high",
            "channel_id": "C123456",
            "created_at": "2024-01-15T10:30:00"
        }
        table_mock = mock_client.table.return_value
        table_mock.execute.return_value.data = [created_task]
        
        result = supabase_service.create_task(task_data)
        
        assert result == created_task
        mock_client.table.assert_called_with("tasks")
        table_mock.insert.assert_called_once()
        insert_data = table_mock.insert.call_args[0][0]
        assert insert_data["description"] == "Test task"
        assert insert_data["status"] == "pending"
        assert insert_data["priority"] == "high"
    
    def test_create_task_with_defaults(self, supabase_service, mock_client):
        """Test task creation with default values."""
        task_data = {
            "assigned_to": "U123456",
            "description": "Simple task"
        }
        
        table_mock = mock_client.table.return_value
        table_mock.execute.return_value.data = [{"id": 2}]
        
        supabase_service.create_task(task_data)
        
        insert_data = table_mock.insert.call_args[0][0]
        assert insert_data["status"] == "pending"
        assert insert_data["priority"] == "medium"
    
    def test_get_user_tasks_all(self, supabase_service, mock_client):
        """Test getting all tasks for a user."""
        tasks = [
            {"id": 1, "description": "Task 1", "status": "pending"},
            {"id": 2, "description": "Task 2", "status": "completed"},
            {"id": 3, "description": "Task 3", "status": "in_progress"}
        ]
        table_mock = mock_client.table.return_value
        table_mock.execute.return_value.data = tasks
        
        result = supabase_service.get_user_tasks("U123456")
        
        assert result == tasks
        mock_client.table.assert_called_with("tasks")
        table_mock.eq.assert_called_with("assigned_to", "U123456")
        table_mock.order.assert_called_with("created_at", desc=True)
    
    def test_get_user_tasks_filtered(self, supabase_service, mock_client):
        """Test getting filtered tasks for a user."""
        pending_tasks = [
            {"id": 1, "description": "Task 1", "status": "pending"},
            {"id": 4, "description": "Task 4", "status": "pending"}
        ]
        table_mock = mock_client.table.return_value
        table_mock.execute.return_value.data = pending_tasks
        
        result = supabase_service.get_user_tasks("U123456", status="pending")
        
        assert result == pending_tasks
        # Check both eq calls were made
        assert table_mock.eq.call_count == 2
        table_mock.eq.assert_any_call("assigned_to", "U123456")
        table_mock.eq.assert_any_call("status", "pending")
    
    def test_update_task_success(self, supabase_service, mock_client):
        """Test successful task update."""
        updates = {
            "status": "completed",
            "description": "Updated task"
        }
        
        updated_task = {
            "id": 1,
            "status": "completed",
            "description": "Updated task",
            "updated_at": "2024-01-15T12:00:00"
        }
        table_mock = mock_client.table.return_value
        table_mock.execute.return_value.data = [updated_task]
        
        result = supabase_service.update_task(1, updates)
        
        assert result == updated_task
        mock_client.table.assert_called_with("tasks")
        table_mock.update.assert_called_once()
        update_data = table_mock.update.call_args[0][0]
        assert update_data["status"] == "completed"
        assert update_data["description"] == "Updated task"
        assert "updated_at" in update_data
        table_mock.eq.assert_called_with("id", 1)
    
    def test_start_time_entry_success(self, supabase_service, mock_client):
        """Test starting a time entry."""
        table_mock = mock_client.table.return_value
        # Mock stopping active entries
        table_mock.execute.side_effect = [
            MagicMock(data=[]),  # No active entries
            MagicMock(data=[{    # New time entry
                "id": 1,
                "user_id": 123,
                "task_id": 456,
                "start_time": "2024-01-15T10:00:00",
                "is_active": True
            }])
        ]
        
        result = supabase_service.start_time_entry(123, task_id=456)
        
        assert result["user_id"] == 123
        assert result["task_id"] == 456
        assert result["is_active"] is True
        
        # Check insert was called
        table_mock.insert.assert_called_once()
        insert_data = table_mock.insert.call_args[0][0]
        assert insert_data["user_id"] == 123
        assert insert_data["task_id"] == 456
        assert insert_data["is_active"] is True
        assert "start_time" in insert_data
    
    def test_stop_active_time_entries(self, supabase_service, mock_client):
        """Test stopping active time entries."""
        active_entries = [
            {"id": 1, "user_id": 123, "is_active": True},
            {"id": 2, "user_id": 123, "is_active": True}
        ]
        
        stopped_entries = [
            {"id": 1, "user_id": 123, "is_active": False, "end_time": "2024-01-15T12:00:00"},
            {"id": 2, "user_id": 123, "is_active": False, "end_time": "2024-01-15T12:00:00"}
        ]
        
        table_mock = mock_client.table.return_value
        # Mock responses: first for select, then for each update
        table_mock.execute.side_effect = [
            MagicMock(data=active_entries),
            MagicMock(data=[stopped_entries[0]]),
            MagicMock(data=[stopped_entries[1]])
        ]
        
        result = supabase_service.stop_active_time_entries(123)
        
        assert len(result) == 2
        assert all(entry["is_active"] is False for entry in result)
        assert all("end_time" in entry for entry in result)
        
        # Check update was called for each entry
        assert table_mock.update.call_count == 2
    
    def test_stop_active_time_entries_none_active(self, supabase_service, mock_client):
        """Test stopping time entries when none are active."""
        table_mock = mock_client.table.return_value
        table_mock.execute.return_value.data = []
        
        result = supabase_service.stop_active_time_entries(123)
        
        assert result == []
        table_mock.update.assert_not_called()
    
    def test_get_user_time_entries_no_filters(self, supabase_service, mock_client):
        """Test getting time entries without date filters."""
        entries = [
            {"id": 1, "user_id": 123, "start_time": "2024-01-15T10:00:00"},
            {"id": 2, "user_id": 123, "start_time": "2024-01-14T09:00:00"}
        ]
        table_mock = mock_client.table.return_value
        table_mock.execute.return_value.data = entries
        
        result = supabase_service.get_user_time_entries(123)
        
        assert result == entries
        table_mock.eq.assert_called_with("user_id", 123)
        table_mock.order.assert_called_with("start_time", desc=True)
        # Date filters should not be called
        table_mock.gte.assert_not_called()
        table_mock.lte.assert_not_called()
    
    def test_get_user_time_entries_with_dates(self, supabase_service, mock_client):
        """Test getting time entries with date filters."""
        start_date = datetime(2024, 1, 10)
        end_date = datetime(2024, 1, 15)
        
        entries = [
            {"id": 3, "user_id": 123, "start_time": "2024-01-12T10:00:00"}
        ]
        table_mock = mock_client.table.return_value
        table_mock.execute.return_value.data = entries
        
        result = supabase_service.get_user_time_entries(123, start_date, end_date)
        
        assert result == entries
        table_mock.gte.assert_called_with("start_time", start_date.isoformat())
        table_mock.lte.assert_called_with("start_time", end_date.isoformat())
    
    @patch('src.services.supabase_client._supabase_service', None)
    @patch('src.services.supabase_client.SupabaseService')
    def test_get_supabase_service_singleton(self, mock_supabase_service_class):
        """Test that get_supabase_service returns singleton instance."""
        mock_instance = MagicMock()
        mock_supabase_service_class.return_value = mock_instance
        
        # First call creates instance
        service1 = get_supabase_service()
        assert service1 == mock_instance
        mock_supabase_service_class.assert_called_once()
        
        # Second call returns same instance
        mock_supabase_service_class.reset_mock()
        service2 = get_supabase_service()
        assert service2 == service1
        mock_supabase_service_class.assert_not_called()
    
    def test_error_handling(self, supabase_service, mock_client):
        """Test error handling in various methods."""
        # Mock an exception on the table mock
        table_mock = mock_client.table.return_value
        table_mock.execute.side_effect = Exception("Database error")
        
        # Test various methods that should raise exceptions
        with pytest.raises(Exception, match="Database error"):
            supabase_service.get_or_create_user("U123", "W123")
        
        with pytest.raises(Exception, match="Database error"):
            supabase_service.create_task({"description": "test"})
        
        with pytest.raises(Exception, match="Database error"):
            supabase_service.get_user_tasks("U123")
        
        with pytest.raises(Exception, match="Database error"):
            supabase_service.update_task(1, {"status": "done"})
        
        with pytest.raises(Exception, match="Database error"):
            supabase_service.start_time_entry(123)
        
        with pytest.raises(Exception, match="Database error"):
            supabase_service.get_user_time_entries(123)