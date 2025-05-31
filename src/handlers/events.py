"""
Event handlers for the Autónomos Dona Slack bot.

This module contains handlers for various Slack events such as
messages, reactions, and app mentions.
"""

import logging
from datetime import datetime
from typing import Dict, Any

from slack_bolt import App, BoltContext
from slack_sdk.web import SlackResponse

from src.models.schemas import ConversationContext
from src.services.supabase_client import SupabaseService
from src.services.slack_client import SlackService, get_slack_service
from src.services.llm_service import get_llm_service
from src.utils.config import settings
from src.utils.context_manager import ContextType

logger = logging.getLogger(__name__)


def register_event_handlers(app: App) -> None:
    """
    Register all event handlers with the Slack app.
    
    Args:
        app: The Slack Bolt application instance
    """
    app.event("app_mention")(handle_app_mention)
    app.event("message")(handle_message)
    app.event("reaction_added")(handle_reaction_added)
    app.event("app_home_opened")(handle_app_home_opened)
    
    logger.info("Event handlers registered")


def handle_app_mention(event: Dict[str, Any], say: Any, context: BoltContext) -> None:
    """
    Handle when the bot is mentioned in a channel.
    
    Args:
        event: The event data from Slack
        say: Function to send a message to the channel
    """
    try:
        user = event.get("user")
        text = event.get("text", "")
        channel = event.get("channel")
        
        # Get services
        slack_service = get_slack_service()
        app = context.get("app") or context.get("client")
        supabase: SupabaseService = app._supabase if hasattr(app, '_supabase') else None
        
        # Determine context type
        context_type = slack_service.context_manager.get_context_type(channel, user)
        privacy_level = slack_service.context_manager.get_privacy_level(context_type)
        
        # Log the conversation
        conversation = None
        if supabase:
            try:
                conversation = supabase.get_or_create_conversation(
                    channel_id=channel,
                    user_id=user,
                    context_type=context_type.value,
                    thread_ts=event.get("thread_ts")
                )
                
                # Log the user's message
                supabase.log_message({
                    "conversation_id": conversation["id"],
                    "sender_type": "user",
                    "sender_id": user,
                    "content": text,
                    "slack_message_ts": event.get("ts"),
                    "metadata": {"event_type": "app_mention"}
                })
                
                # Log activity
                supabase.log_activity({
                    "slack_user_id": user,
                    "activity_type": "app_mention",
                    "entity_type": "conversation",
                    "entity_id": conversation["id"],
                    "metadata": {"channel": channel, "context_type": context_type.value}
                })
            except Exception as e:
                logger.error(f"Error logging conversation: {e}")
        
        # Remove the bot mention from the text
        bot_mention = f"<@{context.get('bot_user_id')}>"
        clean_text = text.replace(bot_mention, "").strip()
        
        # Use LLM for intelligent processing
        response_message = None
        intent_detected = None
        
        try:
            llm_service = get_llm_service()
            
            # Get conversation history for context
            conversation_history = []
            if conversation and supabase:
                try:
                    messages = supabase.get_conversation_messages(conversation["id"], limit=5)
                    for msg in messages[-4:]:  # Last 4 messages for context
                        role = "assistant" if msg.get("sender_type") == "bot" else "user"
                        conversation_history.append({
                            "role": role,
                            "content": msg.get("content", "")
                        })
                except Exception as e:
                    logger.warning(f"Could not get conversation history: {e}")
            
            # Extract intent
            intent_data = llm_service.extract_intent(clean_text)
            intent_detected = intent_data.get("intent", "unknown")
            
            # Generate intelligent response with context awareness
            user_context = {
                "user_id": user,
                "channel_id": channel,
                "context_type": context_type.value,
                "intent": intent_data,
                "is_mention": True
            }
            
            llm_response = llm_service.generate_response(
                user_message=clean_text,
                conversation_context=conversation_history,
                user_context=user_context
            )
            
            # Add user mention to response
            response_message = f"<@{user}>, {llm_response}"
            say(response_message)
            
        except Exception as e:
            logger.error(f"Error processing mention with LLM: {e}")
            # Fallback to simple response
            intent_detected = "fallback"
            response_message = (
                f"<@{user}>, escuché: _{clean_text}_\n\n"
                "Estoy procesando tu mensaje. Usa `/dona-help` para ver comandos disponibles."
            )
            say(response_message)
        
        # Log Dona's response
        if supabase and conversation and response_message:
            try:
                supabase.log_message({
                    "conversation_id": conversation["id"],
                    "sender_type": "dona",
                    "sender_id": context.get('bot_user_id', 'dona'),
                    "content": response_message,
                    "intent_detected": intent_detected,
                    "metadata": {"response_to": event.get("ts")}
                })
            except Exception as e:
                logger.error(f"Error logging bot response: {e}")
            
        logger.info(f"App mention handled for user {user} with intent: {intent_detected}")
        
    except Exception as e:
        logger.error(f"Error handling app mention: {e}", exc_info=True)


