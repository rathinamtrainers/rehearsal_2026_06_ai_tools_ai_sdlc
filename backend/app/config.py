"""Application settings, loaded from environment / .env (pydantic-settings)."""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database — SQLite dev, Postgres prod.
    database_url: str = "sqlite:///./learnflow.db"

    # JWT — HS256 default, RS256-ready.
    jwt_algorithm: str = "HS256"
    jwt_secret_key: str = "dev-only-change-me-to-a-long-random-string"
    jwt_private_key_path: str | None = None
    jwt_public_key_path: str | None = None
    access_token_ttl_minutes: int = 15
    refresh_token_ttl_days: int = 7

    # Brute-force lockout (named / per-user).
    lockout_max_attempts: int = 5
    lockout_window_minutes: int = 10
    lockout_duration_minutes: int = 15

    # Dev convenience: register straight to ACTIVE (skip email verification).
    register_active: bool = True

    # CORS — comma-separated list of allowed origins.
    cors_origins: str = "http://localhost:5173,http://localhost:5174"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def allowed_algorithms(self) -> list[str]:
        # Allowlist for verification — never accept "none" or unexpected algs.
        return [self.jwt_algorithm]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
