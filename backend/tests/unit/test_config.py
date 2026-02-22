from __future__ import annotations

from pathlib import Path

import pytest

from app.config import AIProvider, Settings, _find_secrets_dir


class TestAIProvider:
    def test_provider_values(self) -> None:
        assert AIProvider.OLLAMA == "ollama"
        assert AIProvider.ANTHROPIC == "anthropic"
        assert AIProvider.CLAUDE_LOCAL == "claude_local"
        assert AIProvider.OPENAI == "openai"

    def test_provider_is_string(self) -> None:
        assert isinstance(AIProvider.OLLAMA, str)
        assert isinstance(AIProvider.ANTHROPIC, str)


class TestDefaultSettings:
    """Test that default values are correct when isolated from .env and CLI."""

    def test_default_app_name(self) -> None:
        s = Settings(_env_file=None, _cli_parse_args=[])  # type: ignore[call-arg]
        assert s.app_name == "SousChefAI"

    def test_default_debug(self) -> None:
        s = Settings(_env_file=None, _cli_parse_args=[])  # type: ignore[call-arg]
        assert s.debug is False

    def test_default_host(self) -> None:
        s = Settings(_env_file=None, _cli_parse_args=[])  # type: ignore[call-arg]
        assert s.host == "0.0.0.0"  # noqa: S104

    def test_default_port(self) -> None:
        s = Settings(_env_file=None, _cli_parse_args=[])  # type: ignore[call-arg]
        assert s.port == 6000

    def test_default_allowed_origins(self) -> None:
        s = Settings(_env_file=None, _cli_parse_args=[])  # type: ignore[call-arg]
        assert "http://localhost:6001" in s.allowed_origins

    def test_default_oauth_redirect_base_url(self) -> None:
        s = Settings(_env_file=None, _cli_parse_args=[])  # type: ignore[call-arg]
        assert s.oauth_redirect_base_url == "http://localhost:6000"

    def test_default_jwt_settings(self) -> None:
        s = Settings(_env_file=None, _cli_parse_args=[])  # type: ignore[call-arg]
        assert s.jwt_algorithm == "HS256"
        assert s.access_token_expire_minutes == 60
        assert s.refresh_token_expire_days == 30

    def test_default_ai_provider(self) -> None:
        s = Settings(_env_file=None, _cli_parse_args=[])  # type: ignore[call-arg]
        assert s.ai_provider == AIProvider.OLLAMA


class TestEnvVarOverrides:
    """Test that environment variables override defaults."""

    def test_env_var_overrides_ai_provider(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("AI_PROVIDER", "anthropic")
        s = Settings(_env_file=None, _cli_parse_args=[])  # type: ignore[call-arg]
        assert s.ai_provider == AIProvider.ANTHROPIC

    def test_env_var_overrides_port(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("PORT", "8888")
        s = Settings(_env_file=None, _cli_parse_args=[])  # type: ignore[call-arg]
        assert s.port == 8888

    def test_env_var_overrides_debug(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("DEBUG", "true")
        s = Settings(_env_file=None, _cli_parse_args=[])  # type: ignore[call-arg]
        assert s.debug is True


class TestCLIOverrides:
    """Test that CLI args override environment variables (higher priority)."""

    def test_cli_overrides_env_var(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("AI_PROVIDER", "anthropic")
        s = Settings(
            _env_file=None,  # type: ignore[call-arg]
            _cli_parse_args=["--ai-provider=openai"],
        )
        assert s.ai_provider == AIProvider.OPENAI

    def test_cli_port_override(self) -> None:
        s = Settings(
            _env_file=None,  # type: ignore[call-arg]
            _cli_parse_args=["--port=9999"],
        )
        assert s.port == 9999

    def test_cli_host_override(self) -> None:
        s = Settings(
            _env_file=None,  # type: ignore[call-arg]
            _cli_parse_args=["--host=127.0.0.1"],
        )
        assert s.host == "127.0.0.1"


class TestSecretsOverrides:
    """Test that secrets files override env vars but are overridden by CLI."""

    def test_secrets_dir_overrides_env_var(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Set env var to one value
        monkeypatch.setenv("AI_PROVIDER", "anthropic")
        # Write a secrets file with a different value
        secret_file = tmp_path / "ai_provider"
        secret_file.write_text("openai")
        s = Settings(
            _env_file=None,  # type: ignore[call-arg]
            _secrets_dir=str(tmp_path),
            _cli_parse_args=[],
        )
        assert s.ai_provider == AIProvider.OPENAI

    def test_cli_overrides_secrets(self, tmp_path: Path) -> None:
        # Write a secrets file
        secret_file = tmp_path / "ai_provider"
        secret_file.write_text("anthropic")
        s = Settings(
            _env_file=None,  # type: ignore[call-arg]
            _secrets_dir=str(tmp_path),
            _cli_parse_args=["--ai-provider=openai"],
        )
        assert s.ai_provider == AIProvider.OPENAI

    def test_secrets_port_override(self, tmp_path: Path) -> None:
        secret_file = tmp_path / "port"
        secret_file.write_text("7777")
        s = Settings(
            _env_file=None,  # type: ignore[call-arg]
            _secrets_dir=str(tmp_path),
            _cli_parse_args=[],
        )
        assert s.port == 7777


class TestFindSecretsDir:
    """Test the _find_secrets_dir helper function."""

    def test_returns_none_when_no_secrets_dir_exists(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr("app.config._SECRETS_DIRS", [Path("/nonexistent/abc123")])
        assert _find_secrets_dir() is None

    def test_returns_first_existing_dir(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr("app.config._SECRETS_DIRS", [Path("/nonexistent"), tmp_path])
        assert _find_secrets_dir() == tmp_path


class TestSettingsCustomiseSources:
    """Test that the priority chain works end-to-end."""

    def test_full_priority_chain(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """CLI > secrets > env > defaults."""
        # Default is "ollama"
        # Env sets to "anthropic"
        monkeypatch.setenv("AI_PROVIDER", "anthropic")
        # Secret sets to "openai" (should override env)
        secret_file = tmp_path / "ai_provider"
        secret_file.write_text("openai")
        # CLI sets back to "anthropic" (should override everything)
        s = Settings(
            _env_file=None,  # type: ignore[call-arg]
            _secrets_dir=str(tmp_path),
            _cli_parse_args=["--ai-provider=anthropic"],
        )
        assert s.ai_provider == AIProvider.ANTHROPIC

    def test_existing_fields_preserved(self) -> None:
        """Ensure all original fields still exist with correct defaults."""
        s = Settings(_env_file=None, _cli_parse_args=[])  # type: ignore[call-arg]
        assert s.secret_key == "change-me-in-production"
        assert s.database_url == "sqlite+aiosqlite:///./souschefai.db"
        assert s.google_client_id == ""
        assert s.google_client_secret == ""
        assert s.facebook_client_id == ""
        assert s.facebook_client_secret == ""
        assert s.ollama_base_url == "http://localhost:11434"
        assert s.ollama_model == "llama3.2"
        assert s.anthropic_api_key == ""
        assert s.anthropic_model == "claude-sonnet-4-20250514"
        assert s.openai_api_key == ""
        assert s.openai_model == "gpt-4o"
        assert s.claude_local_model == "claude-sonnet-4-20250514"
        assert s.openfoodfacts_api_url == "https://world.openfoodfacts.org/api/v2"
