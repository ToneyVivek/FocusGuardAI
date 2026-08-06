"""
AI Providers Module

Abstract base class and concrete implementations for AI providers.
"""

from app.ai.providers.base import BaseAIProvider
from app.ai.providers.openai_provider import OpenAIProvider
from app.ai.providers.mock_provider import MockAIProvider

# Optional Gemini provider (only import if package is installed)
try:
    from app.ai.providers.gemini_provider import GeminiProvider
    _gemini_available = True
except ImportError:
    _gemini_available = False
    GeminiProvider = None

__all__ = ['BaseAIProvider', 'OpenAIProvider', 'MockAIProvider']

if _gemini_available:
    __all__.append('GeminiProvider')
