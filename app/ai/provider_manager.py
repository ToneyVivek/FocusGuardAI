"""
Provider Manager with Automatic Failover

Manages multiple AI providers with automatic key rotation and failover.
"""

import logging
import time
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from app.ai.providers.base import BaseAIProvider
from app.ai.providers.gemini_provider import GeminiProvider
from app.ai.providers.grok_provider import GrokProvider
from app.ai.providers.openai_provider import OpenAIProvider
from app.ai.providers.mock_provider import MockAIProvider
from app.config.config import settings

logger = logging.getLogger(__name__)


class ProviderStats:
    """Statistics for a single provider."""
    
    def __init__(self, provider_name: str):
        self.provider_name = provider_name
        self.successful_requests = 0
        self.failed_requests = 0
        self.quota_failures = 0
        self.latencies: List[float] = []
        self.healthy = True
        self.last_health_check: Optional[datetime] = None
    
    def record_success(self, latency: float):
        """Record a successful request."""
        self.successful_requests += 1
        self.latencies.append(latency)
        # Keep only last 100 latencies
        if len(self.latencies) > 100:
            self.latencies = self.latencies[-100:]
    
    def record_failure(self, is_quota_error: bool = False):
        """Record a failed request."""
        self.failed_requests += 1
        if is_quota_error:
            self.quota_failures += 1
    
    def get_average_latency_ms(self) -> float:
        """Get average latency in milliseconds."""
        if not self.latencies:
            return 0.0
        return (sum(self.latencies) / len(self.latencies)) * 1000
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert stats to dictionary."""
        return {
            "name": self.provider_name,
            "healthy": self.healthy,
            "requests": self.successful_requests + self.failed_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "quota_failures": self.quota_failures,
            "average_latency_ms": round(self.get_average_latency_ms(), 2)
        }


class ProviderManager:
    """
    Manages AI providers with automatic failover and key rotation.
    
    This is the only place responsible for choosing providers.
    AIService must never instantiate providers directly.
    """
    
    # Error codes that trigger key rotation (not retry)
    ROTATION_ERROR_CODES = [429, 401, 403]
    
    # Health check cache duration
    HEALTH_CHECK_CACHE_SECONDS = 300  # 5 minutes
    
    def __init__(self):
        """Initialize the provider manager."""
        self.providers: Dict[str, BaseAIProvider] = {}
        self.stats: Dict[str, ProviderStats] = {}
        self.provider_order = settings.provider_order_list
        self.gemini_keys = settings.gemini_api_keys_list
        self.current_gemini_key_index = 0
        self.current_provider_index = 0
        
        # Initialize providers lazily
        self._provider_instances: Dict[str, BaseAIProvider] = {}
        
        logger.info(f"ProviderManager initialized with order: {self.provider_order}")
        logger.info(f"Gemini API keys configured: {len(self.gemini_keys)}")
    
    def _get_provider(self, provider_name: str) -> BaseAIProvider:
        """
        Get or create a provider instance.
        
        Args:
            provider_name: Name of the provider
            
        Returns:
            Provider instance
        """
        if provider_name not in self._provider_instances:
            if provider_name == "gemini":
                self._provider_instances[provider_name] = GeminiProvider()
            elif provider_name == "grok":
                self._provider_instances[provider_name] = GrokProvider()
            elif provider_name == "openai":
                self._provider_instances[provider_name] = OpenAIProvider()
            elif provider_name == "mock":
                self._provider_instances[provider_name] = MockAIProvider()
            else:
                raise ValueError(f"Unknown provider: {provider_name}")
            
            # Initialize stats
            self.stats[provider_name] = ProviderStats(provider_name)
        
        return self._provider_instances[provider_name]
    
    def _is_rotation_error(self, error: Exception) -> bool:
        """
        Determine if an error should trigger key rotation.
        
        Args:
            error: The exception that occurred
            
        Returns:
            True if rotation should occur
        """
        error_str = str(error).lower()
        
        # Check for specific error codes
        for code in self.ROTATION_ERROR_CODES:
            if str(code) in error_str:
                return True
        
        # Check for specific error messages
        rotation_keywords = [
            "quota exceeded",
            "resource exhausted",
            "invalid api key",
            "forbidden",
            "unauthorized"
        ]
        
        for keyword in rotation_keywords:
            if keyword in error_str:
                return True
        
        return False
    
    async def _check_provider_health(self, provider_name: str) -> bool:
        """
        Check if a provider is healthy (with caching).
        
        Args:
            provider_name: Name of the provider
            
        Returns:
            True if healthy, False otherwise
        """
        stats = self.stats.get(provider_name)
        
        # Check cache
        if stats and stats.last_health_check:
            cache_age = (datetime.utcnow() - stats.last_health_check).total_seconds()
            if cache_age < self.HEALTH_CHECK_CACHE_SECONDS:
                return stats.healthy
        
        # Perform health check
        try:
            provider = self._get_provider(provider_name)
            is_healthy = await provider.health_check()
            
            if stats:
                stats.healthy = is_healthy
                stats.last_health_check = datetime.utcnow()
            
            return is_healthy
        except Exception as e:
            logger.warning(f"Health check failed for {provider_name}: {type(e).__name__}")
            if stats:
                stats.healthy = False
                stats.last_health_check = datetime.utcnow()
            return False
    
    async def _try_provider_with_retry(
        self,
        provider_name: str,
        method_name: str,
        *args,
        **kwargs
    ) -> str:
        """
        Try a provider with retry logic (not rotation).
        
        Retries on 500, 502, 503, 504, timeout.
        Only rotates on 429, 401, 403.
        
        Args:
            provider_name: Name of the provider
            method_name: Method to call
            *args: Method arguments
            **kwargs: Method keyword arguments
            
        Returns:
            Method result
            
        Raises:
            Exception if all retries fail
        """
        provider = self._get_provider(provider_name)
        max_retries = 2
        retry_delays = [1, 2]  # Exponential backoff
        
        for attempt in range(max_retries + 1):
            try:
                start_time = time.time()
                method = getattr(provider, method_name)
                result = await method(*args, **kwargs)
                latency = time.time() - start_time
                
                # Record success
                if provider_name in self.stats:
                    self.stats[provider_name].record_success(latency)
                
                return result
                
            except Exception as e:
                if self._is_rotation_error(e):
                    # Don't retry - rotate immediately
                    logger.warning(f"{provider_name} rotation error: {type(e).__name__}")
                    if provider_name in self.stats:
                        self.stats[provider_name].record_failure(is_quota_error=True)
                    raise
                
                # Retry on other errors
                if attempt < max_retries:
                    delay = retry_delays[attempt]
                    logger.info(f"Retrying {provider_name} after {delay}s (attempt {attempt + 1}/{max_retries})")
                    await asyncio.sleep(delay)
                else:
                    # All retries failed
                    if provider_name in self.stats:
                        self.stats[provider_name].record_failure()
                    raise
    
    async def generate_completion(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Generate a completion with automatic failover.
        
        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text
            
        Raises:
            Exception if all providers fail
        """
        last_error = None
        
        for provider_name in self.provider_order:
            try:
                logger.info(f"Attempting provider: {provider_name}")
                
                # Special handling for Gemini key rotation
                if provider_name == "gemini" and self.gemini_keys:
                    result = await self._try_gemini_with_key_rotation(
                        prompt, system_prompt, temperature, max_tokens
                    )
                    logger.info(f"Success with provider: {provider_name}")
                    return result
                else:
                    result = await self._try_provider_with_retry(
                        provider_name, "generate_completion",
                        prompt, system_prompt, temperature, max_tokens
                    )
                    logger.info(f"Success with provider: {provider_name}")
                    return result
                    
            except Exception as e:
                last_error = e
                logger.warning(f"Provider {provider_name} failed: {type(e).__name__}")
                continue
        
        # All providers failed
        logger.error("All providers failed")
        raise Exception(f"All AI providers failed. Last error: {last_error}")
    
    async def _try_gemini_with_key_rotation(
        self,
        prompt: str,
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: Optional[int]
    ) -> str:
        """
        Try Gemini with automatic key rotation.
        
        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text
            
        Raises:
            Exception if all keys fail
        """
        if not self.gemini_keys:
            # No keys configured, use default
            return await self._try_provider_with_retry(
                "gemini", "generate_completion",
                prompt, system_prompt, temperature, max_tokens
            )
        
        last_error = None
        start_index = self.current_gemini_key_index
        
        for i in range(len(self.gemini_keys)):
            key_index = (start_index + i) % len(self.gemini_keys)
            self.current_gemini_key_index = key_index
            
            try:
                logger.info(f"Trying Gemini key #{key_index + 1}/{len(self.gemini_keys)}")
                
                # Create provider with this key
                from google import genai
                provider = GeminiProvider()
                provider.client = genai.Client(api_key=self.gemini_keys[key_index])
                
                # Try the request
                start_time = time.time()
                result = await provider.generate_completion(
                    prompt, system_prompt, temperature, max_tokens
                )
                latency = time.time() - start_time
                
                # Record success
                if "gemini" in self.stats:
                    self.stats["gemini"].record_success(latency)
                
                return result
                
            except Exception as e:
                last_error = e
                if self._is_rotation_error(e):
                    logger.warning(f"Gemini key #{key_index + 1} quota exhausted")
                    if "gemini" in self.stats:
                        self.stats["gemini"].record_failure(is_quota_error=True)
                else:
                    logger.warning(f"Gemini key #{key_index + 1} failed: {type(e).__name__}")
                    if "gemini" in self.stats:
                        self.stats["gemini"].record_failure()
                continue
        
        # All keys exhausted
        logger.warning("All Gemini keys exhausted")
        raise last_error or Exception("All Gemini keys exhausted")
    
    async def generate_structured_completion(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        response_format: Optional[Dict[str, Any]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate a structured completion with automatic failover.
        
        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            response_format: JSON schema for structured output
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated structured response
            
        Raises:
            Exception if all providers fail
        """
        last_error = None
        
        for provider_name in self.provider_order:
            try:
                logger.info(f"Attempting provider for structured: {provider_name}")
                
                # Special handling for Gemini key rotation
                if provider_name == "gemini" and self.gemini_keys:
                    result = await self._try_gemini_structured_with_key_rotation(
                        prompt, system_prompt, response_format, temperature, max_tokens
                    )
                    logger.info(f"Success with provider: {provider_name}")
                    return result
                else:
                    result = await self._try_provider_with_retry(
                        provider_name, "generate_structured_completion",
                        prompt, system_prompt, response_format, temperature, max_tokens
                    )
                    logger.info(f"Success with provider: {provider_name}")
                    return result
                    
            except Exception as e:
                last_error = e
                logger.warning(f"Provider {provider_name} failed: {type(e).__name__}")
                continue
        
        # All providers failed
        logger.error("All providers failed for structured completion")
        raise Exception(f"All AI providers failed. Last error: {last_error}")
    
    async def _try_gemini_structured_with_key_rotation(
        self,
        prompt: str,
        system_prompt: Optional[str],
        response_format: Optional[Dict[str, Any]],
        temperature: float,
        max_tokens: Optional[int]
    ) -> Dict[str, Any]:
        """
        Try Gemini structured completion with automatic key rotation.
        
        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            response_format: JSON schema for structured output
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated structured response
            
        Raises:
            Exception if all keys fail
        """
        if not self.gemini_keys:
            # No keys configured, use default
            return await self._try_provider_with_retry(
                "gemini", "generate_structured_completion",
                prompt, system_prompt, response_format, temperature, max_tokens
            )
        
        last_error = None
        start_index = self.current_gemini_key_index
        
        for i in range(len(self.gemini_keys)):
            key_index = (start_index + i) % len(self.gemini_keys)
            self.current_gemini_key_index = key_index
            
            try:
                logger.info(f"Trying Gemini key #{key_index + 1}/{len(self.gemini_keys)} for structured")
                
                # Create provider with this key
                from google import genai
                provider = GeminiProvider()
                provider.client = genai.Client(api_key=self.gemini_keys[key_index])
                
                # Try the request
                start_time = time.time()
                result = await provider.generate_structured_completion(
                    prompt, system_prompt, response_format, temperature, max_tokens
                )
                latency = time.time() - start_time
                
                # Record success
                if "gemini" in self.stats:
                    self.stats["gemini"].record_success(latency)
                
                return result
                
            except Exception as e:
                last_error = e
                if self._is_rotation_error(e):
                    logger.warning(f"Gemini key #{key_index + 1} quota exhausted")
                    if "gemini" in self.stats:
                        self.stats["gemini"].record_failure(is_quota_error=True)
                else:
                    logger.warning(f"Gemini key #{key_index + 1} failed: {type(e).__name__}")
                    if "gemini" in self.stats:
                        self.stats["gemini"].record_failure()
                continue
        
        # All keys exhausted
        logger.warning("All Gemini keys exhausted for structured completion")
        raise last_error or Exception("All Gemini keys exhausted")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get provider status and statistics.
        
        Returns:
            Status dictionary with provider information
        """
        provider_statuses = []
        
        for provider_name in self.provider_order:
            stats = self.stats.get(provider_name, ProviderStats(provider_name))
            
            status = stats.to_dict()
            
            # Add Gemini-specific info
            if provider_name == "gemini":
                status["keys_available"] = len(self.gemini_keys)
                status["keys_exhausted"] = stats.quota_failures
            
            provider_statuses.append(status)
        
        return {
            "current_provider": self.provider_order[self.current_provider_index] if self.provider_order else None,
            "providers": provider_statuses
        }
