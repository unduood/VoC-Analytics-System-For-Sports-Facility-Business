"""
RabbitMQ connection and message queue management
"""
import json
import logging
from typing import Optional, Any, Dict

import pika
from pika.adapters.blocking_connection import BlockingChannel

from app.config import settings

logger = logging.getLogger(__name__)


class RabbitMQManager:
    """RabbitMQ connection and queue management"""

    def __init__(self):
        self.connection: Optional[pika.BlockingConnection] = None
        self.channel: Optional[BlockingChannel] = None
        self.rabbitmq_url = settings.RABBITMQ_URL

    def connect(self) -> None:
        """Establish connection to RabbitMQ"""
        try:
            parameters = pika.URLParameters(self.rabbitmq_url)
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            logger.info("Successfully connected to RabbitMQ")

            # Declare queues
            self.declare_queue("data_ingestion")
            self.declare_queue("ml_processing")

        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise

    def declare_queue(
        self,
        queue_name: str,
        durable: bool = True,
        **kwargs
    ) -> None:
        """
        Declare a queue

        Args:
            queue_name: Name of the queue
            durable: Whether the queue should survive broker restart
            **kwargs: Additional queue arguments
        """
        if not self.channel:
            raise RuntimeError("Channel not initialized. Call connect() first.")

        self.channel.queue_declare(
            queue=queue_name,
            durable=durable,
            **kwargs
        )
        logger.info(f"Queue '{queue_name}' declared")

    def _ensure_connection(self) -> bool:
        """
        Ensure connection is alive, reconnect if needed

        Returns:
            bool: True if connection is ready, False otherwise
        """
        try:
            # Check if connection exists and is open
            if self.connection and self.connection.is_open and self.channel and self.channel.is_open:
                return True

            # Connection is dead, try to reconnect
            logger.warning("RabbitMQ connection lost, attempting to reconnect...")
            self.connect()
            return True

        except Exception as e:
            logger.error(f"Failed to ensure RabbitMQ connection: {e}")
            return False

    def publish_message(
        self,
        queue_name: str,
        message: Dict[str, Any],
        persistent: bool = True,
        max_retries: int = 3
    ) -> bool:
        """
        Publish a message to a queue with automatic retry

        Args:
            queue_name: Name of the queue
            message: Message data (will be JSON serialized)
            persistent: Whether the message should persist on disk
            max_retries: Maximum number of retry attempts

        Returns:
            bool: True if successful, False otherwise
        """
        for attempt in range(max_retries):
            try:
                # Ensure connection is alive
                if not self._ensure_connection():
                    logger.error("Cannot establish RabbitMQ connection")
                    continue

                properties = pika.BasicProperties(
                    delivery_mode=2 if persistent else 1,  # 2 = persistent
                    content_type="application/json"
                )

                self.channel.basic_publish(
                    exchange="",
                    routing_key=queue_name,
                    body=json.dumps(message),
                    properties=properties
                )
                logger.info(f"Message published to queue '{queue_name}'")
                return True

            except (pika.exceptions.AMQPConnectionError, pika.exceptions.AMQPChannelError) as e:
                logger.warning(f"Connection error on attempt {attempt + 1}/{max_retries}: {e}")
                # Force reconnection on next attempt
                self.connection = None
                self.channel = None
                if attempt < max_retries - 1:
                    continue

            except Exception as e:
                logger.error(f"Failed to publish message: {e}")
                return False

        logger.error(f"Failed to publish message after {max_retries} attempts")
        return False

    def close(self) -> None:
        """Close RabbitMQ connection"""
        try:
            if self.connection and not self.connection.is_closed:
                self.connection.close()
                logger.info("RabbitMQ connection closed")
        except Exception as e:
            logger.error(f"Error closing RabbitMQ connection: {e}")


# Global RabbitMQ manager instance
rabbitmq_manager = RabbitMQManager()
