"""
app/core/config.py - Application Configuration

This module centralizes all configuration settings for the application.
Instead of scattered os.getenv() calls throughout the codebase, we define
all settings here in a typed, validated way using Pydantic Settings.

Benefits of this approach:
1. Type safety - settings have defined types (str, int, etc.)
2. Validation - missing required settings fail fast at startup
3. Documentation - all settings are visible in one place
4. IDE support - autocomplete works with settings.database_url

Usage:
    from app.core.config import settings

    database_url = settings.database_url  # Autocomplete works!
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Pydantic Settings automatically reads environment variables that match
    field names (case-insensitive). For example, the field 'database_url'
    will be populated from the DATABASE_URL environment variable.
    """

    # Configuration for how Pydantic Settings should behave
    model_config = SettingsConfigDict(
        # Load variables from .env file in the project root
        env_file=".env",
        # Ignore empty string values in .env file
        env_ignore_empty=True,
        # Don't raise errors for extra env vars not defined here
        # (e.g., POSTGRES_USER is used by Docker but not by our app)
        extra="ignore",
    )

    # ============ Gemini ============
    gemini_api_key: str = ""

    # ============ Database ============
    # Required - no default value means app won't start without it
    # Format: postgresql+asyncpg://user:password@host:port/database
    database_url: str

    # ============ Redis ============
    # Optional - has a default value for local development
    redis_url: str = "redis://localhost:6379"

    # ============ Qdrant (Vector Database) ============
    # Optional - defaults to local development values
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333

    # ============ JWT Authentication ============
    # Secret key used to sign JWT tokens - MUST be changed in production!
    # In production, use a long random string stored securely
    jwt_secret: str = "dev-secret-change-in-production"

    # Algorithm used for JWT signing
    # HS256 = HMAC with SHA-256 (symmetric key)
    jwt_algorithm: str = "HS256"

    # How long until JWT tokens expire (in minutes)
    jwt_expire_minutes: int = 60


# Create a single instance of Settings to be imported throughout the app
# This instance is created when the module is first imported
settings = Settings()
