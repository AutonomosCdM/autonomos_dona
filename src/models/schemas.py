"""
Pydantic models for data validation and serialization.

This module defines the data models used throughout the application
for type safety and validation.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List

from pydantic import BaseModel, Field, ConfigDict


class TaskStatus(str, Enum):
    """Enumeration of possible task statuses."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    """Enumeration of task priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class User(BaseModel):
    """User model for Slack users."""
    model_config = ConfigDict(from_attributes=True)
    
    id: Optional[int] = None
    slack_user_id: str
    slack_workspace_id: str
    email: Optional[str] = None
    display_name: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None


class Task(BaseModel):
    """Task model for user tasks."""
    model_config = ConfigDict(from_attributes=True)
    
    id: Optional[int] = None
    user_id: int
    title: str
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def mark_completed(self) -> None:
        """Mark the task as completed."""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()


class TimeEntry(BaseModel):
    """Time entry model for time tracking."""
    model_config = ConfigDict(from_attributes=True)
    
    id: Optional[int] = None
    user_id: int
    task_id: Optional[int] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    description: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    def calculate_duration(self) -> Optional[int]:
        """Calculate duration in seconds if end_time is set."""
        if self.start_time and self.end_time:
            delta = self.end_time - self.start_time
            self.duration_seconds = int(delta.total_seconds())
            return self.duration_seconds
        return None
    
    def stop(self) -> None:
        """Stop the time entry."""
        self.end_time = datetime.utcnow()
        self.is_active = False
        self.calculate_duration()


class TaskCreate(BaseModel):
    """Schema for creating a new task."""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: Optional[datetime] = None


class TaskUpdate(BaseModel):
    """Schema for updating an existing task."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    due_date: Optional[datetime] = None


class TimeEntryCreate(BaseModel):
    """Schema for creating a new time entry."""
    task_id: Optional[int] = None
    description: Optional[str] = Field(None, max_length=500)


class UserStats(BaseModel):
    """User statistics model."""
    total_tasks: int = 0
    completed_tasks: int = 0
    pending_tasks: int = 0
    in_progress_tasks: int = 0
    total_time_today: int = 0  # seconds
    total_time_this_week: int = 0  # seconds
    total_time_this_month: int = 0  # seconds
    active_time_entry: Optional[TimeEntry] = None


class SlackCommand(BaseModel):
    """Schema for Slack slash command data."""
    token: str
    team_id: str
    team_domain: str
    channel_id: str
    channel_name: str
    user_id: str
    user_name: str
    command: str
    text: str
    response_url: str
    trigger_id: str


class SlackEvent(BaseModel):
    """Schema for Slack event data."""
    type: str
    user: Optional[str] = None
    text: Optional[str] = None
    ts: str
    channel: Optional[str] = None
    event_ts: str