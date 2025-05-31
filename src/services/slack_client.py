"""
Slack client utilities and helper functions.

This module provides utility functions for common Slack operations
and message formatting.
"""

import logging
from typing import Dict, List, Any, Optional

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from src.utils.config import settings

logger = logging.getLogger(__name__)


class SlackService:
    """Service class for Slack-specific operations and utilities."""
    
    def __init__(self):
        """Initialize the Slack Web API client."""
        self.client = WebClient(token=settings.SLACK_BOT_TOKEN)
        logger.info("Slack service initialized")
    
    def get_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user information from Slack.
        
        Args:
            user_id: Slack user ID
            
        Returns:
            User information dict or None if error
        """
        try:
            response = self.client.users_info(user=user_id)
            return response["user"]
        except SlackApiError as e:
            logger.error(f"Error fetching user info: {e}")
            return None
    
    def send_dm(self, user_id: str, text: str, blocks: Optional[List[Dict]] = None) -> bool:
        """
        Send a direct message to a user.
        
        Args:
            user_id: Slack user ID
            text: Message text
            blocks: Optional block kit blocks
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Open a DM channel
            response = self.client.conversations_open(users=[user_id])
            channel_id = response["channel"]["id"]
            
            # Send the message
            self.client.chat_postMessage(
                channel=channel_id,
                text=text,
                blocks=blocks
            )
            return True
            
        except SlackApiError as e:
            logger.error(f"Error sending DM: {e}")
            return False
    
    def post_ephemeral(self, channel: str, user: str, text: str, 
                      blocks: Optional[List[Dict]] = None) -> bool:
        """
        Post an ephemeral message (only visible to one user).
        
        Args:
            channel: Channel ID
            user: User ID
            text: Message text
            blocks: Optional block kit blocks
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.chat_postEphemeral(
                channel=channel,
                user=user,
                text=text,
                blocks=blocks
            )
            return True
            
        except SlackApiError as e:
            logger.error(f"Error posting ephemeral message: {e}")
            return False
    
    @staticmethod
    def format_task_list(tasks: List[Dict[str, Any]]) -> str:
        """
        Format a list of tasks for Slack display.
        
        Args:
            tasks: List of task dictionaries
            
        Returns:
            Formatted string for Slack
        """
        if not tasks:
            return "_No tasks found_"
        
        lines = ["*Your Tasks:*\n"]
        
        for i, task in enumerate(tasks, 1):
            status_emoji = {
                "pending": ":white_circle:",
                "in_progress": ":large_blue_circle:",
                "completed": ":white_check_mark:",
                "cancelled": ":x:"
            }.get(task.get("status", "pending"), ":white_circle:")
            
            title = task.get("title", "Untitled")
            task_id = task.get("id", "")
            
            lines.append(f"{i}. {status_emoji} *{title}* (#{task_id})")
            
            if task.get("description"):
                lines.append(f"   _{task['description']}_")
        
        return "\n".join(lines)
    
    @staticmethod
    def format_time_duration(seconds: int) -> str:
        """
        Format seconds into a human-readable duration.
        
        Args:
            seconds: Number of seconds
            
        Returns:
            Formatted duration string
        """
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        
        parts = []
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0 or hours == 0:
            parts.append(f"{minutes}m")
        
        return " ".join(parts)
    
    @staticmethod
    def create_task_blocks(task: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Create Block Kit blocks for displaying a task.
        
        Args:
            task: Task dictionary
            
        Returns:
            List of Block Kit blocks
        """
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{task.get('title', 'Untitled')}*"
                }
            }
        ]
        
        if task.get("description"):
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": task["description"]
                }
            })
        
        # Add metadata
        fields = []
        if task.get("status"):
            fields.append({
                "type": "mrkdwn",
                "text": f"*Status:* {task['status'].replace('_', ' ').title()}"
            })
        
        if task.get("created_at"):
            fields.append({
                "type": "mrkdwn",
                "text": f"*Created:* <!date^{int(task['created_at'].timestamp())}^{{date_short_pretty}}|{task['created_at'].strftime('%Y-%m-%d')}>"
            })
        
        if fields:
            blocks.append({
                "type": "section",
                "fields": fields
            })
        
        # Add action buttons
        blocks.append({
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Complete"
                    },
                    "action_id": f"complete_task_{task.get('id')}",
                    "style": "primary"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Edit"
                    },
                    "action_id": f"edit_task_{task.get('id')}"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Delete"
                    },
                    "action_id": f"delete_task_{task.get('id')}",
                    "style": "danger"
                }
            ]
        })
        
        return blocks


# Singleton instance
_slack_service: Optional[SlackService] = None


def get_slack_service() -> SlackService:
    """
    Get the singleton Slack service instance.
    
    Returns:
        SlackService instance
    """
    global _slack_service
    if _slack_service is None:
        _slack_service = SlackService()
    return _slack_service