"""
TRACE AI Explanation Layer & Provider Factory
"""

from typing import Optional
from app.ai.base import LLMProvider
from app.ai.offline_provider import OfflineProvider
from app.ai.openai_provider import OpenAIProvider
from app.ai.anthropic_provider import AnthropicProvider
from app.core.config import settings

def get_llm_provider(provider_name: Optional[str] = None) -> LLMProvider:
    name = (provider_name or settings.DEFAULT_LLM_PROVIDER or "offline").lower()
    if name == "openai":
        return OpenAIProvider()
    elif name == "anthropic":
        return AnthropicProvider()
    else:
        return OfflineProvider()

__all__ = [
    "LLMProvider",
    "OfflineProvider",
    "OpenAIProvider",
    "AnthropicProvider",
    "get_llm_provider"
]
