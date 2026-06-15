from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Infrastructure
    database_url: str = "postgresql+asyncpg://postgres:postgres@127.0.0.1:5433/radar"
    qdrant_url: str = "http://localhost:6333"
    redis_url: str = "redis://localhost:6379"

    # External APIs
    firecrawl_api_key: str = ""
    llm_api_key: str = ""
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    cohere_api_key: str = ""

    # Runtime
    environment: str = "development"
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()
