"""Application settings loaded from environment."""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    """Global application configuration."""

    database_url: str = "sqlite+aiosqlite:///./data/architectai.db"
    redis_url: str = "redis://localhost:6379/0"
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o"
    secret_key: str = "dev-secret-key"
    cors_origins: List[str] = ["http://localhost:3000"]
    bundles_dir: str = "data/bundles"
    max_patch_attempts: int = 3
    max_security_patches: int = 2

    model_config = SettingsConfigDict(env_file=".env", env_prefix="")


settings = Settings()
