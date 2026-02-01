"""
Analysis schemas for request/response validation
"""
from datetime import datetime
from typing import Optional
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict, field_validator


class Sentiment(str, Enum):
    """Sentiment enumeration"""
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


class Intent(str, Enum):
    """Intent enumeration"""
    FEEDBACK = "feedback"
    QUESTION = "question"
    COMPLAINT = "complaint"
    OFF_TOPIC = "off_topic"


class Aspect(str, Enum):
    """Aspect enumeration"""
    EQUIPMENT = "equipment"
    STAFF = "staff"
    CLEANLINESS = "cleanliness"
    ATMOSPHERE = "atmosphere"
    PRICE = "price"
    LOCATION = "location"
    PROGRAMS = "programs"
    AMENITIES = "amenities"


class AspectSentiment(str, Enum):
    """Aspect sentiment enumeration (includes 'none' for not mentioned)"""
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    NONE = "none"


# Analysis source enumeration
class AnalysisSource(str, Enum):
    """Source of analysis result"""
    MODEL = "model"
    USER = "user"
    RATING = "rating"


# Sentiment schemas
class SentimentBase(BaseModel):
    """Base sentiment schema"""
    sentiment: Sentiment
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)

    @field_validator('confidence')
    @classmethod
    def validate_confidence(cls, v):
        if v is not None and (v < 0.0 or v > 1.0):
            raise ValueError('Confidence must be between 0.0 and 1.0')
        return v


class SentimentCreate(SentimentBase):
    """Schema for creating sentiment result"""
    feedback_id: UUID


class SentimentResponse(SentimentBase):
    """Schema for sentiment response with audit fields"""
    id: UUID
    feedback_id: UUID
    source: str = Field(default="model", description="Source: model, user, or rating")
    original_sentiment: Optional[str] = None
    original_confidence: Optional[float] = None
    original_source: Optional[str] = Field(None, description="Original source before user edit")
    is_deleted: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# Intent schemas
class IntentBase(BaseModel):
    """Base intent schema"""
    intent: Intent
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)

    @field_validator('confidence')
    @classmethod
    def validate_confidence(cls, v):
        if v is not None and (v < 0.0 or v > 1.0):
            raise ValueError('Confidence must be between 0.0 and 1.0')
        return v


class IntentCreate(IntentBase):
    """Schema for creating intent result"""
    feedback_id: UUID


class IntentResponse(IntentBase):
    """Schema for intent response with audit fields"""
    id: UUID
    feedback_id: UUID
    source: str = Field(default="model", description="Source: model or user")
    original_intent: Optional[str] = None
    original_confidence: Optional[float] = None
    original_source: Optional[str] = Field(None, description="Original source before user edit")
    is_deleted: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# Aspect sentiment schemas
class AspectSentimentBase(BaseModel):
    """Base aspect sentiment schema"""
    aspect: Aspect
    sentiment: AspectSentiment
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)

    @field_validator('confidence')
    @classmethod
    def validate_confidence(cls, v):
        if v is not None and (v < 0.0 or v > 1.0):
            raise ValueError('Confidence must be between 0.0 and 1.0')
        return v


class AspectSentimentCreate(AspectSentimentBase):
    """Schema for creating aspect sentiment result"""
    feedback_id: UUID


class AspectSentimentResponse(AspectSentimentBase):
    """Schema for aspect sentiment response with audit fields"""
    id: UUID
    feedback_id: UUID
    source: str = Field(default="model", description="Source: model or user")
    original_sentiment: Optional[str] = None
    original_confidence: Optional[float] = None
    original_source: Optional[str] = Field(None, description="Original source before user edit")
    is_deleted: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# Batch analysis request/response
class AnalysisRequest(BaseModel):
    """Schema for requesting analysis"""
    feedback_id: UUID


class AnalysisResponse(BaseModel):
    """Schema for complete analysis response"""
    feedback_id: UUID
    sentiment: Optional[SentimentResponse] = None
    intents: list[IntentResponse] = []
    aspect_sentiments: list[AspectSentimentResponse] = []

    model_config = ConfigDict(from_attributes=True)
