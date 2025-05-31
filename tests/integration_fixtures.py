"""Shared fixtures and utilities for integration tests."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock
import random
import string


class MockDataGenerator:
    """Generate realistic mock data for tests."""
    
    @staticmethod
    def generate_user(user_id=None):
        """Generate mock user data."""
        if not user_id:
            user_id = f"U{''.join(random.choices(string.digits, k=6))}"
        
        return {
            'id': user_id,
            'slack_user_id': user_id,
            'email': f'user_{user_id[-3:]}@example.com',
            'name': f'User {user_id[-3:]}',
            'created_at': datetime.now().isoformat(),
            'preferences': {
                'notifications': True,
                'timezone': 'America/Mexico_City',
                'language': 'es'
            }
        }
    
    @staticmethod
    def generate_task(task_id=None, user_id='U123456', **kwargs):
        """Generate mock task data."""
        if not task_id:
            task_id = f"task-{''.join(random.choices(string.ascii_lowercase + string.digits, k=8))}"
        
        base_task = {
            'id': task_id,
            'title': f'Task {task_id[-4:]}',
            'description': 'Generated test task',
            'assigned_to': user_id,
            'created_by': user_id,
            'status': 'pending',
            'priority': 'medium',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'due_date': (datetime.now() + timedelta(days=7)).isoformat(),
            'tags': ['test'],
            'estimated_hours': 2.0
        }
        
        base_task.update(kwargs)
        return base_task
    
    @staticmethod
    def generate_time_entry(entry_id=None, task_id='task-123', user_id='U123456', **kwargs):
        """Generate mock time entry data."""
        if not entry_id:
            entry_id = f"time-{''.join(random.choices(string.digits, k=8))}"
        
        start = datetime.now() - timedelta(hours=2)
        end = datetime.now() - timedelta(hours=1)
        
        base_entry = {
            'id': entry_id,
            'task_id': task_id,
            'user_id': user_id,
            'start_time': start.isoformat(),
            'end_time': end.isoformat(),
            'duration': 3600,  # 1 hour in seconds
            'description': 'Working on task',
            'created_at': datetime.now().isoformat()
        }
        
        base_entry.update(kwargs)
        return base_entry


class SlackMockFactory:
    """Factory for creating Slack API mocks."""
    
    @staticmethod
    def create_message(text, user_id='U123456', channel_id='C123456', **kwargs):
        """Create mock Slack message."""
        base_message = {
            'type': 'message',
            'text': text,
            'user': user_id,
            'channel': channel_id,
            'ts': f"{datetime.now().timestamp():.6f}",
            'team': 'T123456'
        }
        
        base_message.update(kwargs)
        return base_message
    
    @staticmethod
    def create_slash_command(command, text='', user_id='U123456', **kwargs):
        """Create mock slash command."""
        base_command = {
            'command': command,
            'text': text,
            'user_id': user_id,
            'user_name': f'user_{user_id[-3:]}',
            'channel_id': kwargs.get('channel_id', 'C123456'),
            'channel_name': kwargs.get('channel_name', 'general'),
            'team_id': 'T123456',
            'team_domain': 'test-team',
            'response_url': 'https://hooks.slack.com/commands/test',
            'trigger_id': f"trigger_{''.join(random.choices(string.digits, k=12))}"
        }
        
        base_command.update(kwargs)
        return base_command
    
    @staticmethod
    def create_block_action(action_id, value, user_id='U123456', **kwargs):
        """Create mock block action."""
        return {
            'type': 'block_actions',
            'user': {'id': user_id, 'name': f'user_{user_id[-3:]}'},
            'actions': [{
                'action_id': action_id,
                'value': value,
                'type': kwargs.get('action_type', 'button'),
                'action_ts': f"{datetime.now().timestamp():.6f}"
            }],
            'channel': {'id': 'C123456', 'name': 'general'},
            'trigger_id': f"trigger_{''.join(random.choices(string.digits, k=12))}"
        }


@pytest.fixture
def mock_data_generator():
    """Provide mock data generator."""
    return MockDataGenerator()


@pytest.fixture
def slack_mock_factory():
    """Provide Slack mock factory."""
    return SlackMockFactory()


@pytest.fixture
def populated_database(mock_supabase, mock_data_generator):
    """Create a populated mock database."""
    # Create users
    users = [
        mock_data_generator.generate_user('U123456'),
        mock_data_generator.generate_user('U789012'),
        mock_data_generator.generate_user('U345678')
    ]
    
    # Create tasks
    tasks = []
    for i, user in enumerate(users):
        for j in range(5):  # 5 tasks per user
            task = mock_data_generator.generate_task(
                task_id=f'task-{i}-{j}',
                user_id=user['slack_user_id'],
                status=['pending', 'in_progress', 'completed'][j % 3],
                priority=['low', 'medium', 'high'][j % 3]
            )
            tasks.append(task)
    
    # Create time entries
    time_entries = []
    for task in tasks[:10]:  # First 10 tasks have time entries
        entry = mock_data_generator.generate_time_entry(
            task_id=task['id'],
            user_id=task['assigned_to']
        )
        time_entries.append(entry)
    
    # Configure mock responses
    def mock_table_response(table_name):
        if table_name == 'users':
            return create_mock_query(users)
        elif table_name == 'tasks':
            return create_mock_query(tasks)
        elif table_name == 'time_entries':
            return create_mock_query(time_entries)
        return create_mock_query([])
    
    mock_supabase.table.side_effect = mock_table_response
    
    return {
        'users': users,
        'tasks': tasks,
        'time_entries': time_entries
    }


def create_mock_query(data):
    """Create a mock query object with chainable methods."""
    mock = MagicMock()
    mock.data = data
    
    # Make all methods return self for chaining
    mock.select.return_value = mock
    mock.insert.return_value = mock
    mock.update.return_value = mock
    mock.delete.return_value = mock
    mock.eq.return_value = mock
    mock.neq.return_value = mock
    mock.gte.return_value = mock
    mock.lte.return_value = mock
    mock.order.return_value = mock
    mock.limit.return_value = mock
    
    # Execute returns the data
    mock.execute.return_value = MagicMock(data=data)
    
    return mock


@pytest.fixture
def mock_slack_workspace():
    """Create a complete mock Slack workspace."""
    workspace = {
        'team': {
            'id': 'T123456',
            'name': 'Test Team',
            'domain': 'test-team'
        },
        'channels': [
            {'id': 'C123456', 'name': 'general', 'is_member': True},
            {'id': 'C789012', 'name': 'random', 'is_member': True},
            {'id': 'C345678', 'name': 'dev-team', 'is_member': False}
        ],
        'users': [
            {
                'id': 'U123456',
                'name': 'testuser',
                'real_name': 'Test User',
                'is_admin': True,
                'is_bot': False
            },
            {
                'id': 'U789012',
                'name': 'devuser',
                'real_name': 'Dev User',
                'is_admin': False,
                'is_bot': False
            },
            {
                'id': 'UBOT123',
                'name': 'dona',
                'real_name': 'Dona Bot',
                'is_admin': False,
                'is_bot': True
            }
        ]
    }
    
    return workspace