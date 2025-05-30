# Setup Instructions

This guide will help you set up the Autónomos Dona Slack bot for development or production use.

## Prerequisites

- Python 3.9 or higher
- A Slack workspace where you have admin privileges
- A Supabase account and project
- Git (for cloning the repository)

## 1. Clone the Repository

```bash
git clone https://github.com/your-org/autonomos_dona.git
cd autonomos_dona
```

## 2. Set Up Python Environment

### Create a virtual environment:

```bash
python -m venv venv
```

### Activate the virtual environment:

**On macOS/Linux:**
```bash
source venv/bin/activate
```

**On Windows:**
```bash
venv\Scripts\activate
```

### Install dependencies:

```bash
make install
# or manually:
pip install -r requirements.txt
```

## 3. Slack App Configuration

### Create a Slack App:

1. Go to [api.slack.com/apps](https://api.slack.com/apps)
2. Click "Create New App" → "From scratch"
3. Name your app "Autónomos Dona Bot"
4. Select your workspace

### Configure OAuth & Permissions:

1. Go to "OAuth & Permissions" in the sidebar
2. Add the following Bot Token Scopes:
   - `app_mentions:read` - View messages that mention @bot
   - `channels:history` - View messages in public channels
   - `channels:read` - View basic channel info
   - `chat:write` - Send messages
   - `commands` - Add slash commands
   - `groups:history` - View messages in private channels
   - `groups:read` - View basic private channel info
   - `im:history` - View direct messages
   - `im:read` - View basic DM info
   - `im:write` - Send direct messages
   - `reactions:read` - View emoji reactions
   - `users:read` - View user info

### Enable Socket Mode:

1. Go to "Socket Mode" in the sidebar
2. Enable Socket Mode
3. Generate an app-level token with `connections:write` scope
4. Save this token as `SLACK_APP_TOKEN`

### Install App to Workspace:

1. Go to "OAuth & Permissions"
2. Click "Install to Workspace"
3. Authorize the app
4. Save the `Bot User OAuth Token` as `SLACK_BOT_TOKEN`

### Get Signing Secret:

1. Go to "Basic Information"
2. Find "Signing Secret" under "App Credentials"
3. Save this as `SLACK_SIGNING_SECRET`

### Add Slash Commands:

Go to "Slash Commands" and add:

- `/dona-help` - Display help information
- `/dona-task` - Manage tasks
- `/dona-time` - Track time
- `/dona-status` - View status

For each command, use the Request URL: `https://your-domain.com/slack/commands`

### Subscribe to Events:

1. Go to "Event Subscriptions"
2. Enable Events
3. Add Bot Events:
   - `app_home_opened`
   - `app_mention`
   - `message.im`
   - `reaction_added`

## 4. Supabase Configuration

### Create Tables:

Run the following SQL in your Supabase SQL editor:

```sql
-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    slack_user_id VARCHAR(255) NOT NULL,
    slack_workspace_id VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    display_name VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(slack_user_id, slack_workspace_id)
);

-- Tasks table
CREATE TABLE tasks (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    priority VARCHAR(50) DEFAULT 'medium',
    due_date TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    INDEX idx_user_tasks (user_id, status)
);

-- Time entries table
CREATE TABLE time_entries (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    task_id INTEGER REFERENCES tasks(id) ON DELETE SET NULL,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    INDEX idx_user_time_entries (user_id, is_active),
    INDEX idx_task_time_entries (task_id)
);
```

### Get API Keys:

1. Go to your Supabase project settings
2. Navigate to "API"
3. Copy the `URL` as `SUPABASE_URL`
4. Copy the `anon public` key as `SUPABASE_KEY`

## 5. Environment Configuration

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` and fill in your values:

```env
# Slack Configuration
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_APP_TOKEN=xapp-your-app-token
SLACK_SIGNING_SECRET=your-signing-secret

# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key

# Application Configuration
LOG_LEVEL=INFO
DEBUG=False
```

## 6. Run the Bot

### Development:

```bash
make run
# or manually:
python -m src.app
```

### Production:

For production, consider using:
- systemd service (Linux)
- Docker container
- Process manager like PM2
- Cloud platform (Heroku, AWS, etc.)

## 7. Test the Bot

1. Invite the bot to a channel: `/invite @Autónomos Dona Bot`
2. Test commands:
   - `/dona-help` - Should show help text
   - `/dona-task create My first task` - Create a task
   - `/dona-time start` - Start time tracking
   - `/dona-status` - View your status

## Troubleshooting

### Bot not responding:

1. Check logs for errors
2. Verify all tokens are correct
3. Ensure Socket Mode is enabled
4. Check bot has required permissions

### Database errors:

1. Verify Supabase URL and key
2. Check table schemas match
3. Ensure network connectivity

### Permission errors:

1. Reinstall app to workspace
2. Verify all OAuth scopes are added
3. Check channel permissions

## Next Steps

- Configure additional features
- Set up monitoring and logging
- Customize commands for your team
- Add integrations with other tools