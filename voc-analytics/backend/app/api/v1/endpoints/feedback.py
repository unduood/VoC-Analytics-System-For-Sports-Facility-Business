"""
Feedback CRUD endpoints
"""
import logging
from typing import Optional
from uuid import UUID
from math import ceil
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func, delete, exists, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.feedback import FeedbackRecord
from app.models.analysis import SentimentResult, IntentResult
from app.schemas.feedback import (
    FeedbackResponse,
    FeedbackDetailResponse,
    FeedbackListResponse,
    FeedbackWithAnalysisResponse,
    ProcessingStatus,
    ManualFeedbackCreate
)
from app.schemas.analysis import Sentiment, Intent
from app.exceptions import FeedbackNotFoundError
from app.services.ingestion import IngestionService
from app.services.broadcast_service import broadcast_new_feedback

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/feedback", tags=["Feedback"])


@router.get("", response_model=FeedbackListResponse)
async def list_feedback(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    source_type: Optional[str] = Query(None, description="Filter by source type"),
    processing_status: Optional[ProcessingStatus] = Query(None, description="Filter by processing status"),
    sentiment: Optional[Sentiment] = Query(None, description="Filter by sentiment (positive, neutral, negative)"),
    intent: Optional[Intent] = Query(None, description="Filter by intent (feedback, question, complaint, off_topic)"),
    search: Optional[str] = Query(None, min_length=1, max_length=200, description="Search in text content"),
    start_date: Optional[date] = Query(None, description="Filter by start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="Filter by end date (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db)
):
    """
    List all feedback records with pagination and optional filters

    **Query Parameters:**
    - page: Page number (default: 1)
    - page_size: Items per page (default: 20, max: 100)
    - source_type: Filter by source type (email, instagram, etc.)
    - processing_status: Filter by processing status (pending, processing, completed, failed)
    - sentiment: Filter by sentiment analysis result (positive, neutral, negative)
    - intent: Filter by intent classification result (feedback, question, complaint, off_topic)
    - search: Search keyword in text content (case-insensitive)
    - start_date: Filter records created on or after this date (ISO format)
    - end_date: Filter records created on or before this date (ISO format)

    **Returns:**
    - items: List of feedback records
    - total: Total number of records
    - page: Current page number
    - page_size: Items per page
    - total_pages: Total number of pages
    """
    try:
        # Build filter conditions list
        filter_conditions = []

        # Use COALESCE for effective date (created_at_source with fallback to created_at)
        # This ensures manual feedback (which has no created_at_source) uses created_at
        effective_date = func.coalesce(FeedbackRecord.created_at_source, FeedbackRecord.created_at)

        # Basic filters
        if source_type:
            filter_conditions.append(FeedbackRecord.source_type == source_type)
        if processing_status:
            filter_conditions.append(FeedbackRecord.processing_status == processing_status.value)

        # Search filter (case-insensitive)
        if search:
            filter_conditions.append(FeedbackRecord.text_content.ilike(f"%{search}%"))

        # Date range filters using effective_date (created_at_source with fallback)
        if start_date:
            # Start of the day (00:00:00)
            start_datetime = datetime.combine(start_date, datetime.min.time())
            filter_conditions.append(effective_date >= start_datetime)
        if end_date:
            # End of the day (use next day's start for exclusive upper bound)
            end_datetime = datetime.combine(end_date + timedelta(days=1), datetime.min.time())
            filter_conditions.append(effective_date < end_datetime)

        # Sentiment filter (using EXISTS subquery)
        if sentiment:
            sentiment_exists = exists(
                select(SentimentResult.id).where(
                    and_(
                        SentimentResult.feedback_id == FeedbackRecord.id,
                        SentimentResult.sentiment == sentiment.value,
                        SentimentResult.is_deleted == False
                    )
                )
            )
            filter_conditions.append(sentiment_exists)

        # Intent filter (using EXISTS subquery)
        if intent:
            intent_exists = exists(
                select(IntentResult.id).where(
                    and_(
                        IntentResult.feedback_id == FeedbackRecord.id,
                        IntentResult.intent == intent.value,
                        IntentResult.is_deleted == False
                    )
                )
            )
            filter_conditions.append(intent_exists)

        # Build base query with eager loading of relationships
        query = select(FeedbackRecord).options(
            selectinload(FeedbackRecord.sentiment_results),
            selectinload(FeedbackRecord.intent_results),
            selectinload(FeedbackRecord.aspect_sentiment_results)
        )

        # Apply all filters
        if filter_conditions:
            query = query.where(and_(*filter_conditions))

        # Get total count (without relationships for efficiency)
        count_base = select(FeedbackRecord)
        if filter_conditions:
            count_base = count_base.where(and_(*filter_conditions))
        count_query = select(func.count()).select_from(count_base.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()

        # Apply pagination and order by effective date (created_at_source with fallback)
        offset = (page - 1) * page_size
        query = query.order_by(effective_date.desc()).offset(offset).limit(page_size)

        # Execute query
        result = await db.execute(query)
        records = result.scalars().all()

        # Calculate total pages
        total_pages = ceil(total / page_size) if total > 0 else 0

        return FeedbackListResponse(
            items=[FeedbackWithAnalysisResponse.from_orm_with_analysis(record) for record in records],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )

    except Exception as e:
        logger.error(f"Error listing feedback: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving feedback records"
        )


@router.get("/{feedback_id}", response_model=FeedbackDetailResponse)
async def get_feedback(
    feedback_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a single feedback record with all analysis results

    **Path Parameters:**
    - feedback_id: UUID of the feedback record

    **Returns:**
    - Feedback record with sentiment, intent, and aspect sentiment results
    """
    try:
        # Query with eager loading of relationships
        query = select(FeedbackRecord).where(
            FeedbackRecord.id == feedback_id
        ).options(
            selectinload(FeedbackRecord.sentiment_results),
            selectinload(FeedbackRecord.intent_results),
            selectinload(FeedbackRecord.aspect_sentiment_results)
        )

        result = await db.execute(query)
        record = result.scalar_one_or_none()

        if not record:
            logger.warning(f"Feedback not found: {feedback_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Feedback record with ID '{feedback_id}' not found"
            )

        return FeedbackDetailResponse.model_validate(record)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting feedback {feedback_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving feedback record"
        )


@router.delete("/{feedback_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_feedback(
    feedback_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a feedback record (hard delete)

    **Path Parameters:**
    - feedback_id: UUID of the feedback record

    **Returns:**
    - 204 No Content on success
    """
    try:
        # Check if record exists
        query = select(FeedbackRecord).where(FeedbackRecord.id == feedback_id)
        result = await db.execute(query)
        record = result.scalar_one_or_none()

        if not record:
            logger.warning(f"Feedback not found for deletion: {feedback_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Feedback record with ID '{feedback_id}' not found"
            )

        # Delete record (cascade will delete related analysis results)
        await db.delete(record)
        await db.commit()

        logger.info(f"Deleted feedback record: {feedback_id}")
        return None

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting feedback {feedback_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting feedback record"
        )


@router.post("/manual", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
async def create_manual_feedback(
    feedback_data: ManualFeedbackCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Submit manual feedback for processing

    **Request Body:**
    - text_content: The feedback text content (required)

    **Returns:**
    - Created feedback record with processing status 'pending'
    """
    try:
        # Create feedback record and publish to queue for ML analysis
        ingestion_service = IngestionService(db)

        # Generate unique source_id for manual feedback
        import uuid
        manual_source_id = f"manual_{uuid.uuid4().hex[:12]}"

        feedback_record = await ingestion_service.ingest_and_publish(
            source_type="manual",
            source_id=manual_source_id,
            text_content=feedback_data.text_content,
            raw_data={"submitted_manually": True},
            created_at_source=None
        )

        # Broadcast new feedback event via WebSocket
        await broadcast_new_feedback(
            feedback_id=feedback_record.id,
            source_type="manual",
            text_content=feedback_data.text_content
        )

        logger.info(f"Created manual feedback record: {feedback_record.id}")

        return FeedbackResponse.model_validate(feedback_record)

    except Exception as e:
        logger.error(f"Error creating manual feedback: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating feedback record"
        )
