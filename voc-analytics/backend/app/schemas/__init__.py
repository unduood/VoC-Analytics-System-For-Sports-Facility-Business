"""
Schemas package - exports all Pydantic schemas
"""
from app.schemas.feedback import (
    SourceType,
    ProcessingStatus,
    FeedbackBase,
    FeedbackCreate,
    FeedbackUpdate,
    FeedbackResponse,
    FeedbackDetailResponse,
    FeedbackListResponse,
)

from app.schemas.analysis import (
    Sentiment,
    Intent,
    Aspect,
    AspectSentiment,
    SentimentBase,
    SentimentCreate,
    SentimentResponse,
    IntentBase,
    IntentCreate,
    IntentResponse,
    AspectSentimentBase,
    AspectSentimentCreate,
    AspectSentimentResponse,
    AnalysisRequest,
    AnalysisResponse,
)

from app.schemas.webhooks import (
    EmailWebhookPayload,
    InstagramWebhookPayload,
    WebhookResponse,
)

__all__ = [
    # Enums
    "SourceType",
    "ProcessingStatus",
    "Sentiment",
    "Intent",
    "Aspect",
    "AspectSentiment",
    # Feedback schemas
    "FeedbackBase",
    "FeedbackCreate",
    "FeedbackUpdate",
    "FeedbackResponse",
    "FeedbackDetailResponse",
    "FeedbackListResponse",
    # Analysis schemas
    "SentimentBase",
    "SentimentCreate",
    "SentimentResponse",
    "IntentBase",
    "IntentCreate",
    "IntentResponse",
    "AspectSentimentBase",
    "AspectSentimentCreate",
    "AspectSentimentResponse",
    "AnalysisRequest",
    "AnalysisResponse",
    # Webhook schemas
    "EmailWebhookPayload",
    "InstagramWebhookPayload",
    "WebhookResponse",
]
