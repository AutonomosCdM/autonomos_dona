# Autónomos Dona Slack Bot

A powerful Slack bot designed to help autonomous workers and freelancers manage their tasks, track time, and collaborate effectively.

## Features

- **Task Management**: Create, update, and track tasks directly from Slack
- **Time Tracking**: Start/stop timers and log work hours
- **Status Dashboard**: View your productivity metrics and current activities
- **Smart Notifications**: Get reminded about important tasks and deadlines
- **Team Collaboration**: Share progress and coordinate with team members

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

## Available Commands

- `/dona-help` - Display help information
- `/dona-task [create|list|update]` - Manage tasks
- `/dona-time [start|stop|log]` - Track time
- `/dona-status` - View your current status

### Examples

```
/dona-task create Fix login bug
/dona-time start
/dona-task list
/dona-status
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

See [docs/setup.md](docs/setup.md) for detailed configuration instructions.

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

The bot can be deployed using:
- Docker containers
- Kubernetes
- Cloud platforms (Heroku, AWS, GCP)
- Traditional VPS with systemd

See deployment guide in [docs/deployment.md](docs/deployment.md) for details.

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