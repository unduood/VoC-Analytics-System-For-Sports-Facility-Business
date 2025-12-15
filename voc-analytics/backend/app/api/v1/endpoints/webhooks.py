"""
Webhook endpoints for receiving data from external platforms via Make.com
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.config import settings
from app.schemas.webhooks import (
    EmailWebhookPayload,
    InstagramWebhookPayload,
    WebhookResponse
)
from app.services.ingestion import IngestionService
from app.exceptions import (
    WebhookAuthenticationError,
    DatabaseError,
    QueuePublishError
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


def verify_webhook_token(x_webhook_token: Optional[str] = Header(None)) -> bool:
    """
    Verify webhook authentication token

    Args:
        x_webhook_token: Token from X-Webhook-Token header

    Returns:
        bool: True if valid

    Raises:
        WebhookAuthenticationError: If token is invalid or missing
    """
    if not x_webhook_token:
        logger.warning("Webhook request missing authentication token")
        raise WebhookAuthenticationError()

    if x_webhook_token != settings.WEBHOOK_SECRET:
        logger.warning("Webhook request with invalid token")
        raise WebhookAuthenticationError()

    return True


@router.post("/email", response_model=WebhookResponse, status_code=status.HTTP_200_OK)
async def receive_email_webhook(
    payload: EmailWebhookPayload,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_webhook_token)
):
    """
    Receive email feedback from Make.com webhook

    This endpoint receives email data, creates a feedback record,
    and publishes it to the processing queue.

    **Authentication:** Requires X-Webhook-Token header

    **Request Body:**
    - email_id: Unique email identifier
    - sender_email: Sender email address
    - subject: Email subject
    - body_text: Email body text content
    - received_at: Email received timestamp (ISO format)

    **Returns:**
    - status: Response status
    - message: Success message
    - record_id: Created feedback record UUID
    - source_type: "email"
    """
    logger.info(f"Received email webhook: {payload.email_id}")

    try:
        # Create ingestion service
        ingestion_service = IngestionService(db)

        # Create feedback record and publish to queue
        record = await ingestion_service.ingest_and_publish(
            source_type="email",
            source_id=payload.email_id,
            text_content=payload.body_text,
            raw_data={
                "email_id": payload.email_id,
                "sender_email": payload.sender_email,
                "subject": payload.subject,
                "body_text": payload.body_text,
                "received_at": payload.received_at.isoformat()
            },
            created_at_source=payload.received_at
        )

        logger.info(f"Successfully processed email webhook: {record.id}")

        return WebhookResponse(
            status="success",
            message="Email feedback received and queued for processing",
            record_id=record.id,
            source_type="email"
        )

    except (DatabaseError, QueuePublishError) as e:
        logger.error(f"Error processing email webhook: {e}")
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message
        )
    except Exception as e:
        logger.error(f"Unexpected error processing email webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error processing email webhook"
        )


@router.post("/instagram", response_model=WebhookResponse, status_code=status.HTTP_200_OK)
async def receive_instagram_webhook(
    payload: InstagramWebhookPayload,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_webhook_token)
):
    """
    Receive Instagram comment feedback from Make.com webhook

    This endpoint receives Instagram comment data, creates a feedback record,
    and publishes it to the processing queue.

    **Authentication:** Requires X-Webhook-Token header

    **Request Body:**
    - comment_id: Unique comment identifier
    - comment_text: Comment text content
    - username: Instagram username
    - media_id: Media post ID
    - media_type: Media type (photo, video, etc.)
    - caption: Post caption (optional)
    - comment_timestamp: Comment creation timestamp (ISO format)
    - post_timestamp: Post creation timestamp (ISO format)

    **Returns:**
    - status: Response status
    - message: Success message
    - record_id: Created feedback record UUID
    - source_type: "instagram"
    """
    logger.info(f"Received Instagram webhook: {payload.comment_id}")

    try:
        # Create ingestion service
        ingestion_service = IngestionService(db)

        # Create feedback record and publish to queue
        record = await ingestion_service.ingest_and_publish(
            source_type="instagram",
            source_id=payload.comment_id,
            text_content=payload.comment_text,
            raw_data={
                "comment_id": payload.comment_id,
                "comment_text": payload.comment_text,
                "username": payload.username,
                "media_id": payload.media_id,
                "media_type": payload.media_type,
                "caption": payload.caption,
                "comment_timestamp": payload.comment_timestamp.isoformat(),
                "post_timestamp": payload.post_timestamp.isoformat()
            },
            created_at_source=payload.comment_timestamp
        )

        logger.info(f"Successfully processed Instagram webhook: {record.id}")

        return WebhookResponse(
            status="success",
            message="Instagram comment received and queued for processing",
            record_id=record.id,
            source_type="instagram"
        )

    except (DatabaseError, QueuePublishError) as e:
        logger.error(f"Error processing Instagram webhook: {e}")
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message
        )
    except Exception as e:
        logger.error(f"Unexpected error processing Instagram webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error processing Instagram webhook"
        )
