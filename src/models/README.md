# Models Module Documentation

## Overview

The `models` module defines the data layer of the application using Pydantic models for robust data validation, serialization, and type safety. It serves as the single source of truth for data structures throughout the application.

## Module Purpose and Responsibilities

### Core Responsibilities:
- **Data Validation**: Ensure data integrity with automatic validation
- **Type Safety**: Provide strong typing for better IDE support and runtime checks
- **Serialization**: Handle conversion between Python objects and JSON/database formats
- **Schema Definition**: Define the structure of all data entities
- **Business Logic**: Encapsulate entity-specific business rules

### Architecture Decisions:
1. **Pydantic Models**: Using Pydantic for automatic validation and serialization
2. **Immutable by Default**: Encouraging immutable data structures
3. **Enum Usage**: Using enums for fixed value sets
4. **Separation of Concerns**: Different models for creation, updates, and responses
5. **Forward References**: Support for self-referential and circular dependencies

## Module Structure

```
models/
├── __init__.py          # Module initialization and exports
├── schemas.py           # Pydantic model definitions
└── README.md           # This documentation
```

## API Documentation

### schemas.py

#### Enumerations

##### `class TaskStatus(str, Enum)`
Enumeration of possible task statuses.

**Values:**
- `PENDING`: Task is waiting to be started
- `IN_PROGRESS`: Task is currently being worked on
- `COMPLETED`: Task has been finished
- `CANCELLED`: Task was cancelled

**Example:**
```python
status = TaskStatus.PENDING
print(status.value)  # "pending"
```

##### `class TaskPriority(str, Enum)`
Enumeration of task priority levels.

**Values:**
- `LOW`: Low priority
- `MEDIUM`: Medium priority (default)
- `HIGH`: High priority
- `URGENT`: Urgent, needs immediate attention

#### Core Models

##### `class User(BaseModel)`
Represents a Slack user in the system.

**Attributes:**
- `id`: Optional[int] - Database ID
- `slack_user_id`: str - Slack user identifier
- `slack_workspace_id`: str - Slack workspace identifier
- `email`: Optional[str] - User's email address
- `display_name`: Optional[str] - User's display name
- `created_at`: datetime - When user was created
- `updated_at`: Optional[datetime] - Last update timestamp

**Example:**
```python
user = User(
    slack_user_id="U1234567890",
    slack_workspace_id="T0987654321",
    email="john.doe@example.com",
    display_name="John Doe"
)
```

##### `class Task(BaseModel)`
Represents a task in the system.

**Attributes:**
- `id`: Optional[int] - Database ID
- `user_id`: int - ID of user who owns the task
- `title`: str - Task title
- `description`: Optional[str] - Detailed description
- `status`: TaskStatus - Current status
- `priority`: TaskPriority - Priority level
- `due_date`: Optional[datetime] - When task is due
- `created_at`: datetime - Creation timestamp
- `updated_at`: Optional[datetime] - Last update timestamp
- `completed_at`: Optional[datetime] - Completion timestamp

**Methods:**
- `mark_completed()`: Mark task as completed and set timestamps

**Example:**
```python
task = Task(
    user_id=1,
    title="Review pull request",
    description="Review and approve the new feature PR",
    priority=TaskPriority.HIGH,
    due_date=datetime.now() + timedelta(days=1)
)

# Mark as completed
task.mark_completed()
assert task.status == TaskStatus.COMPLETED
assert task.completed_at is not None
```

##### `class TimeEntry(BaseModel)`
Represents a time tracking entry.

**Attributes:**
- `id`: Optional[int] - Database ID
- `user_id`: int - User tracking time
- `task_id`: Optional[int] - Associated task (if any)
- `start_time`: datetime - When tracking started
- `end_time`: Optional[datetime] - When tracking ended
- `duration_seconds`: Optional[int] - Calculated duration
- `description`: Optional[str] - What was worked on
- `is_active`: bool - Whether currently tracking
- `created_at`: datetime - Creation timestamp

**Methods:**
- `calculate_duration()`: Calculate duration if start and end times exist
- `stop()`: Stop tracking and calculate duration

**Example:**
```python
entry = TimeEntry(
    user_id=1,
    task_id=5,
    start_time=datetime.now(),
    description="Working on API integration"
)

# Stop tracking after some time
time.sleep(3600)  # 1 hour
entry.stop()
print(f"Tracked {entry.duration_seconds} seconds")
```

#### Data Transfer Objects (DTOs)

##### `class TaskCreate(BaseModel)`
Schema for creating a new task.

**Attributes:**
- `title`: str - Task title (1-200 characters)
- `description`: Optional[str] - Description (max 1000 characters)
- `priority`: TaskPriority - Priority level (default: MEDIUM)
- `due_date`: Optional[datetime] - Due date

