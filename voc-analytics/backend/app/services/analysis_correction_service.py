"""
Analysis Correction Service - Human-in-the-loop editing with dual storage sync
"""
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.feedback import FeedbackRecord
from app.models.analysis import SentimentResult, IntentResult, AspectSentimentResult
from app.schemas.analysis import Intent, Sentiment, Aspect
from app.schemas.analysis_correction import (
    AnalysisCorrectionRequest,
    AnalysisCorrectionResponse,
    CorrectionChangesSummary,
    SentimentCorrection,
    IntentCorrection,
    AspectCorrection,
)
from app.schemas.analysis import (
    SentimentResponse,
    IntentResponse,
    AspectSentimentResponse,
)

logger = logging.getLogger(__name__)

# Thai labels for aspects (used in JSONB)
ASPECT_THAI_MAP = {
    "equipment": "อุปกรณ์",
    "staff": "พนักงาน",
    "cleanliness": "ความสะอาด",
    "atmosphere": "บรรยากาศ",
    "price": "ราคา",
    "location": "ทำเล",
    "programs": "โปรแกรม",
    "amenities": "สิ่งอำนวยความสะดวก",
}


class ValidationError(Exception):
    """Raised when business rule validation fails"""
    pass


class NotFoundError(Exception):
    """Raised when a resource is not found"""
    pass


