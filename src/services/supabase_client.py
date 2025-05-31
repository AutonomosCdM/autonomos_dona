"""
Supabase client service for database operations.

This module provides a service class for interacting with Supabase,
handling all database operations for the Autónomos Dona bot.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from supabase import create_client, Client

from src.utils.config import settings
from src.models.schemas import Task, TimeEntry, User

logger = logging.getLogger(__name__)


class SupabaseService:
    """Service class for Supabase database operations."""
    
    def __init__(self):
        """Initialize the Supabase client."""
        try:
            self.client: Client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_KEY
            )
            logger.info("Supabase client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            raise
    
    # User operations
    def get_or_create_user(self, slack_user_id: str, slack_workspace_id: str) -> Dict[str, Any]:
        """
        Get or create a user in the database.
        
        Args:
            slack_user_id: Slack user ID
            slack_workspace_id: Slack workspace ID
            
        Returns:
            User data dictionary
        """
        try:
            # Check if user exists
            result = self.client.table("users").select("*").eq(
                "slack_user_id", slack_user_id
            ).eq(
                "slack_workspace_id", slack_workspace_id
            ).execute()
            
            if result.data:
                return result.data[0]
            
            # Create new user
            new_user = {
                "slack_user_id": slack_user_id,
                "slack_workspace_id": slack_workspace_id,
                "created_at": datetime.utcnow().isoformat()
            }
            
            result = self.client.table("users").insert(new_user).execute()
            logger.info(f"Created new user: {slack_user_id}")
            return result.data[0]
            
        except Exception as e:
            logger.error(f"Error in get_or_create_user: {e}", exc_info=True)
            raise
    
    # Task operations
    def create_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new task.
        
        Args:
            task_data: Task information including assigned_to, description, etc.
            
        Returns:
            Created task data
        """
        try:
            task = {
                "assigned_to": task_data.get("assigned_to"),
                "created_by": task_data.get("created_by"),
                "description": task_data.get("description"),
                "status": task_data.get("status", "pending"),
                "priority": task_data.get("priority", "medium"),
                "channel_id": task_data.get("channel_id"),
                "created_at": datetime.utcnow().isoformat()
            }
            
            result = self.client.table("tasks").insert(task).execute()
            logger.info(f"Created task for user {task_data.get('assigned_to')}")
            return result.data[0]
            
        except Exception as e:
            logger.error(f"Error creating task: {e}", exc_info=True)
            raise
    
    def get_user_tasks(self, user_id: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get tasks for a user.
        
        Args:
            user_id: Slack user ID
            status: Optional task status filter
            
        Returns:
            List of tasks
        """
        try:
            query = self.client.table("tasks").select("*").eq("assigned_to", user_id)
            
            if status:
                query = query.eq("status", status)
            
            result = query.order("created_at", desc=True).execute()
            return result.data
            
        except Exception as e:
            logger.error(f"Error fetching tasks: {e}", exc_info=True)
            raise
    
    def update_task(self, task_id: int, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update a task.
        
        Args:
            task_id: Task ID
            updates: Fields to update
            
        Returns:
            Updated task data
        """
        try:
            updates["updated_at"] = datetime.utcnow().isoformat()
            
            result = self.client.table("tasks").update(updates).eq(
                "id", task_id
            ).execute()
            
            logger.info(f"Updated task {task_id}")
            return result.data[0]
            
        except Exception as e:
            logger.error(f"Error updating task: {e}", exc_info=True)
            raise
    
    # Conversation and message operations
    def create_conversation(self, conversation_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new conversation record.
        
        Args:
            conversation_data: Conversation information
            
        Returns:
            Created conversation data
        """
        try:
            # Get user ID from slack_user_id
            user = self.get_or_create_user(
                conversation_data["user_id"],
                conversation_data.get("slack_workspace_id", settings.SLACK_WORKSPACE_ID)
            )
            
            conversation = {
                "slack_channel_id": conversation_data["slack_channel_id"],
                "slack_thread_ts": conversation_data.get("slack_thread_ts"),
                "user_id": user["id"],
                "context_type": conversation_data["context_type"],
                "status": conversation_data.get("status", "active"),
                "created_at": datetime.utcnow().isoformat()
            }
            
            result = self.client.table("conversations").insert(conversation).execute()
            logger.info(f"Created conversation in channel {conversation_data['slack_channel_id']}")
            return result.data[0]
            
        except Exception as e:
            logger.error(f"Error creating conversation: {e}", exc_info=True)
            raise
    
    def get_or_create_conversation(self, channel_id: str, user_id: str, 
                                   context_type: str, thread_ts: Optional[str] = None) -> Dict[str, Any]:
        """
        Get existing conversation or create new one.
        
        Args:
            channel_id: Slack channel ID
            user_id: Slack user ID
            context_type: 'public' or 'private'
            thread_ts: Optional thread timestamp
            
        Returns:
            Conversation data
        """
        try:
            # Get database user
            user = self.get_or_create_user(user_id, settings.SLACK_WORKSPACE_ID)
            
            # Look for existing active conversation
            query = self.client.table("conversations").select("*").eq(
                "slack_channel_id", channel_id
            ).eq("user_id", user["id"]).eq("status", "active")
            
            if thread_ts:
                query = query.eq("slack_thread_ts", thread_ts)
            
            result = query.execute()
            
            if result.data:
                return result.data[0]
            
            # Create new conversation
            return self.create_conversation({
                "slack_channel_id": channel_id,
                "slack_thread_ts": thread_ts,
                "user_id": user_id,
                "context_type": context_type
            })
            
        except Exception as e:
            logger.error(f"Error in get_or_create_conversation: {e}", exc_info=True)
            raise
    
    def log_message(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Log a message in a conversation.
        
        Args:
            message_data: Message information including conversation_id, content, etc.
            
        Returns:
            Created message data
        """
        try:
            message = {
                "conversation_id": message_data["conversation_id"],
                "sender_type": message_data["sender_type"],
                "sender_id": message_data["sender_id"],
                "content": message_data["content"],
                "slack_message_ts": message_data.get("slack_message_ts"),
                "intent_detected": message_data.get("intent_detected"),
                "metadata": message_data.get("metadata", {}),
                "created_at": datetime.utcnow().isoformat()
            }
            
            result = self.client.table("messages").insert(message).execute()
            logger.debug(f"Logged {message_data['sender_type']} message in conversation {message_data['conversation_id']}")
            return result.data[0]
            
        except Exception as e:
            logger.error(f"Error logging message: {e}", exc_info=True)
            raise
    
    def log_activity(self, activity_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Log an activity for analytics.
        
        Args:
            activity_data: Activity information
            
        Returns:
            Created activity log data
        """
        try:
            # Get user ID if slack_user_id is provided
            user_id = activity_data.get("user_id")
            if activity_data.get("slack_user_id") and not user_id:
                user = self.get_or_create_user(
                    activity_data["slack_user_id"],
                    settings.SLACK_WORKSPACE_ID
                )
                user_id = user["id"]
            
            activity = {
                "user_id": user_id,
                "activity_type": activity_data["activity_type"],
                "entity_type": activity_data.get("entity_type"),
                "entity_id": activity_data.get("entity_id"),
                "metadata": activity_data.get("metadata", {}),
                "created_at": datetime.utcnow().isoformat()
            }
            
            result = self.client.table("activity_logs").insert(activity).execute()
            return result.data[0]
            
        except Exception as e:
            logger.error(f"Error logging activity: {e}", exc_info=True)
            raise
    
    # Time tracking operations
    def start_time_entry(self, user_id: int, task_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Start a new time entry.
        
        Args:
            user_id: Database user ID
            task_id: Optional task ID to track time against
            
        Returns:
            Created time entry
        """
        try:
            # End any active time entries first
            self.stop_active_time_entries(user_id)
            
            entry = {
                "user_id": user_id,
                "task_id": task_id,
                "start_time": datetime.utcnow().isoformat(),
                "is_active": True
            }
            
            result = self.client.table("time_entries").insert(entry).execute()
            logger.info(f"Started time entry for user {user_id}")
            return result.data[0]
            
        except Exception as e:
            logger.error(f"Error starting time entry: {e}", exc_info=True)
            raise
    
    def stop_active_time_entries(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Stop all active time entries for a user.
        
        Args:
            user_id: Database user ID
            
        Returns:
            List of stopped time entries
        """
        try:
            # Get active entries
            active_entries = self.client.table("time_entries").select("*").eq(
                "user_id", user_id
            ).eq("is_active", True).execute()
            
            if not active_entries.data:
                return []
            
            # Stop each active entry
            stopped_entries = []
            end_time = datetime.utcnow().isoformat()
            
            for entry in active_entries.data:
                result = self.client.table("time_entries").update({
                    "end_time": end_time,
                    "is_active": False
                }).eq("id", entry["id"]).execute()
                
                stopped_entries.append(result.data[0])
            
            logger.info(f"Stopped {len(stopped_entries)} time entries for user {user_id}")
            return stopped_entries
            
        except Exception as e:
            logger.error(f"Error stopping time entries: {e}", exc_info=True)
            raise
    
    def get_user_time_entries(self, user_id: int, start_date: Optional[datetime] = None,
                              end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Get time entries for a user within a date range.
        
        Args:
            user_id: Database user ID
            start_date: Optional start date filter
            end_date: Optional end date filter
            
        Returns:
            List of time entries
        """
        try:
            query = self.client.table("time_entries").select("*").eq("user_id", user_id)
            
            if start_date:
                query = query.gte("start_time", start_date.isoformat())
            
            if end_date:
                query = query.lte("start_time", end_date.isoformat())
            
            result = query.order("start_time", desc=True).execute()
            return result.data
            
        except Exception as e:
            logger.error(f"Error fetching time entries: {e}", exc_info=True)
            raise


# Singleton instance
_supabase_service: Optional[SupabaseService] = None


def get_supabase_service() -> SupabaseService:
    """
    Get the singleton Supabase service instance.
    
    Returns:
        SupabaseService instance
    """
    global _supabase_service
    if _supabase_service is None:
        _supabase_service = SupabaseService()
    return _supabase_service