"""
Webhook schemas for external platform integrations
"""
from datetime import datetime
from typing import Optional, Any, Dict, List
from uuid import UUID

from pydantic import BaseModel, Field


class EmailWebhookPayload(BaseModel):
    """Schema for email webhook payload from Make.com"""
    email_id: str = Field(..., description="Unique email identifier")
    sender_email: str = Field(..., description="Sender email address")
    subject: str = Field(..., description="Email subject")
    body_text: str = Field(..., min_length=1, description="Email body text")
    received_at: datetime = Field(..., description="Email received timestamp")


class InstagramWebhookPayload(BaseModel):
    """Schema for Instagram comment webhook payload from Make.com"""
    comment_id: str = Field(..., description="Unique comment identifier")
    comment_text: str = Field(..., min_length=1, description="Comment text content")
    username: str = Field(..., description="Instagram username")
    media_id: str = Field(..., description="Media post ID")
    media_type: str = Field(..., description="Media type (photo, video, etc.)")
    caption: Optional[str] = Field(None, description="Post caption")
    comment_timestamp: datetime = Field(..., description="Comment creation timestamp")
    post_timestamp: datetime = Field(..., description="Post creation timestamp")


class FacebookWebhookEntry(BaseModel):
    """Facebook webhook entry structure"""
    id: str = Field(..., description="Page ID")
    time: int = Field(..., description="Unix timestamp in milliseconds")
    changes: List[Dict[str, Any]] = Field(..., description="Array of changes")


class FacebookWebhookPayload(BaseModel):
    """Root Facebook webhook payload structure"""
    object: str = Field(..., description="Object type (should be 'page')")
    entry: List[FacebookWebhookEntry] = Field(..., description="Array of entries")


class WebhookResponse(BaseModel):
    """Standard response for webhook endpoints"""
    status: str = Field(..., description="Response status")
    message: str = Field(..., description="Response message")
    record_id: Optional[UUID] = Field(None, description="Created feedback record ID (optional)")
    source_type: str = Field(..., description="Feedback source type")
