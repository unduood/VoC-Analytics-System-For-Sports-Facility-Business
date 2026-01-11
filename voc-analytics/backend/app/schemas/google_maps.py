"""
Google Maps review schemas for SerpAPI integration
"""
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field


class GoogleMapsFetchRequest(BaseModel):
    """Request schema for fetching Google Maps reviews"""
    api_key: Optional[str] = Field(
        None,
        description="SerpAPI key (optional if set in environment variables)"
    )
    data_id: Optional[str] = Field(
        None,
        description="Google Maps data_id (optional if set in environment variables)"
    )


class ReviewProcessingDetail(BaseModel):
    """Details of a single review processing result"""
    review_id: str = Field(..., description="Google Maps review_id")
    action: str = Field(
        ...,
        description="Action taken: 'created', 'updated', 'skipped', or 'failed'"
    )
    record_id: Optional[UUID] = Field(
        None,
        description="Feedback record UUID if created/updated"
    )
    reason: Optional[str] = Field(
        None,
        description="Reason for skip/update/failure"
    )


class GoogleMapsFetchResponse(BaseModel):
    """Response schema for Google Maps fetch operation"""
    status: str = Field(..., description="Response status")
    message: str = Field(..., description="Summary message")
    total_fetched: int = Field(..., description="Total reviews fetched from SerpAPI")
    processed: int = Field(..., description="Number of new reviews created")
    updated: int = Field(..., description="Number of reviews updated")
    skipped: int = Field(..., description="Number of reviews skipped (no changes)")
    failed: int = Field(..., description="Number of reviews failed to process")
    details: List[ReviewProcessingDetail] = Field(
        default_factory=list,
        description="Detailed processing results for each review"
    )
