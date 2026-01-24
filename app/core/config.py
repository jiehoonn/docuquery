# app/core/config.py: a central place to load all env variables into a typed
# Python object. Pydantic settings validates them at startup.

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore",
    )

    # PostgreSQL
    database_url: str

    # Redis
    redis_url: str = "redis://localhost:6379"

    # Qdrant
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333

    # JWT (Auth)
    jwt_secret: str = "dev-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

settings = Settings()