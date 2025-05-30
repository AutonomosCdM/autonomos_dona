# Services Module Documentation

## Overview

The `services` module implements the service layer pattern, providing a clean abstraction over external integrations and complex business logic. It acts as the bridge between the application's core logic and external systems like Slack and Supabase.

## Module Purpose and Responsibilities

### Core Responsibilities:
- **External API Integration**: Manage connections to Slack and Supabase APIs
- **Data Access Layer**: Abstract database operations behind service methods
- **Business Logic**: Implement complex operations that span multiple domains
- **Error Handling**: Handle API errors and provide consistent error responses
- **Connection Management**: Maintain singleton instances for efficiency

### Architecture Decisions:
1. **Service Layer Pattern**: Separates business logic from infrastructure concerns
2. **Singleton Pattern**: Single instances prevent connection overhead
3. **Dependency Injection Ready**: Services can be easily mocked for testing
4. **Type Safety**: Full type hints for better IDE support and runtime validation
5. **Async Support**: Services are designed to support async operations

## Module Structure

```
services/
├── __init__.py          # Module initialization and exports
├── slack_client.py      # Slack API integration service
├── supabase_client.py   # Supabase database service
└── README.md           # This documentation
```

## API Documentation

### slack_client.py

#### `class SlackService`
Main service class for Slack API operations.

##### Constructor
```python
def __init__(self):
    """Initialize the Slack Web API client."""
```

##### Methods

###### `get_user_info(user_id: str) -> Optional[Dict[str, Any]]`
Fetch detailed user information from Slack.

**Parameters:**
- `user_id`: Slack user ID (e.g., "U1234567890")

**Returns:**
- User information dictionary or None if error

**Example:**
```python
user_info = slack_service.get_user_info("U1234567890")
# Returns: {"id": "U1234567890", "name": "john", "real_name": "John Doe", ...}
```

###### `send_dm(user_id: str, text: str, blocks: Optional[List[Dict]] = None) -> bool`
Send a direct message to a user.

**Parameters:**
- `user_id`: Target user's Slack ID
- `text`: Plain text message (fallback for notifications)
- `blocks`: Optional Block Kit blocks for rich formatting

**Returns:**
- True if successful, False otherwise

**Example:**
```python
success = slack_service.send_dm(
    "U1234567890",
    "Task completed!",
    blocks=[{
        "type": "section",
        "text": {"type": "mrkdwn", "text": "*Task completed!* :white_check_mark:"}
    }]
)
```

###### `post_ephemeral(channel: str, user: str, text: str, blocks: Optional[List[Dict]] = None) -> bool`
Post an ephemeral message (only visible to one user).

**Parameters:**
- `channel`: Channel ID where message appears
- `user`: User ID who can see the message
- `text`: Message text
- `blocks`: Optional Block Kit blocks

**Returns:**
- True if successful, False otherwise

##### Static Methods

###### `format_task_list(tasks: List[Dict[str, Any]]) -> str`
Format a list of tasks for Slack display.

**Parameters:**
- `tasks`: List of task dictionaries

**Returns:**
- Formatted string with emoji indicators

**Example:**
```python
formatted = SlackService.format_task_list(tasks)
# Returns: "*Your Tasks:*\n1. :white_circle: *Design homepage* (#123)\n..."
```

###### `format_time_duration(seconds: int) -> str`
Format seconds into human-readable duration.

**Parameters:**
- `seconds`: Duration in seconds

**Returns:**
- Formatted string (e.g., "2h 30m")

###### `create_task_blocks(task: Dict[str, Any]) -> List[Dict[str, Any]]`
Create Block Kit blocks for displaying a task.

**Parameters:**
- `task`: Task dictionary

**Returns:**
- List of Block Kit blocks with interactive buttons

#### `get_slack_service() -> SlackService`
Get the singleton Slack service instance.

**Returns:**
- SlackService singleton instance

### supabase_client.py

#### `class SupabaseService`
Main service class for Supabase database operations.

##### Constructor
```python
def __init__(self):
    """Initialize the Supabase client."""
```

##### User Operations

###### `get_or_create_user(slack_user_id: str, slack_workspace_id: str) -> Dict[str, Any]`
Get existing user or create new one.

