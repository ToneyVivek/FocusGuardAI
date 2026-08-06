"""
Grok (xAI) Provider Implementation

Concrete implementation of BaseAIProvider for xAI's Grok models.
Uses the OpenAI-compatible API from xAI.
"""

import logging
import time
import json
from typing import Dict, Any, Optional
from openai import AsyncOpenAI

from app.ai.providers.base import BaseAIProvider
from app.config.config import settings

logger = logging.getLogger(__name__)


class GrokProvider(BaseAIProvider):
    """
    Grok provider implementation using the xAI OpenAI-compatible API.
    """
    
    def __init__(self):
        """Initialize Grok client with API key from settings."""
        print("GrokProvider initialized")
        self.model_name = settings.GROK_MODEL or "grok-beta"
        print(f"[GROK] Using model: {self.model_name}")
        
        if not settings.GROK_API_KEY:
            logger.warning("GROK_API_KEY not set, Grok provider will not work")
        
        self.client = AsyncOpenAI(
            api_key=settings.GROK_API_KEY,
            base_url="https://api.x.ai/v1"
        )
    
    async def generate_completion(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Generate a text completion using Grok.
        
        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text response
        """
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Grok generate_completion error: {type(e).__name__}: {e}")
            raise
    
    async def generate_structured_completion(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        response_schema: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate a structured JSON completion using Grok.
        
        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            response_schema: Optional JSON schema for response validation
            
        Returns:
            Parsed JSON response
        """
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        # Add JSON formatting instruction
        json_instruction = "Respond with valid JSON only. No markdown, no explanations."
        messages.append({"role": "system", "content": json_instruction})
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            
            # Parse JSON
            try:
                return json.loads(content)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Grok JSON response: {e}")
                logger.error(f"Content: {content}")
                raise ValueError(f"Invalid JSON response from Grok: {e}")
            
        except Exception as e:
            logger.error(f"Grok generate_structured_completion error: {type(e).__name__}: {e}")
            raise
    
    def get_provider_name(self) -> str:
        """Get the provider name."""
        return "grok"
    
    async def health_check(self) -> bool:
        """
        Check if the Grok provider is healthy.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5
            )
            return True
        except Exception as e:
            logger.warning(f"Grok health check failed: {type(e).__name__}")
            return False
