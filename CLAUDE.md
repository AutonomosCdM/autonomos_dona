# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project: Autónomos Dona - Slack Executive Assistant

Autónomos Dona is an AI-powered executive assistant that operates within Slack, designed to help the founding team of Autónomos startup with task management, scheduling, and workflow automation.

## Build Commands

```bash
# Install dependencies
make install

# Run the bot
make run

# Run tests
make test

# Lint code
make lint

# Format code
make format
```

## Project Structure

```
autonomos_dona/
├── src/
│   ├── app.py              # Main application entry point
│   ├── handlers/           # Slack event and command handlers
│   ├── services/           # External service integrations (Supabase, Slack)
│   ├── models/             # Data models and schemas
│   └── utils/              # Utilities (config, logging)
├── tests/                  # Unit and integration tests
├── database/               # Database schemas and migrations
├── docs/                   # Documentation
└── requirements.txt        # Python dependencies
```

## Key Technologies

- **Python 3.9+** with Slack Bolt framework
- **Supabase** for data persistence
- **Slack API** for bot functionality
- **Agent-to-Agent (A2A)** architecture for future integrations

## Development Workflow

1. **Environment Setup**: Copy `.env.example` to `.env` and configure Slack/Supabase credentials
2. **Database Setup**: Run the schema in `database/schema.sql` in your Supabase project
3. **Slack App Setup**: Follow instructions in `docs/setup.md`
4. **Local Development**: Use `make run` to start the bot with hot-reload

## Important Notes

- The bot differentiates between public and private contexts automatically
- All interactions are logged for traceability and learning
- Commands are bilingual (Spanish/English) to accommodate the team
- The architecture is designed to evolve from basic assistant to executive secretary

## Coding Standards

- Use type hints for all function parameters and returns
- Follow PEP 8 style guidelines (enforced by flake8)
- All new features must include unit tests
- Document all public APIs and complex logic
- Use async/await for I/O operations when possible

## Commit Conventions

Follow conventional commits format:
- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code formatting
- **refactor**: Code refactoring
- **test**: Test additions/modifications
- **chore**: Maintenance tasks

Format: `type(scope): brief description`

See CONTRIBUTING.md for detailed commit guidelines.

## Testing

Run tests with coverage:
```bash
make test
```

For specific test files:
```bash
pytest tests/test_commands.py -v
```

## Deployment

The bot is designed to run in Socket Mode for development and can be deployed to any Python-capable hosting platform. Production deployment guide is in `docs/deployment.md`.