"""
Custom exceptions for the application
"""
from typing import Optional, Any, Dict


class VoCAnalyticsException(Exception):
    """Base exception for VoC Analytics application"""
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class FeedbackNotFoundError(VoCAnalyticsException):
    """Raised when feedback record is not found"""
    def __init__(self, feedback_id: str):
        super().__init__(
            message=f"Feedback record with ID '{feedback_id}' not found",
            status_code=404,
            details={"feedback_id": feedback_id}
        )


class DuplicateFeedbackError(VoCAnalyticsException):
    """Raised when attempting to create duplicate feedback"""
    def __init__(self, source_type: str, source_id: str):
        super().__init__(
            message=f"Feedback from {source_type} with ID '{source_id}' already exists",
            status_code=409,
            details={
                "source_type": source_type,
                "source_id": source_id
            }
        )


class DatabaseError(VoCAnalyticsException):
    """Raised when database operation fails"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"Database error: {message}",
            status_code=500,
            details=details
        )


class QueuePublishError(VoCAnalyticsException):
    """Raised when message queue publish fails"""
    def __init__(self, queue_name: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"Failed to publish message to queue '{queue_name}'",
            status_code=500,
            details=details or {"queue_name": queue_name}
        )


class WebhookAuthenticationError(VoCAnalyticsException):
    """Raised when webhook authentication fails"""
    def __init__(self):
        super().__init__(
            message="Webhook authentication failed: Invalid or missing token",
            status_code=401
        )


class ValidationError(VoCAnalyticsException):
    """Raised when validation fails"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"Validation error: {message}",
            status_code=422,
            details=details
        )
