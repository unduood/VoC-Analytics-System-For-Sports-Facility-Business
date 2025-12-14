"""
Feedback models
"""
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID

from sqlalchemy import String, Text, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP

from app.models.base import UUIDMixin, TimestampMixin
from app.database import Base


class FeedbackRecord(Base, UUIDMixin, TimestampMixin):
    """
    Main feedback record table - stores feedback from all sources
    """

    __tablename__ = "feedback_records"

    # Source information
    source_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Source type: email, instagram, facebook, google_form, google_maps, manual"
    )

    source_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Unique ID from source (e.g., comment_id, email_id)"
    )

    # Content
    text_content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Main text content of the feedback"
    )

    raw_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Source-specific raw data"
    )

    # Timestamps
    created_at_source: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
        comment="Original timestamp from source"
    )

    # Processing status
    processing_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        server_default="pending",
        comment="Status: pending, processing, completed, failed"
    )

    # Relationships
    sentiment_results: Mapped[list["SentimentResult"]] = relationship(
        "SentimentResult",
        back_populates="feedback",
        cascade="all, delete-orphan"
    )

    intent_results: Mapped[list["IntentResult"]] = relationship(
        "IntentResult",
        back_populates="feedback",
        cascade="all, delete-orphan"
    )

    aspect_sentiment_results: Mapped[list["AspectSentimentResult"]] = relationship(
        "AspectSentimentResult",
        back_populates="feedback",
        cascade="all, delete-orphan"
    )

    # Constraints
    __table_args__ = (
        UniqueConstraint(
            "source_type",
            "source_id",
            name="uq_feedback_source"
        ),
        Index("idx_feedback_source_type", "source_type"),
        Index("idx_feedback_processing_status", "processing_status"),
        Index("idx_feedback_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<FeedbackRecord(id={self.id}, source_type={self.source_type}, status={self.processing_status})>"
