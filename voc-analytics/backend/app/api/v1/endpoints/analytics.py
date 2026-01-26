"""
Analytics API endpoints
Provides dashboard statistics and trends
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List

from app.database import get_db
from app.services.analytics_service import AnalyticsService

router = APIRouter()


@router.get("/overview", response_model=Dict[str, Any])
async def get_dashboard_overview(
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get dashboard overview statistics

    Returns:
        - total_feedbacks: Total number of feedback records
        - sentiment_distribution: Count by sentiment (positive/neutral/negative)
        - source_distribution: Count by source type
        - aspect_summary: Summary statistics for each aspect
        - avg_confidence: Average confidence score across all analyses
        - recent_feedbacks: Last 5 feedback records
    """
    overview = await AnalyticsService.get_overview(db)
    return overview


@router.get("/trends", response_model=List[Dict[str, Any]])
async def get_sentiment_trends(
    period: str = Query(
        '7d',
        description="Time period for trends",
        regex="^(7d|30d|90d)$"
    ),
    db: AsyncSession = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    Get sentiment trends over time

    Args:
        period: Time period ('7d', '30d', or '90d')

    Returns:
        List of trend data points with date and sentiment counts
    """
    trends = await AnalyticsService.get_trends(db, period)
    return trends
