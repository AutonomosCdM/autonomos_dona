# Handlers Module Documentation

## Overview

The `handlers` module is responsible for processing all incoming events and commands from Slack. It serves as the primary interface between the Slack API and the Autónomos Dona bot's business logic, implementing the command pattern for clean separation of concerns.

## Module Purpose and Responsibilities

### Core Responsibilities:
- **Command Processing**: Handle all slash commands (`/dona`, `/dona-task`, etc.)
- **Event Handling**: Process Slack events (messages, mentions, reactions)
- **Request Validation**: Validate incoming requests and acknowledge them
- **Response Management**: Format and send appropriate responses to users
- **Error Handling**: Gracefully handle errors and provide user-friendly feedback

### Architecture Decisions:
1. **Separation of Concerns**: Commands and events are handled in separate modules for clarity
2. **Functional Approach**: Handlers are implemented as pure functions for testability
3. **Dependency Injection**: Services are injected through context to avoid tight coupling
4. **Async-First**: All handlers support async operations for better performance

## Module Structure

```
handlers/
├── __init__.py          # Module initialization and exports
├── commands.py          # Slash command handlers
├── events.py            # Event handlers (messages, reactions, etc.)
└── README.md           # This documentation
```

## API Documentation

### commands.py

#### `register_command_handlers(app: App) -> None`
Registers all slash command handlers with the Slack Bolt application.

**Parameters:**
- `app`: Slack Bolt application instance

**Registered Commands:**
- `/dona` - Main natural language interface
- `/dona-help` - Help and documentation
- `/dona-task` - Task management
- `/dona-remind` - Reminder functionality
- `/dona-summary` - Activity summaries
- `/dona-status` - User status and statistics

#### Command Handler Signature
All command handlers follow this signature:
```python
def handle_command(ack: Ack, respond: Respond, command: Dict[str, Any], context: Dict[str, Any]) -> None
```

**Parameters:**
- `ack`: Function to acknowledge the command (must be called within 3 seconds)
- `respond`: Function to send a response to the user
- `command`: Command payload from Slack
- `context`: Additional context including app instance and user info

### events.py

#### `register_event_handlers(app: App) -> None`
Registers all event handlers with the Slack Bolt application.

**Parameters:**
- `app`: Slack Bolt application instance

**Registered Events:**
- `app_mention` - When the bot is @mentioned
- `message` - Direct messages to the bot
- `reaction_added` - When reactions are added to messages
- `app_home_opened` - When users open the app home tab

#### Event Handler Signature
Event handlers have varying signatures based on the event type:
```python
def handle_event(event: Dict[str, Any], say: Any, context: BoltContext) -> None
```

## Usage Examples

### Basic Command Registration
```python
from slack_bolt import App
from src.handlers import register_command_handlers, register_event_handlers

app = App(
    token=SLACK_BOT_TOKEN,
    signing_secret=SLACK_SIGNING_SECRET
)

# Register all handlers
register_command_handlers(app)
register_event_handlers(app)
```

### Custom Command Handler
```python
def handle_custom_command(ack: Ack, respond: Respond, command: Dict[str, Any]) -> None:
    # Always acknowledge first
    ack()
    
    # Extract command data
    user_id = command.get("user_id")
    text = command.get("text", "")
    
    # Process command
    if text:
        respond(f"Processing: {text}")
    else:
        respond("Please provide a command")
```

### Natural Language Processing
```python
# Example from /dona command handler
text_lower = text.lower()

if "help" in text_lower:
    handle_help_command(ack, respond, command)
elif any(word in text_lower for word in ["task", "tarea", "hacer"]):
    respond("I understand you want to create a task...")
```

### Error Handling Pattern
```python
try:
    # Process command
    result = process_user_request(user_id, text)
    respond(f"Success: {result}")
except Exception as e:
    logger.error(f"Error processing command: {e}", exc_info=True)
    respond("An error occurred. Please try again.")
```

## Dependencies

### External Dependencies:
- `slack_bolt`: Slack Bolt framework for Python
- `slack_sdk`: Slack SDK for API interactions

### Internal Dependencies:
- `src.models.schemas`: Data models and validation
- `src.services.supabase_client`: Database operations
- `src.services.slack_client`: Slack-specific utilities
- `src.utils.config`: Configuration management
- `src.utils.logger`: Logging utilities

