"""
Worker configuration using Pydantic Settings
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Worker settings"""

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://vocuser:vocpassword@localhost:5432/vocdb"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # RabbitMQ
    RABBITMQ_URL: str = "amqp://vocuser:vocpassword@localhost:5672/"

    # Worker Configuration
    WORKER_NAME: str = "voc-worker"
    QUEUE_NAME: str = "data_ingestion"
    PREFETCH_COUNT: int = 1

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )


# Global settings instance
settings = Settings()
