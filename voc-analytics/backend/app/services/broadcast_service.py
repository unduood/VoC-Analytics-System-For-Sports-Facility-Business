"""
Service for broadcasting events via Redis Pub/Sub
"""
import json
import logging
from datetime import datetime
from uuid import UUID, uuid4
from typing import Optional, Dict, Any

from app.redis_client import redis_manager

logger = logging.getLogger(__name__)

# Channel names (must match redis_subscriber.py)
CHANNEL_FEEDBACK_NEW = "voc:feedback:new"
CHANNEL_FEEDBACK_COMPLETED = "voc:feedback:completed"


async def broadcast_new_feedback(
    feedback_id: UUID,
    source_type: str,
    text_content: str,
    processing_status: str = "pending"
) -> bool:
    """
    Publish new feedback event to Redis

    Args:
        feedback_id: UUID of the feedback record
        source_type: Source type (email, instagram, facebook, etc.)
        text_content: Feedback text content (will be truncated)
        processing_status: Current processing status

    Returns:
        True if published successfully, False otherwise
    """
    message = {
        "event": "feedback:new",
        "data": {
            "feedback_id": str(feedback_id),
            "source_type": source_type,
            "text_content": text_content[:200] if text_content else "",
            "processing_status": processing_status,
            "timestamp": datetime.utcnow().isoformat()
        },
        "meta": {
            "message_id": str(uuid4()),
            "sent_at": datetime.utcnow().isoformat()
        }
    }

    return await _publish_message(CHANNEL_FEEDBACK_NEW, message, feedback_id)


async def broadcast_analysis_completed(
    feedback_id: UUID,
    source_type: str,
    analysis_summary: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Publish analysis completed event to Redis

    Args:
        feedback_id: UUID of the feedback record
        source_type: Source type
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

    return await _publish_message(CHANNEL_FEEDBACK_COMPLETED, message, feedback_id)


async def broadcast_analysis_failed(
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

    return await _publish_message(CHANNEL_FEEDBACK_COMPLETED, message, feedback_id)


async def _publish_message(channel: str, message: dict, feedback_id: UUID) -> bool:
    """
    Internal function to publish message to Redis channel

    Args:
        channel: Redis channel name
        message: Message payload
        feedback_id: Feedback ID for logging

    Returns:
        True if published successfully, False otherwise
    """
    if not redis_manager.client:
        logger.warning(f"Redis not available, cannot broadcast {message['event']}")
        return False

    try:
        await redis_manager.client.publish(channel, json.dumps(message))
        logger.info(f"Broadcast {message['event']}: {feedback_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to broadcast {message['event']}: {e}")
        return False
