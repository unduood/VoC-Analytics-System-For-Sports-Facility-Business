"""
Analytics Service - Business logic for dashboard analytics
"""
from datetime import datetime, timedelta, date, time
from typing import List, Dict, Any, Optional
from zoneinfo import ZoneInfo
from sqlalchemy import select, func, and_, case, exists
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.feedback import FeedbackRecord
from app.models.analysis import SentimentResult, IntentResult, AspectSentimentResult

# Application timezone (Thai users)
APP_TIMEZONE = ZoneInfo("Asia/Bangkok")


class AnalyticsService:
    """Service for analytics and dashboard statistics"""

    @staticmethod
    def _build_date_filter(effective_date, start_date: Optional[date], end_date: Optional[date]):
        """
        Build date filter conditions for a given effective_date column.
        Returns a list of filter conditions to be used with and_().

        Dates are interpreted as Bangkok timezone (Asia/Bangkok) since this is
        a Thai application. The resulting datetime is converted to UTC for
        comparison with timezone-aware database timestamps.
        """
        conditions = []
        if start_date:
            # Start of day in Bangkok timezone, then convert to UTC
            start_datetime_local = datetime.combine(start_date, time.min, tzinfo=APP_TIMEZONE)
            start_datetime_utc = start_datetime_local.astimezone(ZoneInfo("UTC"))
            conditions.append(effective_date >= start_datetime_utc)
        if end_date:
            # End of day in Bangkok timezone (23:59:59.999999), then convert to UTC
            end_datetime_local = datetime.combine(end_date, time.max, tzinfo=APP_TIMEZONE)
            end_datetime_utc = end_datetime_local.astimezone(ZoneInfo("UTC"))
            conditions.append(effective_date <= end_datetime_utc)
        return conditions

    @staticmethod
    async def get_overview(
        db: AsyncSession,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Get dashboard overview statistics

        Args:
            db: Database session
            start_date: Optional filter start date (inclusive)
            end_date: Optional filter end date (inclusive)

        Returns: Dashboard overview data including totals, distributions, and summaries
        """
        # Current time for trend calculations
        now = datetime.utcnow()

        # Use effective date: created_at_source (original date) with fallback to created_at
        effective_date = func.coalesce(FeedbackRecord.created_at_source, FeedbackRecord.created_at)
        date_conditions = AnalyticsService._build_date_filter(effective_date, start_date, end_date)

        # Total feedbacks (filtered by date)
        total_stmt = select(func.count(FeedbackRecord.id))
        if date_conditions:
            total_stmt = total_stmt.where(and_(*date_conditions))
        total_result = await db.execute(total_stmt)
        total_feedbacks = total_result.scalar() or 0

        # Calculate trend by comparing selected period vs previous equivalent period
        # Example: If selected Jan 10-20 (11 days), compare with Dec 30 - Jan 9 (previous 11 days)
        trend_percentage = None
        trend_info = None

        if start_date and end_date:
            # Calculate the span in days
            span_days = (end_date - start_date).days + 1

            # Calculate previous period (same length, immediately before selected period)
            prev_end = start_date - timedelta(days=1)
            prev_start = prev_end - timedelta(days=span_days - 1)

            # Current period count (already calculated as total_feedbacks)
            current_count = total_feedbacks

            # Previous period count
            prev_start_dt = datetime.combine(prev_start, time.min, tzinfo=APP_TIMEZONE).astimezone(ZoneInfo("UTC"))
            prev_end_dt = datetime.combine(prev_end, time.max, tzinfo=APP_TIMEZONE).astimezone(ZoneInfo("UTC"))
            prev_stmt = select(func.count(FeedbackRecord.id)).where(
                and_(
                    effective_date >= prev_start_dt,
                    effective_date <= prev_end_dt
                )
            )
            prev_result = await db.execute(prev_stmt)
            previous_count = prev_result.scalar() or 0

            # Calculate trend percentage
            if previous_count > 0:
                trend_percentage = round(((current_count - previous_count) / previous_count) * 100, 1)
            elif current_count > 0:
                trend_percentage = 100.0  # Infinite increase (from 0)
            else:
                trend_percentage = 0.0  # No data in either period

            # Generate human-readable comparison label
            comparison_label = AnalyticsService._get_comparison_label(span_days)

            trend_info = {
                'percentage': trend_percentage,
                'current_count': current_count,
                'previous_count': previous_count,
                'comparison_label': comparison_label,
                'span_days': span_days
            }
        else:
            # Default: compare last 7 days vs the 7 days before that
            today = now.date()
            current_end = today
            current_start = today - timedelta(days=6)  # Last 7 days including today
            prev_end = current_start - timedelta(days=1)
            prev_start = prev_end - timedelta(days=6)  # Previous 7 days

            # Current period count
            current_start_dt = datetime.combine(current_start, time.min, tzinfo=APP_TIMEZONE).astimezone(ZoneInfo("UTC"))
            current_end_dt = datetime.combine(current_end, time.max, tzinfo=APP_TIMEZONE).astimezone(ZoneInfo("UTC"))
            current_stmt = select(func.count(FeedbackRecord.id)).where(
                and_(
                    effective_date >= current_start_dt,
                    effective_date <= current_end_dt
                )
            )
            current_result = await db.execute(current_stmt)
            current_count = current_result.scalar() or 0

            # Previous period count
            prev_start_dt = datetime.combine(prev_start, time.min, tzinfo=APP_TIMEZONE).astimezone(ZoneInfo("UTC"))
            prev_end_dt = datetime.combine(prev_end, time.max, tzinfo=APP_TIMEZONE).astimezone(ZoneInfo("UTC"))
            prev_stmt = select(func.count(FeedbackRecord.id)).where(
                and_(
                    effective_date >= prev_start_dt,
                    effective_date <= prev_end_dt
                )
            )
            prev_result = await db.execute(prev_stmt)
            previous_count = prev_result.scalar() or 0

            # Calculate trend percentage
            if previous_count > 0:
                trend_percentage = round(((current_count - previous_count) / previous_count) * 100, 1)
            elif current_count > 0:
                trend_percentage = 100.0
            else:
                trend_percentage = 0.0

            trend_info = {
                'percentage': trend_percentage,
                'current_count': current_count,
                'previous_count': previous_count,
                'comparison_label': 'vs previous 7 days',
                'span_days': 7
            }

        # Sentiment distribution (joined with FeedbackRecord for date filtering)
        sentiment_stmt = (
            select(
                SentimentResult.sentiment,
                func.count(SentimentResult.id).label('count')
            )
            .join(FeedbackRecord, SentimentResult.feedback_id == FeedbackRecord.id)
            .where(SentimentResult.is_deleted == False)
        )
        if date_conditions:
            sentiment_stmt = sentiment_stmt.where(and_(*date_conditions))
        sentiment_stmt = sentiment_stmt.group_by(SentimentResult.sentiment)
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

        # Intent distribution (joined with FeedbackRecord for date filtering)
        intent_stmt = (
            select(
                IntentResult.intent,
                func.count(IntentResult.id).label('count')
            )
            .join(FeedbackRecord, IntentResult.feedback_id == FeedbackRecord.id)
            .where(IntentResult.is_deleted == False)
        )
        if date_conditions:
            intent_stmt = intent_stmt.where(and_(*date_conditions))
        intent_stmt = intent_stmt.group_by(IntentResult.intent)
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

        # Source distribution (filtered by date)
        source_stmt = (
            select(
                FeedbackRecord.source_type,
                func.count(FeedbackRecord.id).label('count')
            )
        )
        if date_conditions:
            source_stmt = source_stmt.where(and_(*date_conditions))
        source_stmt = source_stmt.group_by(FeedbackRecord.source_type)
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

        # Aspect summary with satisfaction score (0-100 scale) - joined with FeedbackRecord for date filtering
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
            .join(FeedbackRecord, AspectSentimentResult.feedback_id == FeedbackRecord.id)
            .where(AspectSentimentResult.is_deleted == False)
        )
        if date_conditions:
            aspect_stmt = aspect_stmt.where(and_(*date_conditions))
        aspect_stmt = aspect_stmt.group_by(AspectSentimentResult.aspect)
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

        # Average confidence across all analyses (filtered by date)
        confidence_stmt = (
            select(func.avg(SentimentResult.confidence))
            .join(FeedbackRecord, SentimentResult.feedback_id == FeedbackRecord.id)
        )
        if date_conditions:
            confidence_stmt = confidence_stmt.where(and_(*date_conditions))
        confidence_result = await db.execute(confidence_stmt)
        avg_confidence = confidence_result.scalar() or 0.0

        # Calculate average satisfaction score across all aspects
        if aspect_summary:
            avg_satisfaction = round(sum(a['satisfaction_score'] for a in aspect_summary) / len(aspect_summary), 1)
        else:
            avg_satisfaction = 0.0

        # Recent feedbacks (last 5) - ordered by effective date (filtered by date range)
        recent_stmt = select(FeedbackRecord)
        if date_conditions:
            recent_stmt = recent_stmt.where(and_(*date_conditions))
        recent_stmt = recent_stmt.order_by(effective_date.desc()).limit(5)
        recent_result = await db.execute(recent_stmt)
        recent_feedbacks = recent_result.scalars().all()

        # Recent complaints (last 4) with negative aspects (filtered by date range)
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
        )
        if date_conditions:
            recent_complaints_stmt = recent_complaints_stmt.where(and_(*date_conditions))
        recent_complaints_stmt = recent_complaints_stmt.order_by(effective_date.desc()).limit(4)
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
            'trend_info': trend_info,
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
    def _determine_granularity(start_date: date, end_date: date) -> str:
        """
        Determine the appropriate granularity based on date span.
        Supports ranges up to 2,000 days (~5.5 years).

        - ≤ 60 days: daily (max 60 points)
        - 61-180 days: weekly (max ~26 points)
        - 181-730 days: monthly (max ~24 points)
        - > 730 days: quarterly (max ~22 points for 5.5 years)
        """
        span_days = (end_date - start_date).days + 1
        if span_days <= 60:
            return 'daily'
        elif span_days <= 180:
            return 'weekly'
        elif span_days <= 730:
            return 'monthly'
        else:
            return 'quarterly'

    @staticmethod
    def _get_week_start(d: date) -> date:
        """Get the Monday of the week for a given date (ISO week)."""
        return d - timedelta(days=d.weekday())

    @staticmethod
    def _get_month_start(d: date) -> date:
        """Get the first day of the month for a given date."""
        return d.replace(day=1)

    @staticmethod
    def _get_quarter_start(d: date) -> date:
        """Get the first day of the quarter for a given date."""
        quarter_month = ((d.month - 1) // 3) * 3 + 1  # 1, 4, 7, or 10
        return d.replace(month=quarter_month, day=1)

    @staticmethod
    def _get_comparison_label(span_days: int) -> str:
        """
        Generate a human-readable comparison label based on the period length.

        Args:
            span_days: Number of days in the period

        Returns:
            Human-readable label like "vs previous 7 days" or "vs previous month"
        """
        if span_days == 1:
            return 'vs yesterday'
        elif span_days == 7:
            return 'vs previous week'
        elif span_days <= 14:
            return f'vs previous {span_days} days'
        elif span_days <= 31:
            # Check for approximate month (28-31 days)
            if span_days >= 28:
                return 'vs previous month'
            # For 15-27 days, show in weeks if divisible, otherwise days
            weeks = span_days // 7
            if span_days % 7 == 0 and weeks > 1:
                return f'vs previous {weeks} weeks'
            return f'vs previous {span_days} days'
        elif span_days <= 93:
            # Check for approximate quarter (89-93 days)
            if span_days >= 89:
                return 'vs previous quarter'
            # For 32-88 days, convert to months for readability
            months = round(span_days / 30)
            if months == 1:
                return 'vs previous month'
            return f'vs previous {months} months'
        elif span_days <= 366:
            # Check for approximate year (360-366 days)
            if span_days >= 360:
                return 'vs previous year'
            # For 94-359 days, convert to months
            months = round(span_days / 30)
            if months == 1:
                return 'vs previous month'
            return f'vs previous {months} months'
        else:
            # For very long periods (> 1 year), show in years
            years = span_days / 365
            if years >= 1.9:
                return f'vs previous {round(years)} years'
            # Show in months for periods like 400-700 days
            months = round(span_days / 30)
            return f'vs previous {months} months'

    @staticmethod
    async def get_trends(
        db: AsyncSession,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
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
            db: Database session
            start_date: Optional filter start date (inclusive). Defaults to 90 days ago.
            end_date: Optional filter end date (inclusive). Defaults to today.

        Returns: Dict with 'granularity' and 'data' (list of trend data points)
        """
        # Default to last 90 days if no dates provided
        today = datetime.utcnow().date()
        if end_date is None:
            end_date = today
        if start_date is None:
            start_date = today - timedelta(days=89)  # 90 days including today

        # Determine granularity based on span
        granularity = AnalyticsService._determine_granularity(start_date, end_date)

        # Use effective date: created_at_source (original date from source) with fallback to created_at
        effective_date = func.coalesce(FeedbackRecord.created_at_source, FeedbackRecord.created_at)

        # Build date filter conditions (convert Bangkok local time to UTC)
        start_datetime = datetime.combine(start_date, time.min, tzinfo=APP_TIMEZONE).astimezone(ZoneInfo("UTC"))
        end_datetime = datetime.combine(end_date, time.max, tzinfo=APP_TIMEZONE).astimezone(ZoneInfo("UTC"))

        # Build the GROUP BY expression based on granularity
        if granularity == 'daily':
            group_expr = func.date(effective_date)
        elif granularity == 'weekly':
            # Group by ISO week start (Monday) - PostgreSQL specific
            group_expr = func.date_trunc('week', effective_date)
        elif granularity == 'monthly':
            # Group by month start
            group_expr = func.date_trunc('month', effective_date)
        else:  # quarterly
            # Group by quarter start - PostgreSQL specific
            group_expr = func.date_trunc('quarter', effective_date)

        # Query for trends grouped by the appropriate time unit
        stmt = (
            select(
                group_expr.label('period'),
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
                    effective_date >= start_datetime,
                    effective_date <= end_datetime,
                    SentimentResult.is_deleted == False
                )
            )
            .group_by(group_expr)
            .order_by(group_expr)
        )

        result = await db.execute(stmt)
        rows = result.all()

        # Create a dict for quick lookup (normalize keys to date)
        data_dict = {}
        for row in rows:
            if row.period is not None:
                # Handle both date and datetime returns from date_trunc
                if isinstance(row.period, datetime):
                    key = row.period.date()
                else:
                    key = row.period
                data_dict[key] = row

        # Generate complete list of periods and fill gaps with zeros
        trends = []

        # Helper to safely extract values (handles None from SQL aggregates)
        def make_trend_point(period_date: date, row) -> Dict[str, Any]:
            return {
                'date': period_date.isoformat(),
                'total': (row.total or 0) if row else 0,
                'positive': (row.positive or 0) if row else 0,
                'neutral': (row.neutral or 0) if row else 0,
                'negative': (row.negative or 0) if row else 0
            }

        if granularity == 'daily':
            current = start_date
            while current <= end_date:
                row = data_dict.get(current)
                trends.append(make_trend_point(current, row))
                current += timedelta(days=1)

        elif granularity == 'weekly':
            # Start from the Monday of the start_date's week
            current = AnalyticsService._get_week_start(start_date)
            end_week = AnalyticsService._get_week_start(end_date)
            while current <= end_week:
                row = data_dict.get(current)
                trends.append(make_trend_point(current, row))
                current += timedelta(weeks=1)

        elif granularity == 'monthly':
            # Start from the first day of start_date's month
            current = AnalyticsService._get_month_start(start_date)
            end_month = AnalyticsService._get_month_start(end_date)
            while current <= end_month:
                row = data_dict.get(current)
                trends.append(make_trend_point(current, row))
                # Move to next month
                if current.month == 12:
                    current = current.replace(year=current.year + 1, month=1)
                else:
                    current = current.replace(month=current.month + 1)

        else:  # quarterly
            # Start from the first day of start_date's quarter
            current = AnalyticsService._get_quarter_start(start_date)
            end_quarter = AnalyticsService._get_quarter_start(end_date)
            while current <= end_quarter:
                row = data_dict.get(current)
                trends.append(make_trend_point(current, row))
                # Move to next quarter (add 3 months)
                new_month = current.month + 3
                if new_month > 12:
                    current = current.replace(year=current.year + 1, month=new_month - 12)
                else:
                    current = current.replace(month=new_month)

        return {
            'granularity': granularity,
            'data': trends
        }
