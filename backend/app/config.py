from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Values are read from the local `.env` file during development.
    For production, environment variables can be injected directly.
    """

    # Application
    ENVIRONMENT: str = "development"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ai_researcher"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    SEARCH_CACHE_TTL_SECONDS: int = 300
    CACHE_PREFIX: str = "ai_researcher"

    # OpenAI
    OPENAI_API_KEY: str | None = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    LLM_TIMEOUT_SECONDS: int = 30

    # OpenAlex
    OPENALEX_MAILTO: str = "your@email.com"
    OPENALEX_TIMEOUT_SECONDS: int = 30

    # Authentication
    JWT_SECRET_KEY: str = "change-me-to-a-long-random-secret"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_DAYS: int = 7

    # CORS
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @property
    def cors_origins(self) -> list[str]:
        """
        Convert comma-separated CORS origins string into a list of origins.
        """
        return [
            origin.strip()
            for origin in self.CORS_ORIGINS.split(",")
            if origin.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    """
    Return a cached Settings instance so environment parsing happens once.
    """
    return Settings()


settings = get_settings()