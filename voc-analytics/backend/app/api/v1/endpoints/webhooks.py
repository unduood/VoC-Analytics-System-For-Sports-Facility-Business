"""
Webhook endpoints for receiving data from external platforms via Make.com
"""
import hmac
import hashlib
import json
import logging
import uuid
from typing import Optional, Dict, Any
from datetime import datetime
from collections import deque

from fastapi import APIRouter, Depends, Header, HTTPException, status, Query, Request
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from dateutil import parser as date_parser
from datetime import timezone

from app.database import get_db
from app.config import settings
from app.schemas.webhooks import (
    EmailWebhookPayload,
    InstagramWebhookPayload,
    FacebookWebhookPayload,
    GoogleFormWebhookPayload,
    WebhookResponse
)
from app.services.ingestion import IngestionService
from app.services.facebook_service import FacebookService
from app.exceptions import (
    WebhookAuthenticationError,
    DatabaseError,
    QueuePublishError,
    FacebookGraphAPIError
)
from app.models.feedback import FeedbackRecord
from app.models.analysis import SentimentResult, IntentResult, AspectSentimentResult
from app.services.broadcast_service import broadcast_new_feedback

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])

# In-memory store for idempotency (use Redis in production)
# Using deque with maxlen for automatic FIFO eviction
_processed_webhooks = deque(maxlen=10000)


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


async def get_raw_body(request: Request) -> bytes:
    """
    Extract raw request body for signature verification

    Args:
        request: FastAPI request object

    Returns:
        bytes: Raw request body
    """
    return await request.body()