**Validation:**
- Title must be between 1-200 characters
- Description max 1000 characters

**Example:**
```python
task_data = TaskCreate(
    title="Implement user authentication",
    description="Add JWT-based auth to the API",
    priority=TaskPriority.HIGH
)
```

##### `class TaskUpdate(BaseModel)`
Schema for updating an existing task.

**Attributes:**
- `title`: Optional[str] - New title (1-200 characters)
- `description`: Optional[str] - New description (max 1000 characters)
- `status`: Optional[TaskStatus] - New status
- `priority`: Optional[TaskPriority] - New priority
- `due_date`: Optional[datetime] - New due date

**Note:** All fields are optional for partial updates.

**Example:**
```python
updates = TaskUpdate(
    status=TaskStatus.IN_PROGRESS,
    priority=TaskPriority.URGENT
)
```

##### `class TimeEntryCreate(BaseModel)`
Schema for creating a time entry.

**Attributes:**
- `task_id`: Optional[int] - Associated task
- `description`: Optional[str] - Description (max 500 characters)

##### `class UserStats(BaseModel)`
Aggregated user statistics.

**Attributes:**
- `total_tasks`: int - Total number of tasks
- `completed_tasks`: int - Completed tasks count
- `pending_tasks`: int - Pending tasks count
- `in_progress_tasks`: int - In-progress tasks count
- `total_time_today`: int - Seconds tracked today
- `total_time_this_week`: int - Seconds tracked this week
- `total_time_this_month`: int - Seconds tracked this month
- `active_time_entry`: Optional[TimeEntry] - Current tracking

**Example:**
```python
stats = UserStats(
    total_tasks=25,
    completed_tasks=20,
    pending_tasks=3,
    in_progress_tasks=2,
    total_time_today=14400,  # 4 hours
    total_time_this_week=72000  # 20 hours
)
```

#### Slack-Specific Models

##### `class SlackCommand(BaseModel)`
Schema for Slack slash command data.

**Attributes:**
- `token`: str - Verification token
- `team_id`: str - Workspace ID
- `team_domain`: str - Workspace domain
- `channel_id`: str - Channel where command was used
- `channel_name`: str - Channel name
- `user_id`: str - User who invoked command
- `user_name`: str - Username
- `command`: str - Command that was typed
- `text`: str - Text after the command
- `response_url`: str - URL for sending responses
- `trigger_id`: str - ID for opening modals

##### `class SlackEvent(BaseModel)`
Schema for Slack event data.

**Attributes:**
- `type`: str - Event type
- `user`: Optional[str] - User ID
- `text`: Optional[str] - Message text
- `ts`: str - Timestamp
- `channel`: Optional[str] - Channel ID
- `event_ts`: str - Event timestamp

## Usage Examples

### Basic Model Usage
```python
from src.models.schemas import Task, TaskStatus, TaskPriority
from datetime import datetime, timedelta

# Create a task
task = Task(
    user_id=1,
    title="Complete quarterly report",
    description="Compile Q4 metrics and analysis",
    priority=TaskPriority.HIGH,
    due_date=datetime.now() + timedelta(days=7)
)

# Access attributes
print(f"Task: {task.title}")
print(f"Due: {task.due_date}")
print(f"Status: {task.status.value}")

# Update status
task.mark_completed()
```

### Validation Examples
```python
from pydantic import ValidationError
from src.models.schemas import TaskCreate

# Valid task
try:
    task = TaskCreate(
        title="Valid task",
        priority=TaskPriority.MEDIUM
    )
    print("Task created successfully")
except ValidationError as e:
    print(f"Validation error: {e}")

# Invalid task (empty title)
try:
    task = TaskCreate(
        title="",  # Too short!
        priority=TaskPriority.MEDIUM
    )
except ValidationError as e:
    print(f"Validation error: {e}")
    # Output: title must have at least 1 character
```

### Serialization
```python
# Convert to dictionary
task_dict = task.model_dump()

# Convert to JSON
task_json = task.model_dump_json()

# Create from dictionary
task_from_dict = Task(**task_dict)

# Exclude fields
task_public = task.model_dump(exclude={"user_id", "created_at"})
```

### Working with Enums
```python
# Using enums
status = TaskStatus.PENDING
print(status.value)  # "pending"
print(status.name)   # "PENDING"

# Iterate enum values
for status in TaskStatus:
    print(f"{status.name}: {status.value}")

# Validation with enums
task = Task(
    user_id=1,
    title="Test",
    status="pending"  # String automatically converted to enum
)
```