class AnalysisCorrectionService:
    """
    Service for applying human-in-the-loop corrections to analysis results.

    Handles:
    - Sentiment corrections (edit only)
    - Intent corrections (add/edit/delete with constraints)
    - Aspect corrections (add/edit/delete freely)
    - JSONB synchronization
    - Audit trail preservation
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def apply_corrections(
        self,
        feedback_id: UUID,
        request: AnalysisCorrectionRequest,
        user_id: Optional[UUID] = None
    ) -> AnalysisCorrectionResponse:
        """
        Apply all corrections in a single atomic transaction.

        Args:
            feedback_id: ID of the feedback record
            request: Correction request with sentiment/intents/aspects
            user_id: ID of the user making corrections (for audit)

        Returns:
            AnalysisCorrectionResponse with updated analysis

        Raises:
            NotFoundError: If feedback not found
            ValidationError: If business rules violated
        """
        changes = CorrectionChangesSummary()

        # Fetch feedback record with all relationships
        feedback = await self._get_feedback_or_404(feedback_id)

        if feedback.processing_status != 'completed':
            raise ValidationError("Cannot edit analysis before processing is complete")

        try:
            # Phase 1: Validate constraints BEFORE any writes
            if request.intents:
                await self._validate_intent_constraints(feedback_id, request.intents)

            # Phase 2: Apply corrections to normalized tables
            if request.sentiment:
                sentiment_changes = await self._apply_sentiment_correction(
                    feedback_id, request.sentiment, user_id
                )
                changes.sentiment_updated = sentiment_changes.get('updated', 0)
                changes.sentiment_reverted = sentiment_changes.get('reverted', 0)

            if request.intents:
                intent_changes = await self._apply_intent_corrections(
                    feedback_id, request.intents, user_id
                )
                changes.intents_added = intent_changes.get('added', 0)
                changes.intents_updated = intent_changes.get('updated', 0)
                changes.intents_deleted = intent_changes.get('deleted', 0)
                changes.intents_reverted = intent_changes.get('reverted', 0)

            if request.aspects:
                aspect_changes = await self._apply_aspect_corrections(
                    feedback_id, request.aspects, user_id
                )
                changes.aspects_added = aspect_changes.get('added', 0)
                changes.aspects_updated = aspect_changes.get('updated', 0)
                changes.aspects_deleted = aspect_changes.get('deleted', 0)
                changes.aspects_reverted = aspect_changes.get('reverted', 0)

            # Flush pending ORM changes to database before rebuilding JSONB.
            # Required because autoflush=False in session config.
            # Without this, newly added records (db.add) won't be visible
            # to the SELECT queries in _rebuild_analysis_summary().
            await self.db.flush()

            # Phase 3: Rebuild JSONB from normalized tables
            new_summary = await self._rebuild_analysis_summary(feedback_id)

            # Phase 4: Update feedback record with new summary
            await self.db.execute(
                update(FeedbackRecord)
                .where(FeedbackRecord.id == feedback_id)
                .values(analysis_summary=new_summary)
            )

            # Phase 5: Commit everything atomically
            await self.db.commit()

            logger.info(f"Applied corrections to feedback {feedback_id}: {changes}")

            # Phase 6: Fetch and return updated data
            return await self._build_response(feedback_id, new_summary, changes)

        except (ValidationError, NotFoundError):
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to apply corrections to {feedback_id}: {e}")
            raise

    async def _get_feedback_or_404(self, feedback_id: UUID) -> FeedbackRecord:
        """Fetch feedback record or raise NotFoundError"""
        stmt = (
            select(FeedbackRecord)
            .where(FeedbackRecord.id == feedback_id)
            .options(
                selectinload(FeedbackRecord.sentiment_results),
                selectinload(FeedbackRecord.intent_results),
                selectinload(FeedbackRecord.aspect_sentiment_results)
            )
        )
        result = await self.db.execute(stmt)
        feedback = result.scalar_one_or_none()

        if not feedback:
            raise NotFoundError(f"Feedback record with ID '{feedback_id}' not found")

        return feedback

    # === Intent Constraint Validation ===

    async def _validate_intent_constraints(
        self,
        feedback_id: UUID,
        corrections: List[IntentCorrection]
    ) -> None:
        """
        Validate intent business rules:
        1. At least 1 intent must remain after all corrections
        2. off_topic is mutually exclusive with other intents
        """
        # Get current active intents
        stmt = select(IntentResult).where(
            IntentResult.feedback_id == feedback_id,
            IntentResult.is_deleted == False
        )
        result = await self.db.execute(stmt)
        current_intents = {r.id: r.intent for r in result.scalars().all()}

        # Simulate the changes
        result_intents = set(current_intents.values())

        for correction in corrections:
            if correction.delete and correction.id:
                # Remove the deleted intent
                if correction.id in current_intents:
                    result_intents.discard(current_intents[correction.id])
            elif correction.revert and correction.id:
                # Revert will restore original - need to check what that was
                # For now, treat revert as keeping the intent
                pass
            elif not correction.delete:
                # Add or update intent
                if correction.id and correction.id in current_intents:
                    # Update: remove old, add new
                    result_intents.discard(current_intents[correction.id])
                result_intents.add(correction.intent.value)

        # Constraint 1: At least 1 intent
        if len(result_intents) == 0:
            raise ValidationError(
                "At least one intent is required. Cannot delete the last intent."
            )

        # Constraint 2: off_topic exclusivity
        if 'off_topic' in result_intents and len(result_intents) > 1:
            raise ValidationError(
                "'off_topic' cannot coexist with other intents. "
                "Remove other intents first, or don't add 'off_topic'."
            )

    # === Sentiment Correction ===

    async def _apply_sentiment_correction(
        self,
        feedback_id: UUID,
        correction: SentimentCorrection,
        user_id: Optional[UUID]
    ) -> Dict[str, int]:
        """Apply sentiment correction (edit only)"""
        changes = {'updated': 0, 'reverted': 0}

        stmt = select(SentimentResult).where(
            SentimentResult.feedback_id == feedback_id,
            SentimentResult.is_deleted == False
        )
        result = await self.db.execute(stmt)
        sentiment = result.scalar_one_or_none()

        if not sentiment:
            raise NotFoundError("No sentiment result found for this feedback")

        if correction.revert:
            # Revert to original ML/rating prediction
            if sentiment.original_sentiment:
                sentiment.sentiment = sentiment.original_sentiment
                sentiment.confidence = sentiment.original_confidence
                # Restore original source (rating, model, etc.) — not hardcoded 'model'
                sentiment.source = sentiment.original_source or 'model'
                sentiment.original_sentiment = None
                sentiment.original_confidence = None
                sentiment.original_source = None
                sentiment.updated_by = user_id
                sentiment.notes = correction.notes
                changes['reverted'] = 1
        else:
            # Apply new value
            # Preserve original if this is first edit
            if sentiment.original_sentiment is None and sentiment.source != 'user':
                sentiment.original_sentiment = sentiment.sentiment
                sentiment.original_confidence = sentiment.confidence
                sentiment.original_source = sentiment.source

            sentiment.sentiment = correction.sentiment.value
            sentiment.confidence = 1.0  # User corrections have full confidence
            sentiment.source = 'user'
            sentiment.updated_by = user_id
            sentiment.notes = correction.notes
            changes['updated'] = 1

        return changes

    # === Intent Corrections ===

    async def _apply_intent_corrections(
        self,
        feedback_id: UUID,
        corrections: List[IntentCorrection],
        user_id: Optional[UUID]
    ) -> Dict[str, int]:
        """Apply intent corrections (add/edit/delete)"""
        changes = {'added': 0, 'updated': 0, 'deleted': 0, 'reverted': 0}

        for correction in corrections:
            if correction.delete and correction.id:
                await self._soft_delete_intent(correction.id, user_id, correction.notes)
                changes['deleted'] += 1

            elif correction.revert and correction.id:
                reverted = await self._revert_intent(correction.id, user_id, correction.notes)
                if reverted:
                    changes['reverted'] += 1

            elif correction.id:
                # Edit existing
                await self._edit_intent(correction, user_id)
                changes['updated'] += 1

            else:
                # Check if intent already exists (might be soft-deleted)
                existing = await self._find_intent_by_name(
                    feedback_id, correction.intent.value
                )
                if existing:
                    # Resurrect or update existing
                    await self._resurrect_or_update_intent(existing, correction, user_id)
                    changes['updated'] += 1
                else:
                    # Add new
                    await self._add_intent(feedback_id, correction, user_id)
                    changes['added'] += 1

        return changes

    async def _soft_delete_intent(
        self, intent_id: UUID, user_id: Optional[UUID], notes: Optional[str]
    ) -> None:
        """Soft delete an intent"""
        stmt = select(IntentResult).where(IntentResult.id == intent_id)
        result = await self.db.execute(stmt)
        intent = result.scalar_one_or_none()

        if intent:
            intent.is_deleted = True
            intent.updated_by = user_id
            intent.notes = notes

    async def _revert_intent(
        self, intent_id: UUID, user_id: Optional[UUID], notes: Optional[str]
    ) -> bool:
        """Revert intent to original ML prediction"""
        stmt = select(IntentResult).where(IntentResult.id == intent_id)
        result = await self.db.execute(stmt)
        intent = result.scalar_one_or_none()

        if intent and intent.original_intent:
            intent.intent = intent.original_intent
            intent.confidence = intent.original_confidence
            # Restore original source — not hardcoded 'model'
            intent.source = intent.original_source or 'model'
            intent.original_intent = None
            intent.original_confidence = None
            intent.original_source = None
            intent.updated_by = user_id
            intent.notes = notes
            return True
        return False

    async def _edit_intent(
        self, correction: IntentCorrection, user_id: Optional[UUID]
    ) -> None:
        """Edit an existing intent"""
        stmt = select(IntentResult).where(IntentResult.id == correction.id)
        result = await self.db.execute(stmt)
        intent = result.scalar_one_or_none()

        if intent:
            # Preserve original if first edit
            if intent.original_intent is None and intent.source != 'user':
                intent.original_intent = intent.intent
                intent.original_confidence = intent.confidence
                intent.original_source = intent.source

            intent.intent = correction.intent.value
            intent.confidence = 1.0
            intent.source = 'user'
            intent.updated_by = user_id
            intent.notes = correction.notes

    async def _find_intent_by_name(
        self, feedback_id: UUID, intent_name: str
    ) -> Optional[IntentResult]:
        """Find intent by name (including soft-deleted)"""
        stmt = select(IntentResult).where(
            IntentResult.feedback_id == feedback_id,
            IntentResult.intent == intent_name
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _resurrect_or_update_intent(
        self,
        existing: IntentResult,
        correction: IntentCorrection,
        user_id: Optional[UUID]
    ) -> None:
        """Resurrect a soft-deleted intent or update an existing one"""
        # Auto-detect: does the new value match the original ML prediction?
        # This handles cross-session resurrection where the frontend may not
        # know about the soft-deleted record and cannot send revert=true.
        original_value = existing.original_intent or existing.intent
        matches_original = (correction.intent.value == original_value)

        if correction.revert or matches_original:
            # Restoring to original prediction
            if existing.original_intent:
                existing.intent = existing.original_intent
                existing.confidence = existing.original_confidence
                existing.source = existing.original_source or 'model'
                existing.original_intent = None
                existing.original_confidence = None
                existing.original_source = None
            # else: never edited before deletion, values are already original
            existing.is_deleted = False
            existing.updated_by = user_id
            existing.notes = correction.notes
        else:
            # User adding with different value — preserve original before overwriting
            if existing.original_intent is None and existing.source != 'user':
                existing.original_intent = existing.intent
                existing.original_confidence = existing.confidence
                existing.original_source = existing.source

            existing.intent = correction.intent.value
            existing.confidence = 1.0
            existing.source = 'user'
            existing.is_deleted = False
            existing.updated_by = user_id
            existing.notes = correction.notes

    async def _find_original_ml_prediction_intent(
        self, feedback_id: UUID, intent_name: str
    ) -> Optional[IntentResult]:
        """
        Check if this intent was ever an ML prediction for this feedback.

        This handles the case where a record was edited (e.g., A→C) so its
        current intent no longer matches, but its original_intent does.
        """
        stmt = select(IntentResult).where(
            IntentResult.feedback_id == feedback_id,
            IntentResult.original_intent == intent_name
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _add_intent(
        self,
        feedback_id: UUID,
        correction: IntentCorrection,
        user_id: Optional[UUID]
    ) -> None:
        """Add a new intent, recognizing original ML predictions"""
        # Check if this intent was originally an ML prediction for this feedback.
        # This handles: model predicts [A, B] → user edits B→C → user adds B back.
        # Record B now has intent=C, so _find_intent_by_name('B') missed it.
        # But original_intent='B' on that record tells us B was a model prediction.
        original_prediction = await self._find_original_ml_prediction_intent(
            feedback_id, correction.intent.value
        )

        if original_prediction:
            source = original_prediction.original_source or original_prediction.source
            confidence = original_prediction.original_confidence or original_prediction.confidence or 1.0
        else:
            source = 'user'
            confidence = 1.0

        new_intent = IntentResult(
            feedback_id=feedback_id,
            intent=correction.intent.value,
            confidence=confidence,
            source=source,
            updated_by=user_id,
            notes=correction.notes,
            is_deleted=False
        )
        self.db.add(new_intent)

    # === Aspect Corrections ===

    async def _apply_aspect_corrections(
        self,
        feedback_id: UUID,
        corrections: List[AspectCorrection],
        user_id: Optional[UUID]
    ) -> Dict[str, int]:
        """Apply aspect corrections (add/edit/delete)"""
        changes = {'added': 0, 'updated': 0, 'deleted': 0, 'reverted': 0}

        for correction in corrections:
            if correction.delete and correction.id:
                await self._soft_delete_aspect(correction.id, user_id, correction.notes)
                changes['deleted'] += 1

            elif correction.revert and correction.id:
                reverted = await self._revert_aspect(correction.id, user_id, correction.notes)
                if reverted:
                    changes['reverted'] += 1

            elif correction.id:
                # Edit existing
                await self._edit_aspect(correction, user_id)
                changes['updated'] += 1

            else:
                # Check if aspect already exists (might be soft-deleted)
                existing = await self._find_aspect_by_name(
                    feedback_id, correction.aspect.value
                )
                if existing:
                    # Resurrect or update existing
                    await self._resurrect_or_update_aspect(existing, correction, user_id)
                    changes['updated'] += 1
                else:
                    # Add new
                    await self._add_aspect(feedback_id, correction, user_id)
                    changes['added'] += 1

        return changes

    async def _soft_delete_aspect(
        self, aspect_id: UUID, user_id: Optional[UUID], notes: Optional[str]
    ) -> None:
        """Soft delete an aspect"""
        stmt = select(AspectSentimentResult).where(AspectSentimentResult.id == aspect_id)
        result = await self.db.execute(stmt)
        aspect = result.scalar_one_or_none()

        if aspect:
            aspect.is_deleted = True
            aspect.updated_by = user_id
            aspect.notes = notes

    async def _revert_aspect(
        self, aspect_id: UUID, user_id: Optional[UUID], notes: Optional[str]
    ) -> bool:
        """Revert aspect to original ML prediction"""
        stmt = select(AspectSentimentResult).where(AspectSentimentResult.id == aspect_id)
        result = await self.db.execute(stmt)
        aspect = result.scalar_one_or_none()

        if aspect and aspect.original_sentiment:
            aspect.sentiment = aspect.original_sentiment
            aspect.confidence = aspect.original_confidence
            # Restore original source — not hardcoded 'model'
            aspect.source = aspect.original_source or 'model'
            aspect.original_sentiment = None
            aspect.original_confidence = None
            aspect.original_source = None
            aspect.updated_by = user_id
            aspect.notes = notes
            return True
        return False

    async def _edit_aspect(
        self, correction: AspectCorrection, user_id: Optional[UUID]
    ) -> None:
        """Edit an existing aspect"""
        stmt = select(AspectSentimentResult).where(
            AspectSentimentResult.id == correction.id
        )
        result = await self.db.execute(stmt)
        aspect = result.scalar_one_or_none()

        if aspect:
            # Preserve original if first edit
            if aspect.original_sentiment is None and aspect.source != 'user':
                aspect.original_sentiment = aspect.sentiment
                aspect.original_confidence = aspect.confidence
                aspect.original_source = aspect.source

            aspect.aspect = correction.aspect.value
            aspect.sentiment = correction.sentiment.value
            aspect.confidence = 1.0
            aspect.source = 'user'
            aspect.updated_by = user_id
            aspect.notes = correction.notes

    async def _find_aspect_by_name(
        self, feedback_id: UUID, aspect_name: str
    ) -> Optional[AspectSentimentResult]:
        """Find aspect by name (including soft-deleted)"""
        stmt = select(AspectSentimentResult).where(
            AspectSentimentResult.feedback_id == feedback_id,
            AspectSentimentResult.aspect == aspect_name
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _resurrect_or_update_aspect(
        self,
        existing: AspectSentimentResult,
        correction: AspectCorrection,
        user_id: Optional[UUID]
    ) -> None:
        """Resurrect a soft-deleted aspect or update an existing one"""
        # Auto-detect: does the new sentiment match the original ML prediction?
        # This handles cross-session resurrection where the frontend may not
        # know about the soft-deleted record and cannot send revert=true.
        original_sentiment_value = existing.original_sentiment or existing.sentiment
        matches_original = (correction.sentiment.value == original_sentiment_value)

        if correction.revert or matches_original:
            # Restoring to original prediction
            if existing.original_sentiment:
                existing.sentiment = existing.original_sentiment
                existing.confidence = existing.original_confidence
                existing.source = existing.original_source or 'model'
                existing.original_sentiment = None
                existing.original_confidence = None
                existing.original_source = None
            # else: never edited before deletion, values are already original
            existing.is_deleted = False
            existing.updated_by = user_id
            existing.notes = correction.notes
        else:
            # User adding with different value — preserve original before overwriting
            if existing.original_sentiment is None and existing.source != 'user':
                existing.original_sentiment = existing.sentiment
                existing.original_confidence = existing.confidence
                existing.original_source = existing.source

            existing.sentiment = correction.sentiment.value
            existing.confidence = 1.0
            existing.source = 'user'
            existing.is_deleted = False  # Resurrect if was deleted
            existing.updated_by = user_id
            existing.notes = correction.notes

    async def _find_original_ml_prediction_aspect(
        self, feedback_id: UUID, aspect_name: str, sentiment_value: str
    ) -> Optional[AspectSentimentResult]:
        """
        Check if this aspect+sentiment was ever an ML prediction for this feedback.
        """
        stmt = select(AspectSentimentResult).where(
            AspectSentimentResult.feedback_id == feedback_id,
            AspectSentimentResult.aspect == aspect_name,
            AspectSentimentResult.original_sentiment == sentiment_value
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _add_aspect(
        self,
        feedback_id: UUID,
        correction: AspectCorrection,
        user_id: Optional[UUID]
    ) -> None:
        """Add a new aspect, recognizing original ML predictions"""
        original_prediction = await self._find_original_ml_prediction_aspect(
            feedback_id, correction.aspect.value, correction.sentiment.value
        )

        if original_prediction:
            source = original_prediction.original_source or original_prediction.source
            confidence = original_prediction.original_confidence or original_prediction.confidence or 1.0
        else:
            source = 'user'
            confidence = 1.0

        new_aspect = AspectSentimentResult(
            feedback_id=feedback_id,
            aspect=correction.aspect.value,
            sentiment=correction.sentiment.value,
            confidence=confidence,
            source=source,
            updated_by=user_id,
            notes=correction.notes,
            is_deleted=False
        )
        self.db.add(new_aspect)

    # === JSONB Rebuild ===

    async def _rebuild_analysis_summary(self, feedback_id: UUID) -> Dict[str, Any]:
        """
        Rebuild the analysis_summary JSONB from normalized tables.
        This ensures consistency between the JSONB cache and normalized tables.
        """
        # Fetch current state from normalized tables
        sentiment = await self._get_active_sentiment(feedback_id)
        intents = await self._get_active_intents(feedback_id)
        aspects = await self._get_active_aspects(feedback_id)

        # Build sentiment summary
        sentiment_summary = None
        if sentiment:
            # Determine the true origin source for display purposes
            # If currently user-edited, original_source tells us the pre-edit source
            true_origin = sentiment.original_source or sentiment.source
            sentiment_summary = {
                "label": sentiment.sentiment,
                "confidence": sentiment.confidence or 1.0,
                "source": sentiment.source,
                "original_source": sentiment.original_source,
                "edited": sentiment.source == 'user',
                "rating": None,
            }
            # Preserve rating info: if the true origin was 'rating',
            # attempt to extract the rating value from the feedback's raw_data
            if true_origin == 'rating':
                # Mark that this originated from a rating source
                sentiment_summary["from_rating"] = True

        # Build intents summary
        intents_summary = [
            {
                "label": i.intent.capitalize() if i.intent != 'off_topic' else 'Off-topic',
                "confidence": i.confidence or 1.0,
                "source": i.source,
                "original_source": i.original_source,
                "edited": i.source == 'user',
            }
            for i in intents
        ]

        # Build aspects summary
        aspects_summary = [
            {
                "aspect": a.aspect.capitalize(),
                "aspect_thai": ASPECT_THAI_MAP.get(a.aspect, a.aspect),
                "sentiment": a.sentiment,
                "confidence": a.confidence or 1.0,
                "source": a.source,
                "original_source": a.original_source,
                "edited": a.source == 'user',
            }
            for a in aspects
        ]

        # Calculate summary stats
        summary_stats = self._calculate_summary_stats(sentiment, intents, aspects)

        return {
            "sentiment": sentiment_summary,
            "intents": intents_summary,
            "aspects": aspects_summary,
            "summary_stats": summary_stats,
        }

    async def _get_active_sentiment(
        self, feedback_id: UUID
    ) -> Optional[SentimentResult]:
        """Get active (non-deleted) sentiment for feedback"""
        stmt = select(SentimentResult).where(
            SentimentResult.feedback_id == feedback_id,
            SentimentResult.is_deleted == False
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_active_intents(self, feedback_id: UUID) -> List[IntentResult]:
        """Get active (non-deleted) intents for feedback"""
        stmt = select(IntentResult).where(
            IntentResult.feedback_id == feedback_id,
            IntentResult.is_deleted == False
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def _get_active_aspects(
        self, feedback_id: UUID
    ) -> List[AspectSentimentResult]:
        """Get active (non-deleted) aspects for feedback"""
        stmt = select(AspectSentimentResult).where(
            AspectSentimentResult.feedback_id == feedback_id,
            AspectSentimentResult.is_deleted == False
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    def _calculate_summary_stats(
        self,
        sentiment: Optional[SentimentResult],
        intents: List[IntentResult],
        aspects: List[AspectSentimentResult]
    ) -> Dict[str, int]:
        """Calculate summary statistics for the analysis"""
        # Count user corrections (items that have original_* values)
        user_corrections = 0
        if sentiment and sentiment.original_sentiment:
            user_corrections += 1
        user_corrections += sum(1 for i in intents if i.original_intent)
        user_corrections += sum(1 for a in aspects if a.original_sentiment)

        # Count user additions (items added by user without original)
        user_additions = sum(
            1 for a in aspects
            if a.source == 'user' and a.original_sentiment is None
        )
        user_additions += sum(
            1 for i in intents
            if i.source == 'user' and i.original_intent is None
        )

        # Count sentiment types in aspects
        positive_aspects = sum(1 for a in aspects if a.sentiment == 'positive')
        negative_aspects = sum(1 for a in aspects if a.sentiment == 'negative')
        neutral_aspects = sum(1 for a in aspects if a.sentiment == 'neutral')

        # Count model predictions (non-user source)
        model_predictions = sum(1 for a in aspects if a.source == 'model')
        model_predictions += sum(1 for i in intents if i.source == 'model')
        if sentiment and sentiment.source in ('model', 'rating'):
            model_predictions += 1

        return {
            "total_aspects_analyzed": 8,  # All 8 aspects are always considered
            "aspects_with_sentiment": len(aspects),
            "positive_aspects": positive_aspects,
            "negative_aspects": negative_aspects,
            "neutral_aspects": neutral_aspects,
            "model_predictions": model_predictions,
            "user_corrections": user_corrections,
            "user_additions": user_additions,
        }

    # === Response Building ===

    async def _get_all_intents(self, feedback_id: UUID) -> List[IntentResult]:
        """Get ALL intents for feedback (including soft-deleted)"""
        stmt = select(IntentResult).where(
            IntentResult.feedback_id == feedback_id
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def _get_all_aspects(
        self, feedback_id: UUID
    ) -> List[AspectSentimentResult]:
        """Get ALL aspects for feedback (including soft-deleted)"""
        stmt = select(AspectSentimentResult).where(
            AspectSentimentResult.feedback_id == feedback_id
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def _build_response(
        self,
        feedback_id: UUID,
        analysis_summary: Dict[str, Any],
        changes: CorrectionChangesSummary
    ) -> AnalysisCorrectionResponse:
        """Build the response object with updated analysis"""
        # Return ALL records (including soft-deleted) to match the initial data
        # load behavior (SQLAlchemy relationships load all records).
        # The frontend filters by !is_deleted for display purposes, but needs
        # deleted records in the cache so that startEditing() can build
        # originalMlState for cross-session original prediction detection.
        sentiment = await self._get_active_sentiment(feedback_id)
        intents = await self._get_all_intents(feedback_id)
        aspects = await self._get_all_aspects(feedback_id)

        # Get feedback for updated_at
        stmt = select(FeedbackRecord.updated_at).where(FeedbackRecord.id == feedback_id)
        result = await self.db.execute(stmt)
        updated_at = result.scalar_one()

        return AnalysisCorrectionResponse(
            feedback_id=feedback_id,
            sentiment=SentimentResponse.model_validate(sentiment) if sentiment else None,
            intents=[IntentResponse.model_validate(i) for i in intents],
            aspects=[AspectSentimentResponse.model_validate(a) for a in aspects],
            analysis_summary=analysis_summary,
            updated_at=updated_at,
            changes_made=changes,
        )
