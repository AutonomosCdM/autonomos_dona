"""
Context manager for handling public vs private interactions.

This module provides utilities to determine and manage the context
of Slack interactions (public channels vs private messages/channels).
"""

import logging
from typing import Dict, Any, Optional, Tuple
from enum import Enum

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

logger = logging.getLogger(__name__)


class ContextType(Enum):
    """Types of conversation contexts."""
    PUBLIC = "public"
    PRIVATE = "private"
    UNKNOWN = "unknown"


class ContextManager:
    """Manages context determination for Slack interactions."""
    
    def __init__(self, slack_client: WebClient):
        """
        Initialize the context manager.
        
        Args:
            slack_client: Slack Web API client
        """
        self.client = slack_client
        self._channel_cache: Dict[str, Dict[str, Any]] = {}
    
    def get_context_type(self, channel_id: str, user_id: Optional[str] = None) -> ContextType:
        """
        Determine if a conversation is public or private.
        
        Args:
            channel_id: Slack channel ID
            user_id: Optional user ID for DM detection
            
        Returns:
            ContextType enum value
        """
        try:
            # Check if it's a DM (starts with D)
            if channel_id.startswith('D'):
                return ContextType.PRIVATE
            
            # Check if it's a private channel (starts with G)
            if channel_id.startswith('G'):
                return ContextType.PRIVATE
            
            # Get channel info from cache or API
            channel_info = self._get_channel_info(channel_id)
            
            if not channel_info:
                return ContextType.UNKNOWN
            
            # Check channel properties
            if channel_info.get('is_private', False):
                return ContextType.PRIVATE
            
            if channel_info.get('is_im', False) or channel_info.get('is_mpim', False):
                return ContextType.PRIVATE
            
            # Public channel
            return ContextType.PUBLIC
            
        except Exception as e:
            logger.error(f"Error determining context type: {e}")
            return ContextType.UNKNOWN
    
    def _get_channel_info(self, channel_id: str) -> Optional[Dict[str, Any]]:
        """
        Get channel information from cache or API.
        
        Args:
            channel_id: Slack channel ID
            
        Returns:
            Channel information dict or None
        """
        # Check cache first
        if channel_id in self._channel_cache:
            return self._channel_cache[channel_id]
        
        try:
            # Try to get channel info
            response = self.client.conversations_info(channel=channel_id)
            if response['ok']:
                channel_info = response['channel']
                self._channel_cache[channel_id] = channel_info
                return channel_info
                
        except SlackApiError as e:
            if e.response['error'] == 'channel_not_found':
                # Might be a DM, try conversations.open
                try:
                    response = self.client.conversations_open(channel=channel_id)
                    if response['ok']:
                        channel_info = response['channel']
                        channel_info['is_im'] = True
                        self._channel_cache[channel_id] = channel_info
                        return channel_info
                except:
                    pass
            
            logger.error(f"Error getting channel info: {e}")
        
        return None
    
    def should_log_interaction(self, context_type: ContextType) -> bool:
        """
        Determine if an interaction should be logged based on context.
        
        Args:
            context_type: The type of context
            
        Returns:
            True if interaction should be logged
        """
        # Always log everything for traceability
        return True
    
    def get_privacy_level(self, context_type: ContextType) -> str:
        """
        Get the privacy level for a given context.
        
        Args:
            context_type: The type of context
            
        Returns:
            Privacy level string
        """
        if context_type == ContextType.PRIVATE:
            return "confidential"
        elif context_type == ContextType.PUBLIC:
            return "team"
        else:
            return "unknown"
    
    def format_response(self, message: str, context_type: ContextType, 
                       user_id: Optional[str] = None) -> str:
        """
        Format a response based on context type.
        
        Args:
            message: The message to format
            context_type: The type of context
            user_id: Optional user ID for personalization
            
        Returns:
            Formatted message
        """
        if context_type == ContextType.PRIVATE:
            # More personal tone in private
            if user_id:
                return f"<@{user_id}>, {message}"
            return message
        else:
            # More formal tone in public
            return message
    
    def get_allowed_commands(self, context_type: ContextType, user_id: str) -> Dict[str, bool]:
        """
        Get allowed commands based on context and user.
        
        Args:
            context_type: The type of context
            user_id: User ID
            
        Returns:
            Dict of command names to permission booleans
        """
        # Base commands available in all contexts
        base_commands = {
            "help": True,
            "status": True,
            "task": True,
            "remind": True,
            "summary": True,
        }
        
        # Private context allows more sensitive commands
        if context_type == ContextType.PRIVATE:
            base_commands.update({
                "config": True,
                "personal": True,
                "sensitive": True,
                "report": True,
            })
        
        return base_commands
    
    def clear_cache(self) -> None:
        """Clear the channel information cache."""
        self._channel_cache.clear()
        logger.info("Context manager cache cleared")