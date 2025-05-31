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