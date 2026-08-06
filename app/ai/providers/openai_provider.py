"""
OpenAI Provider Implementation

Concrete implementation of BaseAIProvider for OpenAI's GPT models.
"""

import logging
import time
import json
from typing import Dict, Any, Optional
from openai import AsyncOpenAI
from openai import APITimeoutError, RateLimitError, APIConnectionError

from app.ai.providers.base import BaseAIProvider
from app.config.config import settings

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseAIProvider):
    """
    OpenAI provider implementation using the OpenAI API.
    """
    
    def __init__(self):
        """Initialize OpenAI client with API key from settings."""
        self.client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
            timeout=settings.AI_REQUEST_TIMEOUT
        )
        self.model = settings.OPENAI_MODEL or "gpt-4o-mini"
    
    async def generate_completion(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Generate a text completion using OpenAI.
        
        Args:
            prompt: The user prompt to send to the AI
            system_prompt: Optional system prompt to guide AI behavior
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text completion
        """
        start_time = time.time()
        
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            latency = time.time() - start_time
            tokens_used = response.usage.total_tokens if response.usage else 0
            
            logger.info(
                f"OpenAI completion success - model: {self.model}, "
                f"tokens: {tokens_used}, latency: {latency:.2f}s"
            )
            
            return response.choices[0].message.content or ""
            
        except APITimeoutError as e:
            latency = time.time() - start_time
            logger.error(
                f"OpenAI timeout error - model: {self.model}, "
                f"latency: {latency:.2f}s, error: {str(e)}"
            )
            raise
            
        except RateLimitError as e:
            latency = time.time() - start_time
            logger.error(
                f"OpenAI rate limit error - model: {self.model}, "
                f"latency: {latency:.2f}s, error: {str(e)}"
            )
            raise
            
        except APIConnectionError as e:
            latency = time.time() - start_time
            logger.error(
                f"OpenAI connection error - model: {self.model}, "
                f"latency: {latency:.2f}s, error: {str(e)}"
            )
            raise
            
        except Exception as e:
            latency = time.time() - start_time
            logger.error(
                f"OpenAI API error - model: {self.model}, "
                f"latency: {latency:.2f}s, error: {str(e)}"
            )
            raise
    
    async def generate_structured_completion(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        response_format: Optional[Dict[str, Any]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate a structured JSON completion using OpenAI.
        
        Args:
            prompt: The user prompt to send to the AI
            system_prompt: Optional system prompt to guide AI behavior
            response_format: JSON schema for structured output
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated structured response as dictionary
        """
        start_time = time.time()
        
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format={"type": "json_object"} if response_format else None
            )
            
            latency = time.time() - start_time
            tokens_used = response.usage.total_tokens if response.usage else 0
            
            logger.info(
                f"OpenAI structured completion success - model: {self.model}, "
                f"tokens: {tokens_used}, latency: {latency:.2f}s"
            )
            
            content = response.choices[0].message.content or "{}"
            return json.loads(content)
            
        except json.JSONDecodeError as e:
            latency = time.time() - start_time
            logger.error(
                f"OpenAI JSON parsing error - model: {self.model}, "
                f"latency: {latency:.2f}s, error: {str(e)}"
            )
            raise ValueError(f"Failed to parse JSON response: {e}")
            
        except APITimeoutError as e:
            latency = time.time() - start_time
            logger.error(
                f"OpenAI timeout error - model: {self.model}, "
                f"latency: {latency:.2f}s, error: {str(e)}"
            )
            raise
            
        except RateLimitError as e:
            latency = time.time() - start_time
            logger.error(
                f"OpenAI rate limit error - model: {self.model}, "
                f"latency: {latency:.2f}s, error: {str(e)}"
            )
            raise
            
        except APIConnectionError as e:
            latency = time.time() - start_time
            logger.error(
                f"OpenAI connection error - model: {self.model}, "
                f"latency: {latency:.2f}s, error: {str(e)}"
            )
            raise
            
        except Exception as e:
            latency = time.time() - start_time
            logger.error(
                f"OpenAI structured completion error - model: {self.model}, "
                f"latency: {latency:.2f}s, error: {str(e)}"
            )
            raise
    
    def get_provider_name(self) -> str:
        """Get the name of the AI provider."""
        return "openai"
    
    async def health_check(self) -> bool:
        """
        Check if the OpenAI provider is healthy.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5
            )
            return True
        except Exception as e:
            logger.warning(f"OpenAI health check failed: {type(e).__name__}")
            return False
