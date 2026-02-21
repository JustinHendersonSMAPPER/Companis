"""Unit tests for AI service factory."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from app.config import AIProvider


class TestGetAIService:
    @patch("app.services.ai.ollama.OllamaService.__init__", return_value=None)
    @patch("app.config.settings.ai_provider", AIProvider.OLLAMA)
    def test_ollama_provider(self, mock_init: object) -> None:
        from app.services.ai import get_ai_service
        from app.services.ai.ollama import OllamaService

        service = get_ai_service()
        assert isinstance(service, OllamaService)

    @patch("app.services.ai.anthropic.AnthropicService.__init__", return_value=None)
    @patch("app.config.settings.ai_provider", AIProvider.ANTHROPIC)
    def test_anthropic_provider(self, mock_init: object) -> None:
        from app.services.ai import get_ai_service
        from app.services.ai.anthropic import AnthropicService

        service = get_ai_service()
        assert isinstance(service, AnthropicService)

    @patch("app.config.settings.ai_provider", AIProvider.CLAUDE_LOCAL)
    def test_claude_local_provider(self) -> None:
        from app.services.ai import get_ai_service
        from app.services.ai.claude_local import ClaudeLocalService

        service = get_ai_service()
        assert isinstance(service, ClaudeLocalService)

    @patch("app.services.ai.openai_service.OpenAIService.__init__", return_value=None)
    @patch("app.config.settings.ai_provider", AIProvider.OPENAI)
    def test_openai_provider(self, mock_init: object) -> None:
        from app.services.ai import get_ai_service
        from app.services.ai.openai_service import OpenAIService

        service = get_ai_service()
        assert isinstance(service, OpenAIService)

    @patch("app.config.settings.ai_provider", "invalid_provider")
    def test_unknown_provider_raises(self) -> None:
        from app.services.ai import get_ai_service

        with pytest.raises(ValueError, match="Unknown AI provider"):
            get_ai_service()
