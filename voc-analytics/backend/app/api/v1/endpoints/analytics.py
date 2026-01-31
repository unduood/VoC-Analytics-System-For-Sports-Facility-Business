"""
Analytics API endpoints
Provides dashboard statistics and trends
"""
from datetime import date
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.analytics_service import AnalyticsService

router = APIRouter()


@router.get("/overview", response_model=Dict[str, Any])
async def get_dashboard_overview(
    start_date: Optional[date] = Query(None, description="Filter start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="Filter end date (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get dashboard overview statistics

    Args:
        start_date: Optional filter start date (inclusive)
        end_date: Optional filter end date (inclusive)

    Returns:
        - total_feedbacks: Total number of feedback records
        - sentiment_distribution: Count by sentiment (positive/neutral/negative)
        - source_distribution: Count by source type
        - aspect_summary: Summary statistics for each aspect
        - avg_confidence: Average confidence score across all analyses
        - recent_feedbacks: Last 5 feedback records
    """
    overview = await AnalyticsService.get_overview(db, start_date, end_date)
    return overview


@router.get("/trends", response_model=Dict[str, Any])
async def get_sentiment_trends(
    start_date: Optional[date] = Query(None, description="Filter start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="Filter end date (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get sentiment trends over time with automatic granularity.
    Supports date ranges up to 2,000 days (~5.5 years).

    Granularity is automatically determined based on date span:
    - ≤ 60 days: daily (max 60 points)
    - 61-180 days: weekly (max ~26 points)
    - 181-730 days: monthly (max ~24 points)
    - > 730 days: quarterly (max ~22 points)

    Args:
        start_date: Optional filter start date (inclusive). Defaults to 90 days ago.
        end_date: Optional filter end date (inclusive). Defaults to today.

    Returns:
        Dict with 'granularity' ('daily'|'weekly'|'monthly'|'quarterly') and 'data' (list of trend points)
    """
    trends = await AnalyticsService.get_trends(db, start_date, end_date)
    return trends
