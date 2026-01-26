"""
Analytics Service - Business logic for dashboard analytics
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any
from sqlalchemy import select, func, and_, case, cast, Integer, exists
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.feedback import FeedbackRecord
from app.models.analysis import SentimentResult, IntentResult, AspectSentimentResult


class AnalyticsService:
    """Service for analytics and dashboard statistics"""

    @staticmethod
    async def get_overview(db: AsyncSession) -> Dict[str, Any]:
        """
        Get dashboard overview statistics
        Returns: Dashboard overview data including totals, distributions, and summaries
        """
        # Total feedbacks
        total_stmt = select(func.count(FeedbackRecord.id))
        total_result = await db.execute(total_stmt)
        total_feedbacks = total_result.scalar() or 0

        # Calculate trend percentage (compare current week vs previous week)
        now = datetime.utcnow()
        current_week_start = now - timedelta(days=7)
        previous_week_start = now - timedelta(days=14)

        effective_date = func.coalesce(FeedbackRecord.created_at_source, FeedbackRecord.created_at)

        # Current week count
        current_week_stmt = select(func.count(FeedbackRecord.id)).where(
            effective_date >= current_week_start
        )
        current_week_result = await db.execute(current_week_stmt)
        current_week_count = current_week_result.scalar() or 0

        # Previous week count
        previous_week_stmt = select(func.count(FeedbackRecord.id)).where(
            and_(
                effective_date >= previous_week_start,
                effective_date < current_week_start
            )
        )
        previous_week_result = await db.execute(previous_week_stmt)
        previous_week_count = previous_week_result.scalar() or 0

        # Calculate trend percentage
        if previous_week_count > 0:
            trend_percentage = round(((current_week_count - previous_week_count) / previous_week_count) * 100, 1)
        elif current_week_count > 0:
            trend_percentage = 100.0
        else:
            trend_percentage = 0.0

        # Sentiment distribution
        sentiment_stmt = (
            select(
                SentimentResult.sentiment,
                func.count(SentimentResult.id).label('count')
            )
            .where(SentimentResult.is_deleted == False)
            .group_by(SentimentResult.sentiment)
        )
        sentiment_result = await db.execute(sentiment_stmt)
        sentiment_rows = sentiment_result.all()

        sentiment_distribution = {
            'positive': 0,
            'neutral': 0,
            'negative': 0
        }
        for row in sentiment_rows:
            if row.sentiment in sentiment_distribution:
                sentiment_distribution[row.sentiment] = row.count

        # Calculate positive rate
        total_with_sentiment = sum(sentiment_distribution.values())
        positive_rate = round((sentiment_distribution['positive'] / total_with_sentiment * 100), 1) if total_with_sentiment > 0 else 0.0

        # Intent distribution
        intent_stmt = (
            select(
                IntentResult.intent,
                func.count(IntentResult.id).label('count')
            )
            .where(IntentResult.is_deleted == False)
            .group_by(IntentResult.intent)
        )
        intent_result = await db.execute(intent_stmt)
        intent_rows = intent_result.all()

        intent_distribution = {
            'feedback': 0,
            'complaint': 0,
            'question': 0,
            'off_topic': 0
        }
        for row in intent_rows:
            if row.intent in intent_distribution:
                intent_distribution[row.intent] = row.count

        # Complaint count
        complaint_count = intent_distribution['complaint']

        # Source distribution
        source_stmt = (
            select(
                FeedbackRecord.source_type,
                func.count(FeedbackRecord.id).label('count')
            )
            .group_by(FeedbackRecord.source_type)
        )
        source_result = await db.execute(source_stmt)
        source_rows = source_result.all()

        source_distribution = {
            'email': 0,
            'instagram': 0,
            'facebook': 0,
            'google_maps': 0,
            'manual': 0,
            'google_form': 0
        }
        for row in source_rows:
            if row.source_type in source_distribution:
                source_distribution[row.source_type] = row.count

        # Aspect summary with satisfaction score (0-100 scale)
        aspect_stmt = (
            select(
                AspectSentimentResult.aspect,
                func.count(AspectSentimentResult.id).label('total_mentions'),
                func.sum(
                    case(
                        (AspectSentimentResult.sentiment == 'positive', 1),
                        else_=0
                    )
                ).label('positive'),
                func.sum(
                    case(
                        (AspectSentimentResult.sentiment == 'neutral', 1),
                        else_=0
                    )
                ).label('neutral'),
                func.sum(
                    case(
                        (AspectSentimentResult.sentiment == 'negative', 1),
                        else_=0
                    )
                ).label('negative'),
                func.avg(AspectSentimentResult.confidence).label('avg_confidence')
            )
            .where(AspectSentimentResult.is_deleted == False)
            .group_by(AspectSentimentResult.aspect)
        )
        aspect_result = await db.execute(aspect_stmt)
        aspect_rows = aspect_result.all()

        aspect_summary = []
        for row in aspect_rows:
            total = row.total_mentions or 0
            positive = row.positive or 0
            neutral = row.neutral or 0
            negative = row.negative or 0

            # Calculate average sentiment score (-1 to 1)
            if total > 0:
                avg_score = (positive - negative) / total
            else:
                avg_score = 0.0

            # Calculate satisfaction score (0-100 scale)
            # Formula: ((avg_score + 1) / 2) * 100 maps -1..1 to 0..100
            satisfaction_score = round(((avg_score + 1) / 2) * 100, 1)

            aspect_summary.append({
                'aspect': row.aspect,
                'total_mentions': total,
                'positive': positive,
                'neutral': neutral,
                'negative': negative,
                'avg_sentiment_score': round(avg_score, 2),
                'satisfaction_score': satisfaction_score
            })

        # Average confidence across all analyses
        confidence_stmt = select(func.avg(SentimentResult.confidence))
        confidence_result = await db.execute(confidence_stmt)
        avg_confidence = confidence_result.scalar() or 0.0

        # Calculate average satisfaction score across all aspects
        if aspect_summary:
            avg_satisfaction = round(sum(a['satisfaction_score'] for a in aspect_summary) / len(aspect_summary), 1)
        else:
            avg_satisfaction = 0.0

        # Recent feedbacks (last 5) - ordered by effective date (created_at_source with fallback)
        recent_stmt = (
            select(FeedbackRecord)
            .order_by(effective_date.desc())
            .limit(5)
        )
        recent_result = await db.execute(recent_stmt)
        recent_feedbacks = recent_result.scalars().all()

        # Recent complaints (last 4) with negative aspects
        complaint_exists = exists(
            select(IntentResult.id).where(
                and_(
                    IntentResult.feedback_id == FeedbackRecord.id,
                    IntentResult.intent == 'complaint',
                    IntentResult.is_deleted == False
                )
            )
        )
        recent_complaints_stmt = (
            select(FeedbackRecord)
            .options(
                selectinload(FeedbackRecord.aspect_sentiment_results)
            )
            .where(complaint_exists)
            .order_by(effective_date.desc())
            .limit(4)
        )
        recent_complaints_result = await db.execute(recent_complaints_stmt)
        recent_complaints_records = recent_complaints_result.scalars().all()

        recent_complaints = []
        for fb in recent_complaints_records:
            # Get negative aspects for this complaint
            negative_aspects = [
                asp.aspect for asp in fb.aspect_sentiment_results
                if asp.sentiment == 'negative' and not asp.is_deleted
            ]
            recent_complaints.append({
                'id': str(fb.id),
                'text_content': fb.text_content,
                'source_type': fb.source_type,
                'created_at': (fb.created_at_source or fb.created_at).isoformat() if (fb.created_at_source or fb.created_at) else None,
                'negative_aspects': negative_aspects
            })

        return {
            'total_feedbacks': total_feedbacks,
            'trend_percentage': trend_percentage,
            'positive_rate': positive_rate,
            'complaint_count': complaint_count,
            'avg_satisfaction': avg_satisfaction,
            'sentiment_distribution': sentiment_distribution,
            'intent_distribution': intent_distribution,
            'source_distribution': source_distribution,
            'aspect_summary': aspect_summary,
            'avg_confidence': round(avg_confidence, 4),
            'recent_feedbacks': [
                {
                    'id': str(fb.id),
                    'text_content': fb.text_content,
                    'source_type': fb.source_type,
                    # Use created_at_source (original date) with fallback to created_at
                    'created_at': (fb.created_at_source or fb.created_at).isoformat() if (fb.created_at_source or fb.created_at) else None,
                    'processing_status': fb.processing_status
                }
                for fb in recent_feedbacks
            ],
            'recent_complaints': recent_complaints
        }

    @staticmethod
    async def get_trends(db: AsyncSession, period: str = '7d') -> List[Dict[str, Any]]:
        """
        Get sentiment trends over time

        Args:
            db: Database session
            period: Time period ('7d', '30d', '90d')

        Returns: List of trend data points
        """
        # Calculate date range
        days_map = {'7d': 7, '30d': 30, '90d': 90}
        days = days_map.get(period, 7)
        start_date = datetime.utcnow() - timedelta(days=days)

        # Use effective date: created_at_source (original date from source) with fallback to created_at
        # This ensures trends reflect when feedback was actually given, not when it was processed
        effective_date = func.coalesce(FeedbackRecord.created_at_source, FeedbackRecord.created_at)

        # Query for trends grouped by date
        stmt = (
            select(
                func.date(effective_date).label('date'),
                func.count(FeedbackRecord.id).label('total'),
                func.sum(
                    case(
                        (SentimentResult.sentiment == 'positive', 1),
                        else_=0
                    )
                ).label('positive'),
                func.sum(
                    case(
                        (SentimentResult.sentiment == 'neutral', 1),
                        else_=0
                    )
                ).label('neutral'),
                func.sum(
                    case(
                        (SentimentResult.sentiment == 'negative', 1),
                        else_=0
                    )
                ).label('negative'),
            )
            .outerjoin(SentimentResult, FeedbackRecord.id == SentimentResult.feedback_id)
            .where(
                and_(
                    effective_date >= start_date,
                    SentimentResult.is_deleted == False
                )
            )
            .group_by(func.date(effective_date))
            .order_by(func.date(effective_date))
        )

        result = await db.execute(stmt)
        rows = result.all()

        # Create complete date range (fill in missing dates with zeros)
        trends = []
        current_date = start_date.date()
        end_date = datetime.utcnow().date()

        # Create a dict for quick lookup
        data_dict = {row.date: row for row in rows}

        while current_date <= end_date:
            row = data_dict.get(current_date)
            if row:
                trends.append({
                    'date': current_date.isoformat(),
                    'total': row.total or 0,
                    'positive': row.positive or 0,
                    'neutral': row.neutral or 0,
                    'negative': row.negative or 0
                })
            else:
                # Fill missing dates with zeros
                trends.append({
                    'date': current_date.isoformat(),
                    'total': 0,
                    'positive': 0,
                    'neutral': 0,
                    'negative': 0
                })
            current_date += timedelta(days=1)

        return trends