async def verify_facebook_signature(
    request: Request,
    x_hub_signature_256: Optional[str] = Header(None, alias="X-Hub-Signature-256")
) -> bool:
    """
    Verify Facebook webhook signature using HMAC-SHA256

    Facebook sends X-Hub-Signature-256 header with format: sha256=<hex_digest>
    We compute HMAC-SHA256(app_secret, raw_body) and compare with the signature.

    This is the official Facebook webhook security method per:
    https://developers.facebook.com/docs/graph-api/webhooks/getting-started#verification-requests

    Args:
        request: FastAPI request object
        x_hub_signature_256: Signature from X-Hub-Signature-256 header

    Returns:
        bool: True if valid

    Raises:
        HTTPException: If signature is invalid or missing
    """
    if not x_hub_signature_256:
        logger.warning("Facebook webhook missing X-Hub-Signature-256 header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-Hub-Signature-256 header"
        )

    if not settings.FACEBOOK_APP_SECRET:
        logger.error("FACEBOOK_APP_SECRET not configured")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Facebook webhook signature validation not configured"
        )

    # Get raw request body
    body = await request.body()

    # Compute expected signature
    expected_signature = "sha256=" + hmac.new(
        settings.FACEBOOK_APP_SECRET.encode('utf-8'),
        body,
        hashlib.sha256
    ).hexdigest()

    # Use constant-time comparison to prevent timing attacks
    if not hmac.compare_digest(x_hub_signature_256, expected_signature):
        logger.warning(
            f"Facebook webhook signature mismatch. "
            f"Expected: {expected_signature[:20]}..., Got: {x_hub_signature_256[:20]}..."
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid webhook signature"
        )

    logger.debug("Facebook webhook signature verified successfully")
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

        # Broadcast new feedback event via WebSocket
        await broadcast_new_feedback(
            feedback_id=record.id,
            source_type="email",
            text_content=payload.body_text
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

        # Broadcast new feedback event via WebSocket
        await broadcast_new_feedback(
            feedback_id=record.id,
            source_type="instagram",
            text_content=payload.comment_text
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


@router.post("/google-form", response_model=WebhookResponse, status_code=status.HTTP_200_OK)
async def receive_google_form_webhook(
    payload: GoogleFormWebhookPayload,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_webhook_token)
):
    """
    Receive Google Form survey response webhook

    This endpoint receives survey data with ratings, creates a feedback record,
    and publishes it to the processing queue. Unlike other sources, Google Forms
    responses use rating-based analysis instead of ML processing.

    **Authentication:** Requires X-Webhook-Token header

    **Request Body:**
    - Demographics: gender, age_group, timestamp, membership_type, visit_frequency, preferred_period
    - Text: additional_suggestions (optional)
    - Ratings (1-5): overall_rating, equipment_rating, staff_rating, cleanliness_rating,
                     atmosphere_rating, price_rating, location_rating, program_rating, amenities_rating

    **Returns:**
    - status: Response status
    - message: Success message
    - record_id: Created feedback record UUID
    - source_type: "google_form"
    """
    # Generate UUID for source_id (no deduplication for survey responses)
    source_id = str(uuid.uuid4())
    logger.info(f"Received Google Form webhook, generated source_id: {source_id}")

    try:
        # Create ingestion service
        ingestion_service = IngestionService(db)

        # Build text content
        text_content = "[แบบสอบถาม Google Forms]"
        if payload.additional_suggestions:
            text_content = f"{text_content} {payload.additional_suggestions}"

        # Build raw_data with all 16 fields (flat structure)
        raw_data = {
            # Demographics
            "gender": payload.gender,
            "age_group": payload.age_group,
            "timestamp": payload.timestamp.isoformat(),
            "membership_type": payload.membership_type,
            "visit_frequency": payload.visit_frequency,
            "preferred_period": payload.preferred_period,
            # Optional text
            "additional_suggestions": payload.additional_suggestions,
            # Ratings
            "overall_rating": payload.overall_rating,
            "equipment_rating": payload.equipment_rating,
            "staff_rating": payload.staff_rating,
            "cleanliness_rating": payload.cleanliness_rating,
            "atmosphere_rating": payload.atmosphere_rating,
            "price_rating": payload.price_rating,
            "location_rating": payload.location_rating,
            "program_rating": payload.program_rating,
            "amenities_rating": payload.amenities_rating,
        }

        # Create feedback record and publish to queue
        record = await ingestion_service.ingest_and_publish(
            source_type="google_form",
            source_id=source_id,
            text_content=text_content,
            raw_data=raw_data,
            created_at_source=payload.timestamp
        )

        # Broadcast new feedback event via WebSocket
        await broadcast_new_feedback(
            feedback_id=record.id,
            source_type="google_form",
            text_content=text_content
        )

        logger.info(f"Successfully processed Google Form webhook: {record.id}")

        return WebhookResponse(
            status="success",
            message="Google Form response received and queued for processing",
            record_id=record.id,
            source_type="google_form"
        )

    except (DatabaseError, QueuePublishError) as e:
        logger.error(f"Error processing Google Form webhook: {e}")
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message
        )
    except Exception as e:
        logger.error(f"Unexpected error processing Google Form webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error processing Google Form webhook"
        )


# ============================================================================
# Facebook Page Webhook Endpoints
# ============================================================================


@router.get("/facebook", include_in_schema=True)
async def verify_facebook_webhook(
    request: Request,
    hub_mode: str = Query(..., alias="hub.mode"),
    hub_challenge: str = Query(..., alias="hub.challenge"),
    hub_verify_token: str = Query(..., alias="hub.verify_token")
):
    """
    Facebook webhook verification endpoint (GET request)

    Facebook sends a GET request to verify the webhook during setup.
    This endpoint must return the hub.challenge value if verification succeeds.

    **Query Parameters:**
    - hub.mode: Should be "subscribe"
    - hub.verify_token: Must match FACEBOOK_VERIFY_TOKEN in settings
    - hub.challenge: Random string to echo back

    **Returns:**
    - Plain text response with hub.challenge value (200 OK)
    - Or 403 Forbidden if verification fails
    """
    logger.info(f"Facebook webhook verification attempt from {request.client.host}")

    if hub_mode == "subscribe" and hub_verify_token == settings.FACEBOOK_VERIFY_TOKEN:
        logger.info("Facebook webhook verified successfully")
        return PlainTextResponse(content=hub_challenge, status_code=200)
    else:
        logger.warning(f"Facebook webhook verification failed: invalid token or mode")
        raise HTTPException(status_code=403, detail="Verification token mismatch")


