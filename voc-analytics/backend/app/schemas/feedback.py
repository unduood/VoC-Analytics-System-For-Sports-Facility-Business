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


# List response
class FeedbackListResponse(BaseModel):
    """Schema for paginated feedback list"""
    items: list[FeedbackResponse]
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
