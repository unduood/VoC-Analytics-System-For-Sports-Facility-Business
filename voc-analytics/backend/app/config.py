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

    # Facebook Configuration (Optional - can be passed in request)
    FACEBOOK_APP_ID: Optional[str] = None
    FACEBOOK_APP_SECRET: Optional[str] = None
    FACEBOOK_VERIFY_TOKEN: str = "fb-verify-token-change-in-production"
    FACEBOOK_PAGE_ACCESS_TOKEN: Optional[str] = None
    FACEBOOK_GRAPH_API_VERSION: str = "v24.0"  # Latest Facebook Graph API version

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )


# Global settings instance
settings = Settings()
