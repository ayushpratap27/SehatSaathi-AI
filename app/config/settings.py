"""
Centralized application configuration using Pydantic BaseSettings.

All values can be overridden via environment variables or a .env file.
"""

from functools import lru_cache
from typing import List

from pydantic import field_validator
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
    APP_VERSION: str = "1.0.0"
    ENV: str = "development"
    DEBUG: bool = False   # never default to True — leaks SQL and stack traces

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
    # Groq LLM  (Phase 5 — replaces Gemini text generation)
    # ------------------------------------------------------------------ #
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"   # fast, capable 70B model
    GROQ_TEMPERATURE: float = 0.3
    GROQ_MAX_TOKENS: int = 4096
    GROQ_TIMEOUT: int = 60
    GROQ_MAX_RETRIES: int = 2

    # Keep for backward compatibility references; not used for text generation
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"
    GEMINI_TEMPERATURE: float = 0.3
    GEMINI_MAX_TOKENS: int = 4096
    GEMINI_TOP_P: float = 0.95
    GEMINI_TOP_K: int = 40
    GEMINI_TIMEOUT: int = 60
    GEMINI_MAX_RETRIES: int = 2

    # ------------------------------------------------------------------ #
    # Redis  (Phase 8)
    # ------------------------------------------------------------------ #
    REDIS_URL: str = "redis://localhost:6379/0"
    CACHE_TTL_SECONDS: int = 300         # default cache TTL (5 min)

    # ------------------------------------------------------------------ #
    # Gemini Embeddings + RAG  (Phase 6)
    # Now uses sentence-transformers locally — no API key required
    # ------------------------------------------------------------------ #
    GEMINI_EMBEDDING_MODEL: str = "models/text-embedding-004"  # kept for reference
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"     # local model, no API key needed
    EMBEDDING_DIMENSION: int = 384                  # dimension for all-MiniLM-L6-v2
    GEMINI_EMBEDDING_DIMENSION: int = 384           # alias kept for compatibility

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

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """Warn loudly if the default insecure key is used."""
        import logging  # noqa: PLC0415
        if v == "change-this-to-a-long-random-secret-in-production" or len(v) < 32:
            logging.getLogger(__name__).warning(
                "SECRET_KEY is using the default insecure value. "
                "Set a strong random key with: openssl rand -hex 32"
            )
        return v


@lru_cache()
def get_settings() -> Settings:
    """
    Return the cached singleton Settings instance.

    Uses lru_cache so the .env file is read only once per process.
    """
    return Settings()
