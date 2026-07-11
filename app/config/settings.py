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
    DATABASE_URL: str = "sqlite+aiosqlite:///./sehat_saathi.db"
    # PostgreSQL (production): postgresql+asyncpg://user:pass@host:5432/dbname

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
    # Gemini AI  (Phase 5)
    # ------------------------------------------------------------------ #
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"
    GEMINI_TEMPERATURE: float = 0.3      # Lower = more factual, less creative
    GEMINI_MAX_TOKENS: int = 4096
    GEMINI_TOP_P: float = 0.95
    GEMINI_TOP_K: int = 40
    GEMINI_TIMEOUT: int = 60             # seconds per request
    GEMINI_MAX_RETRIES: int = 2          # retries on transient errors

    # ------------------------------------------------------------------ #
    # Gemini Embeddings + RAG  (Phase 6)
    # ------------------------------------------------------------------ #
    GEMINI_EMBEDDING_MODEL: str = "models/text-embedding-004"
    GEMINI_EMBEDDING_DIMENSION: int = 768

    # FAISS / vector store
    VECTOR_STORE_DIR: str = "data/vector_stores"

    # Chunking
    CHUNK_SIZE_WORDS: int = 600
    CHUNK_OVERLAP_WORDS: int = 100

    # Retrieval
    RAG_TOP_K: int = 5
    RAG_SIMILARITY_THRESHOLD: float = 0.25   # minimum cosine score to include chunk
    RAG_MAX_CONTEXT_CHARS: int = 8000        # hard limit on chars sent to Gemini
    RAG_CONVERSATION_HISTORY_LIMIT: int = 5  # number of prior turns kept

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
