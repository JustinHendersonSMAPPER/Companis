from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic_settings import (
    BaseSettings,
    CliSettingsSource,
    PydanticBaseSettingsSource,
    SecretsSettingsSource,
    SettingsConfigDict,
)


class AIProvider(StrEnum):
    OLLAMA = "ollama"
    ANTHROPIC = "anthropic"
    CLAUDE_LOCAL = "claude_local"
    OPENAI = "openai"


# Default secrets directories checked in order (Docker Swarm, then Kubernetes)
_SECRETS_DIRS = [Path("/run/secrets"), Path("/etc/secrets")]


def _find_secrets_dir() -> Path | None:
    """Return the first existing secrets directory, or None if none found."""
    for candidate in _SECRETS_DIRS:
        if candidate.is_dir():
            return candidate
    return None


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        cli_parse_args=True,
        cli_ignore_unknown_args=True,
        cli_kebab_case=True,
    )

    # Application
    app_name: str = "SousChefAI"
    debug: bool = False
    secret_key: str = "change-me-in-production"
    allowed_origins: list[str] = ["http://localhost:6001"]

    # Server
    host: str = "0.0.0.0"
    port: int = 6000

    # Database
    database_url: str = "sqlite+aiosqlite:///./souschefai.db"

    # JWT
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 30

    # OAuth2
    google_client_id: str = ""
    google_client_secret: str = ""
    facebook_client_id: str = ""
    facebook_client_secret: str = ""
    oauth_redirect_base_url: str = "http://localhost:6000"

    # AI Configuration
    ai_provider: AIProvider = AIProvider.OLLAMA
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-20250514"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    claude_local_model: str = "claude-sonnet-4-20250514"

    # Barcode API
    openfoodfacts_api_url: str = "https://world.openfoodfacts.org/api/v2"

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
        **kwargs: Any,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Configure source priority: CLI > secrets > env > .env > init/defaults.

        The framework automatically invokes the CliSettingsSource with any
        cli_parse_args passed to the Settings() constructor, so we create it
        here without explicit args and let the framework handle the rest.
        """
        cli_settings = CliSettingsSource(
            settings_cls,
            cli_ignore_unknown_args=cls.model_config.get("cli_ignore_unknown_args", True),
            cli_kebab_case=cls.model_config.get("cli_kebab_case", True),
        )

        # Only auto-discover secrets dir if caller didn't pass an explicit one
        caller_specified_secrets = (
            isinstance(file_secret_settings, SecretsSettingsSource)
            and file_secret_settings.secrets_dir is not None
        )
        if not caller_specified_secrets:
            secrets_dir = _find_secrets_dir()
            if secrets_dir is not None:
                file_secret_settings = SecretsSettingsSource(
                    settings_cls,
                    secrets_dir=secrets_dir,
                )

        return (
            cli_settings,
            file_secret_settings,
            env_settings,
            dotenv_settings,
            init_settings,
        )


settings = Settings()