@router.post("/facebook", response_model=WebhookResponse, status_code=status.HTTP_200_OK)
async def receive_facebook_webhook(
    request: Request,
    payload: FacebookWebhookPayload,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_facebook_signature)
):
    """
    Facebook Page webhook endpoint for feed events

    Receives real-time notifications when:
    - New comments are posted (verb: "add")
    - Comments are edited (verb: "edited")
    - Comments are removed (verb: "remove")

    **Authentication:** Validates X-Hub-Signature-256 header using HMAC-SHA256

    **Security:**
    - Uses Facebook's official signature verification method
    - Validates HMAC-SHA256(app_secret, raw_body) against X-Hub-Signature-256 header
    - Prevents replay attacks and unauthorized webhook calls

    **Request Body:**
    - object: Object type (should be "page")
    - entry: Array of entries containing changes

    **Returns:**
    - status: Response status
    - message: Success message
    - record_id: Created feedback record UUID (optional)
    - source_type: "facebook"

    **Idempotency:**
    - Duplicate webhook deliveries are detected and skipped
    - Based on combination of entry.id and change timestamp
    """
    logger.info(f"Received Facebook webhook with {len(payload.entry)} entries")

    try:
        # Initialize services
        ingestion_service = IngestionService(db)

        # Initialize Facebook service (may raise ValueError if token not configured)
        try:
            fb_service = FacebookService()
        except ValueError as e:
            logger.error(f"Facebook service initialization failed: {e}")
            # Return 200 to Facebook to prevent retries for configuration errors
            return WebhookResponse(
                status="error",
                message="Facebook service not properly configured",
                record_id=None,
                source_type="facebook"
            )

        record = None  # Track last processed record

        # Process each entry
        for entry in payload.entry:
            # Idempotency check: Create unique key for this webhook event
            entry_id = entry.id
            entry_time = entry.time

            for change in entry.changes:
                # Only process feed changes
                if change.get("field") != "feed":
                    logger.debug(f"Skipping non-feed change: {change.get('field')}")
                    continue

                value = change.get("value", {})
                item = value.get("item")

                # Only process comments
                if item != "comment":
                    logger.debug(f"Skipping non-comment item: {item}")
                    continue

                verb = value.get("verb")
                comment_id = value.get("comment_id")

                if not comment_id:
                    logger.warning("Comment ID missing in webhook payload")
                    continue

                # Idempotency: Check if we've already processed this exact event
                idempotency_key = f"{entry_id}:{entry_time}:{comment_id}:{verb}"
                if idempotency_key in _processed_webhooks:
                    logger.info(f"Skipping duplicate webhook event: {idempotency_key}")
                    continue

                logger.info(f"Processing Facebook comment event: {verb} - {comment_id}")
                logger.debug(f"Webhook value payload: {json.dumps(value, indent=2, default=str)}")

                # Handle different actions
                try:
                    if verb == "add":
                        record = await handle_new_comment(
                            comment_id, value, db, ingestion_service, fb_service
                        )

                    elif verb == "edited":
                        record = await handle_edited_comment(
                            comment_id, value, db, ingestion_service, fb_service
                        )

                    elif verb == "remove":
                        record = await handle_removed_comment(
                            comment_id, db
                        )

                    else:
                        logger.warning(f"Unknown verb: {verb}")
                        continue

                    # Mark as processed after successful handling
                    # deque with maxlen=10000 will automatically evict oldest entries
                    _processed_webhooks.append(idempotency_key)

                except Exception as e:
                    logger.error(f"Error handling {verb} event for {comment_id}: {e}", exc_info=True)
                    # Don't mark as processed if it failed - allow retry
                    # But continue processing other events
                    continue

        return WebhookResponse(
            status="success",
            message="Facebook webhook processed successfully",
            record_id=record.id if record else None,
            source_type="facebook"
        )

    except FacebookGraphAPIError as e:
        logger.error(f"Facebook Graph API error: {e}")
        # Return 200 to Facebook - Graph API errors should not trigger retries
        # The webhook was received successfully, but we couldn't fetch additional data
        return WebhookResponse(
            status="partial_success",
            message=f"Webhook received but Graph API error: {str(e)}",
            record_id=None,
            source_type="facebook"
        )
    except (DatabaseError, QueuePublishError) as e:
        logger.error(f"Error processing Facebook webhook: {e}")
        # Return 200 to Facebook - internal errors should not trigger retries
        # Log for monitoring and manual intervention
        return WebhookResponse(
            status="error",
            message=f"Internal processing error: {e.message}",
            record_id=None,
            source_type="facebook"
        )
    except Exception as e:
        logger.error(f"Unexpected error processing Facebook webhook: {e}", exc_info=True)
        # Return 200 to Facebook to prevent infinite retries
        return WebhookResponse(
            status="error",
            message="Internal server error - webhook logged for review",
            record_id=None,
            source_type="facebook"
        )


