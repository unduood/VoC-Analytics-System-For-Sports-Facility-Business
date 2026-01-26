"""
Redis publisher for worker to broadcast analysis events
Uses synchronous Redis client since worker uses sync code with pika
"""
import json
import logging
from datetime import datetime
from uuid import UUID, uuid4
from typing import Optional, Dict, Any

import redis

from app.config import settings

logger = logging.getLogger(__name__)

# Channel names (must match backend redis_subscriber.py)
CHANNEL_FEEDBACK_COMPLETED = "voc:feedback:completed"

# Redis client singleton
_redis_client: Optional[redis.Redis] = None


def get_redis_client() -> Optional[redis.Redis]:
    """
    Get or create Redis client singleton

    Returns:
        Redis client or None if connection fails
    """
    global _redis_client

    if _redis_client is None:
        try:
            _redis_client = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
            # Test connection
            _redis_client.ping()
            logger.info(f"Redis publisher connected: {settings.REDIS_URL}")
        except Exception as e:
            logger.warning(f"Redis publisher not available: {e}")
            _redis_client = None

    return _redis_client


def publish_analysis_completed(
    feedback_id: UUID,
    source_type: str,
    analysis_summary: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Publish analysis completed event to Redis

    Args:
        feedback_id: UUID of the feedback record
        source_type: Source type (email, instagram, facebook, etc.)
        analysis_summary: ML analysis results

    Returns:
        True if published successfully, False otherwise
    """
    message = {
        "event": "feedback:completed",
        "data": {
            "feedback_id": str(feedback_id),
            "source_type": source_type,
            "processing_status": "completed",
            "analysis_summary": analysis_summary or {},
            "timestamp": datetime.utcnow().isoformat()
        },
        "meta": {
            "message_id": str(uuid4()),
            "sent_at": datetime.utcnow().isoformat()
        }
    }

    return _publish_message(CHANNEL_FEEDBACK_COMPLETED, message, feedback_id)


def publish_analysis_failed(
    feedback_id: UUID,
    source_type: str,
    error_message: str = ""
) -> bool:
    """
    Publish analysis failed event to Redis

    Args:
        feedback_id: UUID of the feedback record
        source_type: Source type
        error_message: Error description

    Returns:
        True if published successfully, False otherwise
    """
    message = {
        "event": "feedback:failed",
        "data": {
            "feedback_id": str(feedback_id),
            "source_type": source_type,
            "processing_status": "failed",
            "error_message": error_message,
            "timestamp": datetime.utcnow().isoformat()
        },
        "meta": {
            "message_id": str(uuid4()),
            "sent_at": datetime.utcnow().isoformat()
        }
    }

    return _publish_message(CHANNEL_FEEDBACK_COMPLETED, message, feedback_id)


def _publish_message(channel: str, message: dict, feedback_id: UUID) -> bool:
    """
    Internal function to publish message to Redis channel

    Args:
        channel: Redis channel name
        message: Message payload
        feedback_id: Feedback ID for logging

    Returns:
        True if published successfully, False otherwise
    """
    client = get_redis_client()

    if not client:
        logger.warning(f"Redis not available, skipping broadcast for {feedback_id}")
        return False

    try:
        client.publish(channel, json.dumps(message))
        logger.info(f"Broadcast {message['event']}: {feedback_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to broadcast {message['event']}: {e}")
        return False
