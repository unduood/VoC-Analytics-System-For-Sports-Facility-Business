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

    def publish_message(
        self,
        queue_name: str,
        message: Dict[str, Any],
        persistent: bool = True
    ) -> bool:
        """
        Publish a message to a queue

        Args:
            queue_name: Name of the queue
            message: Message data (will be JSON serialized)
            persistent: Whether the message should persist on disk

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.channel:
            logger.error("Channel not initialized. Call connect() first.")
            return False

        try:
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

        except Exception as e:
            logger.error(f"Failed to publish message: {e}")
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
