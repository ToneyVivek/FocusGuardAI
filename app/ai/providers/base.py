"""
Base AI Provider Interface

Abstract base class for AI providers (OpenAI, Gemini, etc.).
This allows switching between AI providers without changing the service layer.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class BaseAIProvider(ABC):
    """
    Abstract base class for AI providers.
    
    All AI providers must implement these methods to ensure
    consistent interface across different LLM backends.
    """
    
    @abstractmethod
    async def generate_completion(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Generate a text completion from the AI provider.
        
        Args:
            prompt: The user prompt to send to the AI
            system_prompt: Optional system prompt to guide AI behavior
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text completion
        """
        pass
    
    @abstractmethod
    async def generate_structured_completion(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        response_format: Optional[Dict[str, Any]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate a structured JSON completion from the AI provider.
        
        Args:
            prompt: The user prompt to send to the AI
            system_prompt: Optional system prompt to guide AI behavior
            response_format: JSON schema for structured output
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated structured response as dictionary
        """
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """
        Get the name of the AI provider.
        
        Returns:
            Provider name (e.g., "openai", "gemini")
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if the AI provider is healthy and accessible.
        
        Returns:
            True if healthy, False otherwise
        """
        pass
