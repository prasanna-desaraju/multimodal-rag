"""Application settings using pydantic-settings.

Configuration values are loaded from the environment and `.env` file.
This module exposes a cached `get_settings()` accessor that returns a
singleton `Settings` instance to be injected into higher-level modules.

No sensitive values are hardcoded here; defaults are intentionally
left as `None` to encourage explicit configuration via env/.env.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Pydantic settings model loaded from environment/.env.

    Fields are intentionally permissive (Optional) so callers must handle
    missing values explicitly. This supports SOLID principles by keeping
    configuration separate from business logic and enabling easy testing
    and dependency injection.
    """

    # Secrets / credentials
    GROK_API_KEY: Optional[str] = None

    # Persistent stores
    CHROMA_PERSIST_DIR: Optional[Path] = None

    # Model configuration (future-ready)
    DEFAULT_EMBEDDER: Optional[str] = None
    DEFAULT_LLM_MODEL: Optional[str] = None

    # Chunking and retrieval tuning
    CHUNK_SIZE: Optional[int] = None
    CHUNK_OVERLAP: Optional[int] = None
    RETRIEVAL_TOP_K: Optional[int] = None
    RERANK_TOP_K: Optional[int] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a singleton Settings instance.

    Use this function to obtain configuration throughout the app. The
    result is cached to ensure a single settings object (singleton)
    during process lifetime and to make testing easier (can be
    monkeypatched).
    """

    return Settings()


__all__ = ["Settings", "get_settings"]
