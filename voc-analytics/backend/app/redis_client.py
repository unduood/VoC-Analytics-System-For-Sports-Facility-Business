"""
Redis client manager for caching
"""
import logging
from typing import Optional

from redis.asyncio import Redis

from app.config import settings

logger = logging.getLogger(__name__)


class RedisManager:
    """Redis connection manager for caching operations"""

    def __init__(self):
        self.client: Optional[Redis] = None

    async def connect(self):
        """Initialize Redis connection"""
        try:
            self.client = await Redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
            # Test connection
            await self.client.ping()
            logger.info(f"Redis connected successfully: {settings.REDIS_URL}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            # Don't raise - allow app to continue without Redis
            self.client = None

    async def disconnect(self):
        """Close Redis connection"""
        if self.client:
            try:
                await self.client.close()
                logger.info("Redis connection closed")
            except Exception as e:
                logger.error(f"Error closing Redis connection: {e}")

    async def get(self, key: str) -> Optional[str]:
        """
        Get value from Redis

        Args:
            key: Redis key

        Returns:
            Value as string or None if not found or Redis unavailable
        """
        if not self.client:
            logger.warning("Redis client not available")
            return None

        try:
            return await self.client.get(key)
        except Exception as e:
            logger.error(f"Error getting key '{key}' from Redis: {e}")
            return None

    async def set(self, key: str, value: str, expire: int = 3600):
        """
        Set value in Redis with expiration

        Args:
            key: Redis key
            value: Value to store (as string)
            expire: Expiration time in seconds (default 1 hour)

        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            logger.warning("Redis client not available")
            return False

        try:
            await self.client.set(key, value, ex=expire)
            return True
        except Exception as e:
            logger.error(f"Error setting key '{key}' in Redis: {e}")
            return False

    async def delete(self, key: str):
        """
        Delete key from Redis

        Args:
            key: Redis key to delete

        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            logger.warning("Redis client not available")
            return False

        try:
            await self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Error deleting key '{key}' from Redis: {e}")
            return False


# Global instance
redis_manager = RedisManager()
