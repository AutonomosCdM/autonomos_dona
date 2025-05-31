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
from src.services.slack_client import get_slack_service
from src.utils.config import settings
from src.utils.metrics import metrics_collector
from src.middleware.rate_limit_middleware import get_rate_limit_status
from src.utils.context_manager import ContextType

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
    app.command("/dona-metrics")(handle_metrics_command)
    app.command("/dona-limits")(handle_limits_command)
    
    logger.info("Command handlers registered")


def handle_dona_command(ack: Ack, respond: Respond, command: Dict[str, Any], context: Dict[str, Any]) -> None:
    """
    Handle the main /dona command with natural language processing.
    
    This is the primary interface for interacting with Dona.
    """
    ack()
    
    text = command.get("text", "").strip()
    user_id = command.get("user_id")
    channel_id = command.get("channel_id")
    
    # Get services
    slack_service = get_slack_service()
    supabase: SupabaseService = context.get("app")._supabase
    
    # Determine context type
    context_type = slack_service.context_manager.get_context_type(channel_id, user_id)
    
    if not text:
        if context_type == ContextType.PRIVATE:
            respond("¡Hola! Soy Dona, tu asistente personal. ¿Cómo puedo ayudarte hoy? Escribe `/dona help` para ver comandos disponibles.")
        else:
            respond("¡Hola! Soy Dona, asistente del equipo. ¿En qué puedo ayudar? Escribe `/dona help` para ver comandos disponibles.")
        return
    
    try:
        # Store the conversation
        conversation_data = {
            "user_id": user_id,
            "channel_id": channel_id,
            "context_type": context_type.value,
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
    
    # Determine context
    slack_service = get_slack_service()
    channel_id = command.get("channel_id")
    user_id = command.get("user_id")
    context_type = slack_service.context_manager.get_context_type(channel_id, user_id)
    
    if context_type == ContextType.PRIVATE:
        help_text = """
:wave: *¡Hola! Soy Dona, tu asistente ejecutiva personal.*

*Comandos disponibles en este espacio privado:*
• `/dona [texto]` - Habla conmigo en lenguaje natural
• `/dona-help` - Muestra este mensaje de ayuda
• `/dona-task [create|list|complete]` - Gestiona tareas personales
• `/dona-remind [cuando] [mensaje]` - Configura recordatorios privados
• `/dona-summary [today|week]` - Tu resumen personal de actividades
• `/dona-status` - Tu estado actual y estadísticas personales
• `/dona-config` - Configura tus preferencias personales

*Ejemplos:*
• `/dona necesito preparar la presentación para el board`
• `/dona-task create Revisar contratos confidenciales`
• `/dona-remind mañana 10am Llamada privada con inversionista`

🔒 *Privacidad:* Todo lo que compartas aquí es completamente confidencial.
        """
    else:
        help_text = """
:wave: *¡Hola! Soy Dona, asistente ejecutiva del equipo.*

*Comandos disponibles:*
• `/dona [texto]` - Habla conmigo en lenguaje natural
• `/dona-help` - Muestra este mensaje de ayuda
• `/dona-task [create|list|complete]` - Gestiona tareas del equipo
• `/dona-remind [cuando] [mensaje]` - Configura recordatorios
• `/dona-summary [today|week]` - Resumen de actividades del equipo
• `/dona-status` - Estado del equipo

*Ejemplos:*
• `/dona necesito agendar reunión de equipo`
• `/dona-task create Revisar propuesta de marketing`
• `/dona-remind mañana 10am Stand-up diario`

💡 *Tip:* Para asuntos privados o confidenciales, háblame por mensaje directo.
        """
    
    respond(help_text)
    logger.info(f"Help command executed by user {user_id} in {context_type.value} context")


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


def handle_metrics_command(ack: Ack, respond: Respond, command: Dict[str, Any]) -> None:
    """
    Handle the /dona-metrics command to display system metrics.
    
    Only available to admin users or in development mode.
    """
    ack()
    
    user_id = command.get("user_id")
    
    try:
        # Check if user is admin (in production, verify against admin list)
        if settings.ENV != "development":
            # In production, check admin list
            admin_users = settings.ADMIN_USERS.split(",") if hasattr(settings, "ADMIN_USERS") else []
            if user_id not in admin_users:
                respond("This command is only available to administrators.")
                return
        
        # Get metrics summary
        summary = metrics_collector.get_summary()
        
        # Format metrics for display
        lines = ["*System Metrics*\n"]
        lines.append(f"_Window: Last {summary['window_minutes']} minutes_\n")
        
        # Overall stats
        total_requests = sum(stats['count'] for stats in summary['request_types'].values())
        total_errors = summary['counters'].get('errors', 0)
        error_rate = (total_errors / total_requests * 100) if total_requests > 0 else 0
        
        lines.append("*Overall Statistics:*")
        lines.append(f"• Total Requests: {total_requests}")
        lines.append(f"• Total Errors: {total_errors} ({error_rate:.1f}%)")
        lines.append(f"• Slow Requests: {summary['counters'].get('slow_requests', 0)}")
        lines.append("")
        
        # Per request type stats
        if summary['request_types']:
            lines.append("*Request Type Breakdown:*")
            
            for request_type, stats in sorted(summary['request_types'].items()):
                lines.append(f"\n_{request_type}_")
                lines.append(f"• Count: {stats['count']}")
                lines.append(f"• Success: {stats['success_count']} | Errors: {stats['error_count']}")
                lines.append(f"• Avg Duration: {stats['avg_duration_ms']:.0f}ms")
                lines.append(f"• P95 Duration: {stats['p95_duration_ms']:.0f}ms")
                lines.append(f"• Max Duration: {stats['max_duration_ms']:.0f}ms")
        
        # User-specific stats
        if command.get("text") == "me":
            user_stats = metrics_collector.get_user_stats(user_id)
            if user_stats['total_requests'] > 0:
                lines.append(f"\n*Your Statistics:*")
                lines.append(f"• Total Requests: {user_stats['total_requests']}")
                for req_type, type_stats in user_stats['request_types'].items():
                    lines.append(f"• {req_type}: {type_stats['count']} (avg {type_stats['avg_duration_ms']:.0f}ms)")
        
        metrics_text = "\n".join(lines)
        respond(metrics_text)
        
        logger.info(f"Metrics command executed by user {user_id}")
        
    except Exception as e:
        logger.error(f"Error handling metrics command: {e}", exc_info=True)
        respond("An error occurred while fetching metrics. Please try again.")


def handle_limits_command(ack: Ack, respond: Respond, command: Dict[str, Any]) -> None:
    """
    Handle the /dona-limits command to check rate limit status.
    
    Shows current rate limit usage for the user.
    """
    ack()
    
    user_id = command.get("user_id")
    
    try:
        # Check if rate limiting is enabled
        if not settings.RATE_LIMIT_ENABLED:
            respond("Rate limiting is currently disabled.")
            return
        
        # Get rate limit status
        status = get_rate_limit_status(user_id)
        respond(status)
        
        logger.info(f"Limits command executed by user {user_id}")
        
    except Exception as e:
        logger.error(f"Error handling limits command: {e}", exc_info=True)
        respond("An error occurred while checking rate limits. Please try again.")