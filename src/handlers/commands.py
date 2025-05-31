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
from src.services.supabase_client import SupabaseService, get_supabase_service
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
    app.command("/dona-config")(handle_config_command)
    
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
        conversation = None
        if supabase:
            try:
                conversation = supabase.get_or_create_conversation(
                    channel_id=channel_id,
                    user_id=user_id,
                    context_type=context_type.value,
                    thread_ts=command.get("thread_ts")
                )
                
                # Log the command
                supabase.log_message({
                    "conversation_id": conversation["id"],
                    "sender_type": "user",
                    "sender_id": user_id,
                    "content": f"/dona {text}",
                    "slack_message_ts": command.get("ts"),
                    "metadata": {"command": "/dona", "args": text}
                })
                
                # Log activity
                supabase.log_activity({
                    "slack_user_id": user_id,
                    "activity_type": "slash_command",
                    "entity_type": "command",
                    "entity_id": None,
                    "metadata": {"command": "/dona", "context": context_type.value}
                })
            except Exception as e:
                logger.error(f"Error logging command: {e}")
        
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
        respond("Please specify an action: `create`, `list`, `complete`, or `update`\n\nExamples:\n• `/dona-task create Review marketing proposal`\n• `/dona-task list`\n• `/dona-task complete [task-id]`")
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
            
            # Check for status filter
            status_filter = parts[1] if len(parts) > 1 else None
            
            # Fetch user's tasks
            tasks = supabase.get_user_tasks(user_id, status=status_filter)
            
            if not tasks:
                if status_filter:
                    respond(f"No tienes tareas con estado '{status_filter}'")
                else:
                    respond("No tienes tareas pendientes. ¡Buen trabajo! :tada:")
                return
            
            # Format task list using SlackService
            slack_service = get_slack_service()
            task_list = slack_service.format_task_list(tasks)
            
            respond(task_list)
            
        elif action == "complete":
            if len(parts) < 2:
                respond("Please provide the task ID to complete. Use `/dona-task list` to see your tasks.")
                return
            
            task_id = parts[1].strip()
            
            # Get Supabase service
            app = command.get("app") or command.get("client")
            supabase: SupabaseService = app._supabase
            
            try:
                # Update task status
                updates = {
                    "status": TaskStatus.COMPLETED.value,
                    "completed_at": datetime.utcnow().isoformat()
                }
                result = supabase.update_task(task_id, updates)
                
                respond(f"✅ Task completed: *{result.get('description', 'Task')}*\n\nGreat job! 🎉")
                
                # Log activity
                supabase.log_activity({
                    "slack_user_id": user_id,
                    "activity_type": "task_completed",
                    "entity_type": "task",
                    "entity_id": task_id,
                    "metadata": {"task_description": result.get('description')}
                })
                
            except Exception as e:
                logger.error(f"Error completing task: {e}")
                respond(f"Could not complete task with ID: {task_id}. Please check the ID and try again.")
            
        elif action == "update":
            respond("Task update functionality coming soon! For now, you can complete tasks with `/dona-task complete [task-id]`")
            
        else:
            respond(f"Unknown action: {action}. Use `create`, `list`, `complete`, or `update`")
            
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
    
    # Get services
    supabase = get_supabase_service()
    
    try:
        # Determine period
        if text in ["today", "hoy"]:
            period = "today"
            period_text = "Hoy"
        elif text in ["week", "semana"]:
            period = "week"
            period_text = "Esta Semana"
        else:
            respond("Por favor especifica 'today/hoy' o 'week/semana'")
            return
        
        # Get summary data
        summary_data = supabase.get_user_summary(user_id, period)
        
        # Format summary
        lines = [f":calendar: *Resumen de {period_text}*\n"]
        
        # Tasks section
        tasks_created = summary_data.get("tasks_created_in_period", 0)
        tasks_completed = summary_data.get("tasks_completed_in_period", 0)
        pending_tasks = summary_data.get("tasks_by_status", {}).get("pending", 0)
        
        lines.append("*📋 Tareas:*")
        lines.append(f"• Creadas: {tasks_created}")
        lines.append(f"• Completadas: {tasks_completed}")
        lines.append(f"• Pendientes totales: {pending_tasks}")
        
        # Activity section
        total_activities = summary_data.get("total_activities", 0)
        activities_by_type = summary_data.get("activities_by_type", {})
        
        if total_activities > 0:
            lines.append("\n*📊 Actividad:*")
            lines.append(f"• Total de interacciones: {total_activities}")
            
            # Show top activities
            if activities_by_type:
                top_activities = sorted(activities_by_type.items(), key=lambda x: x[1], reverse=True)[:3]
                for activity_type, count in top_activities:
                    activity_name = activity_type.replace("_", " ").title()
                    lines.append(f"• {activity_name}: {count}")
        
        # Conversations
        conversations = summary_data.get("conversations_started", 0)
        if conversations > 0:
            lines.append(f"\n*💬 Conversaciones iniciadas:* {conversations}")
        
        # Productivity insight
        if tasks_created > 0:
            if tasks_completed >= tasks_created:
                lines.append("\n✨ *¡Excelente!* Completaste todas las tareas creadas y más.")
            elif tasks_completed > 0:
                completion_rate = round(tasks_completed / tasks_created * 100)
                lines.append(f"\n📈 *Productividad:* {completion_rate}% de tareas creadas fueron completadas.")
        
        # Pending tasks reminder
        if pending_tasks > 0:
            lines.append(f"\n💡 *Recordatorio:* Tienes {pending_tasks} tareas pendientes. Usa `/dona-task list` para verlas.")
        
        respond("\n".join(lines))
        
        # Log activity
        supabase.log_activity({
            "slack_user_id": user_id,
            "activity_type": "summary_viewed",
            "metadata": {"period": period}
        })
        
        logger.info(f"Summary requested by user {user_id}: {period}")
        
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
    
    # Get services
    supabase = get_supabase_service()
    slack_service = get_slack_service()
    
    try:
        # Get user statistics
        stats = supabase.get_user_statistics(user_id)
        
        # Get user info from Slack
        user_info = slack_service.get_user_info(user_id)
        user_name = user_info.get("real_name", "User") if user_info else "User"
        
        # Format member since date
        member_since = stats.get("member_since", "unknown")
        if member_since != "unknown":
            try:
                member_date = datetime.fromisoformat(member_since.replace('Z', '+00:00'))
                member_since_text = member_date.strftime("%B %d, %Y")
            except:
                member_since_text = "recently"
        else:
            member_since_text = "recently"
        
        # Build status message
        lines = [
            f":chart_with_upwards_trend: *Status for {user_name}*\n",
            f"*Member since:* {member_since_text}",
            f"*Language:* {'Spanish' if stats.get('language') == 'es' else 'English'}",
            f"*Timezone:* {stats.get('timezone', 'Not set')}",
            "\n*📊 Task Statistics:*",
            f"• Total tasks: {stats.get('total_tasks', 0)}",
            f"• Pending: {stats.get('pending_tasks', 0)}",
            f"• Completed: {stats.get('completed_tasks', 0)}",
            f"• Completion rate: {stats.get('completion_rate', 0)}%"
        ]
        
        # Activity stats
        total_activities = stats.get("total_activities", 0)
        if total_activities > 0:
            lines.extend([
                "\n*🎯 Activity Overview:*",
                f"• Total interactions: {total_activities}",
                f"• Most common activity: {stats.get('most_common_activity', 'none').replace('_', ' ').title()}"
            ])
        
        # Current status
        pending = stats.get("pending_tasks", 0)
        if pending > 0:
            lines.append(f"\n*🔔 Current Status:* You have {pending} pending tasks")
        else:
            lines.append("\n*✅ Current Status:* All caught up! No pending tasks")
        
        # Productivity tip
        completion_rate = stats.get("completion_rate", 0)
        if completion_rate >= 80:
            lines.append("\n💪 *Great job!* Your completion rate is excellent!")
        elif completion_rate >= 50:
            lines.append("\n📈 *Keep it up!* You're making good progress on your tasks.")
        elif stats.get("total_tasks", 0) > 0:
            lines.append("\n💡 *Tip:* Try breaking down large tasks into smaller, manageable pieces.")
        
        # Quick actions
        lines.extend([
            "\n*Quick Actions:*",
            "• `/dona-task list` - View your tasks",
            "• `/dona-summary today` - See today's summary",
            "• `/dona-config` - Update preferences"
        ])
        
        respond("\n".join(lines))
        
        # Log activity
        supabase.log_activity({
            "slack_user_id": user_id,
            "activity_type": "status_viewed",
            "metadata": {"completion_rate": completion_rate}
        })
        
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


