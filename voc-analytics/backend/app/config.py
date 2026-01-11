"""
Application configuration using Pydantic Settings
"""
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings"""

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://vocuser:vocpassword@localhost:5432/vocdb"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # RabbitMQ
    RABBITMQ_URL: str = "amqp://vocuser:vocpassword@localhost:5672/"

    # Security
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    WEBHOOK_SECRET: str = "dev-webhook-secret-change-in-production"

    # API
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "VoC Analytics System"

    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Google Maps / SerpAPI (Optional - can be passed in request)
    SERPAPI_KEY: Optional[str] = None
    GOOGLE_MAPS_DATA_ID: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )


# Global settings instance
settings = Settings()
