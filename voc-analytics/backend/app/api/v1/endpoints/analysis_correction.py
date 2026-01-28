"""
Analysis Correction Endpoint - Human-in-the-loop editing
"""
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.analysis_correction import (
    AnalysisCorrectionRequest,
    AnalysisCorrectionResponse,
)
from app.services.analysis_correction_service import (
    AnalysisCorrectionService,
    ValidationError,
    NotFoundError,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/feedback", tags=["Analysis Correction"])


@router.patch(
    "/{feedback_id}/analysis",
    response_model=AnalysisCorrectionResponse,
    summary="Correct analysis results",
    description="""
Apply human-in-the-loop corrections to ML-generated analysis results.

## Business Rules

### Sentiment (Overall)
- **Edit only** - cannot add or delete
- Exactly one sentiment must exist

### Intents (Multi-label)
- Can add, edit, or delete
- **At least one intent required** - cannot delete the last one
- **'off_topic' is mutually exclusive** - cannot coexist with other intents

### Aspects (Multi-label)
- Can add, edit, or delete freely
- Zero to many aspects allowed

## Atomicity
All corrections are applied atomically - either all succeed or all fail.
Both the normalized tables and the JSONB `analysis_summary` are updated together.

## Audit Trail
- Original ML predictions are preserved in `original_*` fields on first edit
- `source` field changes from 'model' to 'user' when edited
- Use `revert: true` to restore original ML prediction
"""
)
async def correct_analysis(
    feedback_id: UUID,
    request: AnalysisCorrectionRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Apply corrections to analysis results.

    - **sentiment**: Edit the overall sentiment (edit only)
    - **intents**: Add, edit, or delete intent labels
    - **aspects**: Add, edit, or delete aspect-sentiment pairs

    All changes are atomic - either all succeed or all fail.
    """
    try:
        service = AnalysisCorrectionService(db)
        result = await service.apply_corrections(
            feedback_id=feedback_id,
            request=request,
            user_id=None,  # TODO: Extract from auth token when auth is implemented
        )
        return result

    except ValidationError as e:
        logger.warning(f"Validation error correcting {feedback_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )

    except NotFoundError as e:
        logger.warning(f"Not found error correcting {feedback_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

    except Exception as e:
        logger.error(f"Error correcting analysis for {feedback_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to apply analysis corrections"
        )