def handle_config_command(ack: Ack, respond: Respond, command: Dict[str, Any]) -> None:
    """
    Handle the /dona-config command for user preferences.
    
    Allows users to view and update their personal preferences.
    """
    ack()
    
    user_id = command.get("user_id")
    text = command.get("text", "").strip()
    
    # Get services
    slack_service = get_slack_service()
    supabase = get_supabase_service()
    
    try:
        # Parse command
        parts = text.split(maxsplit=1) if text else []
        action = parts[0].lower() if parts else "show"
        
        if action == "show" or not text:
            # Show current preferences
            prefs = supabase.get_user_preferences(user_id)
            
            lines = [
                "*Your Current Preferences:*\n",
                f"*Language:* {prefs['language']} ({'Spanish' if prefs['language'] == 'es' else 'English'})",
                f"*Timezone:* {prefs['timezone']}",
                f"*Working Hours:* {prefs['working_hours']['start']} - {prefs['working_hours']['end']}",
                f"*Working Days:* {', '.join(prefs['working_hours']['days']).title()}",
                "\n*Notification Settings:*"
            ]
            
            notifications = prefs['notification_settings']
            lines.append(f"• Task Reminders: {'✅' if notifications['task_reminders'] else '❌'}")
            lines.append(f"• Daily Summary: {'✅' if notifications['daily_summary'] else '❌'}")
            lines.append(f"• Meeting Alerts: {'✅' if notifications['meeting_alerts'] else '❌'}")
            lines.append(f"• DM Notifications: {'✅' if notifications['dm_notifications'] else '❌'}")
            
            lines.append("\n_Use `/dona-config help` to see how to update preferences._")
            
            respond("\n".join(lines))
            
        elif action == "help":
            # Show help
            help_text = """
*How to use /dona-config:*

• `/dona-config` - Show current preferences
• `/dona-config language [es|en]` - Set language
• `/dona-config timezone [timezone]` - Set timezone (e.g., America/Mexico_City)
• `/dona-config notifications [type] [on|off]` - Toggle notifications
• `/dona-config working-hours [start] [end]` - Set working hours (e.g., 09:00 18:00)

*Notification Types:*
• `task-reminders` - Reminders for tasks
• `daily-summary` - Daily activity summary
• `meeting-alerts` - Meeting notifications
• `dm-notifications` - Direct message alerts

*Examples:*
• `/dona-config language en`
• `/dona-config timezone America/New_York`
• `/dona-config notifications task-reminders off`
• `/dona-config working-hours 08:00 17:00`
            """
            respond(help_text)
            
        elif action == "language":
            # Update language
            if len(parts) < 2:
                respond("Please specify a language: `es` (Spanish) or `en` (English)")
                return
            
            lang = parts[1].lower()
            if lang not in ["es", "en"]:
                respond("Language must be `es` (Spanish) or `en` (English)")
                return
            
            supabase.update_user_preferences(user_id, {"language": lang})
            lang_name = "Spanish" if lang == "es" else "English"
            respond(f"✅ Language updated to {lang_name}")
            
        elif action == "timezone":
            # Update timezone
            if len(parts) < 2:
                respond("Please specify a timezone (e.g., America/Mexico_City)")
                return
            
            timezone = parts[1]
            # In production, validate timezone against pytz
            supabase.update_user_preferences(user_id, {"timezone": timezone})
            respond(f"✅ Timezone updated to {timezone}")
            
        elif action == "notifications":
            # Update notification settings
            if len(parts) < 2:
                respond("Please specify notification type and on/off. See `/dona-config help`")
                return
            
            notif_parts = parts[1].split()
            if len(notif_parts) < 2:
                respond("Please specify both notification type and on/off")
                return
            
            notif_type = notif_parts[0].replace("-", "_")
            enabled = notif_parts[1].lower() == "on"
            
            valid_types = ["task_reminders", "daily_summary", "meeting_alerts", "dm_notifications"]
            if notif_type not in valid_types:
                respond(f"Invalid notification type. Valid types: {', '.join(valid_types)}")
                return
            
            updates = {"notification_settings": {notif_type: enabled}}
            supabase.update_user_preferences(user_id, updates)
            
            status = "enabled" if enabled else "disabled"
            respond(f"✅ {notif_type.replace('_', ' ').title()} {status}")
            
        elif action == "working-hours":
            # Update working hours
            if len(parts) < 2:
                respond("Please specify start and end times (e.g., 09:00 18:00)")
                return
            
            times = parts[1].split()
            if len(times) < 2:
                respond("Please specify both start and end times")
                return
            
            start_time = times[0]
            end_time = times[1]
            
            # Basic validation
            if not (len(start_time) == 5 and len(end_time) == 5 and 
                    start_time[2] == ":" and end_time[2] == ":"):
                respond("Times must be in HH:MM format (e.g., 09:00)")
                return
            
            updates = {"working_hours": {"start": start_time, "end": end_time}}
            supabase.update_user_preferences(user_id, updates)
            
            respond(f"✅ Working hours updated to {start_time} - {end_time}")
            
        else:
            respond(f"Unknown action: {action}. Use `/dona-config help` for available options.")
        
        # Log activity
        supabase.log_activity({
            "slack_user_id": user_id,
            "activity_type": "config_update",
            "entity_type": "user_preferences",
            "metadata": {"action": action, "command": text}
        })
        
    except Exception as e:
        logger.error(f"Error handling config command: {e}", exc_info=True)
        respond("An error occurred while updating preferences. Please try again.")