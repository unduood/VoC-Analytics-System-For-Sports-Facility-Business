"""
Analysis results models
"""
from typing import Optional
from uuid import UUID

from sqlalchemy import String, Float, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import UUIDMixin, TimestampMixin
from app.database import Base


class SentimentResult(Base, UUIDMixin):
    """
    Sentiment analysis results
    """

    __tablename__ = "sentiment_results"

    # Foreign key to feedback
    feedback_id: Mapped[UUID] = mapped_column(
        ForeignKey("feedback_records.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Sentiment
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

    # Timestamp
    created_at: Mapped[Optional[str]] = mapped_column(
        String,
        server_default="NOW()",
        nullable=False
    )

    # Relationship
    feedback: Mapped["FeedbackRecord"] = relationship(
        "FeedbackRecord",
        back_populates="sentiment_results"
    )

    __table_args__ = (
        Index("idx_sentiment_feedback_id", "feedback_id"),
        Index("idx_sentiment_sentiment", "sentiment"),
    )

    def __repr__(self) -> str:
        return f"<SentimentResult(id={self.id}, feedback_id={self.feedback_id}, sentiment={self.sentiment})>"


class IntentResult(Base, UUIDMixin):
    """
    Intent classification results
    """

    __tablename__ = "intent_results"

    # Foreign key to feedback
    feedback_id: Mapped[UUID] = mapped_column(
        ForeignKey("feedback_records.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Intent
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

    # Timestamp
    created_at: Mapped[Optional[str]] = mapped_column(
        String,
        server_default="NOW()",
        nullable=False
    )

    # Relationship
    feedback: Mapped["FeedbackRecord"] = relationship(
        "FeedbackRecord",
        back_populates="intent_results"
    )

    __table_args__ = (
        Index("idx_intent_feedback_id", "feedback_id"),
        Index("idx_intent_intent", "intent"),
    )

    def __repr__(self) -> str:
        return f"<IntentResult(id={self.id}, feedback_id={self.feedback_id}, intent={self.intent})>"


class AspectSentimentResult(Base, UUIDMixin):
    """
    Aspect-based sentiment analysis results
    """

    __tablename__ = "aspect_sentiment_results"

    # Foreign key to feedback
    feedback_id: Mapped[UUID] = mapped_column(
        ForeignKey("feedback_records.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Aspect
    aspect: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Aspect: equipment, staff, cleanliness, atmosphere, price, location, programs, amenities"
    )

    # Sentiment
    sentiment: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Sentiment: positive, neutral, negative, none"
    )

    confidence: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Confidence score (0-1)"
    )

    # Timestamp
    created_at: Mapped[Optional[str]] = mapped_column(
        String,
        server_default="NOW()",
        nullable=False
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
    )

    def __repr__(self) -> str:
        return f"<AspectSentimentResult(id={self.id}, feedback_id={self.feedback_id}, aspect={self.aspect}, sentiment={self.sentiment})>"
