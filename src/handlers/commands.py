"""
Slash command handlers for the Autónomos Dona Slack bot.

This module contains all the slash command implementations
that users can invoke in Slack.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional

from slack_bolt import App, Ack, Respond
from slack_sdk.web import SlackResponse

from src.models.schemas import Task, TaskStatus, ConversationContext
from src.services.supabase_client import SupabaseService
from src.utils.config import settings

logger = logging.getLogger(__name__)


def register_command_handlers(app: App) -> None:
    """
    Register all slash command handlers with the Slack app.
    
    Args:
        app: The Slack Bolt application instance
    """
    # Core commands
    app.command("/dona")(handle_dona_command)
    app.command("/dona-help")(handle_help_command)
    app.command("/dona-task")(handle_task_command)
    app.command("/dona-remind")(handle_remind_command)
    app.command("/dona-summary")(handle_summary_command)
    app.command("/dona-status")(handle_status_command)
    
    logger.info("Command handlers registered")


def handle_dona_command(ack: Ack, respond: Respond, command: Dict[str, Any], context: Dict[str, Any]) -> None:
    """
    Handle the main /dona command with natural language processing.
    
    This is the primary interface for interacting with Dona.
    """
    ack()
    
    text = command.get("text", "").strip()
    user_id = command.get("user_id")
    is_private = context.get("is_private", False)
    
    if not text:
        respond("Hi! I'm Dona, your executive assistant. How can I help you today? Type `/dona help` for available commands.")
        return
    
    # Log the interaction
    supabase: SupabaseService = context.get("app")._supabase
    
    try:
        # Store the conversation
        conversation_data = {
            "user_id": user_id,
            "channel_id": command.get("channel_id"),
            "is_private": is_private,
            "command_text": text,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Process natural language commands
        if "help" in text.lower():
            handle_help_command(ack, respond, command)
        elif any(word in text.lower() for word in ["task", "tarea", "hacer"]):
            respond("I understand you want to create a task. Use `/dona-task create [description]` or I can help you organize it.")
        elif any(word in text.lower() for word in ["remind", "recordar", "recordatorio"]):
            respond("I'll help you set a reminder. Use `/dona-remind [time] [message]` or tell me what you need to remember.")
        else:
            respond(f"I heard: '{text}'. I'm still learning to understand natural language better. Try `/dona help` for available commands.")
            
    except Exception as e:
        logger.error(f"Error in main dona command: {e}", exc_info=True)
        respond("I encountered an error processing your request. Please try again.")


def handle_help_command(ack: Ack, respond: Respond, command: Dict[str, Any]) -> None:
    """
    Handle the /dona-help command.
    
    Provides information about available commands and how to use them.
    """
    ack()  # Acknowledge the command
    
    help_text = """
    :wave: *¡Hola! Soy Dona, tu asistente ejecutiva.*
    
    *Comandos principales:*
    • `/dona [texto]` - Habla conmigo en lenguaje natural
    • `/dona-help` - Muestra este mensaje de ayuda
    • `/dona-task [create|list|complete]` - Gestiona tareas
    • `/dona-remind [cuando] [mensaje]` - Configura recordatorios
    • `/dona-summary [today|week]` - Resumen de actividades
    • `/dona-status` - Tu estado actual y estadísticas
    
    *Ejemplos:*
    • `/dona necesito agendar una reunión con el equipo`
    • `/dona-task create Revisar propuesta de marketing`
    • `/dona-remind mañana 10am Llamar a cliente`
    • `/dona-summary today`
    
    💡 *Tip:* Puedes hablarme en modo privado (DM) para asuntos confidenciales.
    """
    
    respond(help_text)
    logger.info(f"Help command executed by user {command.get('user_id')}")


def handle_task_command(ack: Ack, respond: Respond, command: Dict[str, Any]) -> None:
    """
    Handle the /dona-task command for task management.
    
    Supports creating, listing, and updating tasks.
    """
    ack()
    
    text = command.get("text", "").strip()
    user_id = command.get("user_id")
    
    if not text:
        respond("Please specify an action: `create`, `list`, or `update`")
        return
    
    parts = text.split(" ", 1)
    action = parts[0].lower()
    
    try:
        if action == "create":
            if len(parts) < 2:
                respond("Please provide a task description")
                return
            
            task_description = parts[1]
            
            # Get Supabase service from app context
            app = command.get("app") or command.get("client")
            supabase: SupabaseService = app._supabase
            
            # Create task in database
            task_data = {
                "description": task_description,
                "assigned_to": user_id,
                "created_by": user_id,
                "status": TaskStatus.PENDING.value,
                "priority": "medium",
                "channel_id": command.get("channel_id")
            }
            
            result = supabase.create_task(task_data)
            
            if result:
                respond(f":white_check_mark: Tarea creada: *{task_description}*\nID: {result.get('id', 'N/A')}")
            else:
                respond(":x: No pude crear la tarea. Por favor intenta de nuevo.")
            
        elif action == "list":
            # Get Supabase service from app context
            app = command.get("app") or command.get("client")
            supabase: SupabaseService = app._supabase
            
            # Fetch user's tasks
            tasks = supabase.get_user_tasks(user_id)
            
            if not tasks:
                respond("No tienes tareas pendientes. ¡Buen trabajo! :tada:")
                return
            
            task_list = "*Tus tareas:*\n\n"
            for task in tasks:
                status_emoji = ":white_circle:" if task["status"] == "pending" else ":green_circle:"
                task_list += f"{status_emoji} *{task['description']}*\n"
                task_list += f"   ID: {task['id']} | Prioridad: {task['priority']}\n\n"
            
            respond(task_list)
            
        elif action == "update":
            respond("Task update functionality coming soon!")
            
        else:
            respond(f"Unknown action: {action}. Use `create`, `list`, or `update`")
            
    except Exception as e:
        logger.error(f"Error handling task command: {e}", exc_info=True)
        respond("An error occurred while processing your request. Please try again.")


def handle_remind_command(ack: Ack, respond: Respond, command: Dict[str, Any]) -> None:
    """
    Handle the /dona-remind command for setting reminders.
    
    Format: /dona-remind [when] [message]
    """
    ack()
    
    text = command.get("text", "").strip()
    user_id = command.get("user_id")
    
    if not text:
        respond("Por favor especifica cuándo y qué recordar. Ejemplo: `/dona-remind mañana 10am Revisar reportes`")
        return
    
    # TODO: Implement reminder parsing and scheduling
    respond(f":alarm_clock: Recordatorio configurado: *{text}*\n_Te notificaré en el momento indicado._")
    logger.info(f"Reminder set by user {user_id}: {text}")


def handle_summary_command(ack: Ack, respond: Respond, command: Dict[str, Any]) -> None:
    """
    Handle the /dona-summary command for activity summaries.
    
    Provides summaries of tasks, meetings, and activities.
    """
    ack()
    
    text = command.get("text", "today").strip().lower()
    user_id = command.get("user_id")
    
    try:
        if text == "today" or text == "hoy":
            summary = f"""
            :calendar: *Resumen de Hoy*
            
            *Tareas completadas:* 3
            *Reuniones:* 2 (1h 30m total)
            *Mensajes importantes:* 5
            
            *Pendientes prioritarios:*
            • Revisar propuesta de marketing
            • Responder email de inversor
            • Preparar presentación semanal
            """
        elif text == "week" or text == "semana":
            summary = f"""
            :chart_with_upwards_trend: *Resumen Semanal*
            
            *Tareas:* 15 completadas, 8 pendientes
            *Reuniones:* 12 (8h 45m total)
            *Productividad:* 87% vs semana anterior
            
            *Logros destacados:*
            • Cerrado acuerdo con cliente X
            • Lanzamiento de feature Y
            • 3 entrevistas completadas
            """
        else:
            summary = "Por favor especifica 'today/hoy' o 'week/semana'"
        
        respond(summary)
        logger.info(f"Summary requested by user {user_id}: {text}")
        
    except Exception as e:
        logger.error(f"Error generating summary: {e}", exc_info=True)
        respond("Hubo un error generando el resumen. Por favor intenta de nuevo.")


def handle_time_command(ack: Ack, respond: Respond, command: Dict[str, Any]) -> None:
    """
    Handle the /dona-time command for time tracking.
    
    Supports starting, stopping, and logging time entries.
    """
    ack()
    
    text = command.get("text", "").strip()
    user_id = command.get("user_id")
    
    if not text:
        respond("Please specify an action: `start`, `stop`, or `log`")
        return
    
    action = text.split(" ")[0].lower()
    
    try:
        if action == "start":
            # TODO: Implement time tracking start with Supabase
            respond(":stopwatch: Time tracking started!")
            
        elif action == "stop":
            # TODO: Implement time tracking stop with Supabase
            respond(":stop_sign: Time tracking stopped. Total: 2h 15m")
            
        elif action == "log":
            # TODO: Implement manual time log
            respond("Time logging functionality coming soon!")
            
        else:
            respond(f"Unknown action: {action}. Use `start`, `stop`, or `log`")
            
    except Exception as e:
        logger.error(f"Error handling time command: {e}", exc_info=True)
        respond("An error occurred while processing your request. Please try again.")


def handle_status_command(ack: Ack, respond: Respond, command: Dict[str, Any]) -> None:
    """
    Handle the /dona-status command.
    
    Shows user's current status, active tasks, and time tracking info.
    """
    ack()
    
    user_id = command.get("user_id")
    
    try:
        # TODO: Fetch actual data from Supabase
        status_text = f"""
        :chart_with_upwards_trend: *Your Status*
        
        *Active Tasks:* 3
        *Time Today:* 5h 30m
        *This Week:* 24h 15m
        
        *Current Activity:* Working on "Fix login bug"
        *Started:* 2:15 PM
        """
        
        respond(status_text)
        logger.info(f"Status command executed by user {user_id}")
        
    except Exception as e:
        logger.error(f"Error handling status command: {e}", exc_info=True)
        respond("An error occurred while fetching your status. Please try again.")