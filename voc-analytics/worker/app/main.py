"""
Worker application for processing messages from RabbitMQ
"""
import json
import logging
import signal
import sys
import time

import pika
from pika.adapters.blocking_connection import BlockingChannel
from pika.spec import Basic, BasicProperties

from app.config import settings

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


def process_message(message_data: dict) -> bool:
    """
    Process a message from the queue

    Args:
        message_data: Message data dictionary

    Returns:
        bool: True if processing successful, False otherwise
    """
    try:
        logger.info(f"Processing message: {message_data}")

        # Placeholder for actual processing logic
        # TODO: Implement actual message processing
        # - Parse message data
        # - Perform ML analysis
        # - Store results in database
        # - Publish results to ml_processing queue

        # Simulate processing time
        time.sleep(1)

        logger.info("Message processed successfully")
        return True

    except Exception as e:
        logger.error(f"Error processing message: {e}")
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