**Parameters:**
- `slack_user_id`: Slack user ID
- `slack_workspace_id`: Slack workspace ID

**Returns:**
- User data dictionary

**Example:**
```python
user = supabase.get_or_create_user("U123", "T456")
# Returns: {"id": 1, "slack_user_id": "U123", "slack_workspace_id": "T456", ...}
```

##### Task Operations

###### `create_task(task_data: Dict[str, Any]) -> Dict[str, Any]`
Create a new task in the database.

**Parameters:**
- `task_data`: Dictionary containing task information
  - `assigned_to`: User ID who owns the task
  - `created_by`: User ID who created the task
  - `description`: Task description
  - `status`: Task status (default: "pending")
  - `priority`: Task priority (default: "medium")
  - `channel_id`: Slack channel ID

**Returns:**
- Created task data with generated ID

**Example:**
```python
task = supabase.create_task({
    "assigned_to": "U123",
    "created_by": "U123",
    "description": "Review pull request",
    "priority": "high"
})
```

###### `get_user_tasks(user_id: str, status: Optional[str] = None) -> List[Dict[str, Any]]`
Get all tasks for a user, optionally filtered by status.

**Parameters:**
- `user_id`: Slack user ID
- `status`: Optional status filter ("pending", "completed", etc.)

**Returns:**
- List of task dictionaries ordered by creation date

###### `update_task(task_id: int, updates: Dict[str, Any]) -> Dict[str, Any]`
Update an existing task.

**Parameters:**
- `task_id`: Database task ID
- `updates`: Fields to update

**Returns:**
- Updated task data

##### Time Tracking Operations

###### `start_time_entry(user_id: int, task_id: Optional[int] = None) -> Dict[str, Any]`
Start a new time tracking entry.

**Parameters:**
- `user_id`: Database user ID
- `task_id`: Optional task to track time against

**Returns:**
- Created time entry

**Note:** This automatically stops any active time entries for the user.

###### `stop_active_time_entries(user_id: int) -> List[Dict[str, Any]]`
Stop all active time entries for a user.

**Parameters:**
- `user_id`: Database user ID

**Returns:**
- List of stopped time entries

###### `get_user_time_entries(user_id: int, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> List[Dict[str, Any]]`
Get time entries for a user within a date range.

**Parameters:**
- `user_id`: Database user ID
- `start_date`: Optional start date filter
- `end_date`: Optional end date filter

**Returns:**
- List of time entries ordered by start time

#### `get_supabase_service() -> SupabaseService`
Get the singleton Supabase service instance.

**Returns:**
- SupabaseService singleton instance

## Usage Examples

### Basic Service Usage
```python
from src.services import get_slack_service, get_supabase_service

# Get service instances
slack = get_slack_service()
supabase = get_supabase_service()

# Create a task and notify user
task = supabase.create_task({
    "assigned_to": "U123",
    "description": "Complete project documentation"
})

slack.send_dm(
    "U123",
    f"New task created: {task['description']}"
)
```

### Task Management Flow
```python
# Get or create user
user = supabase.get_or_create_user(slack_user_id, workspace_id)

# Create task
task = supabase.create_task({
    "assigned_to": slack_user_id,
    "created_by": slack_user_id,
    "description": "Review code changes",
    "priority": "high"
})

# Get all user tasks
tasks = supabase.get_user_tasks(slack_user_id)

# Format and send task list
formatted_tasks = slack.format_task_list(tasks)
slack.send_dm(slack_user_id, formatted_tasks)
```

### Time Tracking Example
```python
# Start time tracking
entry = supabase.start_time_entry(user["id"], task_id=task["id"])

# ... work happens ...

# Stop time tracking
stopped_entries = supabase.stop_active_time_entries(user["id"])

# Calculate and format duration
duration = stopped_entries[0]["duration_seconds"]
formatted = slack.format_time_duration(duration)
slack.send_dm(user_id, f"Time tracked: {formatted}")
```

### Error Handling Pattern
```python
try:
    user_info = slack.get_user_info(user_id)
    if user_info:
        # Process user info
        display_name = user_info.get("profile", {}).get("display_name")
    else:
        # Handle missing user
        logger.warning(f"User {user_id} not found")
except Exception as e:
    logger.error(f"Error fetching user info: {e}")
    # Fallback behavior
```

## Dependencies

