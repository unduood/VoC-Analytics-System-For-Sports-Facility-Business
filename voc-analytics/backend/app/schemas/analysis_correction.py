"""
Analysis correction schemas for human-in-the-loop editing
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict, model_validator

from app.schemas.analysis import (
    Sentiment,
    Intent,
    Aspect,
    SentimentResponse,
    IntentResponse,
    AspectSentimentResponse,
)


# === Correction Request Schemas ===

class SentimentCorrection(BaseModel):
    """Correction for overall sentiment (edit only, cannot add/delete)"""
    sentiment: Sentiment = Field(..., description="New sentiment value")
    notes: Optional[str] = Field(None, max_length=500, description="Optional note for audit")
    revert: bool = Field(False, description="If true, revert to original ML prediction")


class IntentCorrection(BaseModel):
    """Correction for a single intent label"""
    id: Optional[UUID] = Field(None, description="Existing intent ID (None = add new)")
    intent: Intent = Field(..., description="Intent label")
    notes: Optional[str] = Field(None, max_length=500, description="Optional note for audit")
    delete: bool = Field(False, description="If true, soft-delete this intent")
    revert: bool = Field(False, description="If true, revert to original ML prediction")

    @model_validator(mode='after')
    def validate_delete_requires_id(self) -> 'IntentCorrection':
        """Delete and revert operations require an existing ID"""
        if (self.delete or self.revert) and self.id is None:
            raise ValueError("Cannot delete or revert a new intent - 'id' is required")
        return self


class AspectCorrection(BaseModel):
    """Correction for a single aspect-sentiment pair"""
    id: Optional[UUID] = Field(None, description="Existing aspect ID (None = add new)")
    aspect: Aspect = Field(..., description="Aspect label")
    sentiment: Sentiment = Field(..., description="Sentiment for this aspect")
    notes: Optional[str] = Field(None, max_length=500, description="Optional note for audit")
    delete: bool = Field(False, description="If true, soft-delete this aspect")
    revert: bool = Field(False, description="If true, revert to original ML prediction")

    @model_validator(mode='after')
    def validate_delete_requires_id(self) -> 'AspectCorrection':
        """Delete and revert operations require an existing ID"""
        if (self.delete or self.revert) and self.id is None:
            raise ValueError("Cannot delete or revert a new aspect - 'id' is required")
        return self


class AnalysisCorrectionRequest(BaseModel):
    """
    Batch correction request for analysis results.

    All corrections are applied atomically - either all succeed or all fail.
    Only include fields that are being modified.

    Business Rules:
    - Sentiment: Edit only (exactly one must exist)
    - Intents: At least one required; 'off_topic' is mutually exclusive with others
    - Aspects: Zero to many allowed; can add/edit/delete freely
    """
    sentiment: Optional[SentimentCorrection] = Field(
        None, description="Overall sentiment correction (edit only)"
    )
    intents: Optional[List[IntentCorrection]] = Field(
        None, description="Intent corrections (add/edit/delete)"
    )
    aspects: Optional[List[AspectCorrection]] = Field(
        None, description="Aspect-sentiment corrections (add/edit/delete)"
    )

    @model_validator(mode='after')
    def validate_has_corrections(self) -> 'AnalysisCorrectionRequest':
        """Ensure at least one correction is provided"""
        if self.sentiment is None and self.intents is None and self.aspects is None:
            raise ValueError("At least one correction must be provided")
        return self

    @model_validator(mode='after')
    def validate_intent_exclusivity(self) -> 'AnalysisCorrectionRequest':
        """
        Validate that off_topic is mutually exclusive with other intents.
        This is a preliminary check - full validation happens in the service
        after considering existing intents.
        """
        if self.intents:
            # Get intents that will remain (not deleted)
            active_intents = [c.intent for c in self.intents if not c.delete]

            # Check for off_topic exclusivity in the request itself
            if Intent.OFF_TOPIC in active_intents and len(active_intents) > 1:
                raise ValueError(
                    "'off_topic' cannot coexist with other intents. "
                    "Remove other intents first or don't include 'off_topic'."
                )
        return self


# === Correction Response Schemas ===

class CorrectionChangesSummary(BaseModel):
    """Summary of changes made during correction"""
    sentiment_updated: int = 0
    sentiment_reverted: int = 0
    intents_added: int = 0
    intents_updated: int = 0
    intents_deleted: int = 0
    intents_reverted: int = 0
    aspects_added: int = 0
    aspects_updated: int = 0
    aspects_deleted: int = 0
    aspects_reverted: int = 0


class AnalysisCorrectionResponse(BaseModel):
    """Response after applying corrections"""
    feedback_id: UUID
    sentiment: Optional[SentimentResponse] = None
    intents: List[IntentResponse] = []
    aspects: List[AspectSentimentResponse] = []
    analysis_summary: Dict[str, Any] = Field(
        ..., description="Updated analysis_summary JSONB"
    )
    updated_at: datetime
    changes_made: CorrectionChangesSummary = Field(
        ..., description="Summary of changes applied"
    )

    model_config = ConfigDict(from_attributes=True)
