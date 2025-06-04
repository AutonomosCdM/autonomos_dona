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

from src.handlers.commands import register_command_handlers
from src.handlers.events import register_event_handlers
from src.services.supabase_client import SupabaseService
from src.utils.config import settings
from src.utils.logger import setup_logging
from src.middleware.logging_middleware import (
    logging_middleware,
    performance_middleware,
    analytics_middleware
)
from src.middleware.rate_limit_middleware import (
    rate_limit_middleware,
    cleanup_rate_limiter
)
from src.utils.metrics_reporter import metrics_reporter
from src.utils.rate_limiter import rate_limiter, RateLimit

# Set up logging
logger = setup_logging()


def add_context_middleware(args, next):
    """Middleware to add context information to requests."""
    # Determine if the interaction is public or private
    event = getattr(args, 'event', None)
    command = getattr(args, 'command', None)
    context = getattr(args, 'context', {})
    
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
    context["is_private"] = is_private
    context["user_id"] = user_id
    
    logger.debug(f"Context: private={is_private}, user={user_id}")
    next()


def create_app(token_verification_enabled=True) -> App:
    """
    Create and configure the Slack Bolt application.
    
    Args:
        token_verification_enabled: Whether to verify the Slack token on startup
    
    Returns:
        App: Configured Slack Bolt application instance
    """
    app = App(
        token=settings.SLACK_BOT_TOKEN,
        signing_secret=settings.SLACK_SIGNING_SECRET,
        token_verification_enabled=token_verification_enabled,
    )
    
    # Add middleware in order (first middleware runs first)
    if settings.RATE_LIMIT_ENABLED:
        app.middleware(rate_limit_middleware)   # Rate limiting (runs first to block early)
    app.middleware(performance_middleware)  # Lightweight performance tracking
    app.middleware(logging_middleware)      # Detailed request logging
    app.middleware(analytics_middleware)    # Analytics collection
    app.middleware(add_context_middleware)  # Context enrichment
    
    # Initialize services
    # TODO: Temporarily disable Supabase completely due to dependency conflicts in production
    logger.info("Supabase temporarily disabled - bot will run without persistent storage (memory only)")
    app._supabase = None  # Set to None to indicate no Supabase
    
    # Configure rate limits from settings
    if settings.RATE_LIMIT_ENABLED:
        rate_limiter.set_rate_limit('user', RateLimit(
            max_tokens=settings.RATE_LIMIT_USER_MAX,
            refill_rate=settings.RATE_LIMIT_USER_MAX / 60,  # Convert per minute to per second
            burst_size=settings.RATE_LIMIT_USER_BURST
        ))
        logger.info(f"Rate limiting enabled: {settings.RATE_LIMIT_USER_MAX} req/min per user")
    
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
        
        # Start background services
        if settings.ENV != "test":  # Don't start in test environment
            metrics_reporter.start()
            logger.info("Metrics reporter started")
            
            # Set up periodic rate limiter cleanup
            if settings.RATE_LIMIT_ENABLED:
                import threading
                def periodic_cleanup():
                    while True:
                        try:
                            cleanup_rate_limiter()
                        except Exception as e:
                            logger.error(f"Error in periodic cleanup: {e}")
                        threading.Event().wait(settings.RATE_LIMIT_CLEANUP_INTERVAL)
                
                cleanup_thread = threading.Thread(target=periodic_cleanup, daemon=True)
                cleanup_thread.start()
                logger.info("Rate limiter cleanup thread started")
        
        # Start the app using Socket Mode
        handler = SocketModeHandler(app, settings.SLACK_APP_TOKEN)
        
        logger.info("Bot is running! Press Ctrl+C to stop.")
        handler.start()
        
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
        metrics_reporter.stop()
    except Exception as e:
        logger.error(f"Error starting bot: {e}", exc_info=True)
        metrics_reporter.stop()
        sys.exit(1)


if __name__ == "__main__":
    main()