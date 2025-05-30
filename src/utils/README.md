# Utils Module Documentation

## Overview

The `utils` module provides common utilities, helper functions, and cross-cutting concerns used throughout the application. It follows the DRY (Don't Repeat Yourself) principle by centralizing shared functionality.

## Module Purpose and Responsibilities

### Core Responsibilities:
- **Configuration Management**: Handle environment variables and settings
- **Logging Setup**: Provide consistent logging across the application
- **Common Utilities**: Shared helper functions and decorators
- **Constants**: Application-wide constants and defaults
- **Error Handling**: Common error handling utilities

### Architecture Decisions:
1. **Centralized Configuration**: Single source of truth for all settings
2. **Structured Logging**: Consistent log format with context
3. **Type Safety**: Full type hints for all utilities
4. **Environment-Based**: Configuration driven by environment variables
5. **Fail-Fast**: Early validation of configuration

## Module Structure

```
utils/
├── __init__.py          # Module initialization and exports
├── config.py            # Configuration management
├── logger.py            # Logging setup and utilities
└── README.md           # This documentation
```

## API Documentation

### config.py

#### `class Settings(BaseSettings)`
Application settings loaded from environment variables using Pydantic.

**Attributes:**
- `SLACK_BOT_TOKEN`: str - Slack bot OAuth token
- `SLACK_APP_TOKEN`: str - Slack app-level token for Socket Mode
- `SLACK_SIGNING_SECRET`: str - Secret for verifying Slack requests
- `SLACK_BOT_USER_ID`: Optional[str] - Bot user ID (auto-detected)
- `SUPABASE_URL`: str - Supabase project URL
- `SUPABASE_KEY`: str - Supabase anonymous/service key
- `LOG_LEVEL`: str - Logging level (default: "INFO")
- `DEBUG`: bool - Debug mode flag (default: False)
- `DB_TABLE_USERS`: str - Users table name (default: "users")
- `DB_TABLE_TASKS`: str - Tasks table name (default: "tasks")
- `DB_TABLE_TIME_ENTRIES`: str - Time entries table name (default: "time_entries")

**Methods:**
- `validate_settings()`: Validate all required settings are present

**Example:**
```python
from src.utils.config import settings

# Access settings
print(f"Bot token: {settings.SLACK_BOT_TOKEN[:10]}...")
print(f"Debug mode: {settings.DEBUG}")
print(f"Log level: {settings.LOG_LEVEL}")

# Settings are immutable
# settings.DEBUG = True  # This will raise an error
```

#### `settings: Settings`
Pre-instantiated settings object available for import.

**Usage:**
```python
from src.utils.config import settings

# Direct access
if settings.DEBUG:
    print("Running in debug mode")
```

#### Exported Constants
For convenience, commonly used settings are exported directly:
- `SLACK_BOT_TOKEN`
- `SLACK_APP_TOKEN`
- `SLACK_SIGNING_SECRET`
- `SUPABASE_URL`
- `SUPABASE_KEY`

### logger.py

#### `setup_logging(log_level: Optional[str] = None, log_file: Optional[str] = None) -> logging.Logger`
Configure logging for the entire application.

**Parameters:**
- `log_level`: Override log level (uses settings.LOG_LEVEL if not provided)
- `log_file`: Optional log file path for file output

**Returns:**
- Configured root logger instance

**Features:**
- Colored console output in debug mode
- File logging support
- Structured log format with timestamps
- Library log level management

**Example:**
```python
from src.utils.logger import setup_logging

# Basic setup
logger = setup_logging()

# With file output
logger = setup_logging(log_file="logs/app.log")

# Override log level
logger = setup_logging(log_level="DEBUG")
```

#### `get_logger(name: str) -> logging.Logger`
Get a logger instance with the specified name.

**Parameters:**
- `name`: Logger name (typically `__name__`)

**Returns:**
- Logger instance

**Example:**
```python
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Use the logger
logger.info("Application started")
logger.debug("Debug information")
logger.error("An error occurred", exc_info=True)
```

## Usage Examples

### Configuration Usage
```python
from src.utils.config import settings

class MyService:
    def __init__(self):
        self.debug = settings.DEBUG
        self.api_url = settings.SUPABASE_URL
        
    def process(self):
        if self.debug:
            print(f"Connecting to {self.api_url}")
```

### Environment-Specific Configuration
```python
# .env file
SLACK_BOT_TOKEN=xoxb-your-token
SLACK_APP_TOKEN=xapp-your-token
SLACK_SIGNING_SECRET=your-secret
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
LOG_LEVEL=DEBUG
DEBUG=true

# Access in code
from src.utils.config import settings

if settings.DEBUG:
    # Development-specific code
    logger.setLevel(logging.DEBUG)
```

### Logging Best Practices
```python
from src.utils.logger import get_logger

logger = get_logger(__name__)

class TaskService:
    def create_task(self, user_id: str, description: str):
        logger.info(f"Creating task for user {user_id}")
        
        try:
            # Task creation logic
            task = self._create_task_in_db(user_id, description)
            logger.debug(f"Task created with ID: {task.id}")
            return task
            
        except DatabaseError as e:
            logger.error(f"Database error creating task: {e}", exc_info=True)
            raise
            
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            raise
```

### Structured Logging
```python
logger = get_logger(__name__)

# Log with context
logger.info("User action", extra={
    "user_id": "U123",
    "action": "task_created",
    "task_id": 456
})

# Log with timing
import time
start = time.time()
# ... operation ...
duration = time.time() - start
logger.info(f"Operation completed in {duration:.2f}s")
```

### Custom Log Formatting
```python
from src.utils.logger import setup_logging
import logging

# Custom formatter
class JSONFormatter(logging.Formatter):
    def format(self, record):
        import json
        return json.dumps({
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "module": record.module,
            "message": record.getMessage(),
            "extra": getattr(record, "extra", {})
        })

# Apply custom formatter
logger = setup_logging()
for handler in logger.handlers:
    handler.setFormatter(JSONFormatter())
```

## Environment Variables

### Required Variables
```bash
# Slack Configuration
SLACK_BOT_TOKEN=xoxb-...
SLACK_APP_TOKEN=xapp-...
SLACK_SIGNING_SECRET=...

# Supabase Configuration
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJ...
```

### Optional Variables
```bash
# Application Settings
LOG_LEVEL=INFO          # DEBUG, INFO, WARNING, ERROR, CRITICAL
DEBUG=false            # Enable debug mode

# Database Tables (defaults shown)
DB_TABLE_USERS=users
DB_TABLE_TASKS=tasks
DB_TABLE_TIME_ENTRIES=time_entries
```

## Dependencies

### External Dependencies:
- `pydantic`: Settings validation and management
- `pydantic-settings`: Environment variable loading
- `python-dotenv`: .env file support
- `colorlog`: Colored logging output (optional)

### Internal Dependencies:
- None (utils module has no internal dependencies)

## Best Practices

1. **Environment Variables**: Never commit secrets to version control
2. **Validation**: Always validate configuration on startup
3. **Defaults**: Provide sensible defaults where possible
4. **Type Safety**: Use type hints for all configurations
5. **Logging Levels**: Use appropriate log levels
6. **Context Logging**: Include relevant context in log messages
7. **Error Logging**: Always log exceptions with `exc_info=True`
8. **Performance**: Avoid logging in tight loops

## Advanced Configuration

### Multi-Environment Support
```python
import os
from pathlib import Path

# Load environment-specific .env file
env = os.getenv("ENVIRONMENT", "development")
env_file = Path(f".env.{env}")
if env_file.exists():
    load_dotenv(env_file)
else:
    load_dotenv(".env")
```

### Configuration Validation
```python
class Settings(BaseSettings):
    SLACK_BOT_TOKEN: str
    
    @field_validator('SLACK_BOT_TOKEN')
    def validate_token_format(cls, v):
        if not v.startswith('xoxb-'):
            raise ValueError('Invalid Slack bot token format')
        return v
```

### Dynamic Configuration
```python
class DynamicSettings(Settings):
    _instance = None
    
    @classmethod
    def get_settings(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def reload(self):
        """Reload settings from environment"""
        self.__init__()
```

### Feature Flags
```python
class Settings(BaseSettings):
    # Feature flags
    FEATURE_TIME_TRACKING: bool = True
    FEATURE_AI_SUGGESTIONS: bool = False
    FEATURE_VOICE_COMMANDS: bool = False
    
    def is_feature_enabled(self, feature: str) -> bool:
        return getattr(self, f"FEATURE_{feature.upper()}", False)
```

## Logging Strategies

### Log Aggregation
```python
# Configure for log aggregation services
logger = setup_logging()

# Add custom handler for log aggregation
if settings.LOG_AGGREGATION_ENABLED:
    from log_aggregator import AggregatorHandler
    handler = AggregatorHandler(
        api_key=settings.LOG_AGGREGATION_KEY,
        service_name="autonomos-dona"
    )
    logger.addHandler(handler)
```

### Performance Logging
```python
import functools
import time

def log_performance(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start
        
        logger.info(
            f"{func.__name__} completed",
            extra={
                "function": func.__name__,
                "duration_ms": duration * 1000,
                "args_count": len(args),
                "kwargs_count": len(kwargs)
            }
        )
        return result
    return wrapper
```

### Audit Logging
```python
class AuditLogger:
    def __init__(self):
        self.logger = get_logger("audit")
    
    def log_action(self, user_id: str, action: str, details: dict):
        self.logger.info(
            f"User action: {action}",
            extra={
                "user_id": user_id,
                "action": action,
                "details": details,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
```

## Future Improvements

1. **Secret Management**: Integration with secret management services
2. **Configuration Hot Reload**: Update settings without restart
3. **Distributed Tracing**: OpenTelemetry integration
4. **Metrics Collection**: Prometheus metrics export
5. **Log Sampling**: Reduce log volume in production
6. **Configuration Versioning**: Track configuration changes
7. **Environment Validation**: Validate environment on startup
8. **Configuration UI**: Web interface for configuration
9. **A/B Testing**: Feature flag management system
10. **Log Analysis**: Built-in log analysis tools

## Testing Utilities

### Mock Configuration
```python
from unittest.mock import patch

def test_with_mock_settings():
    with patch('src.utils.config.settings') as mock_settings:
        mock_settings.DEBUG = True
        mock_settings.LOG_LEVEL = "DEBUG"
        
        # Test code here
        assert mock_settings.DEBUG is True
```

### Test Logging
```python
import logging
from io import StringIO

def test_logging_output():
    # Capture log output
    log_capture = StringIO()
    handler = logging.StreamHandler(log_capture)
    logger = get_logger("test")
    logger.addHandler(handler)
    
    # Generate logs
    logger.info("Test message")
    
    # Verify output
    log_output = log_capture.getvalue()
    assert "Test message" in log_output
```

## Security Considerations

1. **Secret Rotation**: Support for rotating secrets without downtime
2. **Encryption**: Encrypt sensitive configuration values
3. **Access Control**: Limit who can view configuration
4. **Audit Trail**: Log all configuration changes
5. **Validation**: Validate configuration values
6. **Least Privilege**: Only expose necessary configuration
7. **Environment Isolation**: Separate configs per environment

## Performance Optimization

1. **Lazy Loading**: Load configuration only when needed
2. **Caching**: Cache parsed configuration values
3. **Minimal Dependencies**: Keep utils lightweight
4. **Async Support**: Async configuration loading
5. **Memory Efficiency**: Avoid storing large values
6. **Connection Pooling**: Reuse connections efficiently