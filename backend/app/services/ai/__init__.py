from __future__ import annotations

from app.config import AIProvider, settings
from app.services.ai.base import AIService


def get_ai_service() -> AIService:
    provider = settings.ai_provider

    if provider == AIProvider.OLLAMA:
        from app.services.ai.ollama import OllamaService

        return OllamaService()
    if provider == AIProvider.ANTHROPIC:
        from app.services.ai.anthropic import AnthropicService

        return AnthropicService()
    if provider == AIProvider.CLAUDE_LOCAL:
        from app.services.ai.claude_local import ClaudeLocalService

        return ClaudeLocalService()
    if provider == AIProvider.OPENAI:
        from app.services.ai.openai_service import OpenAIService

        return OpenAIService()

    msg = f"Unknown AI provider: {provider}"
    raise ValueError(msg)


__all__ = ["AIService", "get_ai_service"]
