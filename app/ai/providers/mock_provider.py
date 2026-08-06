"""
Mock AI Provider Implementation

Provides predictable, realistic responses for testing without using OpenAI API.
Uses real metrics to generate contextually appropriate responses.
"""

from typing import Dict, Any, Optional

from app.ai.providers.base import BaseAIProvider


class MockAIProvider(BaseAIProvider):
    """
    Mock AI provider for testing and development.
    
    Generates realistic responses based on input metrics without calling
    external APIs. Useful for development and testing.
    """
    
    async def generate_completion(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Generate a mock text completion.
        
        Args:
            prompt: The user prompt (used to extract metrics)
            system_prompt: Optional system prompt
            temperature: Sampling temperature (ignored in mock)
            max_tokens: Maximum tokens (ignored in mock)
            
        Returns:
            Generated mock text completion
        """
        print("Mock provider CALLED")
        # Extract metrics from prompt to generate contextual response
        return self._generate_contextual_response(prompt)
    
    async def generate_structured_completion(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        response_format: Optional[Dict[str, Any]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate a mock structured JSON completion.
        
        Args:
            prompt: The user prompt (used to extract metrics)
            system_prompt: Optional system prompt
            response_format: JSON schema (ignored in mock)
            temperature: Sampling temperature (ignored in mock)
            max_tokens: Maximum tokens (ignored in mock)
            
        Returns:
            Generated mock structured response
        """
        # Return a simple structured response
        return {
            "title": "Mock AI Response",
            "content": self._generate_contextual_response(prompt),
            "type": "mock"
        }
    
    def get_provider_name(self) -> str:
        """Get the name of the AI provider."""
        return "mock"
    
    async def health_check(self) -> bool:
        """
        Check if the Mock provider is healthy (always true).
        
        Returns:
            True (mock provider is always healthy)
        """
        return True
    
    def _generate_contextual_response(self, prompt: str) -> str:
        """
        Generate a contextual response based on prompt metrics.
        
        Args:
            prompt: The prompt containing metrics
            
        Returns:
            Contextual response string
        """
        # Extract key metrics from prompt
        focus_score = self._extract_number(prompt, "Focus Score") or 50  # Default to 50 if not found
        productive_time = self._extract_time(prompt, "Productive Time")
        entertainment_time = self._extract_time(prompt, "Entertainment")
        longest_session = self._extract_number(prompt, "Longest Focus Session") or 30  # Default to 30 if not found
        
        # Generate response based on metrics
        if focus_score >= 80:
            assessment = "excellent"
            tone = "You had a highly productive day with strong focus."
        elif focus_score >= 60:
            assessment = "good"
            tone = "You had a solid day with room for improvement."
        else:
            assessment = "needs improvement"
            tone = "Your productivity was below average today."
        
        response = f"{tone} Your focus score of {focus_score} indicates {assessment} performance. "
        
        if productive_time:
            response += f"You spent {productive_time} on productive tasks. "
        
        if entertainment_time and entertainment_time != "0m":
            response += f"Entertainment time was {entertainment_time}. "
        
        if longest_session > 60:
            response += f"Your longest focus session of {longest_session} minutes shows good deep work capability. "
        
        response += "Keep up the good work and maintain consistent focus habits."
        
        return response
    
    def _extract_number(self, text: str, keyword: str) -> Optional[int]:
        """Extract a number from text after a keyword."""
        try:
            lines = text.split('\n')
            for line in lines:
                if keyword in line:
                    # Extract number from line
                    import re
                    match = re.search(r'\d+', line)
                    if match:
                        return int(match.group())
        except:
            pass
        return None
    
    def _extract_time(self, text: str, keyword: str) -> Optional[str]:
        """Extract time format (e.g., "6h 22m") from text after a keyword."""
        try:
            lines = text.split('\n')
            for line in lines:
                if keyword in line:
                    # Extract time format from line
                    import re
                    match = re.search(r'\d+h\s*\d+m|\d+m|\d+h', line)
                    if match:
                        return match.group()
        except:
            pass
        return None
