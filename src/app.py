"""
Main application entry point for the Autónomos Dona Slack bot.

This module initializes the Slack app, registers handlers,
and starts the bot server.
"""

import logging
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_bolt.middleware import MiddlewareArgs
from slack_bolt.middleware.custom import CustomMiddleware

from src.handlers.commands import register_command_handlers
from src.handlers.events import register_event_handlers
from src.services.supabase_client import SupabaseService
from src.utils.config import settings
from src.utils.logger import setup_logging

# Set up logging
logger = setup_logging()


class ContextMiddleware(CustomMiddleware):
    """Middleware to add context information to requests."""
    
    def process(self, *, args: MiddlewareArgs, next):
        # Determine if the interaction is public or private
        event = args.get("event", {})
        command = args.get("command", {})
        
        # For DMs, channel_type is 'im'
        is_private = False
        user_id = None
        
        if event:
            is_private = event.get("channel_type") == "im"
            user_id = event.get("user")
        elif command:
            # For slash commands, check channel_name
            is_private = command.get("channel_name") == "directmessage"
            user_id = command.get("user_id")
        
        # Add context to args
        args["context"]["is_private"] = is_private
        args["context"]["user_id"] = user_id
        
        logger.debug(f"Context: private={is_private}, user={user_id}")
        next()


def create_app() -> App:
    """
    Create and configure the Slack Bolt application.
    
    Returns:
        App: Configured Slack Bolt application instance
    """
    app = App(
        token=settings.SLACK_BOT_TOKEN,
        signing_secret=settings.SLACK_SIGNING_SECRET,
    )
    
    # Add custom middleware
    app.middleware(ContextMiddleware())
    
    # Initialize services
    supabase_service = SupabaseService()
    app._supabase = supabase_service  # Store as app attribute for access in handlers
    
    # Register handlers
    register_command_handlers(app)
    register_event_handlers(app)
    
    logger.info("Slack app created with middleware and handlers registered")
    return app


def main():
    """Main function to start the bot."""
    try:
        logger.info("Starting Autónomos Dona Slack bot...")
        
        # Create the app
        app = create_app()
        
        # Start the app using Socket Mode
        handler = SocketModeHandler(app, settings.SLACK_APP_TOKEN)
        
        logger.info("Bot is running! Press Ctrl+C to stop.")
        handler.start()
        
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Error starting bot: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()