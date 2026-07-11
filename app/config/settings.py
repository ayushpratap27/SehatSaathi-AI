"""
Centralized application configuration using Pydantic BaseSettings.

All values can be overridden via environment variables or a .env file.
"""

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings.

    Reads from environment variables first, then falls back to the
    values defined here. Sensitive fields (e.g. API keys) should always
    be provided via environment variables and never committed to source.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ------------------------------------------------------------------ #
    # Application
    # ------------------------------------------------------------------ #
    APP_NAME: str = "SehatSaathi-AI"
    APP_DESCRIPTION: str = (
        "AI-powered Medical Report Understanding System — "
        "helping patients understand their health reports in plain language."
    )
    APP_VERSION: str = "0.1.0"
    ENV: str = "development"
    DEBUG: bool = True

    # ------------------------------------------------------------------ #
    # Server
    # ------------------------------------------------------------------ #
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # ------------------------------------------------------------------ #
    # CORS
    # ------------------------------------------------------------------ #
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:8501",  # Streamlit dev
        "http://localhost:3000",  # React (future)
        "http://127.0.0.1:8501",
    ]

    # ------------------------------------------------------------------ #
    # Logging
    # ------------------------------------------------------------------ #
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"

    # ------------------------------------------------------------------ #
    # Database  (SQLite for dev, PostgreSQL for production)
    # ------------------------------------------------------------------ #
    DATABASE_URL: str = "sqlite:///./sehat_saathi.db"

    # ------------------------------------------------------------------ #
    # File Storage
    # ------------------------------------------------------------------ #
    UPLOAD_DIR: str = "data/uploads"
    PROCESSED_DIR: str = "data/processed"
    TEMP_DIR: str = "data/temp"
    MAX_UPLOAD_SIZE_MB: int = 20

    # Allowed MIME types for uploaded medical documents
    ALLOWED_MIME_TYPES: List[str] = [
        "application/pdf",
        "image/png",
        "image/jpeg",
        "image/tiff",
    ]

    # ------------------------------------------------------------------ #
    # AI / LLM  (integrated in future phases)
    # ------------------------------------------------------------------ #
    LLM_PROVIDER: str = "ollama"          # "ollama" | "openai"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3"
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"

    # Embedding model (Phase 4)
    EMBEDDING_MODEL: str = "allenai-specter"

    # ------------------------------------------------------------------ #
    # Security  (Phase 8)
    # ------------------------------------------------------------------ #
    SECRET_KEY: str = "change-this-to-a-long-random-secret-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7


@lru_cache()
def get_settings() -> Settings:
    """
    Return the cached singleton Settings instance.

    Uses lru_cache so the .env file is read only once per process.
    """
    return Settings()
