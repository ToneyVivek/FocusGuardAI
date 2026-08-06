"""
Conversation Memory for AI Chat

Maintains conversation history for context-aware responses.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class ChatMessage:
    """
    Represents a single message in the conversation.
    """
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for API calls."""
        return {
            "role": self.role,
            "content": self.content
        }


class ConversationMemory:
    """
    Manages conversation history for AI chat sessions.
    
    Stores the last N messages to provide context for the AI.
    Does NOT store analytics data - only conversation history.
    """
    
    def __init__(self, max_messages: int = 8):
        """
        Initialize conversation memory.
        
        Args:
            max_messages: Maximum number of messages to keep in memory
        """
        self.max_messages = max_messages
        self.messages: List[ChatMessage] = []
    
    def add_message(self, role: str, content: str) -> None:
        """
        Add a message to the conversation history.
        
        Args:
            role: Message role ("user" or "assistant")
            content: Message content
        """
        message = ChatMessage(role=role, content=content)
        self.messages.append(message)
        
        # Trim to max_messages
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]
    
    def add_user_message(self, content: str) -> None:
        """
        Add a user message to the conversation.
        
        Args:
            content: User's message content
        """
        self.add_message("user", content)
    
    def add_assistant_message(self, content: str) -> None:
        """
        Add an assistant message to the conversation.
        
        Args:
            content: Assistant's response content
        """
        self.add_message("assistant", content)
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """
        Get the conversation history in API format.
        
        Returns:
            List of message dictionaries with role and content
        """
        return [msg.to_dict() for msg in self.messages]
    
    def get_recent_messages(self, count: int) -> List[Dict[str, str]]:
        """
        Get the most recent N messages.
        
        Args:
            count: Number of recent messages to retrieve
            
        Returns:
            List of recent message dictionaries
        """
        recent = self.messages[-count:] if count < len(self.messages) else self.messages
        return [msg.to_dict() for msg in recent]
    
    def clear(self) -> None:
        """Clear all messages from memory."""
        self.messages.clear()
    
    def message_count(self) -> int:
        """Get the current number of messages in memory."""
        return len(self.messages)
    
    def is_empty(self) -> bool:
        """Check if the conversation memory is empty."""
        return len(self.messages) == 0
    
    def get_last_user_message(self) -> Optional[str]:
        """
        Get the content of the last user message.
        
        Returns:
            Last user message content or None if no user messages exist
        """
        for msg in reversed(self.messages):
            if msg.role == "user":
                return msg.content
        return None
    
    def get_last_assistant_message(self) -> Optional[str]:
        """
        Get the content of the last assistant message.
        
        Returns:
            Last assistant message content or None if no assistant messages exist
        """
        for msg in reversed(self.messages):
            if msg.role == "assistant":
                return msg.content
        return None
