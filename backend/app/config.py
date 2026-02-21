from __future__ import annotations

from enum import StrEnum

from pydantic_settings import BaseSettings, SettingsConfigDict


class AIProvider(StrEnum):
    OLLAMA = "ollama"
    ANTHROPIC = "anthropic"
    CLAUDE_LOCAL = "claude_local"
    OPENAI = "openai"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Application
    app_name: str = "SousChefAI"
    debug: bool = False
    secret_key: str = "change-me-in-production"
    allowed_origins: list[str] = ["http://localhost:5173"]

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
    oauth_redirect_base_url: str = "http://localhost:8000"

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


settings = Settings()
