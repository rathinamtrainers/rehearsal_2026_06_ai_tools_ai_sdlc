"""Application settings, loaded from environment / .env (pydantic-settings).

Every tunable the auth layer needs lives here: the database URL, the JWT signing
configuration, the account-lockout thresholds, and the CORS allowlist. Defaults
are dev-friendly (SQLite, a throwaway secret) so the service runs with zero setup;
production overrides them via real environment variables.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database — one URL drives both SQLite (dev) and Postgres (prod).
    database_url: str = "sqlite:///./learnflow.db"

    # JWT — HS256 today; swap algorithm + key source for RS256 (NFR-03).
    jwt_secret: str = "dev-only-change-me-please-0123456789abcdef"
    jwt_algorithm: str = "HS256"
    access_token_ttl_minutes: int = 15
    refresh_token_ttl_days: int = 7

    # Account lockout (AC-AUTH-06).
    max_failed_attempts: int = 5
    lockout_window_minutes: int = 10
    lockout_minutes: int = 15

    # CORS — comma-separated list of allowed origins (the Vite frontend).
    cors_origins: str = "http://localhost:5173"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Cached singleton so every importer shares one parsed configuration."""
    return Settings()


settings = get_settings()
