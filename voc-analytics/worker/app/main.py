"""
Worker application for processing messages from RabbitMQ
"""
import asyncio
import json
import logging
import signal
import sys
from uuid import UUID

import pika
from pika.adapters.blocking_connection import BlockingChannel
from pika.spec import Basic, BasicProperties
from sqlalchemy import select, update

from app.config import settings
from app.database import get_db_session
from app.models import FeedbackRecord, SentimentResult, IntentResult, AspectSentimentResult
from app.nlp_service import get_nlp_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global flag for graceful shutdown
shutdown_flag = False


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    global shutdown_flag
    logger.info(f"Received signal {signum}. Initiating graceful shutdown...")
    shutdown_flag = True


async def process_feedback_analysis(record_id: UUID) -> bool:
    """
    Process ML analysis for a feedback record

    Args:
        record_id: UUID of the feedback record

    Returns:
        bool: True if processing successful, False otherwise
    """
    try:
        async with get_db_session() as db:
            # 1. Fetch feedback record
            logger.info(f"Fetching feedback record: {record_id}")
            result = await db.execute(
                select(FeedbackRecord).where(FeedbackRecord.id == record_id)
            )
            feedback = result.scalar_one_or_none()

            if not feedback:
                logger.error(f"Feedback record not found: {record_id}")
                return False

            logger.info(f"Processing feedback: {feedback.text_content[:100]}...")

            # 2. Update status to 'processing'
            await db.execute(
                update(FeedbackRecord)
                .where(FeedbackRecord.id == record_id)
                .values(processing_status="processing")
            )
            await db.commit()

            # 3. Get NLP service and run analysis
            logger.info("Running ML analysis...")
            nlp_service = get_nlp_service()

            # Run individual analyses to get detailed results
            sentiment_result_data = nlp_service.sentiment.analyze(feedback.text_content)
            intent_result_data = nlp_service.intent.classify(feedback.text_content)
            aspect_results_data = nlp_service.absa.analyze(feedback.text_content, include_none=True)  # ✅ เก็บทุก aspect

            # 4. Store sentiment result
            sentiment_result = SentimentResult(
                feedback_id=record_id,
                sentiment=sentiment_result_data['label'],
                confidence=sentiment_result_data['confidence'],
                source='model'  # Mark as model prediction
            )
            db.add(sentiment_result)
            logger.info(f"Sentiment: {sentiment_result_data['label']} ({sentiment_result_data['confidence']:.2%})")

            # 5. Store intent results (multi-label, can have multiple intents)
            # If no intents detected, store primary intent anyway
            if intent_result_data['labels']:
                for intent_label in intent_result_data['labels']:
                    intent_result = IntentResult(
                        feedback_id=record_id,
                        intent=intent_label,
                        confidence=intent_result_data['probabilities'][intent_label],
                        source='model'  # Mark as model prediction
                    )
                    db.add(intent_result)
                logger.info(f"Intent: {intent_result_data['labels']}")
            else:
                # Store the highest probability intent even if below threshold
                primary = max(intent_result_data['probabilities'], key=intent_result_data['probabilities'].get)
                intent_result = IntentResult(
                    feedback_id=record_id,
                    intent=primary,
                    confidence=intent_result_data['probabilities'][primary],
                    source='model'  # Mark as model prediction
                )
                db.add(intent_result)
                logger.info(f"Intent (primary): {primary} ({intent_result_data['probabilities'][primary]:.2%})")

            # 6. Store aspect sentiment results (Hybrid++: exclude 'none')
            stored_aspects = []
            for aspect in aspect_results_data:
                if aspect['sentiment'] != 'none':  # Only store aspects with sentiment
                    aspect_result = AspectSentimentResult(
                        feedback_id=record_id,
                        aspect=aspect['aspect'],
                        sentiment=aspect['sentiment'],
                        confidence=aspect['confidence'],
                        source='model'  # Mark as model prediction
                    )
                    db.add(aspect_result)
                    stored_aspects.append(aspect)

            # Count aspects for logging
            logger.info(f"Aspects analyzed: {len(aspect_results_data)} total, {len(stored_aspects)} with sentiment stored (excluded {len(aspect_results_data) - len(stored_aspects)} with sentiment='none')")

            # 6.5. Build and store analysis summary (JSONB) - Hybrid++ approach
            analysis_summary = {
                "sentiment": {
                    "label": sentiment_result_data['label'],
                    "confidence": float(sentiment_result_data['confidence']),
                    "probabilities": {k: float(v) for k, v in sentiment_result_data.get('probabilities', {}).items()},
                    "source": "model",
                    "edited": False
                },
                "intents": [
                    {
                        "label": label,
                        "confidence": float(intent_result_data['probabilities'][label]),
                        "source": "model",
                        "edited": False
                    }
                    for label in (intent_result_data['labels'] if intent_result_data['labels'] else [primary])
                ],
                "aspects": [
                    {
                        "aspect": a['aspect'],
                        "aspect_thai": a['aspect_thai'],
                        "sentiment": a['sentiment'],
                        "confidence": float(a['confidence']),
                        "source": "model",
                        "edited": False
                    }
                    for a in stored_aspects  # Only include aspects with sentiment (exclude 'none')
                ],
                "summary_stats": {
                    "total_aspects_analyzed": len(aspect_results_data),  # Total analyzed (including 'none')
                    "aspects_with_sentiment": len(stored_aspects),  # Only stored (excluding 'none')
                    "positive_aspects": sum(1 for a in stored_aspects if a['sentiment'] == 'positive'),
                    "negative_aspects": sum(1 for a in stored_aspects if a['sentiment'] == 'negative'),
                    "neutral_aspects": sum(1 for a in stored_aspects if a['sentiment'] == 'neutral'),
                    "model_predictions": len(stored_aspects),  # All current aspects are from model
                    "user_corrections": 0,
                    "user_additions": 0
                }
            }

            logger.info(f"Summary: {len(stored_aspects)} aspects with sentiment (P:{analysis_summary['summary_stats']['positive_aspects']} N:{analysis_summary['summary_stats']['negative_aspects']} Neu:{analysis_summary['summary_stats']['neutral_aspects']})")

            # 7. Update status to 'completed' and store analysis_summary
            await db.execute(
                update(FeedbackRecord)
                .where(FeedbackRecord.id == record_id)
                .values(
                    processing_status="completed",
                    analysis_summary=analysis_summary
                )
            )

            # 8. Commit all changes
            await db.commit()
            logger.info(f"✅ Successfully processed feedback: {record_id}")

            return True

    except Exception as e:
        logger.error(f"Error processing feedback {record_id}: {e}", exc_info=True)

        # Update status to 'failed'
        try:
            async with get_db_session() as db:
                await db.execute(
                    update(FeedbackRecord)
                    .where(FeedbackRecord.id == record_id)
                    .values(processing_status="failed")
                )
                await db.commit()
        except Exception as db_error:
            logger.error(f"Failed to update status to 'failed': {db_error}")

        return False