# ============================================================================
# Facebook Event Handlers (Helper Functions)
# ============================================================================


async def handle_new_comment(
    comment_id: str,
    webhook_value: Dict[str, Any],
    db: AsyncSession,
    ingestion_service: IngestionService,
    fb_service: FacebookService
) -> FeedbackRecord:
    """
    Handle new comment event

    Steps:
    1. Extract comment details from webhook payload (message, created_time, name, is_hidden)
    2. Extract post_id from webhook
    3. Fetch post details from Graph API (with Redis cache) if needed
    4. Create feedback record with flat raw_data structure
    5. Publish to RabbitMQ for ML processing

    Args:
        comment_id: Facebook comment ID
        webhook_value: Webhook value object containing comment data
        db: Database session
        ingestion_service: Ingestion service instance
        fb_service: Facebook service instance

    Returns:
        Created FeedbackRecord

    Raises:
        FacebookGraphAPIError: If Graph API request fails for post details
    """
    logger.info(f"Processing new comment: {comment_id}")

    # Extract comment data from webhook payload directly
    # Webhook provides: message, created_time (Unix timestamp), from, is_hidden, post_id
    comment_message = webhook_value.get("message", "")
    comment_created_time_unix = webhook_value.get("created_time")  # Unix timestamp (int)
    comment_from = webhook_value.get("from", {})
    comment_is_hidden = webhook_value.get("is_hidden", False)

    # Extract user info from 'from' field
    user_id = comment_from.get("id") if isinstance(comment_from, dict) else None
    user_name = comment_from.get("name") if isinstance(comment_from, dict) else None

    # Extract post_id from webhook (format: {page-id}_{post-id})
    post_id = webhook_value.get("post_id")
    if not post_id:
        logger.warning(f"Post ID not found in webhook for comment {comment_id}")
        post_id = None

    # Convert Unix timestamp to datetime object (UTC)
    # Facebook sends Unix timestamps which are always in UTC
    created_at_source = None
    comment_created_time_iso = None
    if comment_created_time_unix:
        try:
            # Convert Unix timestamp to UTC datetime (timezone-aware)
            created_at_source = datetime.fromtimestamp(comment_created_time_unix, tz=timezone.utc)
            # Store ISO format with timezone for raw_data
            comment_created_time_iso = created_at_source.isoformat()
            logger.debug(f"Converted Unix timestamp {comment_created_time_unix} to {comment_created_time_iso}")
        except (ValueError, TypeError, OSError) as e:
            logger.warning(f"Failed to convert Unix timestamp '{comment_created_time_unix}': {e}")

    # Extract post data from webhook (has some info already)
    post_webhook = webhook_value.get("post", {})
    post_permalink = post_webhook.get("permalink_url") if isinstance(post_webhook, dict) else None

    # Fetch post details from Graph API (cached in Redis) for message and created_time
    # If Graph API fails, post_message and post_created_time will be null
    post_message = None
    post_created_time_iso = None
    if post_id:
        try:
            post_data = await fb_service.get_post_details(post_id)
            post_message = post_data.get("message")
            post_created_time_iso = post_data.get("created_time")  # ISO string from API
            logger.info(f"Fetched post details from Graph API: {post_id}")
        except FacebookGraphAPIError as e:
            logger.warning(f"Failed to fetch post details for {post_id}: {e}")
            # Leave post_message and post_created_time as null
            # Better to have no data than incorrect data

    # Prepare raw_data with FLAT structure (similar to email/instagram)
    # Store fields in logical order: comment fields first, then post fields
    raw_data = {
        # Comment fields (primary data)
        "comment_id": comment_id,
        "message": comment_message,
        "created_time": comment_created_time_iso,
        "name": user_name,
        "user_id": user_id,
        "is_hidden": comment_is_hidden,

        # Post fields (context data)
        "post_id": post_id,
        "post_message": post_message,
        "post_created_time": post_created_time_iso,
        "post_permalink_url": post_permalink,
    }

    # Create feedback record
    # - id: auto-generated UUID by database
    # - source_id: comment_id from Facebook
    # - text_content: comment message
    # - raw_data: flat structure with all comment and post data
    # - created_at_source: datetime object from Unix timestamp
    record = await ingestion_service.ingest_and_publish(
        source_type="facebook",
        source_id=comment_id,
        text_content=comment_message,
        raw_data=raw_data,
        created_at_source=created_at_source
    )

    # Broadcast new feedback event via WebSocket
    await broadcast_new_feedback(
        feedback_id=record.id,
        source_type="facebook",
        text_content=comment_message
    )

    logger.info(f"Created feedback record {record.id} for comment {comment_id}")
    return record