def handle_message(event: Dict[str, Any], say: Any, context: BoltContext) -> None:
    """
    Handle direct messages to the bot.
    
    Args:
        event: The event data from Slack
        say: Function to send a message
    """
    # Only handle DMs, not channel messages
    if event.get("channel_type") != "im":
        return
    
    # Ignore bot's own messages
    if event.get("bot_id"):
        return
    
    try:
        user = event.get("user")
        text = event.get("text", "")
        
        # Get Supabase service
        app = context.get("app") or context.get("client")
        supabase: SupabaseService = app._supabase if hasattr(app, '_supabase') else None
        
        # Log DM conversation
        conversation = None
        if supabase:
            try:
                conversation = supabase.get_or_create_conversation(
                    channel_id=event.get("channel"),
                    user_id=user,
                    context_type="private",
                    thread_ts=event.get("thread_ts")
                )
                
                # Log the user's message
                supabase.log_message({
                    "conversation_id": conversation["id"],
                    "sender_type": "user",
                    "sender_id": user,
                    "content": text,
                    "slack_message_ts": event.get("ts"),
                    "metadata": {"event_type": "direct_message"}
                })
                
                # Log activity
                supabase.log_activity({
                    "slack_user_id": user,
                    "activity_type": "direct_message",
                    "entity_type": "conversation",
                    "entity_id": conversation["id"],
                    "metadata": {"message_length": len(text)}
                })
            except Exception as e:
                logger.error(f"Error logging DM conversation: {e}")
        
        # Use LLM for intelligent DM processing
        try:
            llm_service = get_llm_service()
            
            # Get conversation history for context
            conversation_history = []
            if conversation and supabase:
                try:
                    messages = supabase.get_conversation_messages(conversation["id"], limit=5)
                    for msg in messages[-4:]:  # Last 4 messages for context
                        role = "assistant" if msg.get("sender_type") == "bot" else "user"
                        conversation_history.append({
                            "role": role,
                            "content": msg.get("content", "")
                        })
                except Exception as e:
                    logger.warning(f"Could not get conversation history: {e}")
            
            # Extract intent
            intent_data = llm_service.extract_intent(text)
            
            # Generate intelligent response for private context
            user_context = {
                "user_id": user,
                "channel_id": event.get("channel"),
                "context_type": "private",
                "intent": intent_data,
                "is_direct_message": True
            }
            
            llm_response = llm_service.generate_response(
                user_message=text,
                conversation_context=conversation_history,
                user_context=user_context
            )
            
            say(llm_response)
            
            # Log the LLM interaction
            if supabase and conversation:
                try:
                    supabase.log_message({
                        "conversation_id": conversation["id"],
                        "sender_type": "bot",
                        "sender_id": "dona",
                        "content": llm_response,
                        "metadata": {
                            "intent": intent_data,
                            "llm_model": settings.GROQ_MODEL,
                            "processing_type": "llm",
                            "event_type": "direct_message_response"
                        }
                    })
                except Exception as e:
                    logger.error(f"Error logging LLM response: {e}")
                    
        except Exception as e:
            logger.error(f"Error processing DM with LLM: {e}")
            # Fallback to friendly response
            say(
                "¡Hola! Recibí tu mensaje. Estoy procesando tu solicitud...\n\n"
                "Mientras tanto, puedes usar:\n"
                "• `/dona [tu solicitud]` - Para solicitudes generales\n"
                "• `/dona-help` - Ver todos los comandos disponibles"
            )
            
        logger.info(f"Direct message handled for user {user}")
        
    except Exception as e:
        logger.error(f"Error handling message: {e}", exc_info=True)


def handle_reaction_added(event: Dict[str, Any]) -> None:
    """
    Handle when a reaction is added to a message.
    
    This can be used to trigger actions based on specific reactions.
    
    Args:
        event: The event data from Slack
    """
    try:
        user = event.get("user")
        reaction = event.get("reaction")
        
        # Example: Track when tasks are marked as done with ✅
        if reaction == "white_check_mark":
            # TODO: Implement task completion logic
            logger.info(f"Task potentially completed by {user}")
        
        logger.debug(f"Reaction {reaction} added by user {user}")
        
    except Exception as e:
        logger.error(f"Error handling reaction: {e}", exc_info=True)


def handle_app_home_opened(event: Dict[str, Any], client: Any) -> None:
    """
    Handle when a user opens the app home tab.
    
    Args:
        event: The event data from Slack
        client: Slack Web API client
    """
    try:
        user_id = event.get("user")
        
        # Build the home tab view
        home_view = {
            "type": "home",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "Welcome to Autónomos Dona! :house:",
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*Your Dashboard*\n\nHere's your productivity overview:"
                    }
                },
                {
                    "type": "divider"
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*Today's Stats*\n"
                               "• Tasks completed: 3/5\n"
                               "• Time tracked: 4h 30m\n"
                               "• Current task: Reviewing PR #123"
                    }
                },
                {
                    "type": "divider"
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*Quick Actions*"
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "Create Task"
                            },
                            "action_id": "create_task_button",
                            "style": "primary"
                        },
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "Start Timer"
                            },
                            "action_id": "start_timer_button"
                        },
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "View Tasks"
                            },
                            "action_id": "view_tasks_button"
                        }
                    ]
                }
            ]
        }
        
        # Publish the view
        client.views_publish(
            user_id=user_id,
            view=home_view
        )
        
        logger.info(f"App home opened by user {user_id}")
        
    except Exception as e:
        logger.error(f"Error handling app home: {e}", exc_info=True)