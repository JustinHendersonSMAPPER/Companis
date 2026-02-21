from __future__ import annotations

from app.config import AIProvider, Settings


class TestAIProvider:
    def test_provider_values(self) -> None:
        assert AIProvider.OLLAMA == "ollama"
        assert AIProvider.ANTHROPIC == "anthropic"
        assert AIProvider.CLAUDE_LOCAL == "claude_local"
        assert AIProvider.OPENAI == "openai"

    def test_provider_is_string(self) -> None:
        assert isinstance(AIProvider.OLLAMA, str)
        assert isinstance(AIProvider.ANTHROPIC, str)


class TestSettings:
    def test_default_settings(self) -> None:
        s = Settings(
            _env_file=None,  # type: ignore[call-arg]
        )
        assert s.app_name == "SousChefAI"
        assert s.debug is False
        assert s.jwt_algorithm == "HS256"
        assert s.access_token_expire_minutes == 60
        assert s.refresh_token_expire_days == 30
        assert s.ai_provider == AIProvider.OLLAMA

    def test_settings_allowed_origins_default(self) -> None:
        s = Settings(
            _env_file=None,  # type: ignore[call-arg]
        )
        assert "http://localhost:5173" in s.allowed_origins