async def handle_edited_comment(
    comment_id: str,
    webhook_value: Dict[str, Any],
    db: AsyncSession,
    ingestion_service: IngestionService,
    fb_service: FacebookService
) -> FeedbackRecord:
    """
    Handle edited comment event

    Strategy: Hard delete + recreate
    1. Find existing feedback record by source_id
    2. Hard delete existing record (CASCADE deletes all analysis results)
    3. Create new feedback record with updated data
    4. Publish to RabbitMQ for re-analysis

    Args:
        comment_id: Facebook comment ID
        webhook_value: Webhook value object
        db: Database session
        ingestion_service: Ingestion service instance
        fb_service: Facebook service instance

    Returns:
        Newly created FeedbackRecord

    Raises:
        FacebookGraphAPIError: If Graph API request fails
    """
    logger.info(f"Processing edited comment: {comment_id}")

    # Find existing record
    stmt = select(FeedbackRecord).where(
        FeedbackRecord.source_type == "facebook",
        FeedbackRecord.source_id == comment_id
    )
    result = await db.execute(stmt)
    existing_record = result.scalar_one_or_none()

    if existing_record:
        # Hard delete (CASCADE will delete all analysis results)
        logger.info(f"Deleting old record {existing_record.id} for edited comment")
        await db.delete(existing_record)
        await db.flush()  # Ensure delete is processed before creating new record
    else:
        logger.warning(f"No existing record found for edited comment {comment_id}")

    # Create new record with updated data
    # Note: handle_new_comment calls ingest_and_publish which commits automatically
    record = await handle_new_comment(
        comment_id, webhook_value, db, ingestion_service, fb_service
    )

    logger.info(f"Created new record {record.id} for edited comment {comment_id}")
    return record


async def handle_removed_comment(
    comment_id: str,
    db: AsyncSession
) -> Optional[FeedbackRecord]:
    """
    Handle removed comment event

    Strategy: Hard delete
    - Deletes feedback record from database
    - CASCADE automatically deletes all related analysis results
    - No historical record kept (as per requirements)

    Args:
        comment_id: Facebook comment ID
        db: Database session

    Returns:
        Deleted FeedbackRecord or None if not found
    """
    logger.info(f"Processing removed comment: {comment_id}")

    # Find existing record
    stmt = select(FeedbackRecord).where(
        FeedbackRecord.source_type == "facebook",
        FeedbackRecord.source_id == comment_id
    )
    result = await db.execute(stmt)
    record = result.scalar_one_or_none()

    if not record:
        logger.warning(f"No record found for removed comment {comment_id}")
        return None

    # Hard delete (CASCADE will automatically delete all analysis results)
    logger.info(f"Hard deleting record {record.id} for removed comment {comment_id}")
    await db.delete(record)
    await db.commit()

    logger.info(f"Successfully deleted record for removed comment {comment_id}")
    return record
