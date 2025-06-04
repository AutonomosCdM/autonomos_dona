-- Minimal Dona Slack Bot Schema for Supabase
-- Version: 1.0 (Minimal)
-- Date: 2025-06-04

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table (linked to Slack users)
CREATE TABLE users (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    slack_user_id VARCHAR(255) NOT NULL,
    slack_workspace_id VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    full_name VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(slack_user_id, slack_workspace_id)
);

-- Conversations table
CREATE TABLE conversations (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    slack_channel_id VARCHAR(255) NOT NULL,
    slack_thread_ts VARCHAR(255),
    user_id UUID REFERENCES users(id),
    context_type VARCHAR(20) NOT NULL CHECK (context_type IN ('public', 'private')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Messages table  
CREATE TABLE messages (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    sender_type VARCHAR(20) NOT NULL CHECK (sender_type IN ('user', 'dona', 'bot')),
    sender_id VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    slack_message_ts VARCHAR(255),
    intent_detected VARCHAR(100),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tasks table (simplified)
CREATE TABLE tasks (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    created_by VARCHAR(255) NOT NULL,
    assigned_to VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'cancelled')),
    priority VARCHAR(10) DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'urgent')),
    channel_id VARCHAR(255),
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Activity logs table (for analytics)
CREATE TABLE activity_logs (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    slack_user_id VARCHAR(255) NOT NULL,
    activity_type VARCHAR(50) NOT NULL,
    entity_type VARCHAR(50),
    entity_id UUID,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- User preferences table (simplified)
CREATE TABLE user_preferences (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES users(id) UNIQUE,
    language VARCHAR(10) DEFAULT 'es',
    timezone VARCHAR(50) DEFAULT 'America/Mexico_City',
    notification_settings JSONB DEFAULT '{
        "task_reminders": true,
        "daily_summary": true,
        "meeting_alerts": true,
        "dm_notifications": true
    }'::jsonb,
    working_hours JSONB DEFAULT '{
        "start": "09:00",
        "end": "18:00",
        "days": ["monday", "tuesday", "wednesday", "thursday", "friday"]
    }'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create essential indexes
CREATE INDEX idx_users_slack_ids ON users(slack_user_id, slack_workspace_id);
CREATE INDEX idx_conversations_user_id ON conversations(user_id);
CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_tasks_assigned_to ON tasks(assigned_to);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_activity_logs_user_id ON activity_logs(slack_user_id);

-- Create update timestamp function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at columns
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_conversations_updated_at BEFORE UPDATE ON conversations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tasks_updated_at BEFORE UPDATE ON tasks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_preferences_updated_at BEFORE UPDATE ON user_preferences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();