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
from app.services.redis_publisher import publish_analysis_completed, publish_analysis_failed

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


def rating_to_sentiment(rating: int) -> str:
    """
    Convert Google Maps rating (0-5) to sentiment label

    Mapping:
    - 0, 1, 2 → "negative"
    - 3 → "neutral"
    - 4, 5 → "positive"

    Args:
        rating: Integer rating 0-5

    Returns:
        Sentiment label string
    """
    if rating in [0, 1, 2]:
        return "negative"
    elif rating == 3:
        return "neutral"
    elif rating in [4, 5]:
        return "positive"
    else:
        logger.warning(f"Unexpected rating value: {rating}, defaulting to neutral")
        return "neutral"


# =====================================================
# VALUE NORMALIZATION FUNCTIONS
# =====================================================
# ML models return values in formats that don't match
# the backend schema enums. These functions normalize them.

SENTIMENT_MAPPING = {
    "pos": "positive",
    "neg": "negative",
    "neu": "neutral",
    "positive": "positive",
    "negative": "negative",
    "neutral": "neutral",
}

INTENT_MAPPING = {
    "Feedback": "feedback",
    "Question": "question",
    "Complaint": "complaint",
    "Off-topic": "off_topic",
    "feedback": "feedback",
    "question": "question",
    "complaint": "complaint",
    "off_topic": "off_topic",
}

ASPECT_MAPPING = {
    "Equipment": "equipment",
    "Staff": "staff",
    "Cleanliness": "cleanliness",
    "Atmosphere": "atmosphere",
    "Price": "price",
    "Location": "location",
    "Programs": "programs",
    "Program": "programs",
    "Amenities": "amenities",
    # Lowercase versions (already correct)
    "equipment": "equipment",
    "staff": "staff",
    "cleanliness": "cleanliness",
    "atmosphere": "atmosphere",
    "price": "price",
    "location": "location",
    "programs": "programs",
    "amenities": "amenities",
}

# Ordered list of (rating_field, aspect_label) tuples for Google Forms
# Order matches existing AspectLabel enum/convention in the project:
# equipment → staff → cleanliness → atmosphere → price → location → programs → amenities
GOOGLE_FORM_ASPECT_MAPPING = [
    ("equipment_rating", "equipment"),
    ("staff_rating", "staff"),
    ("cleanliness_rating", "cleanliness"),
    ("atmosphere_rating", "atmosphere"),
    ("price_rating", "price"),
    ("location_rating", "location"),
    ("program_rating", "programs"),
    ("amenities_rating", "amenities"),
]

# Thai labels for aspects (used in analysis_summary for frontend display)
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


def normalize_sentiment(value: str) -> str:
    """Normalize sentiment label to match backend enum"""
    normalized = SENTIMENT_MAPPING.get(value, value.lower())
    if normalized not in ["positive", "negative", "neutral"]:
        logger.warning(f"Unknown sentiment value: {value}, defaulting to neutral")
        return "neutral"
    return normalized


def normalize_intent(value: str) -> str:
    """Normalize intent label to match backend enum"""
    normalized = INTENT_MAPPING.get(value, value.lower().replace("-", "_"))
    if normalized not in ["feedback", "question", "complaint", "off_topic"]:
        logger.warning(f"Unknown intent value: {value}, defaulting to feedback")
        return "feedback"
    return normalized


