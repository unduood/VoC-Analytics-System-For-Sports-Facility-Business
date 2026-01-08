"""
Analysis results models
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import String, Float, ForeignKey, Index, func, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import TIMESTAMP

from app.models.base import UUIDMixin
from app.database import Base


class SentimentResult(Base, UUIDMixin):
    """
    Sentiment analysis results

    Column Order (for reference):
    1. id (from UUIDMixin)
    2. feedback_id
    3. sentiment, confidence
    4. source
    5. original_sentiment, original_confidence
    6. created_at, updated_at, updated_by
    7. is_deleted
    8. notes
    """

    __tablename__ = "sentiment_results"

    # 2. Foreign Key
    feedback_id: Mapped[UUID] = mapped_column(
        ForeignKey("feedback_records.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # 3. Core Data
    sentiment: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Sentiment: positive, neutral, negative"
    )

    confidence: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Confidence score (0-1)"
    )

    # 4. Audit Source
    source: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default="model",
        comment="Source: model | user"
    )

    # 5. Edit History
    original_sentiment: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="Original sentiment before user edit"
    )

    original_confidence: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Original confidence before user edit"
    )

    # 6. Audit Timestamps
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    updated_at: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
        onupdate=func.now(),
        comment="Last update timestamp"
    )

    updated_by: Mapped[Optional[UUID]] = mapped_column(
        nullable=True,
        comment="User ID who made the update"
    )

    # 7. Soft Delete
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="false",
        comment="Soft delete flag"
    )

    # 8. Notes
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="User notes for edit reason"
    )

    # Relationship
    feedback: Mapped["FeedbackRecord"] = relationship(
        "FeedbackRecord",
        back_populates="sentiment_results"
    )

    __table_args__ = (
        Index("idx_sentiment_feedback_id", "feedback_id"),
        Index("idx_sentiment_sentiment", "sentiment"),
        Index("idx_sentiment_source", "source"),
        Index("idx_sentiment_updated", "updated_at"),
        Index("idx_sentiment_deleted", "is_deleted"),
    )

    def __repr__(self) -> str:
        return f"<SentimentResult(id={self.id}, feedback_id={self.feedback_id}, sentiment={self.sentiment}, source={self.source})>"


class IntentResult(Base, UUIDMixin):
    """
    Intent classification results

    Column Order (for reference):
    1. id (from UUIDMixin)
    2. feedback_id
    3. intent, confidence
    4. source
    5. original_intent, original_confidence
    6. created_at, updated_at, updated_by
    7. is_deleted
    8. notes
    """

    __tablename__ = "intent_results"

    # 2. Foreign Key
    feedback_id: Mapped[UUID] = mapped_column(
        ForeignKey("feedback_records.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # 3. Core Data
    intent: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Intent: feedback, question, complaint, off_topic"
    )

    confidence: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Confidence score (0-1)"
    )

    # 4. Audit Source
    source: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default="model",
        comment="Source: model | user"
    )

    # 5. Edit History
    original_intent: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Original intent before user edit"
    )

    original_confidence: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Original confidence before user edit"
    )

    # 6. Audit Timestamps
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    updated_at: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
        onupdate=func.now(),
        comment="Last update timestamp"
    )

    updated_by: Mapped[Optional[UUID]] = mapped_column(
        nullable=True,
        comment="User ID who made the update"
    )

    # 7. Soft Delete
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="false",
        comment="Soft delete flag"
    )

    # 8. Notes
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="User notes for edit reason"
    )

    # Relationship
    feedback: Mapped["FeedbackRecord"] = relationship(
        "FeedbackRecord",
        back_populates="intent_results"
    )

    __table_args__ = (
        Index("idx_intent_feedback_id", "feedback_id"),
        Index("idx_intent_intent", "intent"),
        Index("idx_intent_source", "source"),
        Index("idx_intent_updated", "updated_at"),
        Index("idx_intent_deleted", "is_deleted"),
    )

    def __repr__(self) -> str:
        return f"<IntentResult(id={self.id}, feedback_id={self.feedback_id}, intent={self.intent}, source={self.source})>"


class AspectSentimentResult(Base, UUIDMixin):
    """
    Aspect-based sentiment analysis results

    Column Order (for reference):
    1. id (from UUIDMixin)
    2. feedback_id
    3. aspect, sentiment, confidence
    4. source
    5. original_sentiment, original_confidence
    6. created_at, updated_at, updated_by
    7. is_deleted
    8. notes
    """

    __tablename__ = "aspect_sentiment_results"

    # 2. Foreign Key
    feedback_id: Mapped[UUID] = mapped_column(
        ForeignKey("feedback_records.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # 3. Core Data
    aspect: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Aspect: equipment, staff, cleanliness, atmosphere, price, location, programs, amenities"
    )

    sentiment: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Sentiment: positive, neutral, negative (note: 'none' not stored in Hybrid++ approach)"
    )

    confidence: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Confidence score (0-1)"
    )

    # 4. Audit Source
    source: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default="model",
        comment="Source: model | user"
    )

    # 5. Edit History
    original_sentiment: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="Original sentiment before user edit"
    )

    original_confidence: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Original confidence before user edit"
    )

    # 6. Audit Timestamps
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    updated_at: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
        onupdate=func.now(),
        comment="Last update timestamp"
    )

    updated_by: Mapped[Optional[UUID]] = mapped_column(
        nullable=True,
        comment="User ID who made the update"
    )

    # 7. Soft Delete
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="false",
        comment="Soft delete flag"
    )

    # 8. Notes
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="User notes for edit reason"
    )

    # Relationship
    feedback: Mapped["FeedbackRecord"] = relationship(
        "FeedbackRecord",
        back_populates="aspect_sentiment_results"
    )

    __table_args__ = (
        Index("idx_aspect_sentiment_feedback_id", "feedback_id"),
        Index("idx_aspect_sentiment_aspect", "aspect"),
        Index("idx_aspect_sentiment_sentiment", "sentiment"),
        Index("idx_aspect_source", "source"),
        Index("idx_aspect_updated", "updated_at"),
        Index("idx_aspect_deleted", "is_deleted"),
    )

    def __repr__(self) -> str:
        return f"<AspectSentimentResult(id={self.id}, feedback_id={self.feedback_id}, aspect={self.aspect}, sentiment={self.sentiment}, source={self.source})>"
