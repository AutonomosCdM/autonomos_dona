"""
Rate limiting middleware for Slack commands.

This middleware enforces rate limits on commands to prevent
abuse and ensure fair usage of the bot.
"""

import logging
from typing import Dict, Any, Callable

from slack_bolt import Ack, Respond

from src.utils.rate_limiter import rate_limiter
from src.utils.metrics import metrics_collector

logger = logging.getLogger(__name__)


def rate_limit_middleware(args: Dict[str, Any], next: Callable) -> None:
    """
    Middleware to enforce rate limits on commands.
    
    Checks rate limits before allowing command execution.
    Responds with appropriate error messages when limits are exceeded.
    """
    # Only apply to commands
    command = args.get("command")
    if not command:
        next()
        return
    
    user_id = command.get("user_id")
    command_name = command.get("command")
    
    if not user_id:
        logger.warning("Command without user_id, allowing through")
        next()
        return
    
    # Check rate limit
    allowed, limit_info = rate_limiter.check_rate_limit(
        user_id=user_id,
        command=f"command:{command_name}"
    )
    
    if allowed:
        # Request allowed, continue
        next()
    else:
        # Rate limit exceeded
        _handle_rate_limit_exceeded(args, limit_info)


def _handle_rate_limit_exceeded(args: Dict[str, Any], limit_info: Dict[str, Any]) -> None:
    """Handle rate limit exceeded scenario."""
    ack: Ack = args.get("ack")
    respond: Respond = args.get("respond")
    command = args.get("command", {})
    
    # Acknowledge immediately
    if ack:
        ack()
    
    # Record metrics
    metrics_collector.record_request(
        request_type=f"command:{command.get('command', 'unknown')}",
        duration_ms=0,
        status="rate_limited",
        user_id=command.get("user_id", "unknown"),
        metadata={
            "limit_type": limit_info.get("limit_type"),
            "retry_after": limit_info.get("retry_after", 0)
        }
    )
    
    # Log the rate limit hit
    logger.warning(
        f"Rate limit exceeded for user {command.get('user_id')} "
        f"on command {command.get('command')} "
        f"(type: {limit_info.get('limit_type')})"
    )
    
    # Craft user-friendly error message
    retry_after = limit_info.get("retry_after", 60)
    retry_minutes = max(1, int(retry_after / 60))
    
    if limit_info.get("limit_type") == "global":
        message = (
            "⚠️ El sistema está experimentando mucho tráfico en este momento. "
            f"Por favor, intenta de nuevo en {retry_minutes} minuto{'s' if retry_minutes > 1 else ''}."
        )
    elif limit_info.get("limit_type") == "command":
        command_name = limit_info.get("command", "").replace("command:", "")
        message = (
            f"⏱️ Has usado el comando `{command_name}` demasiadas veces. "
            f"Por favor, espera {retry_minutes} minuto{'s' if retry_minutes > 1 else ''} antes de usarlo de nuevo."
        )
    else:  # user limit
        message = (
            "🚦 Has alcanzado el límite de solicitudes. "
            f"Por favor, espera {retry_minutes} minuto{'s' if retry_minutes > 1 else ''} antes de continuar. "
            "\n\n_Tip: Puedes agrupar múltiples tareas en un solo comando._"
        )
    
    # Send response
    if respond:
        respond(message)


def cleanup_rate_limiter() -> None:
    """
    Periodic cleanup function for rate limiter.
    Should be called periodically to prevent memory growth.
    """
    try:
        removed = rate_limiter.cleanup_old_buckets()
        if removed > 0:
            logger.info(f"Rate limiter cleanup: removed {removed} old buckets")
    except Exception as e:
        logger.error(f"Error during rate limiter cleanup: {e}", exc_info=True)


def get_rate_limit_status(user_id: str, command: str = None) -> str:
    """
    Get formatted rate limit status for a user.
    
    Args:
        user_id: User ID to check
        command: Optional command to check
        
    Returns:
        Formatted status message
    """
    info = rate_limiter.get_limit_info(user_id, command)
    
    lines = ["*📊 Rate Limit Status*\n"]
    
    # User limit
    if "user_limit" in info:
        user_limit = info["user_limit"]
        tokens_pct = (user_limit["tokens_remaining"] / user_limit["max_tokens"]) * 100
        
        lines.append(f"*User Limit:*")
        lines.append(f"• Remaining: {user_limit['tokens_remaining']}/{user_limit['max_tokens']} ({tokens_pct:.0f}%)")
        lines.append(f"• Refill rate: {user_limit['refill_rate'] * 60:.0f} requests/min\n")
    
    # Command limit
    if "command_limit" in info:
        cmd_limit = info["command_limit"]
        tokens_pct = (cmd_limit["tokens_remaining"] / cmd_limit["max_tokens"]) * 100
        
        lines.append(f"*Command Limit ({cmd_limit['command']}):*")
        lines.append(f"• Remaining: {cmd_limit['tokens_remaining']}/{cmd_limit['max_tokens']} ({tokens_pct:.0f}%)")
        lines.append(f"• Refill rate: {cmd_limit['refill_rate'] * 60:.0f} requests/min")
    
    return "\n".join(lines)