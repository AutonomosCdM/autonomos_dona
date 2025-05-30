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
from src.services.slack_client import SlackService
from src.utils.config import settings

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
        is_private = context.get("is_private", False)
        
        # Get Supabase service
        app = context.get("app") or context.get("client")
        supabase: SupabaseService = app._supabase if hasattr(app, '_supabase') else None
        
        # Log the conversation
        if supabase:
            conversation_data = {
                "slack_channel_id": channel,
                "user_id": user,
                "context_type": "private" if is_private else "public",
                "status": "active"
            }
            # TODO: Create conversation record
        
        # Remove the bot mention from the text
        bot_mention = f"<@{context.get('bot_user_id')}>"
        clean_text = text.replace(bot_mention, "").strip()
        
        # Process natural language
        if any(word in clean_text.lower() for word in ["help", "ayuda", "como"]):
            say(
                f"¡Hola <@{user}>! :wave:\n"
                "Soy Dona, tu asistente ejecutiva. Puedo ayudarte con:\n"
                "• `/dona` - Habla conmigo en lenguaje natural\n"
                "• `/dona-task create [descripción]` - Crear tareas\n"
                "• `/dona-remind [cuándo] [mensaje]` - Configurar recordatorios\n"
                "• `/dona-summary` - Ver resumen de actividades"
            )
        elif any(word in clean_text.lower() for word in ["task", "tarea", "hacer"]):
            say(
                f"<@{user}>, para crear una tarea usa:\n"
                "`/dona-task create [descripción]`\n\n"
                "O simplemente dime qué necesitas hacer con `/dona necesito...`"
            )
        elif any(word in clean_text.lower() for word in ["meeting", "reunión", "agendar"]):
            say(
                f"<@{user}>, pronto podré ayudarte a agendar reuniones. "
                "Por ahora, puedo crear recordatorios con:\n"
                "`/dona-remind [cuándo] [mensaje]`"
            )
        else:
            say(
                f"<@{user}>, escuché: _{clean_text}_\n\n"
                "Estoy aprendiendo a entender mejor el lenguaje natural. "
                "Por ahora, usa `/dona` seguido de tu solicitud o `/dona-help` para ver comandos disponibles."
            )
            
        logger.info(f"App mention handled for user {user}")
        
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
        if supabase:
            conversation_data = {
                "slack_channel_id": event.get("channel"),
                "user_id": user,
                "context_type": "private",
                "status": "active"
            }
            # TODO: Create conversation and message records
        
        # Natural language processing for DMs
        text_lower = text.lower()
        
        if any(greeting in text_lower for greeting in ["hola", "hello", "hi", "buenos días", "buenas tardes"]):
            say(
                f"¡Hola <@{user}>! :wave:\n\n"
                "Soy Dona, tu asistente ejecutiva personal. ¿En qué puedo ayudarte hoy?\n\n"
                "Puedes pedirme cosas como:\n"
                "• _'Necesito crear una tarea para...'_\n"
                "• _'Recuérdame mañana a las 10am...'_\n"
                "• _'¿Cuáles son mis tareas pendientes?'_\n"
                "• _'Muéstrame mi resumen del día'_"
            )
        elif any(word in text_lower for word in ["tarea", "task", "hacer", "necesito"]):
            say(
                "Entiendo que necesitas gestionar una tarea. Te ayudaré con eso.\n\n"
                "Por ahora, usa: `/dona-task create [descripción]`\n\n"
                "Pronto podré entender tus solicitudes de forma más natural. 🚀"
            )
        elif any(word in text_lower for word in ["recordar", "recordatorio", "remind", "avísame"]):
            say(
                "Claro, te ayudaré con el recordatorio.\n\n"
                "Usa: `/dona-remind [cuándo] [mensaje]`\n\n"
                "Ejemplo: `/dona-remind mañana 10am Llamar al cliente`"
            )
        elif any(word in text_lower for word in ["resumen", "summary", "status", "estado"]):
            say(
                "Para ver tu resumen de actividades, usa:\n\n"
                "• `/dona-summary today` - Resumen de hoy\n"
                "• `/dona-summary week` - Resumen semanal\n"
                "• `/dona-status` - Tu estado actual"
            )
        else:
            say(
                "Recibí tu mensaje. Aunque todavía estoy aprendiendo a procesar lenguaje natural, "
                "aquí están los comandos que puedes usar:\n\n"
                "• `/dona [solicitud]` - Intenta entender tu pedido\n"
                "• `/dona-help` - Ver todos los comandos\n"
                "• `/dona-task` - Gestionar tareas\n"
                "• `/dona-remind` - Crear recordatorios\n\n"
                "_💡 Tip: En nuestras conversaciones privadas, puedes compartir información confidencial conmigo._"
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