### External Dependencies:
- `slack_sdk`: Official Slack SDK for Python
- `supabase`: Supabase Python client
- `pydantic`: Data validation and settings management

### Internal Dependencies:
- `src.utils.config`: Application configuration
- `src.models.schemas`: Data models and validation
- `src.utils.logger`: Logging utilities

## Configuration

Services require the following environment variables:

### Slack Configuration:
- `SLACK_BOT_TOKEN`: Bot user OAuth token
- `SLACK_APP_TOKEN`: App-level token for Socket Mode
- `SLACK_SIGNING_SECRET`: Request signature verification

### Supabase Configuration:
- `SUPABASE_URL`: Project URL
- `SUPABASE_KEY`: Anonymous/service key

## Best Practices

1. **Use Singleton Pattern**: Always use `get_*_service()` functions
2. **Handle Errors Gracefully**: Services should not crash the application
3. **Log Important Operations**: Track all API calls for debugging
4. **Validate Input**: Check parameters before making API calls
5. **Return Consistent Types**: Always return expected types or None
6. **Implement Retries**: Handle transient network errors
7. **Cache When Possible**: Reduce API calls for frequently accessed data

## Service Design Patterns

### Error Handling
```python
def safe_api_call(self, operation):
    try:
        result = operation()
        return result
    except SpecificAPIError as e:
        logger.error(f"API error: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise
```

### Retry Logic
```python
def with_retry(self, operation, max_attempts=3):
    for attempt in range(max_attempts):
        try:
            return operation()
        except TransientError:
            if attempt == max_attempts - 1:
                raise
            time.sleep(2 ** attempt)  # Exponential backoff
```

### Caching Pattern
```python
class CachedService:
    def __init__(self):
        self._cache = {}
        self._cache_ttl = 300  # 5 minutes
    
    def get_cached_or_fetch(self, key, fetcher):
        if key in self._cache:
            data, timestamp = self._cache[key]
            if time.time() - timestamp < self._cache_ttl:
                return data
        
        data = fetcher()
        self._cache[key] = (data, time.time())
        return data
```

## Future Improvements

1. **Async Operations**: Full async/await support for better performance
2. **Connection Pooling**: Reuse database connections efficiently
3. **Circuit Breaker**: Prevent cascading failures
4. **Metrics Collection**: Track service performance and usage
5. **Request Batching**: Combine multiple operations for efficiency
6. **Event Sourcing**: Track all state changes for audit trail
7. **GraphQL Support**: More efficient data fetching
8. **Webhook Management**: Handle Slack events via webhooks
9. **Rate Limit Handling**: Respect and manage API rate limits
10. **Multi-tenancy**: Support multiple workspaces efficiently

## Testing Services

### Mocking Services
```python
from unittest.mock import Mock, patch

def test_task_creation():
    # Mock Supabase service
    mock_supabase = Mock()
    mock_supabase.create_task.return_value = {
        "id": 1,
        "description": "Test task"
    }
    
    # Test with mock
    with patch('src.services.get_supabase_service', return_value=mock_supabase):
        # Your test code here
        pass
```

### Integration Testing
```python
def test_slack_integration():
    # Use test workspace
    slack = SlackService()
    
    # Test with real API (in test workspace)
    result = slack.get_user_info(TEST_USER_ID)
    assert result is not None
    assert result["id"] == TEST_USER_ID
```

## Security Considerations

1. **API Key Management**: Never hardcode credentials
2. **Input Sanitization**: Validate all external input
3. **SQL Injection Prevention**: Use parameterized queries
4. **Rate Limiting**: Implement client-side rate limiting
5. **Audit Logging**: Track all data modifications
6. **Encryption**: Use TLS for all API communications
7. **Token Rotation**: Support credential rotation
8. **Principle of Least Privilege**: Minimal permissions for service accounts

## Performance Optimization

1. **Lazy Loading**: Initialize connections only when needed
2. **Connection Reuse**: Maintain persistent connections
3. **Batch Operations**: Group similar database operations
4. **Selective Fetching**: Only request needed fields
5. **Response Caching**: Cache frequently accessed data
6. **Async I/O**: Use async operations for parallel execution
7. **Query Optimization**: Use indexes and optimize queries
8. **Compression**: Enable compression for large payloads