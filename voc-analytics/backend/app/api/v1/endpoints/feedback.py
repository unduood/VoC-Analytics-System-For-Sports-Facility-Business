"""
Feedback CRUD endpoints
"""
import logging
from typing import Optional
from uuid import UUID
from math import ceil

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.feedback import FeedbackRecord
from app.schemas.feedback import (
    FeedbackResponse,
    FeedbackDetailResponse,
    FeedbackListResponse,
    ProcessingStatus
)
from app.exceptions import FeedbackNotFoundError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/feedback", tags=["Feedback"])


@router.get("", response_model=FeedbackListResponse)
async def list_feedback(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    source_type: Optional[str] = Query(None, description="Filter by source type"),
    processing_status: Optional[ProcessingStatus] = Query(None, description="Filter by processing status"),
    db: AsyncSession = Depends(get_db)
):
    """
    List all feedback records with pagination and optional filters

    **Query Parameters:**
    - page: Page number (default: 1)
    - page_size: Items per page (default: 20, max: 100)
    - source_type: Filter by source type (email, instagram, etc.)
    - processing_status: Filter by processing status (pending, processing, completed, failed)

    **Returns:**
    - items: List of feedback records
    - total: Total number of records
    - page: Current page number
    - page_size: Items per page
    - total_pages: Total number of pages
    """
    try:
        # Build base query
        query = select(FeedbackRecord)

        # Apply filters
        if source_type:
            query = query.where(FeedbackRecord.source_type == source_type)
        if processing_status:
            query = query.where(FeedbackRecord.processing_status == processing_status.value)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.order_by(FeedbackRecord.created_at.desc()).offset(offset).limit(page_size)

        # Execute query
        result = await db.execute(query)
        records = result.scalars().all()

        # Calculate total pages
        total_pages = ceil(total / page_size) if total > 0 else 0

        return FeedbackListResponse(
            items=[FeedbackResponse.model_validate(record) for record in records],
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