def process_message(message_data: dict) -> bool:
    """
    Process a message from the queue (synchronous wrapper for async processing)

    Args:
        message_data: Message data dictionary

    Returns:
        bool: True if processing successful, False otherwise
    """
    try:
        logger.info(f"Received message: {message_data}")

        # Parse message
        record_id = UUID(message_data.get('record_id'))
        action = message_data.get('action', 'analyze')

        if action != 'analyze':
            logger.warning(f"Unknown action: {action}")
            return False

        # Run async processing in event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            success = loop.run_until_complete(process_feedback_analysis(record_id))
            return success
        finally:
            loop.close()

    except ValueError as e:
        logger.error(f"Invalid record_id in message: {e}")
        return False
    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)
        return False


def callback(
    channel: BlockingChannel,
    method: Basic.Deliver,
    properties: BasicProperties,
    body: bytes
):
    """
    Callback function for consuming messages

    Args:
        channel: Channel object
        method: Delivery method
        properties: Message properties
        body: Message body
    """
    try:
        # Parse message
        message_data = json.loads(body.decode())
        logger.info(f"Received message from queue '{method.routing_key}'")

        # Process message
        success = process_message(message_data)

        if success:
            # Acknowledge message
            channel.basic_ack(delivery_tag=method.delivery_tag)
            logger.info("Message acknowledged")
        else:
            # Reject and requeue message
            channel.basic_nack(
                delivery_tag=method.delivery_tag,
                requeue=True
            )
            logger.warning("Message rejected and requeued")

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in message: {e}")
        # Reject without requeue for invalid messages
        channel.basic_nack(
            delivery_tag=method.delivery_tag,
            requeue=False
        )

    except Exception as e:
        logger.error(f"Error in callback: {e}")
        # Reject and requeue on unexpected errors
        channel.basic_nack(
            delivery_tag=method.delivery_tag,
            requeue=True
        )


def main():
    """Main worker function"""
    global shutdown_flag

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    logger.info(f"Starting {settings.WORKER_NAME}...")

    # Pre-load ML models
    logger.info("="*60)
    logger.info("🤖 Initializing ML models...")
    logger.info("="*60)
    try:
        nlp_service = get_nlp_service()
        logger.info("✅ ML models loaded successfully")
    except Exception as e:
        logger.error(f"❌ Failed to load ML models: {e}")
        logger.error("Worker cannot start without ML models")
        sys.exit(1)

    logger.info(f"Connecting to RabbitMQ: {settings.RABBITMQ_URL}")

    connection = None
    channel = None

    try:
        # Connect to RabbitMQ
        parameters = pika.URLParameters(settings.RABBITMQ_URL)
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()

        logger.info("Connected to RabbitMQ successfully")

        # Declare queue
        channel.queue_declare(
            queue=settings.QUEUE_NAME,
            durable=True
        )
        logger.info(f"Queue '{settings.QUEUE_NAME}' declared")

        # Set QoS (Quality of Service)
        channel.basic_qos(prefetch_count=settings.PREFETCH_COUNT)
        logger.info(f"QoS set: prefetch_count={settings.PREFETCH_COUNT}")

        # Start consuming
        channel.basic_consume(
            queue=settings.QUEUE_NAME,
            on_message_callback=callback,
            auto_ack=False
        )

        logger.info(f"Worker is ready. Waiting for messages on queue '{settings.QUEUE_NAME}'...")
        logger.info("Press CTRL+C to exit")

        # Start consuming with shutdown check
        while not shutdown_flag:
            try:
                connection.process_data_events(time_limit=1)
            except Exception as e:
                logger.error(f"Error processing events: {e}")
                break

        logger.info("Shutting down worker...")

    except KeyboardInterrupt:
        logger.info("Interrupted by user")

    except Exception as e:
        logger.error(f"Worker error: {e}")
        sys.exit(1)

    finally:
        # Cleanup
        if channel and channel.is_open:
            channel.stop_consuming()
            logger.info("Stopped consuming messages")

        if connection and connection.is_open:
            connection.close()
            logger.info("RabbitMQ connection closed")

        logger.info("Worker shutdown complete")


if __name__ == "__main__":
    main()
