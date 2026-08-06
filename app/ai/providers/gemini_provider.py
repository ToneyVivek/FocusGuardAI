"""
Google Gemini Provider Implementation

Concrete implementation of BaseAIProvider for Google's Gemini models.
"""

import logging
import time
import json
from typing import Dict, Any, Optional
from google import genai

from app.ai.providers.base import BaseAIProvider
from app.config.config import settings

logger = logging.getLogger(__name__)


class GeminiProvider(BaseAIProvider):
    """
    Google Gemini provider implementation using the Gemini API.
    """
    
    def __init__(self):
        """Initialize Gemini client with API key from settings."""
        print("GeminiProvider initialized")
        
        # Get first available API key from the list
        api_keys = settings.gemini_api_keys_list
        if api_keys:
            api_key = api_keys[0]
            print(f"[GEMINI] Using API key #1 of {len(api_keys)}")
        else:
            # Fallback to old single key if configured for backward compatibility
            api_key = getattr(settings, 'GEMINI_API_KEY', '') or ""
            print(f"[GEMINI] Using legacy single API key configuration")
        
        if not api_key:
            print("[GEMINI] WARNING: No API key configured - provider will not work")
            self.client = None
            self.model_name = settings.GEMINI_MODEL or "gemini-flash-latest"
            return
        
        try:
            self.client = genai.Client(api_key=api_key)
            
            # Auto-select a working Flash model
            self.model_name = self._select_working_model()
            print(f"[GEMINI] Using model: {self.model_name}")
        except Exception as e:
            print(f"[GEMINI] Failed to initialize client: {type(e).__name__}: {e}")
            self.client = None
            self.model_name = settings.GEMINI_MODEL or "gemini-flash-latest"
    
    def _select_working_model(self) -> str:
        """
        Select a working Flash model by testing each one.
        
        Returns:
            The first Flash model that successfully responds to a test call.
        """
        try:
            print("[GEMINI] Listing available models...")
            models = self.client.models.list()
            print(f"[GEMINI] Got {len(list(models))} models")
            
            flash_models = []
            for model in models:
                print(f"[GEMINI] Processing model: {model}")
                try:
                    model_name = model.name
                    print(f"[GEMINI] Model name: {model_name}")
                    if model_name.startswith("models/"):
                        model_name = model_name[7:]
                    
                    supported_actions = []
                    if hasattr(model, 'supported_actions'):
                        supported_actions = model.supported_actions
                        print(f"[GEMINI] Supported actions: {supported_actions}")
                    
                    is_flash = "flash" in model_name.lower()
                    supports_generate = "generateContent" in supported_actions
                    
                    if is_flash and supports_generate:
                        flash_models.append(model_name)
                        print(f"[GEMINI] Added Flash model: {model_name}")
                except AttributeError as e:
                    print(f"[GEMINI] AttributeError processing model: {e}")
                    import traceback
                    print(f"[GEMINI] Traceback:\n{traceback.format_exc()}")
                    continue
            
            print(f"[GEMINI] Found {len(flash_models)} Flash models supporting generateContent")
            
            # Try each Flash model until one works
            for candidate_model in flash_models:
                try:
                    response = self.client.models.generate_content(
                        model=candidate_model,
                        contents="test"
                    )
                    print(f"[GEMINI] Selected working model: {candidate_model}")
                    return candidate_model
                except Exception as e:
                    print(f"[GEMINI] Model {candidate_model} failed: {type(e).__name__}: {e}")
                    continue
            
            # Fallback to configured model if none worked
            print(f"[GEMINI] No Flash model worked, using configured: {settings.GEMINI_MODEL}")
            return settings.GEMINI_MODEL or "gemini-flash-latest"
            
        except Exception as e:
            print(f"[GEMINI] Error selecting model: {type(e).__name__}: {e}")
            import traceback
            print(f"[GEMINI] Full traceback:\n{traceback.format_exc()}")
            return settings.GEMINI_MODEL or "gemini-flash-latest"
    
    async def generate_completion(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Generate a text completion using Gemini.
        
        Args:
            prompt: The user prompt to send to the AI
            system_prompt: Optional system prompt to guide AI behavior
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text completion
        """
        if self.client is None:
            raise ValueError("Gemini provider not initialized - no API key configured")
        
        print("Gemini API CALLED")
        print(f"[GEMINI] Provider: gemini")
        print(f"[GEMINI] Model: {self.model_name}")
        print(f"[GEMINI] Prompt length: {len(prompt)}")
        print(f"[GEMINI] System prompt: {system_prompt[:100] if system_prompt else None}")
        print(f"[GEMINI] Temperature: {temperature}")
        print(f"[GEMINI] Max tokens: {max_tokens}")
        
        start_time = time.time()
        
        # Build the prompt with system instruction if provided
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        else:
            full_prompt = prompt
        
        print(f"[GEMINI] Full prompt length: {len(full_prompt)}")
        
        try:
            # Generate response using new google-genai API
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=full_prompt,
                config={
                    "temperature": temperature,
                    "max_output_tokens": max_tokens,
                }
            )
            
            latency = time.time() - start_time
            print(f"[GEMINI] Response received - latency: {latency:.2f}s")
            print(f"[GEMINI] Response text: {response.text[:200] if response.text else 'None'}")
            
            logger.info(
                f"Gemini completion success - model: {self.model_name}, "
                f"latency: {latency:.2f}s"
            )
            
            return response.text or ""
            
        except Exception as e:
            latency = time.time() - start_time
            print(f"[GEMINI] Exception type: {type(e).__name__}")
            print(f"[GEMINI] Exception message: {str(e)}")
            import traceback
            print(f"[GEMINI] Traceback:\n{traceback.format_exc()}")
            logger.error(
                f"Gemini API error - model: {self.model_name}, "
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
        Generate a structured JSON completion using Gemini.
        
        Args:
            prompt: The user prompt to send to the AI
            system_prompt: Optional system prompt to guide AI behavior
            response_format: JSON schema for structured output
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated structured response as dictionary
        """
        if self.client is None:
            raise ValueError("Gemini provider not initialized - no API key configured")
        
        print(f"[GEMINI] Structured completion called")
        print(f"[GEMINI] Provider: gemini")
        print(f"[GEMINI] Model: {self.model_name}")
        print(f"[GEMINI] Prompt length: {len(prompt)}")
        print(f"[GEMINI] Response format: {response_format}")
        
        start_time = time.time()
        
        # Build the prompt with system instruction and JSON requirement
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        else:
            full_prompt = prompt
        
        # Add JSON format instruction
        full_prompt += "\n\nRespond with valid JSON only. No markdown, no additional text."
        
        if response_format:
            full_prompt += f"\n\nJSON Schema: {json.dumps(response_format)}"
        
        print(f"[GEMINI] Full prompt length: {len(full_prompt)}")
        
        try:
            # Generate response using new google-genai API
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=full_prompt,
                config={
                    "temperature": temperature,
                    "max_output_tokens": max_tokens,
                    "response_mime_type": "application/json",
                }
            )
            
            latency = time.time() - start_time
            print(f"[GEMINI] Response received - latency: {latency:.2f}s")
            
            # Log raw response before parsing
            content = response.text or "{}"
            print(f"[GEMINI] Raw response (first 500 chars): {content[:500]}")
            
            # Strip markdown JSON wrappers if present
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            
            print(f"[GEMINI] Stripped response (first 500 chars): {content[:500]}")
            
            # Parse JSON response
            parsed = json.loads(content)
            print(f"[GEMINI] JSON parsed successfully")
            
            logger.info(
                f"Gemini structured completion success - model: {self.model_name}, "
                f"latency: {latency:.2f}s"
            )
            
            return parsed
            
        except json.JSONDecodeError as e:
            latency = time.time() - start_time
            print(f"[GEMINI] JSON decode error: {str(e)}")
            print(f"[GEMINI] Content that failed to parse: {content[:500]}")
            import traceback
            print(f"[GEMINI] Traceback:\n{traceback.format_exc()}")
            logger.error(
                f"Gemini JSON parsing error - model: {self.model_name}, "
                f"latency: {latency:.2f}s, error: {str(e)}"
            )
            raise ValueError(f"Failed to parse JSON response: {e}")
            
        except Exception as e:
            latency = time.time() - start_time
            print(f"[GEMINI] Exception type: {type(e).__name__}")
            print(f"[GEMINI] Exception message: {str(e)}")
            import traceback
            print(f"[GEMINI] Traceback:\n{traceback.format_exc()}")
            logger.error(
                f"Gemini structured completion error - model: {self.model_name}, "
                f"latency: {latency:.2f}s, error: {str(e)}"
            )
            raise
    
    def get_provider_name(self) -> str:
        """Get the name of the AI provider."""
        return "gemini"
    
    async def health_check(self) -> bool:
        """
        Check if the Gemini provider is healthy.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents="test",
                config={"max_output_tokens": 5}
            )
            return True
        except Exception as e:
            logger.warning(f"Gemini health check failed: {type(e).__name__}")
            return False
