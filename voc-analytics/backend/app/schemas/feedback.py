"""
Feedback schemas for request/response validation
"""
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict


class SourceType(str, Enum):
    """Source type enumeration"""
    EMAIL = "email"
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    GOOGLE_FORM = "google_form"
    GOOGLE_MAPS = "google_maps"
    MANUAL = "manual"


class ProcessingStatus(str, Enum):
    """Processing status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# Base schema
class FeedbackBase(BaseModel):
    """Base feedback schema"""
    source_type: SourceType
    source_id: Optional[str] = None
    text_content: str = Field(..., min_length=1, description="Main text content")
    raw_data: Optional[Dict[str, Any]] = None
    created_at_source: Optional[datetime] = None


# Create schema
class FeedbackCreate(FeedbackBase):
    """Schema for creating feedback"""
    pass


# Update schema
class FeedbackUpdate(BaseModel):
    """Schema for updating feedback"""
    text_content: Optional[str] = Field(None, min_length=1)
    raw_data: Optional[Dict[str, Any]] = None
    processing_status: Optional[ProcessingStatus] = None


# Manual feedback create schema
class ManualFeedbackCreate(BaseModel):
    """Schema for creating manual feedback (simplified)"""
    text_content: str = Field(..., min_length=1, max_length=5000, description="Feedback text content")


# Response schema
class FeedbackResponse(FeedbackBase):
    """Schema for feedback response"""
    id: UUID
    processing_status: ProcessingStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Response with relationships
class FeedbackDetailResponse(FeedbackResponse):
    """Schema for detailed feedback response with analysis results"""
    sentiment_results: list["SentimentResponse"] = []
    intent_results: list["IntentResponse"] = []
    aspect_sentiment_results: list["AspectSentimentResponse"] = []

    model_config = ConfigDict(from_attributes=True)


# Response with analysis for list (matches frontend expected format)
class FeedbackWithAnalysisResponse(FeedbackResponse):
    """Schema for feedback response with analysis results (frontend format)"""
    sentiment_result: Optional["SentimentResponse"] = None
    intent_results: list["IntentResponse"] = []
    aspect_results: list["AspectSentimentResponse"] = []
    analysis_summary: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_orm_with_analysis(cls, record) -> "FeedbackWithAnalysisResponse":
        """Create response from ORM record with relationships loaded"""
        return cls(
            id=record.id,
            source_type=record.source_type,
            source_id=record.source_id,
            text_content=record.text_content,
            raw_data=record.raw_data,
            created_at_source=record.created_at_source,
            processing_status=record.processing_status,
            created_at=record.created_at,
            updated_at=record.updated_at,
            sentiment_result=record.sentiment_results[0] if record.sentiment_results else None,
            intent_results=record.intent_results or [],
            aspect_results=record.aspect_sentiment_results or [],
            analysis_summary=record.analysis_summary,
        )


# List response
class FeedbackListResponse(BaseModel):
    """Schema for paginated feedback list"""
    items: list[FeedbackWithAnalysisResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# Import forward references
from app.schemas.analysis import (
    SentimentResponse,
    IntentResponse,
    AspectSentimentResponse
)

# Update forward references
FeedbackDetailResponse.model_rebuild()
FeedbackWithAnalysisResponse.model_rebuild()
