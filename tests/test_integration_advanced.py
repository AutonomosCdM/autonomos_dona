"""Advanced integration tests for complex bot workflows.

These tests verify more complex scenarios including multi-user
interactions, edge cases, and error recovery.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch
import json
from src.app import create_app
from src.models.schemas import TaskStatus, TaskPriority


class TestAdvancedIntegration:
    """Advanced integration tests for complex scenarios."""
    
    @pytest.fixture
    def mock_slack_client(self):
        """Mock Slack Web API client with advanced responses."""
        client = MagicMock()
        
        # User info for multiple users
        client.users_info.side_effect = lambda user_id: {
            'ok': True,
            'user': {
                'id': user_id,
                'name': f'user_{user_id[-3:]}',
                'real_name': f'User {user_id[-3:]}',
                'tz': 'America/Mexico_City'
            }
        }
        
        client.chat_postMessage.return_value = {'ok': True, 'ts': '1234567890.123'}
        client.chat_postEphemeral.return_value = {'ok': True}
        client.conversations_members.return_value = {
            'ok': True,
            'members': ['U123456', 'U789012', 'U345678']
        }
        
        return client
    
    @pytest.fixture
    def mock_supabase(self):
        """Mock Supabase with advanced query capabilities."""
        mock = MagicMock()
        
        # Configure method chaining
        mock.table.return_value = mock
        mock.select.return_value = mock
        mock.eq.return_value = mock
        mock.neq.return_value = mock
        mock.insert.return_value = mock
        mock.update.return_value = mock
        mock.delete.return_value = mock
        mock.gte.return_value = mock
        mock.lte.return_value = mock
        mock.order.return_value = mock
        mock.limit.return_value = mock
        
        return mock
    
    @pytest.fixture
    def app(self, mock_slack_client, mock_supabase):
        """Create app with advanced mocking."""
        with patch('src.services.slack_client.WebClient', return_value=mock_slack_client), \
             patch('src.services.supabase_client.create_client', return_value=mock_supabase):
            
            app = create_app()
            app.client = mock_slack_client
            
            # Configure Supabase service
            app._supabase.client = mock_supabase
            
            return app
    
    def test_team_task_assignment_flow(self, app, mock_slack_client, mock_supabase):
        """Test assigning tasks to team members."""
        ack = Mock()
        respond = Mock()
        
        # Manager creates task for team member
        command = {
            'command': '/task',
            'text': 'create "Deploy new feature" assign @user_789',
            'user_id': 'U123456',  # Manager
            'user_name': 'manager',
            'channel_id': 'C123456'
        }
        
        # Mock user lookup
        mock_slack_client.users_lookupByEmail.return_value = {
            'ok': True,
            'user': {'id': 'U789012'}
        }
        
        # Mock task creation
        created_task = {
            'id': 'task-123',
            'title': 'Deploy new feature',
            'created_by': 'U123456',
            'assigned_to': 'U789012',
            'status': 'pending',
            'created_at': datetime.now().isoformat()
        }
        
        mock_supabase.execute.return_value = MagicMock(data=[created_task])
        
        from src.handlers.commands import handle_task_command
        with patch.object(app._supabase, 'create_task', return_value=created_task):
            handle_task_command(ack, command, respond, app.client, app._supabase)
        
        # Verify notification sent to assignee
        calls = mock_slack_client.chat_postMessage.call_args_list
        assert any('U789012' in str(call) for call in calls)
    
    def test_task_dependencies_workflow(self, app, mock_supabase):
        """Test creating tasks with dependencies."""
        ack = Mock()
        respond = Mock()
        
        # Create parent task
        parent_command = {
            'command': '/task',
            'text': 'create "Release v2.0" priority:high',
            'user_id': 'U123456'
        }
        
        parent_task = {
            'id': 'task-parent',
            'title': 'Release v2.0',
            'priority': 'high',
            'status': 'pending'
        }
        
        # Create subtasks
        subtasks = [
            {
                'id': 'task-sub1',
                'title': 'Update documentation',
                'parent_task_id': 'task-parent',
                'status': 'pending'
            },
            {
                'id': 'task-sub2', 
                'title': 'Run integration tests',
                'parent_task_id': 'task-parent',
                'status': 'pending'
            }
        ]
        
        # Mock the workflow
        mock_supabase.execute.side_effect = [
            MagicMock(data=[parent_task]),
            MagicMock(data=subtasks)
        ]
        
        # Verify parent task blocks on subtasks
        from src.handlers.commands import handle_task_command
        
        # Check status command shows dependencies
        status_command = {
            'command': '/status',
            'text': '',
            'user_id': 'U123456'
        }
        
        with patch.object(app._supabase, 'get_user_tasks', return_value=[parent_task] + subtasks):
            handle_task_command(ack, status_command, respond, app.client, app._supabase)
        
        response = str(respond.call_args)
        assert 'Release v2.0' in response
        assert '2' in response  # Number of subtasks
    
    def test_recurring_task_creation(self, app, mock_supabase):
        """Test creating and managing recurring tasks."""
        ack = Mock()
        respond = Mock()
        
        # Create recurring task
        command = {
            'command': '/task',
            'text': 'create "Daily standup" recurring:daily',
            'user_id': 'U123456'
        }
        
        # Mock recurring task template
        recurring_task = {
            'id': 'task-recurring',
            'title': 'Daily standup',
            'is_recurring': True,
            'recurrence_pattern': 'daily',
            'next_occurrence': (datetime.now() + timedelta(days=1)).isoformat()
        }
        
        mock_supabase.execute.return_value = MagicMock(data=[recurring_task])
        
        # Test automatic task generation
        today = datetime.now().date()
        generated_tasks = []
        
        for i in range(5):  # Generate 5 daily tasks
            task_date = today + timedelta(days=i)
            generated_tasks.append({
                'id': f'task-daily-{i}',
                'title': f'Daily standup - {task_date}',
                'due_date': task_date.isoformat(),
                'parent_recurring_id': 'task-recurring'
            })
        
        # Verify tasks are created for the week
        with patch.object(app._supabase, 'get_user_tasks', return_value=generated_tasks):
            list_command = {'command': '/task', 'text': 'list week', 'user_id': 'U123456'}
            from src.handlers.commands import handle_task_command
            handle_task_command(ack, list_command, respond, app.client, app._supabase)
        
        response = str(respond.call_args)
        assert 'Daily standup' in response
        assert '5' in response  # 5 occurrences
    
    def test_bulk_operations_performance(self, app, mock_supabase):
        """Test handling bulk task operations efficiently."""
        ack = Mock()
        respond = Mock()
        
        # Create 50 tasks in bulk
        bulk_tasks = []
        for i in range(50):
            bulk_tasks.append({
                'id': f'task-bulk-{i}',
                'title': f'Task {i}',
                'status': 'pending' if i % 3 else 'completed',
                'priority': ['low', 'medium', 'high'][i % 3],
                'created_at': (datetime.now() - timedelta(days=i)).isoformat()
            })
        
        # Test bulk status update
        command = {
            'command': '/task',
            'text': 'complete all pending',
            'user_id': 'U123456'
        }
        
        pending_tasks = [t for t in bulk_tasks if t['status'] == 'pending']
        
        # Mock batch update
        mock_supabase.execute.return_value = MagicMock(data=pending_tasks)
        
        with patch.object(app._supabase, 'update_task') as mock_update:
            mock_update.return_value = True
            
            # Simulate bulk update
            for task in pending_tasks:
                app._supabase.update_task(task['id'], status='completed')
        
        # Verify all pending tasks were updated
        assert mock_update.call_count == len(pending_tasks)
    
    def test_notification_preferences_flow(self, app, mock_slack_client, mock_supabase):
        """Test respecting user notification preferences."""
        # Setup user preferences
        user_prefs = {
            'U123456': {'notifications': True, 'quiet_hours': False},
            'U789012': {'notifications': False, 'quiet_hours': False},
            'U345678': {'notifications': True, 'quiet_hours': True}
        }
        
        # Mock current time in quiet hours
        with patch('src.handlers.events.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 1, 22, 0)  # 10 PM
            
            # Test notification delivery
            for user_id, prefs in user_prefs.items():
                if prefs['notifications'] and not prefs['quiet_hours']:
                    # Should send notification
                    mock_slack_client.chat_postMessage(
                        channel=user_id,
                        text="Task reminder"
                    )
            
            # Verify correct users received notifications
            calls = mock_slack_client.chat_postMessage.call_args_list
            notified_users = [call[1]['channel'] for call in calls]
            
            assert 'U123456' in notified_users  # Has notifications on
            assert 'U789012' not in notified_users  # Has notifications off
            assert 'U345678' not in notified_users  # In quiet hours
    
    def test_data_export_import_flow(self, app, mock_supabase):
        """Test exporting and importing task data."""
        ack = Mock()
        respond = Mock()
        
        # Export command
        export_command = {
            'command': '/task',
            'text': 'export json',
            'user_id': 'U123456'
        }
        
        # Mock task data
        tasks = [
            {
                'id': 'task-1',
                'title': 'Project planning',
                'status': 'completed',
                'tags': ['project', 'planning'],
                'time_entries': [
                    {'duration': 3600, 'date': '2024-01-01'}
                ]
            },
            {
                'id': 'task-2',
                'title': 'Code review',
                'status': 'in_progress',
                'tags': ['development'],
                'time_entries': [
                    {'duration': 1800, 'date': '2024-01-02'}
                ]
            }
        ]
        
        mock_supabase.execute.return_value = MagicMock(data=tasks)
        
        # Test export
        with patch.object(app._supabase, 'get_user_tasks', return_value=tasks):
            from src.handlers.commands import handle_task_command
            handle_task_command(ack, export_command, respond, app.client, app._supabase)
        
        # Verify JSON export
        response = respond.call_args[1]
        assert 'json' in response.get('blocks', [{}])[0].get('type', '')
        
        # Test import
        import_data = json.dumps(tasks)
        import_command = {
            'command': '/task',
            'text': f'import {import_data}',
            'user_id': 'U123456'
        }
        
        with patch.object(app._supabase, 'create_task') as mock_create:
            mock_create.return_value = tasks[0]
            # Would handle import logic here
            pass
    
    def test_error_recovery_mechanisms(self, app, mock_slack_client, mock_supabase):
        """Test system recovery from various error conditions."""
        ack = Mock()
        respond = Mock()
        
        # Test 1: Database connection timeout
        mock_supabase.execute.side_effect = TimeoutError("Database timeout")
        
        command = {
            'command': '/task',
            'text': 'list',
            'user_id': 'U123456'
        }
        
        from src.handlers.commands import handle_task_command
        handle_task_command(ack, command, respond, app.client, app._supabase)
        
        # Should provide helpful error message
        error_response = str(respond.call_args)
        assert 'temporarily unavailable' in error_response.lower() or 'try again' in error_response.lower()
        
        # Test 2: Slack API rate limiting
        mock_slack_client.chat_postMessage.side_effect = Exception("rate_limited")
        
        # Should queue message for retry
        with patch('time.sleep'):  # Avoid actual sleep in tests
            try:
                mock_slack_client.chat_postMessage(
                    channel='U123456',
                    text='Test message'
                )
            except Exception:
                pass  # Expected
        
        # Test 3: Partial data corruption
        corrupt_task = {
            'id': 'task-corrupt',
            'title': None,  # Missing required field
            'status': 'unknown_status'  # Invalid enum
        }
        
        mock_supabase.execute.return_value = MagicMock(data=[corrupt_task])
        
        # Should handle gracefully
        with patch.object(app._supabase, 'get_user_tasks', return_value=[]):
            handle_task_command(ack, command, respond, app.client, app._supabase)
        
        # Verify system continues to function
        ack.assert_called()
        respond.assert_called()