## Command Details

### `/dona` - Main Interface
- **Purpose**: Natural language interface for all bot functions
- **Usage**: `/dona [natural language request]`
- **Examples**:
  - `/dona help me organize my tasks`
  - `/dona necesito agendar una reunión`
  - `/dona what's my status today?`

### `/dona-task` - Task Management
- **Purpose**: Create, list, and manage tasks
- **Usage**: `/dona-task [action] [parameters]`
- **Actions**:
  - `create [description]` - Create a new task
  - `list` - Show all tasks
  - `complete [task_id]` - Mark task as complete
  - `update [task_id] [updates]` - Update task details

### `/dona-remind` - Reminders
- **Purpose**: Set time-based reminders
- **Usage**: `/dona-remind [when] [message]`
- **Examples**:
  - `/dona-remind tomorrow 10am Call client`
  - `/dona-remind in 2 hours Review PR`

### `/dona-summary` - Activity Summaries
- **Purpose**: Get activity summaries for different time periods
- **Usage**: `/dona-summary [period]`
- **Periods**: `today`, `week`, `month`

### `/dona-status` - Current Status
- **Purpose**: View current work status and statistics
- **Usage**: `/dona-status`
- **Shows**: Active tasks, time tracking, productivity metrics

## Event Handling Details

### App Mentions
- Triggered when users @mention the bot in channels
- Provides contextual help based on mention content
- Supports natural language processing

### Direct Messages
- Handles private conversations with the bot
- More conversational interface
- Stores conversation context for continuity

### Reactions
- Monitors specific emoji reactions for quick actions
- Example: ✅ to mark tasks complete
- Extensible for custom workflows

### App Home
- Provides a dashboard interface
- Shows user statistics and quick actions
- Updated dynamically based on user data

## Best Practices

1. **Always Acknowledge Commands**: Call `ack()` within 3 seconds
2. **User-Friendly Responses**: Provide clear, helpful feedback
3. **Error Messages**: Never expose technical errors to users
4. **Logging**: Log all significant actions for debugging
5. **Validation**: Validate all user input before processing
6. **Localization**: Support both English and Spanish responses
7. **Privacy**: Handle DMs with appropriate privacy considerations

## Future Improvements

1. **Enhanced NLP**: Integrate more sophisticated natural language processing
2. **Command Aliases**: Support multiple ways to invoke the same function
3. **Batch Operations**: Allow bulk task operations
4. **Interactive Modals**: Use Slack modals for complex inputs
5. **Scheduled Messages**: Implement delayed message sending
6. **Context Awareness**: Maintain conversation context across interactions
7. **Smart Suggestions**: Proactive assistance based on user patterns
8. **Voice Commands**: Support for voice-to-text commands
9. **Rich Media**: Support for file attachments and images
10. **Analytics**: Track command usage for insights

## Testing

Handlers can be tested using the Slack Bolt testing framework:

```python
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler
from src.handlers.commands import handle_dona_command

def test_dona_command():
    # Mock objects
    ack = Mock()
    respond = Mock()
    command = {
        "user_id": "U123456",
        "text": "help",
        "channel_id": "C123456"
    }
    
    # Test handler
    handle_dona_command(ack, respond, command, {})
    
    # Assertions
    ack.assert_called_once()
    respond.assert_called_with_contains("I'm Dona")
```

## Error Handling Strategy

1. **Validation Errors**: Return helpful user messages
2. **Service Errors**: Log and return generic error message
3. **Network Errors**: Implement retry logic
4. **Rate Limits**: Queue requests and notify users
5. **Unknown Commands**: Suggest similar commands

## Security Considerations

1. **Input Sanitization**: Always sanitize user input
2. **Command Verification**: Verify Slack signatures
3. **Permission Checks**: Validate user permissions
4. **Data Privacy**: Handle sensitive data appropriately
5. **Rate Limiting**: Prevent command abuse

## Performance Optimization

1. **Async Operations**: Use async for I/O operations
2. **Caching**: Cache frequently accessed data
3. **Lazy Loading**: Load services only when needed
4. **Batch Processing**: Group similar operations
5. **Response Streaming**: Stream large responses