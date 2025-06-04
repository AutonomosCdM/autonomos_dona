# Autónomos Dona Slack Bot

[![CI Pipeline](https://github.com/autonomos-team/autonomos_dona/actions/workflows/ci.yml/badge.svg)](https://github.com/autonomos-team/autonomos_dona/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/autonomos-team/autonomos_dona/branch/main/graph/badge.svg)](https://codecov.io/gh/autonomos-team/autonomos_dona)
[![Python Version](https://img.shields.io/badge/python-3.9%20|%203.10%20|%203.11-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

An AI-powered Slack assistant designed specifically for the founding team of Autónomos startup. Dona helps with task management, productivity analytics, and intelligent conversation.

## What Dona Actually Does

- **Natural Language Chat**: Responds intelligently in Spanish/English using Groq LLM
- **Task Management**: Create, list, and complete tasks with full tracking
- **Productivity Analytics**: Real summaries and statistics from your Slack activity
- **Personal Configuration**: Set language, timezone, and notification preferences
- **Context Awareness**: Adapts responses for public channels vs private messages

## Quick Start

### Prerequisites

- Python 3.9 or higher
- Slack workspace with admin access
- Supabase account

### Installation

1. Clone the repository:
```bash
git clone https://github.com/your-org/autonomos_dona.git
cd autonomos_dona
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
make install
```

4. Configure environment:
```bash
cp .env.example .env
# Edit .env with your Slack and Supabase credentials
```

5. Run the bot:
```bash
make run
```

## Working Commands

- `/dona [message]` - Chat naturally with AI assistant
- `/dona-help` - Context-aware help (different for public/private)
- `/dona-task create [description]` - Create new task
- `/dona-task list [status]` - List your tasks  
- `/dona-task complete [task-id]` - Mark task as done
- `/dona-summary [today|week]` - Get productivity analytics
- `/dona-status` - Your personal statistics and current state
- `/dona-config` - View/update personal preferences

### Real Examples

```
/dona necesito crear una presentación para el board
/dona-task create Revisar contratos Q4
/dona-task list pending
/dona-summary week
/dona-config language en
```

## Project Structure

```
autonomos_dona/
├── src/
│   ├── app.py              # Main application entry
│   ├── handlers/           # Slack event handlers
│   ├── services/           # External service integrations
│   ├── models/             # Data models
│   └── utils/              # Utilities and helpers
├── tests/                  # Test suite
├── docs/                   # Documentation
├── requirements.txt        # Python dependencies
└── Makefile               # Common commands
```

## Development

### Running Tests

```bash
make test
```

### Code Formatting

```bash
make format
```

### Linting

```bash
make lint
```

### Creating a Development Build

```bash
make dev
```

## Configuration

The bot requires the following environment variables:

| Variable | Description |
|----------|-------------|
| `SLACK_BOT_TOKEN` | Bot User OAuth Token |
| `SLACK_APP_TOKEN` | App-Level Token |
| `SLACK_SIGNING_SECRET` | Signing Secret |
| `SUPABASE_URL` | Supabase Project URL |
| `SUPABASE_KEY` | Supabase Anonymous Key |
| `GROQ_API_KEY` | Groq API Key for LLM |

Current project uses Supabase project: `wqqxctsyoeoqcqkoaagv`

## Architecture

The bot follows a modular architecture with clear separation of concerns:

- **Handlers**: Process Slack events and commands
- **Services**: Manage external integrations (Supabase, Slack API)
- **Models**: Define data structures and validation
- **Utils**: Provide shared functionality

See [docs/architecture.md](docs/architecture.md) for detailed technical documentation.

## Contributing

We welcome contributions! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Style

- Follow PEP 8 guidelines
- Use type hints for all functions
- Write descriptive docstrings
- Add tests for new functionality

## Testing

The project uses pytest for testing:

```bash
# Run all tests
make test

# Run specific test file
pytest tests/test_commands.py

# Run with coverage
pytest --cov=src tests/
```

## Deployment

### Local Development

```bash
make dev
```

### Production

Currently deployed on Render.com using:
- Background worker service
- Python 3.9 runtime  
- Supabase as database
- Socket Mode for Slack connectivity

Configuration in `render.yaml`

## Troubleshooting

### Bot not responding

1. Check the logs for errors
2. Verify all tokens in `.env` are correct
3. Ensure Socket Mode is enabled in Slack app settings
4. Confirm bot has necessary permissions

### Database connection issues

1. Verify Supabase URL and key
2. Check network connectivity
3. Ensure database tables are created

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support and questions:
- Create an issue on GitHub
- Join our Slack community
- Email: support@autonomos.com

## Acknowledgments

- Built with [Slack Bolt for Python](https://slack.dev/bolt-python/)
- Database powered by [Supabase](https://supabase.com/)
- Thanks to all contributors and the Autónomos team

---

Made with ❤️ by the Autónomos Team