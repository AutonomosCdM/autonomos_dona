# Technical Architecture

## Overview

The Autónomos Dona Slack bot is built using a modular Python architecture with clear separation of concerns. The system is designed to be scalable, maintainable, and easy to extend with new features.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                     Slack Workspace                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │   Users     │  │  Channels   │  │   Events    │     │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘     │
└─────────┼────────────────┼────────────────┼────────────┘
          │                │                │
          ▼                ▼                ▼
┌─────────────────────────────────────────────────────────┐
│                    Slack Bolt App                        │
│  ┌─────────────────────────────────────────────────┐    │
│  │              Socket Mode Handler                 │    │
│  └─────────────────────────────────────────────────┘    │
└───────────────────────────┬─────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────┐
│                    Application Core                      │
│                                                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │  Commands   │  │   Events    │  │  Actions    │     │
│  │  Handler    │  │  Handler    │  │  Handler    │     │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘     │
│         │                │                │              │
│         └────────────────┴────────────────┘             │
│                          │                               │
│  ┌───────────────────────▼─────────────────────────┐    │
│  │               Business Logic                     │    │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────────┐     │    │
│  │  │  Task   │  │  Time   │  │   User      │     │    │
│  │  │ Manager │  │ Tracker │  │  Manager    │     │    │
│  │  └─────────┘  └─────────┘  └─────────────┘     │    │
│  └─────────────────────────────────────────────────┘    │
└───────────────────────────┬─────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────┐
│                    Service Layer                         │
│                                                          │
│  ┌─────────────────┐           ┌─────────────────┐      │
│  │ Supabase Client │           │  Slack Client  │      │
│  └────────┬────────┘           └────────┬────────┘      │
└───────────┼─────────────────────────────┼───────────────┘
            │                             │
            ▼                             ▼
    ┌───────────────┐             ┌───────────────┐
    │   Supabase    │             │   Slack API   │
    │   Database    │             │               │
    └───────────────┘             └───────────────┘
```

## Core Components

### 1. Slack Integration Layer

**Technology:** Slack Bolt for Python

The Slack integration layer handles all communication with Slack:
- **Socket Mode Handler**: Maintains WebSocket connection for real-time events
- **Command Handlers**: Process slash commands (`/dona-task`, `/dona-time`, etc.)
- **Event Handlers**: React to mentions, messages, and other Slack events
- **Interactive Components**: Handle button clicks and form submissions

### 2. Application Core

The core application logic is organized into specialized handlers:

**Command Processing:**
- Parses and validates command input
- Routes to appropriate business logic
- Formats and returns responses

**Event Processing:**
- Filters relevant events
- Extracts context and user information
- Triggers appropriate actions

**State Management:**
- Maintains user session context
- Tracks ongoing operations
- Manages conversation flow

### 3. Business Logic Layer

Domain-specific logic is encapsulated in service modules:

**Task Management:**
- Create, list, and complete tasks ✅
- Assign priorities ✅
- Basic task tracking ✅

**LLM Integration:**
- Natural language processing ✅
- Intent extraction ✅
- Bilingual responses (ES/EN) ✅

**User Management:**
- User registration and profiles ✅
- Activity tracking ✅
- Personal preferences ✅

### 4. Data Persistence Layer

**Technology:** Supabase (PostgreSQL)

Database schema supports:
- User profiles linked to Slack IDs
- Task storage with full CRUD operations
- Time tracking entries
- Audit trails and activity logs

### 5. External Services

**Slack Web API:**
- User information retrieval
- Rich message formatting
- File uploads and management

**Future Integrations:**
- Calendar services
- Email providers
- Document management systems

## Design Patterns

### 1. Service Pattern

Each external integration is wrapped in a service class:
```python
class SupabaseService:
    def __init__(self):
        self.client = create_client(...)
    
    def get_user_tasks(self, user_id):
        # Implementation
```

### 2. Handler Pattern

Slack events are processed through dedicated handlers:
```python
def handle_task_command(ack, respond, command):
    ack()  # Acknowledge immediately
    # Process command
    respond(result)  # Send response
```

### 3. Repository Pattern

Database operations are abstracted:
```python
class TaskRepository:
    def create(self, task_data):
        # Database operation
    
    def find_by_user(self, user_id):
        # Database query
```

### 4. Factory Pattern

Complex objects are created through factories:
```python
class BlockKitFactory:
    @staticmethod
    def create_task_blocks(task):
        # Generate Slack blocks
```

## Security Considerations

### 1. Authentication

- Slack signing secret validates all requests
- OAuth tokens stored securely
- User permissions verified on each action

### 2. Data Protection

- All sensitive data encrypted at rest (Supabase)
- TLS for all external communications
- No sensitive data in logs

### 3. Access Control

- Workspace-level isolation
- User-specific data access
- Admin-only commands protected

## Scalability

### 1. Horizontal Scaling

- Stateless application design
- Multiple instances can run concurrently
- Load balancer ready

### 2. Database Optimization

- Indexed queries for performance
- Connection pooling
- Query optimization

### 3. Caching Strategy

- In-memory caching for frequent data
- Redis integration ready
- TTL-based cache invalidation

## Monitoring and Observability

### 1. Logging

- Structured logging with context
- Log levels for different environments
- Centralized log aggregation ready

### 2. Metrics

- Response time tracking
- Error rate monitoring
- User activity metrics

### 3. Health Checks

- Application health endpoint
- Database connectivity checks
- External service status monitoring

## Development Workflow

### 1. Local Development

```bash
# Start local environment
make dev

# Run with hot reload
python -m src.app --reload
```

### 2. Testing Strategy

- Unit tests for business logic
- Integration tests for Slack handlers
- End-to-end tests with mock Slack

### 3. Deployment Pipeline

```
Local → GitHub → CI/CD → Staging → Production
```

## Known Limitations

### 1. Missing Features (TODOs)

Current gaps in functionality:
- Reminder scheduling (fake responses only)
- Time tracking (not implemented)
- Task updates (only create/list/complete)

### 2. Current Scope

Dona is focused on:
- Slack-only integration
- Basic task management
- Conversation analytics
- Personal productivity insights

## Technology Stack Summary

- **Language:** Python 3.9+
- **Framework:** Slack Bolt (Socket Mode)
- **Database:** Supabase (PostgreSQL) - project: wqqxctsyoeoqcqkoaagv
- **LLM:** Groq API (Llama 3.1-8B-Instant)
- **Authentication:** Slack OAuth
- **Deployment:** Render.com (Background Worker)
- **Monitoring:** Structured logging + Rate limiting
- **Testing:** Pytest framework