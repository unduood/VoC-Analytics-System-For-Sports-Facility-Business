"""
Google Maps review endpoints for SerpAPI integration
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.config import settings
from app.models.feedback import FeedbackRecord
from app.schemas.google_maps import (
    GoogleMapsFetchRequest,
    GoogleMapsFetchResponse,
    ReviewProcessingDetail
)
from app.services.serpapi_service import SerpAPIService, SerpAPIError
from app.services.ingestion import IngestionService
from app.exceptions import (
    WebhookAuthenticationError,
    DatabaseError,
    QueuePublishError
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/google-maps", tags=["Google Maps"])


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
        logger.warning("Google Maps request missing authentication token")
        raise WebhookAuthenticationError()

    if x_webhook_token != settings.WEBHOOK_SECRET:
        logger.warning("Google Maps request with invalid token")
        raise WebhookAuthenticationError()

    return True


async def _get_existing_feedback_record(
    db: AsyncSession,
    source_type: str,
    source_id: str
) -> Optional[FeedbackRecord]:
    """
    Get existing feedback record by source_type and source_id

    Args:
        db: Database session
        source_type: Type of source (e.g., "google_maps")
        source_id: Unique ID from source (e.g., review_id)

    Returns:
        FeedbackRecord if exists, None otherwise
    """
    stmt = select(FeedbackRecord).where(
        FeedbackRecord.source_type == source_type,
        FeedbackRecord.source_id == source_id
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


def _check_if_update_needed(
    existing_record: FeedbackRecord,
    new_data: dict
) -> bool:
    """
    Check if existing record needs update by comparing BOTH:
    1. original snippet (actual review text content) - PRIMARY
    2. iso_date_of_last_edit (timestamp when review was last edited) - SECONDARY

    Update is triggered if EITHER changes (OR condition)

    Args:
        existing_record: Existing feedback record from database
        new_data: New data from SerpAPI

    Returns:
        True if update needed (text OR timestamp changed), False otherwise
    """
    try:
        # Check 1: Compare original snippet (review text content)
        existing_snippet = existing_record.raw_data.get("original", existing_record.raw_data.get("snippet", ""))
        new_snippet = new_data["raw_data"].get("original", new_data["raw_data"].get("snippet", ""))
        snippet_changed = existing_snippet != new_snippet

        # Check 2: Compare iso_date_of_last_edit (edit timestamp)
        existing_last_edit = existing_record.raw_data.get("iso_date_of_last_edit")
        new_last_edit = new_data["raw_data"].get("iso_date_of_last_edit")
        timestamp_changed = existing_last_edit != new_last_edit

        # Update if EITHER changed (OR condition)
        if snippet_changed or timestamp_changed:
            logger.info(
                f"Review update detected: "
                f"snippet_changed={snippet_changed}, timestamp_changed={timestamp_changed} | "
                f"old_edit_date={existing_last_edit}, new_edit_date={new_last_edit} | "
                f"old_text='{existing_snippet[:50]}...', new_text='{new_snippet[:50]}...'"
            )
            return True

        # No changes detected
        logger.debug(f"No changes detected for review: {existing_record.source_id}")
        return False

    except Exception as e:
        logger.warning(f"Error comparing review data: {e}, assuming update needed for safety")
        return True


async def _delete_and_recreate_feedback(
    db: AsyncSession,
    existing_record: FeedbackRecord,
    new_data: dict,
    ingestion_service: IngestionService
) -> FeedbackRecord:
    """
    Hard delete existing feedback record and create a new one with updated data

    This approach is used when review content has actually changed (not just metadata).
    Hard delete ensures:
    - All old analysis results are removed (via CASCADE)
    - No orphaned data or audit trail confusion
    - Clean slate for re-analysis

    Steps:
    1. Hard delete old feedback record (CASCADE deletes all analysis results)
    2. Create new feedback record with updated data
    3. Commit changes
    4. Publish new record to RabbitMQ for analysis

    Args:
        db: Database session
        existing_record: Existing feedback record to delete
        new_data: New review data from SerpAPI
        ingestion_service: Ingestion service for queue publishing

    Returns:
        FeedbackRecord: Newly created feedback record
    """
    old_id = existing_record.id
    logger.info(
        f"Hard deleting existing review (content changed): "
        f"old_id={old_id}, source_id={existing_record.source_id}"
    )

    # 1. Hard delete old record
    # CASCADE will automatically delete all related:
    # - sentiment_results
    # - intent_results
    # - aspect_sentiment_results
    await db.delete(existing_record)
    await db.flush()  # Ensure delete is processed before insert

    logger.info(f"Old feedback record deleted: {old_id} (CASCADE deleted all analysis results)")

    # 2. Create new feedback record with updated content
    new_record = FeedbackRecord(
        source_type="google_maps",
        source_id=new_data["source_id"],
        text_content=new_data["text_content"],
        raw_data=new_data["raw_data"],
        created_at_source=new_data["created_at_source"],
        processing_status="pending"
    )

    db.add(new_record)
    await db.commit()
    await db.refresh(new_record)

    logger.info(
        f"New feedback record created: new_id={new_record.id}, "
        f"source_id={new_record.source_id}, "
        f"text='{new_record.text_content[:50]}...'"
    )

    # 3. Publish new record to queue for ML analysis
    ingestion_service.publish_to_queue(new_record.id)

    logger.info(f"New record published to queue: {new_record.id}")

    return new_record


@router.post("/fetch-reviews", response_model=GoogleMapsFetchResponse)
async def fetch_google_maps_reviews(
    request: GoogleMapsFetchRequest,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_webhook_token)
):
    """
    Fetch latest Google Maps reviews via SerpAPI and process them

    This endpoint:
    1. Fetches reviews from SerpAPI (20 latest reviews)
    2. Checks for duplicates/updates via (source_type, source_id)
    3. Creates new records or updates existing ones
    4. Publishes to RabbitMQ for ML processing

    **Authentication:** Requires X-Webhook-Token header

    **Request Body:**
    - api_key: SerpAPI key (optional if SERPAPI_KEY in env)
    - data_id: Google Maps place ID (optional if GOOGLE_MAPS_DATA_ID in env)

    **Returns:**
    - status: Response status
    - message: Summary message
    - total_fetched: Total reviews from SerpAPI
    - processed: New reviews created
    - updated: Existing reviews updated
    - skipped: Reviews with no changes
    - failed: Reviews that failed processing
    - details: List of per-review processing results
    """
    # 1. Resolve configuration (request body OR environment variables)
    api_key = request.api_key or settings.SERPAPI_KEY
    data_id = request.data_id or settings.GOOGLE_MAPS_DATA_ID

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="SerpAPI key required (provide in request or set SERPAPI_KEY in environment)"
        )
    if not data_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google Maps data_id required (provide in request or set GOOGLE_MAPS_DATA_ID in environment)"
        )

    logger.info(f"Fetching Google Maps reviews for data_id: {data_id}")

    # 2. Fetch reviews from SerpAPI
    try:
        serpapi_service = SerpAPIService(api_key)
        reviews = await serpapi_service.fetch_google_maps_reviews(data_id, max_reviews=20)
    except SerpAPIError as e:
        logger.error(f"SerpAPI error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to fetch reviews from SerpAPI: {str(e)}"
        )

    # 3. Process each review
    ingestion_service = IngestionService(db)
    results = {
        "processed": 0,
        "updated": 0,
        "skipped": 0,
        "failed": 0,
        "details": []
    }

    for review in reviews:
        review_id = "unknown"  # Initialize for error handling
        feedback_data = None  # Initialize for error handling

        try:
            # Check if this is a rating-only review (no text content)
            snippet = review.get("snippet", "")
            review_id = review.get("review_id", "unknown")

            if not snippet or not snippet.strip():
                # Rating-only review - skip (not an error)
                results["skipped"] += 1
                results["details"].append(ReviewProcessingDetail(
                    review_id=review_id,
                    action="skipped",
                    reason="Rating-only review (no text content)"
                ))
                logger.debug(f"Skipped rating-only review: {review_id}")
                continue

            # Parse review
            feedback_data = SerpAPIService.parse_review_to_feedback_data(review)
            if not feedback_data:
                # Has snippet but parse failed - this is an error
                results["failed"] += 1
                results["details"].append(ReviewProcessingDetail(
                    review_id=review_id,
                    action="failed",
                    reason="Failed to parse review data"
                ))
                logger.warning(f"Failed to parse review: {review_id}")
                continue

            # Check for existing record
            existing_record = await _get_existing_feedback_record(
                db,
                source_type="google_maps",
                source_id=feedback_data["source_id"]
            )

            if existing_record:
                # Check if update needed (text content changed)
                needs_update = _check_if_update_needed(existing_record, feedback_data)

                if needs_update:
                    # DELETE AND RECREATE LOGIC (Hard delete old, create new)
                    new_record = await _delete_and_recreate_feedback(
                        db,
                        existing_record,
                        feedback_data,
                        ingestion_service
                    )
                    results["updated"] += 1
                    results["details"].append(ReviewProcessingDetail(
                        review_id=feedback_data["source_id"],
                        action="updated",
                        record_id=new_record.id,  # Return new record ID
                        reason="Review content changed (old record deleted, new record created)"
                    ))
                    logger.info(f"Recreated review: {feedback_data['source_id']}")
                else:
                    # SKIP LOGIC (No content changes)
                    results["skipped"] += 1
                    results["details"].append(ReviewProcessingDetail(
                        review_id=feedback_data["source_id"],
                        action="skipped",
                        record_id=existing_record.id,
                        reason="No changes detected (same content)"
                    ))
                    logger.debug(f"Skipped unchanged review: {feedback_data['source_id']}")
            else:
                # CREATE LOGIC
                record = await ingestion_service.ingest_and_publish(
                    source_type="google_maps",
                    source_id=feedback_data["source_id"],
                    text_content=feedback_data["text_content"],
                    raw_data=feedback_data["raw_data"],
                    created_at_source=feedback_data["created_at_source"]
                )
                results["processed"] += 1
                results["details"].append(ReviewProcessingDetail(
                    review_id=feedback_data["source_id"],
                    action="created",
                    record_id=record.id
                ))
                logger.info(f"Created new review: {feedback_data['source_id']}")

        except (DatabaseError, QueuePublishError) as e:
            # Specific database/queue errors
            logger.error(f"Database/Queue error processing review {review_id}: {e}")
            results["failed"] += 1
            results["details"].append(ReviewProcessingDetail(
                review_id=feedback_data.get("source_id") if feedback_data else review_id,
                action="failed",
                reason=f"Database/Queue error: {str(e)}"
            ))
        except Exception as e:
            # Catch-all for unexpected errors
            logger.error(f"Unexpected error processing review {review_id}: {e}", exc_info=True)
            results["failed"] += 1
            results["details"].append(ReviewProcessingDetail(
                review_id=feedback_data.get("source_id") if feedback_data else review_id,
                action="failed",
                reason=f"Unexpected error: {str(e)}"
            ))

    # 4. Return detailed response
    logger.info(
        f"Completed processing {len(reviews)} reviews: "
        f"processed={results['processed']}, updated={results['updated']}, "
        f"skipped={results['skipped']}, failed={results['failed']}"
    )

    return GoogleMapsFetchResponse(
        status="success",
        message=f"Processed {len(reviews)} Google Maps reviews",
        total_fetched=len(reviews),
        **results
    )
