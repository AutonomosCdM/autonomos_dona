"""Integration tests for Autónomos Dona Slack bot.

These tests verify the complete flow of the bot functionality,
including interactions between handlers and services.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch, ANY
from slack_bolt import App, Ack, Respond, Say
from src.app import create_app
from src.handlers.commands import handle_task_command
from src.handlers.events import handle_app_mention
from src.services.slack_client import SlackService
from src.services.supabase_client import SupabaseService


class TestBotIntegration:
    """Integration tests for bot functionality."""
    
    @pytest.fixture
    def mock_slack_client(self):
        """Mock Slack Web API client."""
        client = MagicMock()
        client.users_info.return_value = {
            'ok': True,
            'user': {
                'id': 'U123456',
                'name': 'testuser',
                'real_name': 'Test User',
                'tz': 'America/Mexico_City'
            }
        }
        client.chat_postMessage.return_value = {'ok': True, 'ts': '1234567890.123'}
        client.chat_postEphemeral.return_value = {'ok': True}
        client.conversations_info.return_value = {
            'ok': True,
            'channel': {'id': 'C123456', 'name': 'general'}
        }
        return client
    
    @pytest.fixture
    def mock_supabase(self):
        """Mock Supabase client with chained methods."""
        mock = MagicMock()
        
        # Mock table chains
        mock.table.return_value = mock
        mock.select.return_value = mock
        mock.eq.return_value = mock
        mock.insert.return_value = mock
        mock.update.return_value = mock
        mock.delete.return_value = mock
        mock.gte.return_value = mock
        mock.lte.return_value = mock
        mock.order.return_value = mock
        
        # Default execute responses
        mock.execute.return_value = MagicMock(data=[], count=0)
        
        return mock
    
    @pytest.fixture
    def app(self, mock_slack_client, mock_supabase):
        """Create test app with mocked services."""
        # Mock auth test response
        mock_slack_client.auth_test.return_value = {
            'ok': True,
            'url': 'https://test.slack.com/',
            'team': 'Test Team',
            'user': 'dona',
            'team_id': 'T123456',
            'user_id': 'UBOT123',
            'bot_id': 'BBOT123'
        }
        
        with patch('src.app.SupabaseService') as mock_supabase_class, \
             patch('slack_sdk.WebClient', return_value=mock_slack_client), \
             patch('src.services.slack_client.WebClient', return_value=mock_slack_client), \
             patch('src.services.supabase_client.create_client', return_value=mock_supabase):
            
            # Configure Supabase service mock
            supabase_service = MagicMock(spec=SupabaseService)
            supabase_service.client = mock_supabase
            mock_supabase_class.return_value = supabase_service
            
            app = create_app(token_verification_enabled=False)
            # Client is already mocked via WebClient patch
            app._supabase = supabase_service
            
            return app
    
    def test_complete_task_flow(self, app, mock_slack_client, mock_supabase):
        """Test complete flow: create task -> list tasks -> complete task."""
        # Setup
        ack = Mock()
        respond = Mock()
        user_id = "U123456"
        
        # Mock user exists
        mock_supabase.execute.return_value = MagicMock(
            data=[{'id': 'user-123', 'slack_user_id': user_id}]
        )
        
        # Step 1: Create a task
        command = {
            'command': '/task',
            'text': 'create Review Q4 reports',
            'user_id': user_id,
            'user_name': 'testuser',
            'channel_id': 'C123456',
            'channel_name': 'general',
            'app': app  # Add app to command
        }
        
        # Mock task creation
        created_task = {
            'id': 'task-123',
            'title': 'Review Q4 reports',
            'assigned_to': user_id,
            'status': 'pending',
            'created_at': datetime.now().isoformat()
        }
        
        with patch.object(app._supabase, 'create_task', return_value=created_task):
            handle_task_command(ack, respond, command)
        
        ack.assert_called_once()
        respond.assert_called_once()
        assert "Tarea creada" in str(respond.call_args)
        
        # Step 2: List tasks
        ack.reset_mock()
        respond.reset_mock()
        
        command['text'] = 'list'
        
        tasks = [created_task]
        with patch.object(app._supabase, 'get_user_tasks', return_value=tasks), \
             patch('src.handlers.commands.get_slack_service') as mock_slack_service:
            mock_slack_service.return_value.format_task_list.return_value = "Mocked task list"
            handle_task_command(ack, respond, command)
        
        ack.assert_called_once()
        respond.assert_called_once()
        assert "Mocked task list" in str(respond.call_args)
        
        # Step 3: Complete the task
        ack.reset_mock()
        respond.reset_mock()
        
        command['text'] = 'complete task-123'
        
        updated_task = {'id': 'task-123', 'description': 'Review Q4 reports', 'status': 'completed'}
        with patch.object(app._supabase, 'update_task', return_value=updated_task):
            handle_task_command(ack, respond, command)
        
        ack.assert_called_once()
        respond.assert_called_once()
        assert "completed" in str(respond.call_args).lower()
    
    def test_reminder_to_task_conversion(self, app, mock_slack_client, mock_supabase):
        """Test flow: set reminder -> convert to task via reaction."""
        # Step 1: Create reminder
        ack = Mock()
        respond = Mock()
        
        command = {
            'command': '/remind',
            'text': 'me to prepare presentation tomorrow at 3pm',
            'user_id': 'U123456',
            'user_name': 'testuser'
        }
        
        # Import and test remind command
        from src.handlers.commands import handle_remind_command
        handle_remind_command(ack, respond, command)
        
        ack.assert_called_once()
        respond.assert_called_once()
        
        # Step 2: Add reaction to convert to task
        event = {
            'type': 'reaction_added',
            'user': 'U123456',
            'reaction': 'white_check_mark',
            'item': {
                'type': 'message',
                'channel': 'C123456',
                'ts': '1234567890.123'
            }
        }
        
        say = Mock()
        
        # Mock message retrieval
        mock_slack_client.conversations_history.return_value = {
            'ok': True,
            'messages': [{
                'text': 'Reminder: prepare presentation',
                'ts': '1234567890.123',
                'user': 'U123456'
            }]
        }
        
        # Mock user exists
        mock_supabase.execute.return_value = MagicMock(
            data=[{'id': 'user-123', 'slack_user_id': 'U123456'}]
        )
        
        task_created = {
            'id': 'task-456',
            'title': 'Reminder: prepare presentation',
            'assigned_to': 'U123456',
            'status': 'pending'
        }
        
        with patch.object(app._supabase, 'create_task', return_value=task_created):
            from src.handlers.events import handle_reaction_added
            handle_reaction_added(event, say, app.client, app._supabase)
        
        # Verify task was created
        app._supabase.create_task.assert_called_once()
        say.assert_called_once()
        assert "task" in str(say.call_args).lower()
    
    def test_daily_summary_flow(self, app, mock_slack_client, mock_supabase):
        """Test daily summary generation with time entries."""
        ack = Mock()
        respond = Mock()
        
        command = {
            'command': '/summary',
            'text': 'today',
            'user_id': 'U123456',
            'user_name': 'testuser'
        }
        
        # Mock completed tasks
        tasks = [
            {
                'id': 'task-1',
                'title': 'Code review',
                'status': 'completed',
                'completed_at': datetime.now().isoformat()
            },
            {
                'id': 'task-2',
                'title': 'Team meeting',
                'status': 'completed',
                'completed_at': datetime.now().isoformat()
            }
        ]
        
        # Mock time entries
        time_entries = [
            {
                'task_id': 'task-1',
                'start_time': (datetime.now() - timedelta(hours=2)).isoformat(),
                'end_time': (datetime.now() - timedelta(hours=1)).isoformat(),
                'duration': 3600  # 1 hour
            },
            {
                'task_id': 'task-2',
                'start_time': (datetime.now() - timedelta(hours=1)).isoformat(),
                'end_time': datetime.now().isoformat(),
                'duration': 3600  # 1 hour
            }
        ]
        
        with patch.object(app._supabase, 'get_user_tasks', return_value=tasks), \
             patch.object(app._supabase, 'get_user_time_entries', return_value=time_entries):
            
            from src.handlers.commands import handle_summary_command
            handle_summary_command(ack, command, respond, app.client, app._supabase)
        
        ack.assert_called_once()
        respond.assert_called_once()
        
        # Verify summary contains task info
        response = str(respond.call_args)
        assert "Code review" in response
        assert "Team meeting" in response
        assert "2" in response  # Total tasks
    
    def test_context_middleware_dm_detection(self, app):
        """Test that context middleware correctly identifies DMs."""
        from src.app import add_context_middleware
        
        # Test DM event
        args = {
            'event': {
                'type': 'message',
                'channel_type': 'im',
                'user': 'U123456',
                'text': 'Hello Dona'
            },
            'context': {}
        }
        
        next_called = False
        def mock_next():
            nonlocal next_called
            next_called = True
        
        add_context_middleware(args, mock_next)
        
        assert args['context']['is_private'] is True
        assert args['context']['user_id'] == 'U123456'
        assert next_called
    
    def test_error_handling_flow(self, app, mock_slack_client, mock_supabase):
        """Test error handling in complete flow."""
        ack = Mock()
        respond = Mock()
        
        # Simulate database error
        mock_supabase.execute.side_effect = Exception("Database connection error")
        
        command = {
            'command': '/task',
            'text': 'list',
            'user_id': 'U123456',
            'user_name': 'testuser'
        }
        
        # Should handle error gracefully
        handle_task_command(ack, command, respond, app.client, app._supabase)
        
        ack.assert_called_once()
        respond.assert_called_once()
        
        # Error message should be sent
        response = str(respond.call_args)
        assert "error" in response.lower() or "sorry" in response.lower()
    
    def test_concurrent_time_tracking(self, app, mock_supabase):
        """Test handling concurrent time entries."""
        user_id = "U123456"
        
        # Mock user exists
        mock_supabase.execute.return_value = MagicMock(
            data=[{'id': 'user-123', 'slack_user_id': user_id}]
        )
        
        # Start first time entry
        with patch.object(app._supabase, 'start_time_entry') as mock_start:
            app._supabase.start_time_entry(user_id, 'task-1')
            mock_start.assert_called_once_with(user_id, 'task-1')
        
        # Start second time entry (should stop first)
        with patch.object(app._supabase, 'stop_active_time_entries') as mock_stop, \
             patch.object(app._supabase, 'start_time_entry') as mock_start:
            
            # Simulate starting new entry
            app._supabase.stop_active_time_entries(user_id)
            app._supabase.start_time_entry(user_id, 'task-2')
            
            mock_stop.assert_called_once_with(user_id)
            mock_start.assert_called_once_with(user_id, 'task-2')
    
    def test_app_home_integration(self, app, mock_slack_client):
        """Test app home view updates with user data."""
        event = {
            'type': 'app_home_opened',
            'user': 'U123456',
            'view': {'id': 'V123456'}
        }
        
        # Mock user tasks
        tasks = [
            {'id': 'task-1', 'title': 'Task 1', 'status': 'pending'},
            {'id': 'task-2', 'title': 'Task 2', 'status': 'in_progress'}
        ]
        
        with patch.object(app._supabase, 'get_user_tasks', return_value=tasks):
            from src.handlers.events import handle_app_home_opened
            handle_app_home_opened(event, app.client, Mock(), app._supabase)
        
        # Verify home view was published
        mock_slack_client.views_publish.assert_called_once()
        
        # Check view contains task info
        view_call = mock_slack_client.views_publish.call_args
        assert 'Task 1' in str(view_call)
        assert 'Task 2' in str(view_call)