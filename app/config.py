"""Configuration management with Pydantic settings."""

import os
from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # App
    app_name: str = "BEI Knowledge Hub"
    app_version: str = "3.0.0"
    environment: str = "development"
    debug: bool = False

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4
    log_level: str = "info"

    # Gemini API
    gemini_api_key: str = "test-key"  # Default for tests

    # Supabase
    supabase_url: Optional[str] = None
    supabase_service_role_key: Optional[str] = None

    # Observability
    langfuse_public_key: Optional[str] = None
    langfuse_secret_key: Optional[str] = None
    langfuse_host: str = "https://cloud.langfuse.com"

    # Optional: Frappe Integration
    frappe_api_url: Optional[str] = None
    frappe_api_key: Optional[str] = None
    frappe_api_secret: Optional[str] = None

    # Authentication
    api_key: str = "default-api-key-change-me"

    # Search settings
    default_top_k: int = 5
    similarity_threshold: float = 0.5
    rrf_k_constant: int = 60

    # Vision settings
    quality_threshold: float = 0.5

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global config instance
config = get_settings()