### Time Tracking Example
```python
from src.models.schemas import TimeEntry
from datetime import datetime, timedelta

# Start tracking
entry = TimeEntry(
    user_id=1,
    task_id=10,
    start_time=datetime.now()
)

# Simulate work
entry.end_time = datetime.now() + timedelta(hours=2, minutes=30)

# Calculate duration
duration = entry.calculate_duration()
print(f"Worked for {duration} seconds")  # 9000 seconds (2.5 hours)

# Or use the stop method
entry2 = TimeEntry(user_id=1, start_time=datetime.now())
# ... work happens ...
entry2.stop()
print(f"Duration: {entry2.duration_seconds}")
```

### Model Inheritance
```python
# Base model with common fields
class TimestampedModel(BaseModel):
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

# Inherit from base
class CustomTask(TimestampedModel):
    title: str
    completed: bool = False
```

## Dependencies

### External Dependencies:
- `pydantic`: Data validation using Python type annotations
- `python-dateutil`: Date/time handling utilities

### Internal Dependencies:
- None (models module has no internal dependencies)

## Best Practices

1. **Use Type Hints**: Always specify types for better IDE support
2. **Validation Rules**: Add field validators for business rules
3. **Default Values**: Provide sensible defaults where appropriate
4. **Immutability**: Consider using frozen models for immutable data
5. **Serialization**: Use model_dump() instead of dict()
6. **Optional Fields**: Use Optional[] for nullable fields
7. **Field Descriptions**: Add Field() descriptions for documentation
8. **Custom Validators**: Implement validators for complex rules

## Advanced Features

### Custom Validators
```python
from pydantic import field_validator

class TaskWithValidation(Task):
    @field_validator('due_date')
    def due_date_must_be_future(cls, v):
        if v and v < datetime.now():
            raise ValueError('Due date must be in the future')
        return v
```

### Computed Fields
```python
from pydantic import computed_field

class TaskWithComputed(Task):
    @computed_field
    @property
    def is_overdue(self) -> bool:
        if self.due_date and self.status != TaskStatus.COMPLETED:
            return datetime.now() > self.due_date
        return False
```

### Model Configuration
```python
class StrictTask(BaseModel):
    model_config = ConfigDict(
        # Validate on assignment
        validate_assignment=True,
        # Use enum values
        use_enum_values=True,
        # Forbid extra attributes
        extra='forbid',
        # Populate by field name
        populate_by_name=True
    )
```

### JSON Schema Generation
```python
# Generate JSON Schema
schema = Task.model_json_schema()

# Use for API documentation
print(json.dumps(schema, indent=2))
```

## Future Improvements

1. **GraphQL Support**: Add GraphQL schema generation
2. **Database Models**: Separate API models from ORM models
3. **Versioning**: Support multiple API versions
4. **Internationalization**: Multi-language validation messages
5. **Custom Types**: Add custom Pydantic types for common patterns
6. **Performance**: Optimize serialization for large datasets
7. **Caching**: Add model-level caching strategies
8. **Audit Fields**: Automatic audit trail fields
9. **Soft Deletes**: Support logical deletion
10. **Field Encryption**: Encrypt sensitive fields

## Testing Models

### Unit Testing
```python
def test_task_creation():
    task = Task(
        user_id=1,
        title="Test Task",
        description="Test Description"
    )
    
    assert task.title == "Test Task"
    assert task.status == TaskStatus.PENDING
    assert task.priority == TaskPriority.MEDIUM

def test_task_validation():
    with pytest.raises(ValidationError):
        Task(
            user_id="not_an_int",  # Should be int
            title=""  # Too short
        )
```

### Property-Based Testing
```python
from hypothesis import given, strategies as st

@given(
    title=st.text(min_size=1, max_size=200),
    priority=st.sampled_from(TaskPriority)
)
def test_task_properties(title, priority):
    task = Task(
        user_id=1,
        title=title,
        priority=priority
    )
    assert len(task.title) <= 200
    assert task.priority in TaskPriority
```

## Migration Strategies

### Schema Evolution
```python
# Version 1
class TaskV1(BaseModel):
    title: str
    completed: bool

# Version 2 (backward compatible)
class TaskV2(BaseModel):
    title: str
    completed: bool
    priority: TaskPriority = TaskPriority.MEDIUM  # New field with default
    
    @classmethod
    def from_v1(cls, v1_task: TaskV1) -> 'TaskV2':
        return cls(
            title=v1_task.title,
            completed=v1_task.completed
        )
```

## Performance Considerations

1. **Lazy Loading**: Use lazy evaluation for expensive computations
2. **Selective Validation**: Skip validation in performance-critical paths
3. **Caching**: Cache serialized representations
4. **Batch Operations**: Process multiple models efficiently
5. **Memory Usage**: Be mindful of large model collections
6. **JSON Parsing**: Use orjson for faster JSON operations