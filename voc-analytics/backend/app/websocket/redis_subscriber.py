"""
Redis Pub/Sub subscriber for receiving events from worker
"""
import asyncio
import json
import logging
from typing import Callable, Awaitable, Optional

from redis.asyncio import Redis
from redis.asyncio.client import PubSub

from app.config import settings

logger = logging.getLogger(__name__)

# Channel names
CHANNEL_FEEDBACK_NEW = "voc:feedback:new"
CHANNEL_FEEDBACK_COMPLETED = "voc:feedback:completed"

ALL_CHANNELS = [CHANNEL_FEEDBACK_NEW, CHANNEL_FEEDBACK_COMPLETED]


class RedisSubscriber:
    """Subscribes to Redis channels and forwards events to WebSocket"""

    def __init__(self):
        self.redis: Optional[Redis] = None
        self.pubsub: Optional[PubSub] = None
        self.running = False
        self._task: Optional[asyncio.Task] = None

    async def connect(self):
        """Initialize Redis connection for pub/sub"""
        try:
            self.redis = Redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
            # Test connection
            await self.redis.ping()
            self.pubsub = self.redis.pubsub()
            logger.info("Redis subscriber connected")
        except Exception as e:
            logger.error(f"Failed to connect Redis subscriber: {e}")
            self.redis = None
            self.pubsub = None

    async def subscribe(self, on_message: Callable[[str, dict], Awaitable[None]]):
        """
        Subscribe to channels and start listening

        Args:
            on_message: Callback function(channel, data) called when message received
        """
        if not self.pubsub:
            logger.warning("Redis pub/sub not available, skipping subscription")
            return

        try:
            await self.pubsub.subscribe(*ALL_CHANNELS)
            self.running = True
            self._task = asyncio.create_task(self._listen(on_message))
            logger.info(f"Subscribed to Redis channels: {ALL_CHANNELS}")
        except Exception as e:
            logger.error(f"Failed to subscribe to Redis channels: {e}")

    async def _listen(self, on_message: Callable[[str, dict], Awaitable[None]]):
        """Listen for messages on subscribed channels"""
        while self.running:
            try:
                message = await self.pubsub.get_message(
                    ignore_subscribe_messages=True,
                    timeout=1.0
                )
                if message and message['type'] == 'message':
                    channel = message['channel']
                    try:
                        data = json.loads(message['data'])
                        await on_message(channel, data)
                    except json.JSONDecodeError as e:
                        logger.error(f"Invalid JSON in Redis message: {e}")
            except asyncio.CancelledError:
                logger.info("Redis listener cancelled")
                break
            except Exception as e:
                logger.error(f"Error in Redis listener: {e}")
                await asyncio.sleep(1)

    async def disconnect(self):
        """Close Redis connection"""
        self.running = False

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        if self.pubsub:
            try:
                await self.pubsub.unsubscribe()
                await self.pubsub.close()
            except Exception as e:
                logger.error(f"Error closing pubsub: {e}")

        if self.redis:
            try:
                await self.redis.close()
            except Exception as e:
                logger.error(f"Error closing Redis: {e}")

        logger.info("Redis subscriber disconnected")


# Global instance
redis_subscriber = RedisSubscriber()
