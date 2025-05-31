"""
Configuration management using environment variables.

This module handles loading configuration from environment variables
and provides a centralized settings object.
"""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings


# Load environment variables from .env file
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Slack Configuration
    SLACK_BOT_TOKEN: str = Field(..., description="Slack bot OAuth token")
    SLACK_APP_TOKEN: str = Field(..., description="Slack app-level token")
    SLACK_SIGNING_SECRET: str = Field(..., description="Slack signing secret")
    SLACK_BOT_USER_ID: Optional[str] = Field(None, description="Bot user ID (auto-detected)")
    SLACK_WORKSPACE_ID: str = Field("T000000", description="Slack workspace ID")
    
    # Supabase Configuration
    SUPABASE_URL: str = Field(..., description="Supabase project URL")
    SUPABASE_KEY: str = Field(..., description="Supabase anonymous key")
    
    # Application Configuration
    LOG_LEVEL: str = Field("INFO", description="Logging level")
    DEBUG: bool = Field(False, description="Debug mode")
    ENV: str = Field("development", description="Environment (development, test, production)")
    ADMIN_USERS: str = Field("", description="Comma-separated list of admin user IDs")
    
    # Rate Limiting Configuration
    RATE_LIMIT_ENABLED: bool = Field(True, description="Enable rate limiting")
    RATE_LIMIT_USER_MAX: int = Field(60, description="Max requests per user per minute")
    RATE_LIMIT_USER_BURST: int = Field(10, description="Max burst size for user requests")
    RATE_LIMIT_CLEANUP_INTERVAL: int = Field(3600, description="Cleanup interval in seconds")
    
    # Database Tables (for reference)
    DB_TABLE_USERS: str = Field("users", description="Users table name")
    DB_TABLE_TASKS: str = Field("tasks", description="Tasks table name")
    DB_TABLE_TIME_ENTRIES: str = Field("time_entries", description="Time entries table name")
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        
    def validate_settings(self) -> None:
        """Validate that all required settings are present."""
        required_fields = [
            "SLACK_BOT_TOKEN",
            "SLACK_APP_TOKEN",
            "SLACK_SIGNING_SECRET",
            "SUPABASE_URL",
            "SUPABASE_KEY"
        ]
        
        missing_fields = []
        for field in required_fields:
            if not getattr(self, field, None):
                missing_fields.append(field)
        
        if missing_fields:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing_fields)}\n"
                "Please check your .env file."
            )


# Create settings instance
try:
    settings = Settings()
    settings.validate_settings()
except Exception as e:
    print(f"Error loading settings: {e}")
    print("Please ensure all required environment variables are set in your .env file")
    raise


# Export commonly used settings
SLACK_BOT_TOKEN = settings.SLACK_BOT_TOKEN
SLACK_APP_TOKEN = settings.SLACK_APP_TOKEN
SLACK_SIGNING_SECRET = settings.SLACK_SIGNING_SECRET
SUPABASE_URL = settings.SUPABASE_URL
SUPABASE_KEY = settings.SUPABASE_KEY