def normalize_aspect(value: str) -> str:
    """Normalize aspect label to match backend enum"""
    normalized = ASPECT_MAPPING.get(value, value.lower())
    if normalized not in ["equipment", "staff", "cleanliness", "atmosphere", "price", "location", "programs", "amenities"]:
        logger.warning(f"Unknown aspect value: {value}, skipping")
        return None
    return normalized


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

            # 3. Check if Google Form source (NO ML processing - all rating-based)
            is_google_form = feedback.source_type == "google_form"

            if is_google_form:
                # ============================================================
                # GOOGLE FORM: Rating-based analysis (NO ML processing)
                # ============================================================
                logger.info("Processing Google Form feedback with rating-based analysis")
                raw_data = feedback.raw_data or {}

                # 3a. Sentiment from overall_rating
                overall_rating = raw_data.get("overall_rating")
                sentiment_label = rating_to_sentiment(overall_rating) if overall_rating else "neutral"
                sentiment_result = SentimentResult(
                    feedback_id=record_id,
                    sentiment=sentiment_label,
                    confidence=1.0,
                    source='rating'
                )
                db.add(sentiment_result)
                logger.info(f"Sentiment from overall_rating={overall_rating}: {sentiment_label}")

                # 3b. NO Intent results for Google Forms

                # 3c. Aspect results from each rating field (in specified order)
                stored_aspects = []
                for rating_field, aspect_label in GOOGLE_FORM_ASPECT_MAPPING:
                    rating = raw_data.get(rating_field)
                    if rating is not None:
                        aspect_sentiment = rating_to_sentiment(rating)
                        aspect_result = AspectSentimentResult(
                            feedback_id=record_id,
                            aspect=aspect_label,
                            sentiment=aspect_sentiment,
                            confidence=1.0,
                            source='rating'
                        )
                        db.add(aspect_result)
                        stored_aspects.append({
                            "aspect": aspect_label,
                            "aspect_thai": ASPECT_THAI_MAP.get(aspect_label, aspect_label),
                            "sentiment": aspect_sentiment,
                            "confidence": 1.0,
                            "rating": rating,
                            "source": "rating",
                            "edited": False
                        })

                logger.info(f"Created {len(stored_aspects)} aspect results from ratings")

                # 3d. Build analysis_summary (NO intents key for Google Forms)
                analysis_summary = {
                    "sentiment": {
                        "label": sentiment_label,
                        "confidence": 1.0,
                        "source": "rating",
                        "rating": overall_rating,
                        "edited": False
                    },
                    "aspects": stored_aspects,
                    "summary_stats": {
                        "total_aspects_analyzed": len(stored_aspects),
                        "aspects_with_sentiment": len(stored_aspects),
                        "positive_aspects": sum(1 for a in stored_aspects if a['sentiment'] == 'positive'),
                        "negative_aspects": sum(1 for a in stored_aspects if a['sentiment'] == 'negative'),
                        "neutral_aspects": sum(1 for a in stored_aspects if a['sentiment'] == 'neutral'),
                        "rating_based": True,
                        "model_predictions": 0,
                        "user_corrections": 0,
                        "user_additions": 0
                    }
                }

                # 3e. Update status to 'completed' and store analysis_summary
                await db.execute(
                    update(FeedbackRecord)
                    .where(FeedbackRecord.id == record_id)
                    .values(
                        processing_status="completed",
                        analysis_summary=analysis_summary
                    )
                )
                await db.commit()
                logger.info(f"✅ Successfully processed Google Form feedback: {record_id}")

                # 3f. Broadcast analysis completed event
                publish_analysis_completed(
                    feedback_id=record_id,
                    source_type=feedback.source_type,
                    analysis_summary=analysis_summary
                )

                return True

            # ============================================================
            # OTHER SOURCES: ML-based analysis (Google Maps, Email, etc.)
            # ============================================================

            # 4. Check if this is Google Maps review with rating
            is_google_maps = feedback.source_type == "google_maps"
            rating = feedback.raw_data.get("rating") if feedback.raw_data else None
            use_rating_sentiment = is_google_maps and rating is not None

            logger.info("Running ML analysis...")
            nlp_service = get_nlp_service()

            # 5a. Sentiment Analysis - Rating-based OR Model-based
            if use_rating_sentiment:
                # RATING-BASED SENTIMENT (Bypass ML Model)
                sentiment_label = rating_to_sentiment(rating)
                sentiment_result_data = {
                    'label': sentiment_label,
                    'confidence': 1.0,  # 100% confidence from rating
                    'probabilities': {sentiment_label: 1.0}
                }
                logger.info(
                    f"Using rating-based sentiment for Google Maps review: "
                    f"rating={rating} → sentiment={sentiment_label}"
                )
            else:
                # MODEL-BASED SENTIMENT (Original behavior)
                sentiment_result_data = nlp_service.sentiment.analyze(feedback.text_content)
                logger.info(
                    f"Using model-based sentiment: {sentiment_result_data['label']} "
                    f"({sentiment_result_data['confidence']:.2%})"
                )

            # 5b. Intent Analysis (ALWAYS run model)
            intent_result_data = nlp_service.intent.classify(feedback.text_content)

            # 5c. ABSA Analysis (ALWAYS run model)
            aspect_results_data = nlp_service.absa.analyze(feedback.text_content, include_none=True)

            # 6. Store sentiment result with correct source
            normalized_sentiment = normalize_sentiment(sentiment_result_data['label'])
            sentiment_result = SentimentResult(
                feedback_id=record_id,
                sentiment=normalized_sentiment,
                confidence=sentiment_result_data['confidence'],
                source='rating' if use_rating_sentiment else 'model'  # ✅ Track source
            )
            db.add(sentiment_result)
            logger.info(
                f"Sentiment: {normalized_sentiment} "
                f"({sentiment_result_data['confidence']:.2%}) "
                f"[source: {'rating' if use_rating_sentiment else 'model'}]"
            )

            # 7. Store intent results (multi-label, can have multiple intents)
            # If no intents detected, store primary intent anyway
            if intent_result_data['labels']:
                normalized_intents = []
                for intent_label in intent_result_data['labels']:
                    normalized_intent = normalize_intent(intent_label)
                    intent_result = IntentResult(
                        feedback_id=record_id,
                        intent=normalized_intent,
                        confidence=intent_result_data['probabilities'][intent_label],
                        source='model'  # Mark as model prediction
                    )
                    db.add(intent_result)
                    normalized_intents.append(normalized_intent)
                logger.info(f"Intent: {normalized_intents}")
            else:
                # Store the highest probability intent even if below threshold
                primary = max(intent_result_data['probabilities'], key=intent_result_data['probabilities'].get)
                normalized_primary = normalize_intent(primary)
                intent_result = IntentResult(
                    feedback_id=record_id,
                    intent=normalized_primary,
                    confidence=intent_result_data['probabilities'][primary],
                    source='model'  # Mark as model prediction
                )
                db.add(intent_result)
                logger.info(f"Intent (primary): {normalized_primary} ({intent_result_data['probabilities'][primary]:.2%})")

            # 8. Store aspect sentiment results (Hybrid++: exclude 'none')
            stored_aspects = []
            for aspect in aspect_results_data:
                if aspect['sentiment'] != 'none':  # Only store aspects with sentiment
                    normalized_aspect_name = normalize_aspect(aspect['aspect'])
                    if normalized_aspect_name is None:
                        continue  # Skip unknown aspects
                    aspect_result = AspectSentimentResult(
                        feedback_id=record_id,
                        aspect=normalized_aspect_name,
                        sentiment=aspect['sentiment'],  # ABSA sentiment is already lowercase
                        confidence=aspect['confidence'],
                        source='model'  # Mark as model prediction
                    )
                    db.add(aspect_result)
                    # Store normalized version for summary
                    stored_aspects.append({
                        **aspect,
                        'aspect': normalized_aspect_name
                    })

            # Count aspects for logging
            logger.info(f"Aspects analyzed: {len(aspect_results_data)} total, {len(stored_aspects)} with sentiment stored (excluded {len(aspect_results_data) - len(stored_aspects)} with sentiment='none')")

            # 9. Build and store analysis summary (JSONB) - Hybrid++ approach
            # Use normalized values for summary
            summary_intents = normalized_intents if intent_result_data['labels'] else [normalized_primary]
            analysis_summary = {
                "sentiment": {
                    "label": normalized_sentiment,
                    "confidence": float(sentiment_result_data['confidence']),
                    "probabilities": {k: float(v) for k, v in sentiment_result_data.get('probabilities', {}).items()},
                    "source": "rating" if use_rating_sentiment else "model",  # ✅ Track source
                    "rating": rating if use_rating_sentiment else None,  # ✅ Include rating if used
                    "edited": False
                },
                "intents": [
                    {
                        "label": intent_label,
                        "confidence": float(intent_result_data['probabilities'].get(
                            # Find original label for confidence lookup
                            next((k for k, v in INTENT_MAPPING.items() if v == intent_label), intent_label),
                            0.0
                        )),
                        "source": "model",
                        "edited": False
                    }
                    for intent_label in summary_intents
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

            # 10. Update status to 'completed' and store analysis_summary
            await db.execute(
                update(FeedbackRecord)
                .where(FeedbackRecord.id == record_id)
                .values(
                    processing_status="completed",
                    analysis_summary=analysis_summary
                )
            )

            # 11. Commit all changes
            await db.commit()
            logger.info(f"✅ Successfully processed feedback: {record_id}")

            # 12. Broadcast analysis completed event via WebSocket
            publish_analysis_completed(
                feedback_id=record_id,
                source_type=feedback.source_type,
                analysis_summary=analysis_summary
            )

            return True

    except Exception as e:
        logger.error(f"Error processing feedback {record_id}: {e}", exc_info=True)

        # Update status to 'failed'
        source_type = "unknown"
        try:
            async with get_db_session() as db:
                # Get source_type for broadcast
                result = await db.execute(
                    select(FeedbackRecord.source_type).where(FeedbackRecord.id == record_id)
                )
                row = result.scalar_one_or_none()
                if row:
                    source_type = row

                await db.execute(
                    update(FeedbackRecord)
                    .where(FeedbackRecord.id == record_id)
                    .values(processing_status="failed")
                )
                await db.commit()
        except Exception as db_error:
            logger.error(f"Failed to update status to 'failed': {db_error}")

        # Broadcast analysis failed event via WebSocket
        publish_analysis_failed(
            feedback_id=record_id,
            source_type=source_type,
            error_message=str(e)
        )

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
