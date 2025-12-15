"""
Data ingestion service for creating feedback records and publishing to queue
"""
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.feedback import FeedbackRecord
from app.rabbitmq import rabbitmq_manager
from app.exceptions import (
    DuplicateFeedbackError,
    DatabaseError,
    QueuePublishError
)

logger = logging.getLogger(__name__)


class IngestionService:
    """Service for handling feedback data ingestion"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_feedback_record(
        self,
        source_type: str,
        source_id: str,
        text_content: str,
        raw_data: Dict[str, Any],
        created_at_source: Optional[datetime] = None
    ) -> FeedbackRecord:
        """
        Create a new feedback record in the database.
        If a record with the same source_type and source_id exists, return the existing record.

        Args:
            source_type: Type of source (email, instagram, etc.)
            source_id: Unique ID from the source platform
            text_content: Main text content of the feedback
            raw_data: Full raw data from the source
            created_at_source: Original timestamp from source

        Returns:
            FeedbackRecord: Created or existing feedback record

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            # Check if record already exists
            stmt = select(FeedbackRecord).where(
                FeedbackRecord.source_type == source_type,
                FeedbackRecord.source_id == source_id
            )
            result = await self.db.execute(stmt)
            existing_record = result.scalar_one_or_none()

            if existing_record:
                logger.info(
                    f"Feedback record already exists: {source_type}/{source_id}, "
                    f"returning existing record ID: {existing_record.id}"
                )
                return existing_record

            # Create new record
            feedback = FeedbackRecord(
                source_type=source_type,
                source_id=source_id,
                text_content=text_content,
                raw_data=raw_data,
                created_at_source=created_at_source,
                processing_status="pending"
            )

            self.db.add(feedback)
            await self.db.commit()
            await self.db.refresh(feedback)

            logger.info(
                f"Created new feedback record: {feedback.id} "
                f"from {source_type}/{source_id}"
            )

            return feedback

        except IntegrityError as e:
            await self.db.rollback()
            logger.error(f"Integrity error creating feedback: {e}")
            # Check again for existing record (race condition)
            stmt = select(FeedbackRecord).where(
                FeedbackRecord.source_type == source_type,
                FeedbackRecord.source_id == source_id
            )
            result = await self.db.execute(stmt)
            existing_record = result.scalar_one_or_none()
            if existing_record:
                return existing_record
            raise DatabaseError(
                message="Failed to create feedback record",
                details={"source_type": source_type, "source_id": source_id}
            )

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating feedback record: {e}")
            raise DatabaseError(
                message=f"Unexpected error: {str(e)}",
                details={"source_type": source_type, "source_id": source_id}
            )

    def publish_to_queue(self, record_id: UUID, queue_name: str = "data_ingestion") -> bool:
        """
        Publish a message to RabbitMQ queue for processing

        Args:
            record_id: UUID of the feedback record
            queue_name: Name of the queue to publish to

        Returns:
            bool: True if successful

        Raises:
            QueuePublishError: If publishing fails
        """
        try:
            message = {
                "record_id": str(record_id),
                "action": "analyze",
                "timestamp": datetime.utcnow().isoformat()
            }

            success = rabbitmq_manager.publish_message(
                queue_name=queue_name,
                message=message
            )

            if not success:
                raise QueuePublishError(
                    queue_name=queue_name,
                    details={"record_id": str(record_id)}
                )

            logger.info(f"Published record {record_id} to queue '{queue_name}'")
            return True

        except Exception as e:
            logger.error(f"Failed to publish to queue: {e}")
            raise QueuePublishError(
                queue_name=queue_name,
                details={"record_id": str(record_id), "error": str(e)}
            )

    async def ingest_and_publish(
        self,
        source_type: str,
        source_id: str,
        text_content: str,
        raw_data: Dict[str, Any],
        created_at_source: Optional[datetime] = None
    ) -> FeedbackRecord:
        """
        Convenience method to create feedback record and publish to queue

        Args:
            source_type: Type of source (email, instagram, etc.)
            source_id: Unique ID from the source platform
            text_content: Main text content of the feedback
            raw_data: Full raw data from the source
            created_at_source: Original timestamp from source

        Returns:
            FeedbackRecord: Created feedback record

        Raises:
            DatabaseError: If database operation fails
            QueuePublishError: If queue publishing fails
        """
        # Create record
        record = await self.create_feedback_record(
            source_type=source_type,
            source_id=source_id,
            text_content=text_content,
            raw_data=raw_data,
            created_at_source=created_at_source
        )

        # Publish to queue
        self.publish_to_queue(record.id)

        return record
