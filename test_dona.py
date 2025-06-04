#!/usr/bin/env python3
"""Simple test script for Dona bot credentials."""

import os
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

# Load environment variables (force reload)
load_dotenv(override=True)

def main():
    print("🤖 Testing Dona Bot Credentials...")
    
    # Get tokens
    bot_token = os.getenv("SLACK_BOT_TOKEN")
    app_token = os.getenv("SLACK_APP_TOKEN")
    
    print(f"Bot Token: {bot_token[:30]}...")
    print(f"App Token: {app_token[:30]}...")
    
    try:
        # Create simple app
        app = App(token=bot_token)
        
        @app.message("hello")
        def handle_message(message, say):
            say(f"Hello <@{message['user']}>!")
        
        # Start Socket Mode
        handler = SocketModeHandler(app, app_token)
        print("✅ Dona bot started successfully!")
        handler.start()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()